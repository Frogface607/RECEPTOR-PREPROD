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
import {
  buildTeamLaborReadiness,
  buildTeamLaborSetupProgress,
} from "./team/team-labor-readiness";
import type { TeamShiftPlanVarianceSummary } from "./team/team-shift-plan-variance";
import type { TeamOpsReadiness } from "./team/team-ops-readiness";

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

  test("surfaces shift plan variance as owner evidence and action", () => {
    const shiftPlanVariance = {
      plannedShifts: 2,
      actualShifts: 2,
      coveredActualShifts: 1,
      planCoveragePct: 50,
      plannedHours: 16,
      actualHours: 18,
      hoursDelta: 2,
      plannedLaborCost: 8000,
      actualLaborCost: 9500,
      laborDelta: 1500,
      unplannedActualShifts: 0,
      missedPlanShifts: 0,
      dayOffWorkedShifts: 1,
      hourVarianceShifts: 0,
      missingRateShifts: 0,
      issues: [
        {
          id: "member-1-2026-06-26-day-off",
          member: {
            id: "member-1",
            name: "Маша",
            roleId: "service",
            venueId: "venue-1",
            status: "active",
            shiftLabel: "зал",
            hourlyRate: 500,
          },
          roleTitle: "Зал",
          dateKey: "2026-06-26",
          dateLabel: "пт, 26.06",
          status: "day_off_worked",
          tone: "risk",
          plannedShifts: 0,
          actualShifts: 1,
          plannedHours: 0,
          actualHours: 8,
          hoursDelta: 8,
          plannedLaborCost: 0,
          actualLaborCost: 4000,
          laborDelta: 4000,
          revenue: 50000,
        },
      ],
    } satisfies TeamShiftPlanVarianceSummary;

    const review = buildOwnerReview({
      summary,
      dishes,
      categories,
      shifts,
      brief,
      dataQuality: quality,
      dataMode: "live",
      shiftPlanVariance,
    });

    expect(review.evidence).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          label: "План/факт",
          value: "50%",
          detail: expect.stringContaining("Маша"),
          tone: "risk",
        }),
      ]),
    );
    expect(review.actions).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          target: "shift-plan-variance",
          role: "manager",
          title: "Разобрать выход в выходной",
          tone: "risk",
        }),
      ]),
    );
    expect(review.tasks[0]).toMatchObject({
      roleId: "venue_manager",
      priority: "high",
      sourceLabel: "ФОТ и смены",
    });
  });

  test("surfaces Team OS readiness as owner evidence and action", () => {
    const team = {
      score: 72,
      status: "attention",
      roleCoveragePct: 100,
      laborCoveragePct: 100,
      learningAdmissionPct: 50,
      learningAveragePct: 42,
      actions: [
        {
          id: "learning",
          tone: "setup",
          title: "Дожать обучение",
          detail: "Маша: закрыть обязательный модуль роли.",
          href: "#learning-progress",
        },
      ],
    } satisfies TeamOpsReadiness;

    const review = buildOwnerReview({
      summary,
      dishes,
      categories,
      shifts,
      brief,
      dataQuality: quality,
      dataMode: "live",
      team,
    });

    expect(review.evidence).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          label: "Команда",
          value: "72%",
          detail: expect.stringContaining("Маша"),
          tone: "watch",
        }),
      ]),
    );
    expect(review.actions).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          target: "team-learning",
          role: "manager",
          title: "Дожать обучение",
        }),
      ]),
    );
    expect(review.tasks[0]).toMatchObject({
      roleId: "venue_manager",
      sourceLabel: "Команда",
    });
  });

  test("adds a first task from FOT setup progress", () => {
    const staff = [
      {
        id: "petr",
        name: "Петр",
        roleId: "service" as const,
        venueId: "venue-1",
        status: "active" as const,
        shiftLabel: "iiko",
      },
    ];
    const labor = buildLaborBi({
      staff,
      shifts: [
        {
          shiftId: "shift-petr",
          openTime: "2026-06-26T16:00:00",
          closeTime: "2026-06-27T00:00:00",
          revenue: 80000,
          items: 160,
          employee: "Петр",
        },
      ],
    });
    const laborReadiness = buildTeamLaborReadiness(staff, labor);
    const laborSetupProgress = buildTeamLaborSetupProgress(
      staff,
      laborReadiness,
    );

    const review = buildOwnerReview({
      summary,
      dishes,
      categories,
      shifts,
      brief,
      dataQuality: quality,
      dataMode: "live",
      labor,
      laborSetupProgress,
    });

    expect(review.tasks[0]).toMatchObject({
      title: expect.stringContaining("Заполнить ставку ФОТ"),
      roleId: "service",
      audienceMemberId: "petr",
      audienceMemberName: "Петр",
      priority: "high",
      sourceLabel: "ФОТ setup",
    });
  });
});
