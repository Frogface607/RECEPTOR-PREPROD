import { describe, expect, test, vi } from "vitest";
import { RmsIikoClient } from "./rms-client";

function mockFetch() {
  return mockFetchPayload({
    products: [
      {
        id: "r-1",
        name: "Tomato",
        num: "T-10",
        code: "99",
        unit: "kg",
        purchasePrice: 320,
      },
    ],
  });
}

function mockFetchPayload(payload: unknown) {
  const calls: string[] = [];
  const fetchImpl = vi.fn(async (input: RequestInfo | URL) => {
    const url = input.toString();
    calls.push(url);
    if (url.includes("/resto/api/auth")) {
      return new Response("session-key-1234567890", { status: 200 });
    }

    return new Response(
      JSON.stringify(payload),
      { status: 200, headers: { "Content-Type": "application/json" } },
    );
  });
  return { fetchImpl, calls };
}

describe("RmsIikoClient nomenclature", () => {
  test("fetches RMS products and keeps article separate from quick dial code", async () => {
    const { fetchImpl, calls } = mockFetch();
    const client = new RmsIikoClient({
      host: "sandbox.iiko.local",
      login: "Sergey",
      password: "secret",
      today: "2026-05-29",
      fetchImpl,
    });

    const products = await client.searchNomenclature("tomato");
    expect(products).toHaveLength(1);
    expect(products[0]).toMatchObject({
      id: "r-1",
      article: "T-10",
      quickDialCode: "99",
      unit: "g",
      purchasePrice: 320,
      purchasePricePerUnit: 0.32,
      pricePerKg: 320,
    });
    expect(calls.some((url) => url.includes("/resto/api/v2/entities/products/list"))).toBe(true);
  });

  test("probes RMS cost fields without exposing product rows", async () => {
    const { fetchImpl } = mockFetch();
    const client = new RmsIikoClient({
      host: "sandbox.iiko.local",
      login: "Sergey",
      password: "secret",
      today: "2026-05-29",
      fetchImpl,
    });

    const probe = await client.probeCostFields();

    expect(probe).toMatchObject({
      endpoint: "/resto/api/v2/entities/products/list",
      costStatus: "ready",
      rawRows: 1,
      normalizedProducts: 1,
      normalizedPriceRows: 1,
      productsWithCachedCost: 1,
      productsWithPurchasePrice: 1,
      productsWithTechCardPrice: 1,
    });
    expect(probe.costFieldCounts.purchasePrice).toBe(1);
    expect(probe.priceFieldCounts.purchasePrice).toBe(1);
    expect(probe.rawFieldCounts.name).toBe(1);
    expect(JSON.stringify(probe)).not.toContain("Tomato");
  });

  test("probes nested RMS cost fields", async () => {
    const { fetchImpl } = mockFetchPayload({
      products: [
        {
          id: "r-2",
          name: "Flour",
          unit: "kg",
          purchase: {
            pricePerUnit: 0.09,
          },
        },
      ],
    });
    const client = new RmsIikoClient({
      host: "sandbox.iiko.local",
      login: "Sergey",
      password: "secret",
      today: "2026-05-29",
      fetchImpl,
    });

    const probe = await client.probeCostFields();

    expect(probe).toMatchObject({
      costStatus: "ready",
      normalizedPriceRows: 1,
      productsWithCachedCost: 1,
      productsWithTechCardPrice: 1,
    });
    expect(probe.costFieldCounts["purchase.pricePerUnit"]).toBe(1);
    expect(probe.priceFieldCounts["purchase.pricePerUnit"]).toBe(1);
  });

  test("distinguishes menu prices from purchasing costs in RMS probe", async () => {
    const { fetchImpl } = mockFetchPayload({
      products: [
        {
          id: "menu-price-only",
          name: "Beer 0.5",
          unit: "pcs",
          price: 390,
          sizePrices: [{ price: { currentPrice: 390 } }],
        },
      ],
    });
    const client = new RmsIikoClient({
      host: "sandbox.iiko.local",
      login: "Sergey",
      password: "secret",
      today: "2026-05-29",
      fetchImpl,
    });

    const probe = await client.probeCostFields();

    expect(probe).toMatchObject({
      costStatus: "menu-prices-only",
      normalizedPriceRows: 0,
      productsWithTechCardPrice: 0,
    });
    expect(probe.costFieldCounts).toEqual({});
    expect(probe.menuPriceFieldCounts.price).toBe(1);
    expect(probe.menuPriceFieldCounts.sizePrices).toBe(1);
  });

  test("fetches normalized RMS prices separately from nomenclature", async () => {
    const { fetchImpl } = mockFetch();
    const client = new RmsIikoClient({
      host: "sandbox.iiko.local",
      login: "Sergey",
      password: "secret",
      today: "2026-05-29",
      fetchImpl,
    });

    await expect(client.fetchPrices()).resolves.toMatchObject([
      {
        skuId: "r-1",
        pricePerUnit: 0.32,
        pricePerKg: 320,
        rawField: "purchasePrice",
      },
    ]);
  });
});
