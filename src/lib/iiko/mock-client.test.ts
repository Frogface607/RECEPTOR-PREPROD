import { describe, expect, test, beforeAll } from "vitest";
import { MockIikoClient } from "./mock-client";
import {
  RevenueSummarySchema,
  DishStatSchema,
  CategoryStatSchema,
  ShiftStatSchema,
  ProductSchema,
  type Period,
} from "./models";
import { SANDBOX_VENUE } from "@/lib/mock/sandbox-fixtures";

/**
 * Mock client is deterministic — repeated calls with the same period must
 * return the same numbers. This is what makes UI screenshots stable for
 * sandbox views and keeps tests independent of the wall-clock.
 *
 * Anchor date for the mock "today" is 2026-05-29 (the day the spec was written).
 */
const ANCHOR = "2026-05-29";

let client: MockIikoClient;

beforeAll(() => {
  client = new MockIikoClient({ today: ANCHOR });
});

describe("MockIikoClient.getRevenueSummary", () => {
  test("LAST_WEEK returns 7 daily points", async () => {
    const period: Period = { type: "LAST_WEEK" };
    const summary = await client.getRevenueSummary(period);
    expect(summary.points).toHaveLength(7);
  });

  test("TODAY returns exactly one point for the anchor date", async () => {
    const summary = await client.getRevenueSummary({ type: "TODAY" });
    expect(summary.points).toHaveLength(1);
    expect(summary.points[0].date).toBe(ANCHOR);
  });

  test("CURRENT_MONTH returns one point per day so far", async () => {
    // anchor is 2026-05-29 → days 1..29 = 29 points
    const summary = await client.getRevenueSummary({ type: "CURRENT_MONTH" });
    expect(summary.points.length).toBeGreaterThanOrEqual(28);
    expect(summary.points.length).toBeLessThanOrEqual(31);
  });

  test("output validates against RevenueSummarySchema", async () => {
    const summary = await client.getRevenueSummary({ type: "LAST_WEEK" });
    expect(() => RevenueSummarySchema.parse(summary)).not.toThrow();
  });

  test("daily revenue stays inside plausible range (₽80k–₽400k)", async () => {
    const summary = await client.getRevenueSummary({ type: "LAST_MONTH" });
    for (const p of summary.points) {
      expect(p.revenue).toBeGreaterThanOrEqual(80_000);
      expect(p.revenue).toBeLessThanOrEqual(400_000);
    }
  });

  test("weekend days carry more revenue than weekdays on average", async () => {
    const summary = await client.getRevenueSummary({ type: "LAST_MONTH" });
    const isWeekend = (d: string) => {
      const day = new Date(d + "T00:00:00").getUTCDay(); // 0 = Sun, 6 = Sat
      return day === 0 || day === 6;
    };
    const weekend = summary.points.filter((p) => isWeekend(p.date));
    const weekday = summary.points.filter((p) => !isWeekend(p.date));
    const avg = (arr: typeof summary.points) =>
      arr.reduce((s, p) => s + p.revenue, 0) / arr.length;
    expect(avg(weekend)).toBeGreaterThan(avg(weekday));
  });

  test("summary totals are consistent with points sum", async () => {
    const summary = await client.getRevenueSummary({ type: "LAST_WEEK" });
    const sum = summary.points.reduce((s, p) => s + p.revenue, 0);
    expect(summary.revenue).toBe(sum);
  });

  test("average check is plausible (₽800–₽3500)", async () => {
    const summary = await client.getRevenueSummary({ type: "LAST_WEEK" });
    expect(summary.averageCheck).toBeGreaterThanOrEqual(800);
    expect(summary.averageCheck).toBeLessThanOrEqual(3500);
  });

  test("is deterministic — same period → same totals", async () => {
    const a = await client.getRevenueSummary({ type: "LAST_WEEK" });
    const b = await client.getRevenueSummary({ type: "LAST_WEEK" });
    expect(a.revenue).toBe(b.revenue);
    expect(a.points).toEqual(b.points);
  });
});

