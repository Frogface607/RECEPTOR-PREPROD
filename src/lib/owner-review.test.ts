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
        expect.objectContaining({
          label: "Экономика",
          value: "маржа не доказана",
          tone: "risk",
        }),
      ]),
    );
    expect(review.verdict).toBe("ФОТ давит, а маржа пока не доказана.");
    expect(review.actions).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          title: "Разобрать дорогую смену",
          target: "shift-diagnostics",
          role: "manager",
          tone: "risk",
        }),
        expect.objectContaining({
          title: "Блюдо не связано с iiko",
          target: "margin-mapping",
          role: "chef",
        }),
      ]),
    );
    expect(review.hypotheses[0]).toMatchObject({
      title: "ФОТ выше целевой нормы",
      tone: "risk",
      role: "manager",
    });
    expect(review.tasks[0]).toMatchObject({
      title: expect.stringContaining("Разобрать дорогую смену"),
      priority: "high",
      roleId: "venue_manager",
      sourceLabel: "ФОТ и смены",
    });
    expect(review.tasks[0].title).toContain("ФОТ");
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

  test("turns low shift productivity into owner action even when FOT is priced", () => {
    const labor = buildLaborBi({
      shifts: [
        {
          shiftId: "shift-low-productivity",
          openTime: "2026-06-26T12:00:00",
          closeTime: "2026-06-26T22:00:00",
          revenue: 30000,
          items: 60,
          employee: "Смена",
          workers: [
            {
              name: "Команда зала",
              hours: 10,
              shiftPay: 3000,
              sales: 30000,
            },
          ],
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

    expect(review.actions).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          title: "Низкая выручка на человеко-час",
          target: "shift-diagnostics",
          role: "manager",
          tone: "watch",
        }),
      ]),
    );
    expect(review.tasks[0]).toMatchObject({
      title: expect.stringContaining("Низкая выручка на человеко-час"),
      priority: "medium",
      roleId: "venue_manager",
      sourceLabel: "ФОТ и смены",
    });
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
    expect(review.actions).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          title: "Добавить сотрудника из iiko",
          target: "labor-member",
          memberName: "Кассир",
        }),
      ]),
    );
    expect(review.tasks[0]).toMatchObject({
      title: expect.stringContaining("Добавить сотрудника из iiko"),
      roleId: "venue_manager",
      sourceLabel: "ФОТ и смены",
    });
  });

  test("prioritizes unproven shift economics when labor and margin are incomplete", () => {
    const labor = buildLaborBi({
      shifts: [
        {
          shiftId: "shift-petr",
          openTime: "2026-06-26T18:00:00",
          closeTime: "2026-06-27T02:00:00",
          revenue: 90000,
          items: 180,
          employee: "Петр",
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

    expect(review.verdict).toBe(
      "Сначала нужно доказать экономику смены: ФОТ и маржа неполные.",
    );
    expect(review.evidence).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          label: "Экономика",
          value: "не доказана",
          detail: expect.stringContaining("ФОТ покрыт"),
          tone: "risk",
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

    expect(review.evidence).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          label: "Маржа",
          detail: expect.stringContaining("Паста"),
        }),
      ]),
    );
    expect(review.evidence).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          label: "Маржа",
          detail: expect.stringContaining("без закупочной цены"),
        }),
      ]),
    );
    expect(review.actions).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          title: "RMS не отдает закупочную цену",
          target: "margin-diagnostics",
          role: "owner",
        }),
      ]),
    );
    expect(review.tasks[0]).toMatchObject({
      title: expect.stringContaining("RMS не отдает закупочную цену"),
      roleId: "operations_manager",
      sourceLabel: "Маржа и техкарты",
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

  test("turns proven low margin into an owner review action", () => {
    const lowMarginDishes: DishStat[] = [
      {
        dishName: "Cheap pasta",
        dishGroup: "Kitchen",
        dishAmountInt: 10,
        dishSumInt: 1000,
      },
      {
        dishName: "Healthy steak",
        dishGroup: "Kitchen",
        dishAmountInt: 10,
        dishSumInt: 10000,
      },
    ];
    const margin = buildMenuMarginReadiness({
      dishes: lowMarginDishes,
      products: [
        {
          id: "cheap-pasta",
          name: "Cheap pasta",
          purchasePrice: 55,
          sizePrices: [],
        },
        {
          id: "healthy-steak",
          name: "Healthy steak",
          purchasePrice: 250,
          sizePrices: [],
        },
      ],
    });

    const review = buildOwnerReview({
      summary,
      dishes: lowMarginDishes,
      categories,
      shifts,
      brief,
      dataQuality: quality,
      dataMode: "live",
      margin,
    });

    expect(review.verdict).toContain("Cheap pasta");
    expect(review.evidence).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          value: "100%",
          detail: expect.stringContaining("Cheap pasta"),
          tone: "watch",
        }),
      ]),
    );
    expect(review.actions).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          target: "margin-risk",
          role: "chef",
          tone: "watch",
          title: expect.stringContaining("Cheap pasta"),
          detail: expect.stringContaining("45%"),
        }),
      ]),
    );
    expect(review.tasks[0]).toMatchObject({
      title: expect.stringContaining("Cheap pasta"),
      roleId: "chef",
      priority: "medium",
    });
  });
});
