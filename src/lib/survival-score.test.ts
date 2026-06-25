import { describe, expect, test } from "vitest";
import { buildSurvivalBrief } from "./survival-score";
import type { DailyBrief } from "./brief/daily-brief";
import type { CategoryStat, DishStat } from "./iiko/models";

const baseBrief: DailyBrief = {
  period: "LAST_WEEK",
  comparisonPeriod: "LAST_MONTH",
  headline: "Выручка просела",
  revenue: {
    current: 800_000,
    previous: 1_200_000,
    deltaPct: -33.3,
    comparisonAvailable: true,
  },
  highlights: [],
  signals: [],
  actions: [],
};

const concentratedCategories: CategoryStat[] = [
  { categoryName: "Горячая кухня", dishSumInt: 520_000 },
  { categoryName: "Барная карта", dishSumInt: 180_000 },
  { categoryName: "Десерты", dishSumInt: 100_000 },
];

const riskyDishes: DishStat[] = [
  {
    dishName: "Стейк",
    dishGroup: "Горячая кухня",
    dishAmountInt: 80,
    dishSumInt: 260_000,
  },
  {
    dishName: "Лимонад",
    dishGroup: "Безалкогольные напитки",
    dishAmountInt: 240,
    dishSumInt: 95_000,
  },
  {
    dishName: "Паста",
    dishGroup: "Горячая кухня",
    dishAmountInt: 55,
    dishSumInt: 90_000,
  },
  {
    dishName: "Салат",
    dishGroup: "Закуски",
    dishAmountInt: 20,
    dishSumInt: 25_000,
  },
];

describe("buildSurvivalBrief", () => {
  test("turns revenue collapse and menu concentration into a critical owner brief", () => {
    const brief = buildSurvivalBrief({
      dailyBrief: baseBrief,
      dishes: riskyDishes,
      categories: concentratedCategories,
    });

    expect(brief.status).toBe("critical");
    expect(brief.score).toBeGreaterThanOrEqual(70);
    expect(brief.factors.map((factor) => factor.id)).toContain("revenue-drop");
    expect(brief.factors.map((factor) => factor.id)).toContain(
      "category-concentration",
    );
    expect(brief.actions[0]).toContain("сегодня");
    expect(brief.taskDrafts[0]).toMatchObject({
      priority: "high",
      roleId: "venue_manager",
    });
  });

  test("keeps missing margin data explicit instead of pretending profit is known", () => {
    const brief = buildSurvivalBrief({
      dailyBrief: baseBrief,
      dishes: riskyDishes,
      categories: concentratedCategories,
    });

    expect(brief.missingData).toContain("себестоимость");
    expect(brief.questions.some((q) => q.role === "chef")).toBe(true);
  });

  test("marks a stable week as watch when margin layer is still absent", () => {
    const brief = buildSurvivalBrief({
      dailyBrief: {
        ...baseBrief,
        revenue: {
          current: 1_200_000,
          previous: 1_100_000,
          deltaPct: 9.1,
          comparisonAvailable: true,
        },
      },
      dishes: [
        { dishName: "Блюдо A", dishGroup: "Кухня", dishAmountInt: 20, dishSumInt: 90_000 },
        { dishName: "Блюдо B", dishGroup: "Бар", dishAmountInt: 24, dishSumInt: 82_000 },
        { dishName: "Блюдо C", dishGroup: "Закуски", dishAmountInt: 18, dishSumInt: 75_000 },
      ],
      categories: [
        { categoryName: "Кухня", dishSumInt: 400_000 },
        { categoryName: "Бар", dishSumInt: 390_000 },
        { categoryName: "Закуски", dishSumInt: 410_000 },
      ],
    });

    expect(brief.status).toBe("watch");
    expect(brief.score).toBeLessThan(35);
    expect(brief.factors.map((factor) => factor.id)).toContain("margin-unknown");
  });

  test("adds data coverage as an operational factor and task", () => {
    const brief = buildSurvivalBrief({
      dailyBrief: {
        ...baseBrief,
        revenue: {
          current: 800_000,
          previous: 0,
          deltaPct: 0,
          comparisonAvailable: false,
        },
      },
      dishes: riskyDishes,
      categories: concentratedCategories,
      dataQuality: {
        status: "risk",
        requestedDays: 365,
        activeDays: 75,
        missingDays: 290,
        coveragePct: 21,
        firstDataDate: "2025-10-17",
        lastDataDate: "2025-12-30",
        basis: "Выручка после скидок, по продажам iiko",
        summary: "75 из 365 дней с продажами (21%)",
        warnings: ["В периоде есть продажи только за 75 из 365 дней."],
      },
    });

    expect(brief.factors.map((factor) => factor.id)).toContain("data-coverage");
    expect(brief.factors.map((factor) => factor.id)).toContain(
      "comparison-missing",
    );
    expect(brief.taskDrafts[0]).toMatchObject({
      roleId: "venue_manager",
      priority: "high",
      dueLabel: "сегодня",
    });
  });
});