describe("MockIikoClient.getDishStatistics", () => {
  test("returns DishStat[] sorted by dishSumInt descending", async () => {
    const dishes = await client.getDishStatistics({ type: "LAST_WEEK" }, 10);
    expect(dishes.length).toBeGreaterThan(0);
    for (let i = 1; i < dishes.length; i++) {
      expect(dishes[i].dishSumInt).toBeLessThanOrEqual(dishes[i - 1].dishSumInt);
    }
  });

  test("respects topN limit", async () => {
    const dishes = await client.getDishStatistics({ type: "LAST_WEEK" }, 5);
    expect(dishes.length).toBeLessThanOrEqual(5);
  });

  test("each row validates against DishStatSchema", async () => {
    const dishes = await client.getDishStatistics({ type: "LAST_WEEK" }, 10);
    for (const d of dishes) {
      expect(() => DishStatSchema.parse(d)).not.toThrow();
    }
  });

  test("signature hot dish appears in top dishes", async () => {
    const dishes = await client.getDishStatistics({ type: "LAST_MONTH" }, 20);
    expect(dishes.some((d) => d.dishName === "Стейк из говядины")).toBe(true);
  });
});

describe("MockIikoClient.getCategoryStatistics", () => {
  test("returns at least the 5 sandbox categories", async () => {
    const cats = await client.getCategoryStatistics({ type: "LAST_WEEK" });
    const names = new Set(cats.map((c) => c.categoryName));
    expect(names.has("Горячая кухня")).toBe(true);
    expect(names.has("Закуски и салаты")).toBe(true);
    expect(names.has("Барная карта")).toBe(true);
    expect(names.has("Десерты")).toBe(true);
    expect(names.has("Безалкогольные напитки")).toBe(true);
  });

  test("each row validates against CategoryStatSchema", async () => {
    const cats = await client.getCategoryStatistics({ type: "LAST_WEEK" });
    for (const c of cats) {
      expect(() => CategoryStatSchema.parse(c)).not.toThrow();
    }
  });

  test("category sums add up close to total revenue (±1%)", async () => {
    const period: Period = { type: "LAST_WEEK" };
    const summary = await client.getRevenueSummary(period);
    const cats = await client.getCategoryStatistics(period);
    const sum = cats.reduce((s, c) => s + c.dishSumInt, 0);
    const delta = Math.abs(sum - summary.revenue) / summary.revenue;
    expect(delta).toBeLessThanOrEqual(0.01);
  });
});

describe("MockIikoClient.getShifts", () => {
  test("returns one shift per day in the period", async () => {
    const shifts = await client.getShifts({ type: "LAST_WEEK" });
    expect(shifts).toHaveLength(7);
  });

  test("each row validates against ShiftStatSchema", async () => {
    const shifts = await client.getShifts({ type: "LAST_WEEK" });
    for (const s of shifts) {
      expect(() => ShiftStatSchema.parse(s)).not.toThrow();
    }
  });

  test("shift open is in the evening (18:00 local)", async () => {
    const shifts = await client.getShifts({ type: "LAST_WEEK" });
    for (const s of shifts) {
      expect(s.openTime).toMatch(/T18:00:00$/);
    }
  });
});

describe("MockIikoClient.searchNomenclature", () => {
  test("case-insensitive substring match on product name", async () => {
    const results = await client.searchNomenclature("стейк");
    expect(results.length).toBeGreaterThan(0);
    expect(results.every((p) => p.name.toLowerCase().includes("стейк"))).toBe(true);
  });

  test("empty query returns empty list", async () => {
    const results = await client.searchNomenclature("");
    expect(results).toEqual([]);
  });

  test("each result validates against ProductSchema", async () => {
    const results = await client.searchNomenclature("чай");
    for (const r of results) {
      expect(() => ProductSchema.parse(r)).not.toThrow();
    }
  });
});

describe("SANDBOX_VENUE fixture", () => {
  test("has expected anchoring details", () => {
    expect(SANDBOX_VENUE.name).toBe("Тестовое заведение");
    expect(SANDBOX_VENUE.timezone).toBe("Asia/Irkutsk");
  });
});
