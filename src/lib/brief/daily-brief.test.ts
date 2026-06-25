import { describe, expect, test } from "vitest";
import { buildDailyBrief, renderDailyBriefText } from "./daily-brief";
import { MockIikoClient } from "@/lib/iiko/mock-client";
import type { IikoClient } from "@/lib/iiko/types";
import type { Period, RevenueSummary } from "@/lib/iiko/models";

describe("buildDailyBrief", () => {
  test("builds a deterministic owner brief from iiko data", async () => {
    const brief = await buildDailyBrief(
      new MockIikoClient({ today: "2026-05-29" }),
      "LAST_WEEK",
    );

    expect(brief.period).toBe("LAST_WEEK");
    expect(brief.comparisonPeriod).toBe("LAST_MONTH");
    expect(brief.headline).toMatch(/Выручка/);
    expect(brief.highlights).toHaveLength(3);
    expect(brief.signals.length).toBeGreaterThanOrEqual(2);
    expect(brief.signals.map((s) => s.title)).toContain("Разброс по дням");
    expect(brief.actions).toHaveLength(3);
    expect(brief.revenue.current).toBeGreaterThan(0);
  });

  test("renders a plain-text brief for delivery channels", async () => {
    const brief = await buildDailyBrief(
      new MockIikoClient({ today: "2026-05-29" }),
      "YESTERDAY",
    );

    const text = renderDailyBriefText(brief, {
      venueName: "Тестовый ресторан",
      generatedAt: new Date("2026-05-30T06:00:00.000Z"),
    });

    expect(text).toContain("Ежедневный бриф Receptor: Тестовый ресторан");
    expect(text).toContain("Главное:");
    expect(text).toContain("Диагностика:");
    expect(text).toContain("Что сделать сегодня:");
    expect(text).toContain(brief.headline);
  });

  test("uses custom date ranges for owner brief data", async () => {
    const brief = await buildDailyBrief(
      new MockIikoClient({ today: "2026-05-29" }),
      { type: "CUSTOM", from: "2025-01-01", to: "2025-12-31" },
    );

    expect(brief.period).toBe("CUSTOM");
    expect(brief.comparisonPeriod).toBe("CUSTOM");
    expect(brief.signals.length).toBeGreaterThan(0);
    expect(brief.revenue.current).toBeGreaterThan(0);
  });

  test("does not report fake growth when comparison has no revenue", async () => {
    const current: RevenueSummary = {
      revenue: 120000,
      averageCheck: 1500,
      itemsSold: 80,
      uniqueDishes: 3,
      points: [{ date: "2026-05-01", revenue: 120000 }],
    };
    const previous: RevenueSummary = {
      revenue: 0,
      averageCheck: 0,
      itemsSold: 0,
      uniqueDishes: 0,
      points: [],
    };
    const client: IikoClient = {
      getRevenueSummary: async (period: Period) =>
        period.type === "CUSTOM" && period.from === "2026-05-01"
          ? current
          : previous,
      getDishStatistics: async () => [
        {
          dishName: "Паста",
          dishGroup: "Кухня",
          dishAmountInt: 10,
          dishSumInt: 50000,
        },
      ],
      getCategoryStatistics: async () => [
        { categoryName: "Кухня", dishSumInt: 120000 },
      ],
      getShifts: async () => [],
      searchNomenclature: async () => [],
    };

    const brief = await buildDailyBrief(client, {
      type: "CUSTOM",
      from: "2026-05-01",
      to: "2026-05-01",
    });

    expect(brief.revenue.comparisonAvailable).toBe(false);
    expect(brief.revenue.deltaPct).toBe(0);
    expect(brief.headline.replace(/\u00a0/g, " ")).toBe(
      "Выручка за выбранный период: 120 000 ₽.",
    );
    expect(brief.highlights[0]).toContain("нет базы сравнения");
    expect(brief.actions[0]).toContain("стартовую базу");
  });
});
