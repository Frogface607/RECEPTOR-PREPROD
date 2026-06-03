import { describe, expect, test, afterEach, vi } from "vitest";
import { CloudIikoClient } from "./cloud-client";
import {
  DishStatSchema,
  CategoryStatSchema,
  ShiftStatSchema,
} from "./models";

/**
 * OLAP method ports for the real Cloud client. Verified against mocked fetch
 * (no live key in CI). When Edison apiLogin arrives, only the real response
 * shape needs a 30-min sanity check — the wiring is locked here.
 */

const API_LOGIN = "test-login";
const ORG = "edison-org";
const ANCHOR = "2026-05-29";
const TOKEN = "tok-123";

type Resp = { data: unknown; status?: number };

function mockFetch(responses: Resp[]) {
  const calls: { url: string; init?: RequestInit }[] = [];
  const queue = [...responses];
  const spy = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    calls.push({ url: input.toString(), init });
    const next = queue.shift();
    if (!next) throw new Error(`unexpected fetch ${input}`);
    return new Response(JSON.stringify(next.data), {
      status: next.status ?? 200,
      headers: { "Content-Type": "application/json" },
    });
  });
  vi.stubGlobal("fetch", spy);
  return { calls };
}

afterEach(() => vi.unstubAllGlobals());

function client() {
  return new CloudIikoClient({
    apiLogin: API_LOGIN,
    organizationId: ORG,
    today: ANCHOR,
  });
}

describe("CloudIikoClient.getDishStatistics", () => {
  test("parses OLAP rows, sorts by revenue desc, applies topN", async () => {
    mockFetch([
      { data: { token: TOKEN } },
      {
        data: {
          data: [
            { DishName: "Бургер Нечто", DishGroup: "Бургеры", DishDiscountSumInt: 165600, DishAmountInt: 240 },
            { DishName: "Edison Sour", DishGroup: "Авторские коктейли", DishDiscountSumInt: 98400, DishAmountInt: 167 },
            { DishName: "Крафт IPA 0.5л", DishGroup: "Крафтовое пиво", DishDiscountSumInt: 142100, DishAmountInt: 374 },
          ],
        },
      },
    ]);

    const dishes = await client().getDishStatistics({ type: "LAST_WEEK" }, 2);
    expect(dishes).toHaveLength(2);
    expect(dishes[0].dishName).toBe("Бургер Нечто");
    expect(dishes[1].dishName).toBe("Крафт IPA 0.5л");
    for (const d of dishes) {
      expect(() => DishStatSchema.parse(d)).not.toThrow();
    }
  });

  test("sends DishName+DishGroup groupBy in OLAP body", async () => {
    const { calls } = mockFetch([
      { data: { token: TOKEN } },
      { data: { data: [] } },
    ]);
    await client().getDishStatistics({ type: "LAST_WEEK" }, 10);
    const body = JSON.parse(calls[1].init?.body as string);
    expect(body.groupByRowFields).toContain("DishName");
    expect(body.groupByRowFields).toContain("DishGroup");
  });
});

describe("CloudIikoClient.getCategoryStatistics", () => {
  test("parses category OLAP rows", async () => {
    mockFetch([
      { data: { token: TOKEN } },
      {
        data: {
          data: [
            { DishGroup: "Бургеры", DishDiscountSumInt: 1200000 },
            { DishGroup: "Крафтовое пиво", DishDiscountSumInt: 850000 },
          ],
        },
      },
    ]);
    const cats = await client().getCategoryStatistics({ type: "LAST_WEEK" });
    expect(cats).toHaveLength(2);
    expect(cats[0].categoryName).toBe("Бургеры");
    for (const c of cats) {
      expect(() => CategoryStatSchema.parse(c)).not.toThrow();
    }
  });
});

describe("CloudIikoClient.getShifts", () => {
  test("derives one day-shift per OLAP OpenDate row", async () => {
    mockFetch([
      { data: { token: TOKEN } },
      {
        data: {
          data: [
            { OpenDate: "2026-05-28", DishDiscountSumInt: 195000, DishAmountInt: 110 },
            { OpenDate: "2026-05-29", DishDiscountSumInt: 215000, DishAmountInt: 126 },
          ],
        },
      },
    ]);
    const shifts = await client().getShifts({ type: "LAST_WEEK" });
    expect(shifts).toHaveLength(2);
    expect(shifts[0].revenue).toBe(195000);
    for (const s of shifts) {
      expect(() => ShiftStatSchema.parse(s)).not.toThrow();
    }
  });
});

describe("CloudIikoClient.searchNomenclature (graceful on Cloud)", () => {
  test("returns empty list rather than throwing (deferred, documented)", async () => {
    const results = await client().searchNomenclature("бургер");
    expect(results).toEqual([]);
  });
});
