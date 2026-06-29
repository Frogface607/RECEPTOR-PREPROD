import { afterEach, describe, expect, test, vi } from "vitest";
import { RmsIikoClient } from "./rms-client";

const HOST = "sandbox.iiko.local";
const LOGIN = "Sergey";
const PASSWORD = "secret";
const ANCHOR = "2026-05-31";
const SESSION = "session-key-1234567890";

type MockResponse = {
  status?: number;
  body: unknown;
  contentType?: string;
};

function mockFetch(responses: MockResponse[]) {
  const calls: { url: string; init?: RequestInit }[] = [];
  const queue = [...responses];
  const fetchImpl = vi.fn(
    async (input: RequestInfo | URL, init?: RequestInit) => {
      calls.push({ url: input.toString(), init });
      const next = queue.shift();
      if (!next) throw new Error(`unexpected fetch ${input.toString()}`);
      const body =
        typeof next.body === "string" ? next.body : JSON.stringify(next.body);
      return new Response(body, {
        status: next.status ?? 200,
        headers: {
          "Content-Type": next.contentType ?? "application/json",
        },
      });
    },
  );
  return { fetchImpl, calls };
}

function client(fetchImpl: typeof fetch) {
  return new RmsIikoClient({
    host: HOST,
    login: LOGIN,
    password: PASSWORD,
    today: ANCHOR,
    fetchImpl,
  });
}

afterEach(() => vi.restoreAllMocks());

