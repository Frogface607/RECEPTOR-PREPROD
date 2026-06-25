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
  const fetchImpl = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
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
  });
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
            { DishName: "A", DishGroup: "Beer", DishDiscountSumInt: 100, DishAmountInt: 2 },
            { DishName: "B", DishGroup: null, DishDiscountSumInt: 500, DishAmountInt: 3.4 },
          ],
        },
      },
    ]);

    const dishes = await client(fetchImpl).getDishStatistics({ type: "TODAY" }, 2);
    expect(dishes[0]).toMatchObject({
      dishName: "B",
      dishGroup: "—",
      dishAmountInt: 3,
      dishSumInt: 500,
    });
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
});
