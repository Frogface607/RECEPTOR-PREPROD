import { describe, expect, test } from "vitest";
import {
  getRevenueTool,
  getDishStatisticsTool,
  getShiftsTool,
  comparePeriodsTool,
  getOwnerBriefTool,
  searchNomenclatureTool,
  AI_TOOLS,
} from "./tools";
import { MockIikoClient } from "@/lib/iiko/mock-client";

const ANCHOR = "2026-05-29";

function client() {
  return new MockIikoClient({ today: ANCHOR });
}

describe("AI_TOOLS catalog", () => {
  test("exposes the Phase-4 tools (get_olap_report deferred)", () => {
    const names = AI_TOOLS.map((t) => t.name);
    expect(names).toEqual([
      "get_revenue",
      "get_dish_statistics",
      "get_shifts",
      "compare_periods",
      "get_owner_brief",
      "get_nomenclature_search",
    ]);
  });

  test("each tool has a description and a JSON-schema input", () => {
    for (const t of AI_TOOLS) {
      expect(typeof t.description).toBe("string");
      expect(t.description.length).toBeGreaterThan(20);
      expect(t.input_schema.type).toBe("object");
      expect(t.input_schema.properties).toBeTruthy();
    }
  });
});

describe("getRevenueTool", () => {
  test("returns total + points for LAST_WEEK", async () => {
    const out = await getRevenueTool.handler(
      { period: "LAST_WEEK" },
      client(),
    );
    expect(out.revenue).toBeGreaterThan(0);
    expect(out.points.length).toBe(7);
  });

  test("includes a human-readable summary line", async () => {
    const out = await getRevenueTool.handler(
      { period: "LAST_WEEK" },
      client(),
    );
    expect(out.summary).toMatch(/₽/);
    expect(out.summary).toMatch(/7 дней/);
  });

  test("rejects invalid period via Zod", async () => {
    await expect(
      getRevenueTool.handler({ period: "WHENEVER" as never }, client()),
    ).rejects.toThrow();
  });
});

describe("getDishStatisticsTool", () => {
  test("respects topN (default 10)", async () => {
    const a = await getDishStatisticsTool.handler(
      { period: "LAST_WEEK" },
      client(),
    );
    const b = await getDishStatisticsTool.handler(
      { period: "LAST_WEEK", top_n: 3 },
      client(),
    );
    expect(a.dishes.length).toBeLessThanOrEqual(10);
    expect(b.dishes.length).toBeLessThanOrEqual(3);
  });

  test("summary names the top dish", async () => {
    const out = await getDishStatisticsTool.handler(
      { period: "LAST_MONTH" },
      client(),
    );
    expect(out.summary.toLowerCase()).toContain(
      out.dishes[0].dishName.toLowerCase(),
    );
  });
});

describe("getShiftsTool", () => {
  test("returns shifts with employee + revenue", async () => {
    const out = await getShiftsTool.handler(
      { period: "LAST_WEEK" },
      client(),
    );
    expect(out.shifts.length).toBe(7);
    expect(out.shifts[0].employee).toBeTruthy();
  });

  test("includes totals", async () => {
    const out = await getShiftsTool.handler(
      { period: "LAST_WEEK" },
      client(),
    );
    const sum = out.shifts.reduce((s, x) => s + x.revenue, 0);
    expect(out.totalRevenue).toBe(sum);
  });
});

describe("comparePeriodsTool", () => {
  test("returns revenue + delta for two periods", async () => {
    const out = await comparePeriodsTool.handler(
      { period_a: "LAST_WEEK", period_b: "CURRENT_WEEK" },
      client(),
    );
    expect(typeof out.revenue_a).toBe("number");
    expect(typeof out.revenue_b).toBe("number");
    expect(typeof out.delta_pct).toBe("number");
  });

  test("delta_pct is signed correctly", async () => {
    // Two periods where weekend-heavy one should be higher.
    const out = await comparePeriodsTool.handler(
      { period_a: "LAST_WEEK", period_b: "TODAY" },
      client(),
    );
    if (out.revenue_b > out.revenue_a) {
      expect(out.delta_pct).toBeGreaterThan(0);
    } else if (out.revenue_b < out.revenue_a) {
      expect(out.delta_pct).toBeLessThan(0);
    }
  });
});

describe("searchNomenclatureTool", () => {
  test("finds dishes by partial name", async () => {
    const out = await searchNomenclatureTool.handler(
      { query: "стейк" },
      client(),
    );
    expect(out.products.length).toBeGreaterThan(0);
    expect(
      out.products.every((p) => p.name.toLowerCase().includes("стейк")),
    ).toBe(true);
  });

  test("returns count in summary", async () => {
    const out = await searchNomenclatureTool.handler(
      { query: "коктейль" },
      client(),
    );
    expect(out.summary).toMatch(/\d+/);
  });

  test("rejects empty query via Zod", async () => {
    await expect(
      searchNomenclatureTool.handler({ query: "" }, client()),
    ).rejects.toThrow();
  });
});

describe("getOwnerBriefTool", () => {
  test("combines money, menu, categories and shifts", async () => {
    const out = await getOwnerBriefTool.handler(
      { period: "LAST_WEEK" },
      client(),
    );

    expect(out.revenue.total).toBeGreaterThan(0);
    expect(out.menu.topDish?.dishName).toBeTruthy();
    expect(out.menu.topCategory?.categoryName).toBeTruthy();
    expect(out.shifts.count).toBeGreaterThan(0);
    expect(out.risks.length).toBeGreaterThan(0);
    expect(out.signals.length).toBeGreaterThan(0);
    expect(out.signals.map((signal) => signal.title)).toContain(
      "Категорийная зависимость",
    );
    expect(out.actions.length).toBeGreaterThan(0);
  });
});
