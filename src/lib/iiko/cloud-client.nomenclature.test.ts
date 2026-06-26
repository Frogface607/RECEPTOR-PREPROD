import { afterEach, describe, expect, test, vi } from "vitest";
import { CloudIikoClient } from "./cloud-client";

const TOKEN = "tok-123";

function mockFetch(responses: unknown[]) {
  const queue = [...responses];
  const spy = vi.fn(async () => {
    const next = queue.shift();
    if (!next) throw new Error("unexpected fetch");
    return new Response(JSON.stringify(next), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  });
  vi.stubGlobal("fetch", spy);
}

afterEach(() => vi.unstubAllGlobals());

describe("CloudIikoClient nomenclature", () => {
  test("fetches Cloud nomenclature and searches normalized products", async () => {
    mockFetch([
      { token: TOKEN },
      {
        products: [
          {
            id: "p-1",
            name: "Burger",
            num: "1001",
            code: "11",
            measureUnit: "kg",
            purchasePrice: 1200,
            sizePrices: [{ price: { currentPrice: 690 } }],
          },
        ],
      },
    ]);

    const client = new CloudIikoClient({
      apiLogin: "test-login",
      organizationId: "org-1",
      today: "2026-05-29",
    });

    const results = await client.searchNomenclature("burger");
    expect(results).toHaveLength(1);
    expect(results[0]).toMatchObject({
      id: "p-1",
      article: "1001",
      quickDialCode: "11",
      unit: "g",
      price: 690,
      purchasePrice: 1200,
    });
  });
});
