import { describe, expect, test } from "vitest";
import type { DailyBrief } from "./brief/daily-brief";
import type { RevenueDataQuality } from "./iiko/data-quality";
import type {
  CategoryStat,
  DishStat,
  RevenueSummary,
  ShiftStat,
} from "./iiko/models";
import { buildMenuMarginReadiness } from "./menu-margin-readiness";
import { buildOwnerReview } from "./owner-review";
import { buildLaborBi } from "./team/labor-bi";

const summary: RevenueSummary = {
  revenue: 100000,
  averageCheck: 2500,
  itemsSold: 120,
  uniqueDishes: 12,
  points: [{ date: "2026-06-26", revenue: 100000 }],
};

const dishes: DishStat[] = [
  {
    dishName: "Паста",
    dishGroup: "Кухня",
    dishAmountInt: 20,
    dishSumInt: 20000,
  },
];

const categories: CategoryStat[] = [
  {
    categoryName: "Кухня",
    dishSumInt: 20000,
  },
  {
    categoryName: "Бар",
    dishSumInt: 80000,
  },
];

const shifts: ShiftStat[] = [
  {
    shiftId: "shift-expensive",
    openTime: "2026-06-26T12:00:00",
    closeTime: "2026-06-26T22:00:00",
    revenue: 100000,
    items: 120,
    employee: "Смена",
  },
];

const brief: DailyBrief = {
  period: "CUSTOM",
  comparisonPeriod: "CUSTOM",
  headline: "Период ниже базы",
  revenue: {
    current: 100000,
    previous: 110000,
    deltaPct: -9.1,
    comparisonAvailable: true,
  },
  highlights: [],
  signals: [],
  actions: [],
};

const quality: RevenueDataQuality = {
  status: "ok",
  requestedDays: 1,
  activeDays: 1,
  missingDays: 0,
  coveragePct: 100,
  firstDataDate: "2026-06-26",
  lastDataDate: "2026-06-26",
  basis: "Выручка после скидок, по продажам iiko",
  summary: "Покрыт 1 из 1 дней",
  warnings: [],
};

describe("buildOwnerReview", () => {
  test("adds labor evidence and a task when payroll is expensive", () => {
    const labor = buildLaborBi({
      shifts: [
        {
          ...shifts[0],
          workers: [
            {
              name: "Команда зала",
              hours: 10,
              shiftPay: 35000,
              sales: 100000,
            },
          ],
        },
      ],
    });
    const margin = buildMenuMarginReadiness({
      dishes,
      products: [],
    });

    const review = buildOwnerReview({
      summary,
      dishes,
      categories,
      shifts,
      brief,
      dataQuality: quality,
      dataMode: "live",
      labor,
      margin,
    });

    expect(review.evidence).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          label: "ФОТ",
          value: "35%",
          tone: "risk",
        }),
        expect.objectContaining({
          label: "Маржа",
          value: "0%",
          tone: "risk",
        }),
      ]),
    );
    expect(review.hypotheses[0]).toMatchObject({
      title: "ФОТ выше целевой нормы",
      tone: "risk",
      role: "manager",
    });
    expect(review.tasks[0]).toMatchObject({
      title: "Проверьте состав смены, часы и фактическую загрузку зала.",
      priority: "high",
      roleId: "venue_manager",
    });
    expect(review.hypotheses).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          title: "ФОТ давит, а маржа не доказана",
          why: expect.stringContaining("Паста"),
          tone: "risk",
          role: "owner",
        }),
      ]),
    );
  });

  test("names first labor blocker in owner evidence", () => {
    const labor = buildLaborBi({
      shifts: [
        {
          shiftId: "shift-cashier",
          openTime: "2026-06-26T18:00:00",
          closeTime: "2026-06-27T02:00:00",
          revenue: 80000,
          items: 180,
          employee: "Кассир",
        },
      ],
    });

    const review = buildOwnerReview({
      summary,
      dishes,
      categories,
      shifts,
      brief,
      dataQuality: quality,
      dataMode: "live",
      labor,
    });

    expect(review.evidence).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          label: "ФОТ",
          detail: expect.stringContaining("Кассир"),
        }),
      ]),
    );
  });

  test("asks to check RMS prices when linked items have no cost", () => {
    const margin = buildMenuMarginReadiness({
      dishes,
      products: [
        {
          id: "pasta-product",
          name: "Паста полуфабрикат",
          sizePrices: [],
        },
      ],
      mappings: [
        {
          id: "mapping-pasta",
          venueId: "venue-1",
          dishKey: "паста",
          dishName: "Паста",
          dishGroup: "Кухня",
          iikoProductId: "pasta-product",
          iikoProductName: "Паста полуфабрикат",
          iikoArticle: "",
          mappingType: "manual",
          status: "active",
          confidence: 1,
          note: "",
        },
      ],
    });

    const review = buildOwnerReview({
      summary,
      dishes,
      categories,
      shifts,
      brief,
      dataQuality: quality,
      dataMode: "live",
      margin,
    });

    expect(review.hypotheses).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          title: "Маржа пока не доказана",
          check: expect.stringContaining("RMS-права"),
        }),
      ]),
    );
  });
});