describe("RmsIikoClient", () => {
  test("authenticates and parses revenue OLAP rows", async () => {
    const { fetchImpl, calls } = mockFetch([
      { body: SESSION, contentType: "text/plain" },
      {
        body: {
          data: [
            {
              "OpenDate.Typed": "2026-05-30",
              DishAmountInt: 457,
              DishDiscountSumInt: 172745,
              DishSumInt: 999202590,
              UniqOrderId: 120,
            },
            {
              "OpenDate.Typed": "2026-05-31",
              DishAmountInt: 922.73,
              DishDiscountSumInt: 299527,
              DishSumInt: 377773,
              UniqOrderId: 210,
            },
          ],
        },
      },
      {
        body: {
          data: [
            { DishName: "A", DishDiscountSumInt: 100 },
            { DishName: "B", DishDiscountSumInt: 200 },
          ],
        },
      },
    ]);

    const summary = await client(fetchImpl).getRevenueSummary({
      type: "CUSTOM",
      from: "2026-05-30",
      to: "2026-05-31",
    });

    expect(summary.revenue).toBe(472272);
    expect(summary.averageCheck).toBe(1431);
    expect(summary.itemsSold).toBe(1380);
    expect(summary.uniqueDishes).toBe(2);
    expect(summary.points).toEqual([
      { date: "2026-05-30", revenue: 172745 },
      { date: "2026-05-31", revenue: 299527 },
    ]);
    expect(calls[0].url).toContain("/resto/api/auth");
    const body = JSON.parse(calls[1].init?.body as string);
    expect(body.filters["OpenDate.Typed"].from).toBe("2026-05-30");
    expect(body.filters["OpenDate.Typed"].to).toBe("2026-05-31");
    expect(body.groupByRowFields).toEqual(["OpenDate.Typed"]);
    expect(body.aggregateFields).toContain("DishDiscountSumInt");
    expect(body.aggregateFields).toContain("UniqOrderId");
    expect(body.aggregateFields).not.toContain("DishSumInt");
  });

  test("parses and sorts dish statistics", async () => {
    const { fetchImpl } = mockFetch([
      { body: SESSION, contentType: "text/plain" },
      {
        body: {
          data: [
            {
              DishName: "A",
              DishGroup: "Beer",
              DishDiscountSumInt: 100,
              DishAmountInt: 2,
            },
            {
              DishName: "B",
              DishGroup: null,
              DishDiscountSumInt: 500,
              DishAmountInt: 3.4,
            },
          ],
        },
      },
    ]);

    const dishes = await client(fetchImpl).getDishStatistics(
      { type: "TODAY" },
      2,
    );
    expect(dishes[0]).toMatchObject({
      dishName: "B",
      dishGroup: "—",
      dishAmountInt: 3,
      dishSumInt: 500,
    });
  });

  test("uses RMS session fields for cashier shift breakdown", async () => {
    const { fetchImpl, calls } = mockFetch([
      { body: SESSION, contentType: "text/plain" },
      {
        body: {
          data: [
            {
              "Session.Id": "session-1",
              "SessionOpenDate.Typed": "2026-05-30T12:00:00",
              "SessionCloseDate.Typed": "2026-05-30T23:00:00",
              CashierName: "Мария",
              DishAmountInt: 310,
              DishDiscountSumInt: 145000,
            },
          ],
        },
      },
    ]);

    const shifts = await client(fetchImpl).getShifts({
      type: "CUSTOM",
      from: "2026-05-30",
      to: "2026-05-30",
    });

    expect(shifts).toEqual([
      {
        shiftId: "rms-shift-session-1",
        openTime: "2026-05-30T12:00:00",
        closeTime: "2026-05-30T23:00:00",
        revenue: 145000,
        items: 310,
        employee: "Мария",
      },
    ]);
    const body = JSON.parse(calls[1].init?.body as string);
    expect(body.groupByRowFields).toEqual([
      "Session.Id",
      "SessionOpenDate.Typed",
      "SessionCloseDate.Typed",
      "CashierName",
    ]);
  });

  test("falls back to OpenDate shift rows when session fields fail", async () => {
    const { fetchImpl, calls } = mockFetch([
      { body: SESSION, contentType: "text/plain" },
      { status: 400, body: { error: "Unknown field Session.Id" } },
      { status: 400, body: { error: "Unknown field Session.Id" } },
      { status: 400, body: { error: "Unknown field Session.Id" } },
      {
        status: 400,
        body: { error: "Unknown field CashSessionOpenDate.Typed" },
      },
      { status: 400, body: { error: "Unknown field SessionDate.Typed" } },
      {
        body: {
          data: [
            {
              "OpenDate.Typed": "2026-05-30",
              DishAmountInt: 310,
              DishDiscountSumInt: 145000,
            },
          ],
        },
      },
    ]);

    const shifts = await client(fetchImpl).getShifts({
      type: "CUSTOM",
      from: "2026-05-30",
      to: "2026-05-30",
    });

    expect(shifts[0]).toMatchObject({
      shiftId: "rms-shift-2026-05-30-0",
      openTime: "2026-05-30T00:00:00",
      revenue: 145000,
      employee: "Смена",
    });
    const fallbackBody = JSON.parse(calls.at(-1)?.init?.body as string);
    expect(fallbackBody.groupByRowFields).toEqual(["OpenDate.Typed"]);
  });

  test("falls back to default organization when RMS org endpoints are unavailable", async () => {
    const { fetchImpl } = mockFetch([
      { body: SESSION, contentType: "text/plain" },
      { status: 404, body: "not found", contentType: "text/plain" },
      { status: 404, body: "not found", contentType: "text/plain" },
      { status: 404, body: "not found", contentType: "text/plain" },
      { status: 404, body: "not found", contentType: "text/plain" },
    ]);

    await expect(client(fetchImpl).listOrganizations()).resolves.toEqual([
      { id: "default", name: HOST },
    ]);
  });

  test("probes RMS assembly charts for tech-card diagnostics", async () => {
    const { fetchImpl, calls } = mockFetch([
      { body: SESSION, contentType: "text/plain" },
      {
        body: {
          assemblyCharts: [
            {
              id: "chart-1",
              product: { id: "dish-burger", name: "Burger" },
              items: [
                {
                  product: {
                    id: "beef",
                    name: "Beef",
                    num: "B-10",
                    unit: "kg",
                  },
                  amount: 120,
                },
                {
                  ingredientId: "bun",
                  ingredientName: "Bun",
                  quantity: 1,
                  measureUnit: { name: "pcs" },
                },
              ],
            },
            {
              id: "chart-2",
              name: "Sauce",
              items: [],
            },
          ],
          preparedCharts: [{ id: "prep-1" }],
        },
      },
    ]);

    const probe = await client(fetchImpl).probeAssemblyCharts();

    expect(probe).toMatchObject({
      endpoint: "/resto/api/v2/assemblyCharts/getAll",
      status: "ready",
      dateFrom: "2025-05-31",
      dateTo: "2027-05-31",
      assemblyCharts: 2,
      preparedCharts: 1,
      chartsWithItems: 1,
      totalItems: 2,
      normalizedCharts: 2,
      chartsWithDishLink: 1,
      ingredientRows: 2,
      ingredientRowsWithProductLink: 2,
      ingredientRowsWithAmount: 2,
      ingredientRowsWithUnit: 2,
    });
    expect(probe.rawFieldCounts.id).toBe(2);
    expect(probe.rawFieldCounts.items).toBe(1);
    expect(probe.ingredientFieldCounts.product).toBe(1);
    expect(probe.ingredientFieldCounts.quantity).toBe(1);
    expect(calls[1].url).toContain("/resto/api/v2/assemblyCharts/getAll");
    expect(calls[1].url).toContain("dateFrom=2025-05-31");
    expect(calls[1].url).toContain("dateTo=2027-05-31");
    expect(calls[1].url).toContain("includePreparedCharts=false");
  });

  test("normalizes alternate RMS assembly chart row shapes", async () => {
    const { fetchImpl } = mockFetch([
      { body: SESSION, contentType: "text/plain" },
      {
        body: [
          {
            chartId: "chart-3",
            dishId: "dish-salad",
            dishName: "Salad",
            rows: [
              {
                nomenclature: {
                  id: "tomato",
                  name: "Tomato",
                  article: "T-1",
                  unit: "kg",
                },
                netto: "0,2",
              },
            ],
          },
        ],
      },
    ]);

    await expect(
      client(fetchImpl).probeAssemblyCharts(),
    ).resolves.toMatchObject({
      status: "ready",
      assemblyCharts: 1,
      normalizedCharts: 1,
      chartsWithDishLink: 1,
      chartsWithItems: 1,
      ingredientRows: 1,
      ingredientRowsWithProductLink: 1,
      ingredientRowsWithAmount: 1,
      ingredientRowsWithUnit: 1,
    });
  });

  test("fetches normalized RMS assembly charts for BI", async () => {
    const { fetchImpl } = mockFetch([
      { body: SESSION, contentType: "text/plain" },
      {
        body: {
          assemblyCharts: [
            {
              assemblyChartId: "chart-4",
              productId: "dish-pasta",
              productName: "Pasta",
              ingredients: [
                {
                  productId: "flour",
                  productName: "Flour",
                  amount: 0.12,
                  unit: "kg",
                },
              ],
            },
            {
              assemblyChartId: "chart-flat",
              "product.id": "dish-flat",
              "product.name": "Flat dish",
              ingredients: [
                {
                  "product.id": "flat-flour",
                  "product.name": "Flat flour",
                  "product.num": "F-10",
                  "product.unit.name": "kg",
                  nettoQty: "0,25",
                },
              ],
            },
          ],
        },
      },
    ]);

    await expect(client(fetchImpl).fetchAssemblyCharts()).resolves.toEqual([
      {
        id: "chart-4",
        productId: "dish-pasta",
        productName: "Pasta",
        name: "Pasta",
        items: [
          {
            productId: "flour",
            productName: "Flour",
            article: undefined,
            amount: 0.12,
            unit: "kg",
            rawField: "ingredients",
          },
        ],
      },
      {
        id: "chart-flat",
        productId: "dish-flat",
        productName: "Flat dish",
        name: "Flat dish",
        items: [
          {
            productId: "flat-flour",
            productName: "Flat flour",
            article: "F-10",
            amount: 0.25,
            unit: "kg",
            rawField: "ingredients",
          },
        ],
      },
    ]);
  });

  test("reports forbidden RMS assembly charts access without throwing", async () => {
    const { fetchImpl } = mockFetch([
      { body: SESSION, contentType: "text/plain" },
      { status: 403, body: "forbidden", contentType: "text/plain" },
    ]);

    await expect(
      client(fetchImpl).probeAssemblyCharts(),
    ).resolves.toMatchObject({
      endpoint: "/resto/api/v2/assemblyCharts/getAll",
      status: "forbidden",
      assemblyCharts: 0,
      error: "HTTP 403: forbidden",
    });
  });
});
