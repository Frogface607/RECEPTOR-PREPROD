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
import type {
  StaffMember,
  TeamAnnouncement,
  TeamAnnouncementRead,
  TeamAuditEvent,
  TeamTask,
  TeamTaskComment,
} from "./team/team-os";

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

function buildReadyLabor() {
  return buildLaborBi({
    shifts: [
      {
        ...shifts[0],
        workers: [
          {
            name: "Смена",
            hours: 8,
            shiftPay: 8000,
            sales: 100000,
          },
        ],
      },
    ],
  });
}

function buildReadyMargin() {
  return buildMenuMarginReadiness({
    dishes,
    products: [
      {
        id: "pasta-product",
        name: "Паста",
        purchasePrice: 300,
        sizePrices: [],
      },
    ],
  });
}

function buildReadyTeam(): TeamOpsReadiness {
  return {
    score: 100,
    status: "ready",
    roleCoveragePct: 100,
    laborCoveragePct: 100,
    learningAdmissionPct: 100,
    learningAveragePct: 100,
    actions: [
      {
        id: "ready",
        tone: "good",
        title: "Команда готова",
        detail: "Роли, ставки и обучение закрыты.",
        href: "#team-actions",
      },
    ],
  };
}

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
          title: "ФОТ по Команда зала требует маржу рядом",
          target: "shift-diagnostics",
          role: "manager",
          tone: "risk",
          sourceLabel: "ФОТ и маржа",
          impactLabel: "ФОТ 35%",
        }),
        expect.objectContaining({
          title: "Разобрать дорогую смену",
          target: "shift-diagnostics",
          role: "manager",
          tone: "risk",
          impactLabel: expect.stringMatching(/^10\s000 ₽$/),
        }),
        expect.objectContaining({
          title: "Блюдо не связано с iiko",
          target: "margin-mapping",
          role: "chef",
          impactLabel: expect.stringMatching(/^20\s000\s₽$/),
        }),
      ]),
    );
    expect(review.hypotheses).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          title: "ФОТ выше целевой нормы",
          tone: "risk",
          role: "manager",
        }),
      ]),
    );
    expect(review.tasks[0]).toMatchObject({
      title: "Разобрать ФОТ и маржу: Команда зала",
      priority: "high",
      roleId: "venue_manager",
      sourceLabel: "ФОТ и маржа",
      impactLabel: "ФОТ 35%",
      contextNote: expect.stringContaining("решение по часам без маржи"),
    });
    expect(review.tasks[0].title.length).toBeLessThan(80);
    expect(review.hypotheses).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          title: "ФОТ по Команда зала требует маржу рядом",
          why: expect.stringContaining("себестоимость покрывает только 0%"),
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
          title: "Разобрать слабую смену",
          target: "shift-diagnostics",
          role: "manager",
          tone: "watch",
          impactLabel: "ФОТ 10%",
          learningModuleId: "restaurant-numbers-basics",
          learningModuleTitle: "Цифры ресторана простым языком",
          learningChecklistTitle: "Если BI показал перерасход ФОТ",
          briefingQuestion: "какая смена, человек или ставка съедает прибыль",
        }),
      ]),
    );
    expect(review.tasks[0]).toMatchObject({
      title: "Разобрать слабую смену",
      priority: "medium",
      roleId: "venue_manager",
      sourceLabel: "ФОТ и смены",
      learningModuleId: "restaurant-numbers-basics",
      learningModuleTitle: "Цифры ресторана простым языком",
      learningChecklistTitle: "Если BI показал перерасход ФОТ",
      contextNote: expect.stringContaining(
        "Урок для команды: Цифры ресторана простым языком.",
      ),
    });
    expect(review.tasks[0].contextNote).toContain("Проверка:");
    expect(review.tasks[0].contextNote).toContain(
      "Вопрос: какая смена, человек или ставка съедает прибыль.",
    );
    expect(review.tasks[0].contextNote).toContain(
      "Зачем: понять, сколько ФОТ 10% стоит смене и прибыли.",
    );
    expect(review.tasks[0].contextNote).toContain(
      "Чеклист: Если BI показал перерасход ФОТ.",
    );
    expect(review.questions).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          role: "manager",
          text: "какая смена, человек или ставка съедает прибыль",
        }),
      ]),
    );
  });

  test("opens linked employee when personal FOT efficiency is risky", () => {
    const labor = buildLaborBi({
      shifts: [
        {
          shiftId: "shift-manager-expensive",
          openTime: "2026-06-26T12:00:00",
          closeTime: "2026-06-26T22:00:00",
          revenue: 50000,
          items: 120,
          employee: "Смена",
          workers: [
            {
              memberId: "manager-1",
              name: "Мария",
              hours: 10,
              shiftPay: 18000,
              sales: 50000,
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
          title: "Сотрудник дорогой к выручке",
          target: "labor-member",
          memberId: "manager-1",
          memberName: "Мария",
          role: "manager",
          tone: "risk",
          impactLabel: expect.stringMatching(/^5\s500\s₽$/),
          learningModuleId: "restaurant-numbers-basics",
          learningModuleTitle: "Цифры ресторана простым языком",
        }),
      ]),
    );
    expect(review.tasks[0]).toMatchObject({
      title: expect.stringContaining("Сотрудник дорогой к выручке"),
      priority: "high",
      roleId: "venue_manager",
      sourceLabel: "ФОТ и смены",
      impactLabel: expect.stringMatching(/^5\s500\s₽$/),
      learningModuleId: "restaurant-numbers-basics",
      learningModuleTitle: "Цифры ресторана простым языком",
      contextNote: expect.stringContaining("Перерасход к цели"),
    });
    expect(review.tasks[0].contextNote).toContain(
      "Урок для команды: Цифры ресторана простым языком.",
    );
    expect(review.tasks[0].contextNote).toContain(
      "Чеклист: Если BI показал перерасход ФОТ.",
    );
  });

  test("connects missing iiko shifts with the iiko discipline learning module", () => {
    const labor = buildLaborBi({
      shifts: [],
    });

    const review = buildOwnerReview({
      summary,
      dishes,
      categories,
      shifts: [],
      brief,
      dataQuality: quality,
      dataMode: "live",
      labor,
    });

    expect(review.actions).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          title: "Смены не найдены",
          target: "iiko-settings",
          learningModuleId: "iiko-cash-discipline",
          learningModuleTitle: "iiko и кассовая дисциплина на смене",
          learningChecklistTitle: "Если Receptor не видит смены iiko",
        }),
      ]),
    );
    expect(review.hypotheses).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          title: "Смены пока не найдены",
          learningModuleId: "iiko-cash-discipline",
          learningModuleTitle: "iiko и кассовая дисциплина на смене",
          learningChecklistTitle: "Если Receptor не видит смены iiko",
        }),
      ]),
    );
    expect(review.tasks).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          title: expect.stringContaining("права на OLAP смены"),
          sourceLabel: "Данные iiko",
          learningModuleId: "iiko-cash-discipline",
          learningModuleTitle: "iiko и кассовая дисциплина на смене",
          learningChecklistTitle: "Если Receptor не видит смены iiko",
          contextNote: expect.stringContaining(
            "Урок для команды: iiko и кассовая дисциплина на смене.",
          ),
        }),
      ]),
    );
    expect(review.tasks).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          sourceLabel: "Данные iiko",
          contextNote: expect.stringContaining(
            "Чеклист: Если Receptor не видит смены iiko.",
          ),
        }),
      ]),
    );
  });

  test("connects employee FOT risk with proven weak margin in hypotheses", () => {
    const labor = buildLaborBi({
      shifts: [
        {
          shiftId: "shift-manager-expensive",
          openTime: "2026-06-26T12:00:00",
          closeTime: "2026-06-26T22:00:00",
          revenue: 50000,
          items: 120,
          employee: "Shift",
          workers: [
            {
              memberId: "manager-1",
              name: "Maria",
              hours: 10,
              shiftPay: 18000,
              sales: 50000,
            },
          ],
        },
      ],
    });
    const margin = buildMenuMarginReadiness({
      dishes: [
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
      ],
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
      dishes,
      categories,
      shifts,
      brief,
      dataQuality: quality,
      dataMode: "live",
      labor,
      margin,
    });

    expect(review.hypotheses).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          title: "Проверить смену: Maria и слабая маржа",
          why: expect.stringContaining("Cheap pasta"),
          check: expect.stringContaining("проблема может быть в меню"),
          role: "owner",
          tone: "risk",
          taskTitle: "Разобрать ФОТ и маржу: Maria",
          learningModuleId: "tech-card-discipline",
          learningModuleTitle: "Техкарта как договор внутри команды",
          learningChecklistTitle: "Если BI показал недобор валовой прибыли",
          briefingQuestion:
            "какая цена, порция, списание, ставка или состав смены объясняет разрыв прибыли",
        }),
      ]),
    );
    expect(review.tasks).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          title: "Разобрать ФОТ и маржу: Maria",
          sourceLabel: "ФОТ и маржа",
          audienceMemberId: "manager-1",
          audienceMemberName: "Maria",
          learningModuleId: "tech-card-discipline",
          learningChecklistTitle: "Если BI показал недобор валовой прибыли",
          contextNote: expect.stringContaining(
            "Вопрос: какая цена, порция, списание, ставка или состав смены объясняет разрыв прибыли.",
          ),
        }),
      ]),
    );
    expect(review.tasks).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          sourceLabel: "ФОТ и маржа",
          contextNote: expect.stringContaining(
            "Чеклист: Если BI показал недобор валовой прибыли.",
          ),
        }),
      ]),
    );
  });

  test("does not create another FOT-margin task for the same employee contour", () => {
    const labor = buildLaborBi({
      shifts: [
        {
          shiftId: "shift-manager-expensive",
          openTime: "2026-06-26T12:00:00",
          closeTime: "2026-06-26T22:00:00",
          revenue: 50000,
          items: 120,
          employee: "Смена",
          workers: [
            {
              memberId: "manager-1",
              name: "Мария",
              hours: 10,
              shiftPay: 18000,
              sales: 50000,
            },
          ],
        },
      ],
    });
    const margin = buildMenuMarginReadiness({
      dishes,
      products: [],
    });
    const teamTasks: TeamTask[] = [
      {
        id: "task-existing-fot-margin",
        venueId: "venue-1",
        title: "Проверить смену Марии и себестоимость топ-позиций",
        source: "copilot",
        sourceLabel: "ФОТ и маржа",
        priority: "high",
        status: "accepted",
        audience: { type: "member", memberId: "manager-1" },
        dueLabel: "сегодня",
      },
    ];

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
      teamTasks,
    });

    expect(review.actions).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          sourceLabel: "ФОТ и маржа",
          memberId: "manager-1",
          existingTaskId: "task-existing-fot-margin",
          existingTaskStatus: "accepted",
        }),
      ]),
    );
    expect(
      review.tasks.some(
        (task) =>
          task.sourceLabel === "ФОТ и маржа" &&
          task.audienceMemberId === "manager-1",
      ),
    ).toBe(false);
    expect(review.operationalPulse).toMatchObject({
      openTaskContours: ["ФОТ и маржа"],
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

  test("keeps shift economics in the first owner evidence tiles", () => {
    const review = buildOwnerReview({
      summary,
      dishes,
      categories,
      shifts,
      brief,
      dataQuality: quality,
      dataMode: "live",
      labor: buildReadyLabor(),
      margin: buildReadyMargin(),
      team: buildReadyTeam(),
    });

    expect(review.evidence.slice(0, 4).map((item) => item.label)).toEqual([
      "Деньги",
      "ФОТ",
      "Маржа",
      "Экономика",
    ]);
    expect(review.evidence[3]).toMatchObject({
      value: "связана",
      tone: "good",
      detail: expect.stringContaining("Себестоимость покрывает"),
    });
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
          learningModuleId: "tech-card-discipline",
          learningModuleTitle: "Техкарта как договор внутри команды",
          learningChecklistTitle: "Если BI показал недобор валовой прибыли",
          briefingQuestion:
            "какая цена, порция, списание или себестоимость объясняет провал маржи",
        }),
      ]),
    );
    expect(review.tasks[0]).toMatchObject({
      title: expect.stringContaining("RMS не отдает закупочную цену"),
      roleId: "operations_manager",
      sourceLabel: "Маржа и техкарты",
      learningModuleId: "tech-card-discipline",
      learningModuleTitle: "Техкарта как договор внутри команды",
      learningChecklistTitle: "Если BI показал недобор валовой прибыли",
      contextNote: expect.stringContaining(
        "Урок для команды: Техкарта как договор внутри команды.",
      ),
    });
    expect(review.tasks[0].contextNote).toContain("Проверка:");
    expect(review.tasks[0].contextNote).toContain(
      "Вопрос: какая цена, порция, списание или себестоимость объясняет провал маржи.",
    );
    expect(review.tasks[0].contextNote).toMatch(
      /Зачем: закрыть 20\s000\s₽ выручки без понятной себестоимости\./,
    );
    expect(review.tasks[0].contextNote).toContain(
      "Чеклист: Если BI показал недобор валовой прибыли.",
    );
    expect(review.hypotheses).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          title: "Маржа пока не доказана",
          check: expect.stringContaining("RMS-права"),
        }),
      ]),
    );
  });

  test("focuses missing ingredient price tasks on the tech-card price checklist", () => {
    const margin = buildMenuMarginReadiness({
      dishes: [
        {
          dishName: "Pasta",
          dishGroup: "Kitchen",
          dishAmountInt: 10,
          dishSumInt: 30000,
        },
      ],
      products: [
        {
          id: "pasta-base",
          name: "Pasta",
          sizePrices: [],
        },
        {
          id: "flour",
          name: "Flour",
          unit: "g",
          pricePerKg: 100,
          sizePrices: [],
        },
        {
          id: "egg",
          name: "Egg",
          unit: "pcs",
          sizePrices: [],
        },
      ],
      techCards: [
        {
          id: "chart-pasta",
          productId: "pasta-base",
          productName: "Pasta",
          items: [
            {
              productId: "flour",
              productName: "Flour",
              amount: 0.12,
              unit: "kg",
            },
            {
              productId: "egg",
              productName: "Egg",
              amount: 2,
              unit: "pcs",
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
      margin,
    });

    expect(review.actions).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          title: "Техкарта есть, не хватает цен ингредиентов",
          target: "margin-diagnostics",
          learningModuleId: "tech-card-discipline",
          learningChecklistTitle: "Если в техкарте нет цен ингредиентов",
          detail: expect.stringContaining("Egg"),
        }),
      ]),
    );
    expect(review.tasks[0]).toMatchObject({
      learningChecklistTitle: "Если в техкарте нет цен ингредиентов",
      contextNote: expect.stringContaining(
        "Чеклист: Если в техкарте нет цен ингредиентов.",
      ),
    });
    expect(review.hypotheses).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          learningChecklistTitle: "Если в техкарте нет цен ингредиентов",
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
          impactLabel: "150 ₽",
          learningModuleId: "tech-card-discipline",
          learningModuleTitle: "Техкарта как договор внутри команды",
        }),
      ]),
    );
    expect(review.actions[0].detail).toContain(
      "Недобор валовой прибыли к цели: 150 ₽.",
    );
    expect(review.tasks[0]).toMatchObject({
      title: expect.stringContaining("Cheap pasta"),
      roleId: "chef",
      priority: "medium",
      impactLabel: "150 ₽",
      contextNote: expect.stringContaining(
        "Чеклист: Если BI показал недобор валовой прибыли.",
      ),
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
          learningModuleId: "shift-open-close",
          learningModuleTitle: "Открытие и закрытие смены без хаоса",
          learningChecklistTitle: "Если план и факт смен не совпали",
          briefingQuestion:
            "какое отклонение графика изменило ФОТ или нагрузку смены",
        }),
      ]),
    );
    expect(review.hypotheses).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          title: "Разобрать выход в выходной",
          taskSourceLabel: "ФОТ и смены",
          taskTitle: "Разобрать выход в выходной",
          learningModuleId: "shift-open-close",
          learningChecklistTitle: "Если план и факт смен не совпали",
          briefingQuestion:
            "какое отклонение графика изменило ФОТ или нагрузку смены",
        }),
      ]),
    );
    expect(review.tasks[0]).toMatchObject({
      title: "Разобрать выход в выходной",
      roleId: "venue_manager",
      priority: "high",
      sourceLabel: "ФОТ и смены",
      learningModuleId: "shift-open-close",
      learningModuleTitle: "Открытие и закрытие смены без хаоса",
      learningChecklistTitle: "Если план и факт смен не совпали",
      contextNote: expect.stringContaining(
        "Урок для команды: Открытие и закрытие смены без хаоса.",
      ),
    });
    expect(review.tasks[0].contextNote).toContain(
      "Вопрос: какое отклонение графика изменило ФОТ или нагрузку смены.",
    );
    expect(review.tasks[0].contextNote).toContain(
      "Чеклист: Если план и факт смен не совпали.",
    );
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
          detail: "Маша: Восьмерка продаж и апселл в сервисе.",
          href: "#learning-progress",
          learningModuleId: "sales-eight-upsell",
          learningModuleTitle: "Восьмерка продаж и апселл в сервисе",
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
          learningModuleId: "sales-eight-upsell",
          learningModuleTitle: "Восьмерка продаж и апселл в сервисе",
          briefingQuestion:
            "какой обязательный модуль мешает сотруднику выйти в смену",
        }),
      ]),
    );
    expect(review.tasks[0]).toMatchObject({
      roleId: "venue_manager",
      sourceLabel: "Команда",
      learningModuleId: "sales-eight-upsell",
      learningModuleTitle: "Восьмерка продаж и апселл в сервисе",
    });
    expect(review.tasks[0].contextNote).toContain(
      "Вопрос: какой обязательный модуль мешает сотруднику выйти в смену.",
    );
    expect(review.tasks[0].contextNote).toContain(
      "Урок для команды: Восьмерка продаж и апселл в сервисе.",
    );
  });

  test("shows operational proof from open tasks and recently closed loops", () => {
    const teamTasks: TeamTask[] = [
      {
        id: "task-open",
        venueId: "venue-1",
        title: "Разобрать дорогую смену",
        source: "copilot",
        sourceLabel: "ФОТ и маржа",
        impactLabel: "ФОТ 35%",
        priority: "high",
        status: "new",
        audience: { type: "role", roleId: "venue_manager" },
        dueLabel: "сегодня",
      },
      {
        id: "task-closed",
        venueId: "venue-1",
        title: "Пройти обучение",
        source: "manager",
        priority: "medium",
        status: "done",
        audience: { type: "member", memberId: "service-1" },
        dueLabel: "до смены",
      },
    ];
    const teamAuditEvents: TeamAuditEvent[] = [
      {
        id: "audit-learning-closed",
        venueId: "venue-1",
        type: "task_status_updated",
        sourceLabel: "Обучение",
        impactLabel: "1 допуск",
        targetType: "task",
        targetId: "task-closed",
        summary:
          "Автоматически закрыта задача обучения после сдачи модуля: Как рекомендовать блюдо без давления.",
        createdAtLabel: "12:10",
      },
    ];

    const review = buildOwnerReview({
      summary,
      dishes,
      categories,
      shifts,
      brief,
      dataQuality: quality,
      dataMode: "live",
      teamTasks,
      teamAuditEvents,
    });

    expect(review.evidence).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          label: "Контуры",
          value: "1 открыто",
          detail: expect.stringContaining("1 закрыто недавно"),
          tone: "risk",
        }),
        expect.objectContaining({
          label: "Контуры",
          detail: expect.stringContaining("Разобрать дорогую смену"),
        }),
      ]),
    );
    expect(review.operationalPulse).toMatchObject({
      title: "Есть срочные действия команды",
      tone: "risk",
      openTasks: 1,
      urgentOpenTasks: 1,
      openTaskContours: ["ФОТ и маржа"],
      closedLoops: 1,
      recentEvents: [
        expect.objectContaining({
          label: "Обучение",
          summary: expect.stringContaining("1 допуск"),
          timeLabel: "12:10",
          tone: "good",
          target: "team-journal",
        }),
      ],
      action: {
        label: "Открыть Team OS",
        target: "team-actions",
      },
    });
    expect(review.operationalPulse?.detail).toContain("ФОТ и маржа");
    expect(review.operationalPulse?.detail).toContain(
      "Разобрать дорогую смену",
    );
    expect(review.operationalPulse?.detail).toContain("ФОТ 35%");
    expect(review.evidence).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          label: "Контуры",
          detail: expect.stringContaining("ФОТ 35%"),
        }),
      ]),
    );
  });

  test("shows FOT and shift plan fixes in the owner operational pulse", () => {
    const teamAuditEvents: TeamAuditEvent[] = [
      {
        id: "audit-labor-rate",
        venueId: "venue-1",
        type: "member_labor_rate_updated",
        targetType: "member",
        targetId: "service-1",
        summary: "Ставка ФОТ обновлена: Маша.",
        createdAtLabel: "13:20",
      },
      {
        id: "audit-shift-plan",
        venueId: "venue-1",
        type: "shift_plan_updated",
        targetType: "shift_plan",
        targetId: "plan-1",
        summary: "План смены обновлен: Маша, 2026-06-26 16:00-00:00.",
        createdAtLabel: "13:25",
      },
    ];

    const review = buildOwnerReview({
      summary,
      dishes,
      categories,
      shifts,
      brief,
      dataQuality: quality,
      dataMode: "live",
      teamTasks: [],
      teamAuditEvents,
    });

    expect(review.operationalPulse).toMatchObject({
      title: "Открытых задач нет",
      tone: "good",
      openTasks: 0,
      closedLoops: 0,
      recentEvents: [
        {
          label: "ФОТ",
          summary: "Ставка ФОТ обновлена: Маша.",
          timeLabel: "13:20",
          tone: "good",
          target: "labor-rate",
        },
        {
          label: "План",
          summary: "План смены обновлен: Маша, 2026-06-26 16:00-00:00.",
          timeLabel: "13:25",
          tone: "good",
          target: "shift-plan",
        },
      ],
    });
  });

  test("uses task contour labels in the owner operational pulse", () => {
    const teamAuditEvents: TeamAuditEvent[] = [
      {
        id: "audit-task-margin",
        venueId: "venue-1",
        type: "task_created",
        sourceLabel: "ФОТ и маржа",
        targetType: "task",
        targetId: "task-margin",
        summary: "Создана задача: разобрать ФОТ и слабую маржу.",
        createdAtLabel: "14:10",
      },
    ];

    const review = buildOwnerReview({
      summary,
      dishes,
      categories,
      shifts,
      brief,
      dataQuality: quality,
      dataMode: "live",
      teamTasks: [],
      teamAuditEvents,
    });

    expect(review.operationalPulse?.recentEvents[0]).toMatchObject({
      label: "ФОТ и маржа",
      summary: expect.stringContaining("разобрать ФОТ"),
      timeLabel: "14:10",
      target: "team-journal",
    });
  });

  test("keeps task contour labels when an operational loop is closed", () => {
    const teamAuditEvents: TeamAuditEvent[] = [
      {
        id: "audit-task-margin-done",
        venueId: "venue-1",
        type: "task_status_updated",
        sourceLabel: "ФОТ и маржа",
        impactLabel: "120 000 ₽",
        targetType: "task",
        targetId: "task-margin",
        summary: "Статус задачи обновлен: done.",
        createdAtLabel: "14:30",
      },
    ];

    const review = buildOwnerReview({
      summary,
      dishes,
      categories,
      shifts,
      brief,
      dataQuality: quality,
      dataMode: "live",
      teamTasks: [],
      teamAuditEvents,
    });

    expect(review.operationalPulse).toMatchObject({
      closedLoops: 1,
      recentEvents: [
        expect.objectContaining({
          label: "ФОТ и маржа",
          summary: expect.stringContaining("120 000 ₽"),
          tone: "good",
          target: "team-journal",
        }),
      ],
    });
    expect(review.operationalPulse?.detail).toContain("ФОТ и маржа");
    expect(review.operationalPulse?.detail).toContain("120 000 ₽");
  });

  test("shows team announcements as owner communication proof", () => {
    const teamAnnouncements: TeamAnnouncement[] = [
      {
        id: "announcement-fot",
        venueId: "venue-1",
        title: "ФОТ перед отчетом",
        body: "Проверьте ставки и смены до вечернего отчета.",
        priority: "important",
        audience: { type: "role", roleId: "venue_manager" },
        createdByName: "Мария",
        createdAtLabel: "14:10",
      },
    ];
    const teamAnnouncementReads: TeamAnnouncementRead[] = [
      {
        announcementId: "announcement-fot",
        memberId: "manager-1",
        readAtLabel: "14:12",
      },
    ];

    const review = buildOwnerReview({
      summary,
      dishes,
      categories,
      shifts,
      brief,
      dataQuality: quality,
      dataMode: "live",
      teamTasks: [],
      teamAuditEvents: [],
      teamAnnouncements,
      teamAnnouncementReads,
    });

    expect(review.evidence).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          label: "Связь",
          value: "1 объявление",
          detail: expect.stringContaining("1 прочтение"),
          tone: "good",
        }),
      ]),
    );
    expect(review.operationalPulse).toMatchObject({
      title: "Команда получила контекст",
      tone: "good",
      openTasks: 0,
      closedLoops: 0,
      recentEvents: [
        {
          label: "Объявление",
          summary: "ФОТ перед отчетом",
          timeLabel: "14:10",
          tone: "watch",
          target: "team-journal",
        },
      ],
      action: {
        label: "Открыть связь",
        target: "team-journal",
      },
    });
  });

  test("turns unread important announcements into owner actions", () => {
    const teamStaff: StaffMember[] = [
      {
        id: "service-1",
        name: "Илья",
        roleId: "service",
        venueId: "venue-1",
        status: "active",
        shiftLabel: "вечер",
      },
      {
        id: "service-2",
        name: "Оля",
        roleId: "service",
        venueId: "venue-1",
        status: "active",
        shiftLabel: "вечер",
      },
    ];
    const teamAnnouncements: TeamAnnouncement[] = [
      {
        id: "announcement-service",
        venueId: "venue-1",
        title: "Зал: фокус на ужин",
        body: "Каждый стол получает рекомендацию.",
        priority: "important",
        audience: { type: "role", roleId: "service" },
        createdByName: "Мария",
        createdAtLabel: "14:10",
      },
    ];
    const teamAnnouncementReads: TeamAnnouncementRead[] = [
      {
        announcementId: "announcement-service",
        memberId: "service-1",
        readAtLabel: "14:12",
      },
    ];

    const review = buildOwnerReview({
      summary,
      dishes,
      categories,
      shifts,
      brief,
      dataQuality: quality,
      dataMode: "live",
      labor: buildReadyLabor(),
      margin: buildReadyMargin(),
      team: buildReadyTeam(),
      teamTasks: [],
      teamAuditEvents: [],
      teamStaff,
      teamAnnouncements,
      teamAnnouncementReads,
    });

    expect(review.operationalPulse).toMatchObject({
      title: "Связь не закрыта",
      tone: "watch",
      action: {
        label: "Открыть связь",
        target: "team-journal",
      },
    });
    expect(review.readiness).toMatchObject({
      status: "partial",
      action: {
        label: "Открыть связь",
        target: "team-journal",
      },
    });
    expect(review.evidence).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          label: "Связь",
          detail: expect.stringContaining("1 без подтверждения"),
          tone: "watch",
        }),
      ]),
    );
    expect(review.actions).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          title: "Дожать связь",
          target: "team-journal",
          role: "manager",
          tone: "watch",
        }),
      ]),
    );
    expect(review.tasks).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          title: expect.stringContaining("Дожать связь"),
          roleId: "venue_manager",
          sourceLabel: "Команда",
        }),
      ]),
    );
  });

  test("blocks profit readiness until FOT and margin are proven", () => {
    const review = buildOwnerReview({
      summary,
      dishes,
      categories,
      shifts,
      brief,
      dataQuality: quality,
      dataMode: "live",
    });

    expect(review.readiness).toMatchObject({
      status: "blocked",
      title: "Прибыль не доказана",
      tone: "risk",
      action: {
        label: "Проверить смены",
        target: "shift-coverage",
      },
    });
    expect(review.readiness.detail).toContain(
      "Покрытие: продажи 100%, ФОТ без покрытия, себестоимость без покрытия.",
    );
    expect(review.readiness.detail).toContain("ФОТ");
    expect(review.readiness.detail).toContain("себестоимость");
  });

  test("keeps profit readiness partial while Team OS has an open loop", () => {
    const teamTasks: TeamTask[] = [
      {
        id: "task-open-loop",
        venueId: "venue-1",
        title: "Проверить апсейл в вечерней смене",
        source: "copilot",
        priority: "medium",
        status: "accepted",
        audience: { type: "role", roleId: "venue_manager" },
        dueLabel: "сегодня",
      },
    ];

    const review = buildOwnerReview({
      summary,
      dishes,
      categories,
      shifts,
      brief,
      dataQuality: quality,
      dataMode: "live",
      labor: buildReadyLabor(),
      margin: buildReadyMargin(),
      team: buildReadyTeam(),
      teamTasks,
      teamAuditEvents: [],
    });

    expect(review.readiness).toMatchObject({
      status: "partial",
      title: "Прибыль требует проверки",
      score: 95,
      tone: "watch",
      action: {
        label: "Открыть задачи",
        target: "team-actions",
      },
    });
    expect(review.readiness.detail).toContain(
      "Покрытие: продажи 100%, ФОТ 100% выручки, себестоимость 100% выручки.",
    );
    expect(review.readiness.detail).toContain("1 открытая задача Team OS");
  });

  test("prioritizes money-weighted BI actions over communication chores", () => {
    const staff: StaffMember[] = [
      {
        id: "waiter-1",
        name: "Официант",
        roleId: "service",
        venueId: "venue-1",
        status: "active",
        shiftLabel: "Зал",
      },
    ];
    const announcements: TeamAnnouncement[] = [
      {
        id: "announcement-1",
        venueId: "venue-1",
        title: "Подтвердить важное объявление",
        body: "Проверить чтение командой.",
        priority: "important",
        audience: { type: "venue", venueId: "venue-1" },
        createdByName: "Receptor",
        createdAtLabel: "сегодня",
      },
    ];

    const review = buildOwnerReview({
      summary,
      dishes,
      categories,
      shifts,
      brief,
      dataQuality: quality,
      dataMode: "live",
      margin: buildMenuMarginReadiness({
        dishes,
        products: [],
      }),
      teamStaff: staff,
      teamAnnouncements: announcements,
      teamAnnouncementReads: [],
    });

    expect(review.actions[0]).toMatchObject({
      target: "margin-mapping",
      impactLabel: expect.stringContaining("20"),
    });
    expect(review.actions).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          target: "team-journal",
        }),
      ]),
    );
  });

  test("prioritizes money-weighted BI hypotheses before setup noise", () => {
    const labor = buildLaborBi({
      shifts: [
        {
          ...shifts[0],
          workers: [
            {
              name: "Официант",
              hours: 8,
              sales: 100000,
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
      margin: buildMenuMarginReadiness({
        dishes,
        products: [],
      }),
    });

    expect(review.hypotheses[0]).toMatchObject({
      taskSourceLabel: "Маржа и техкарты",
      impactLabel: expect.stringContaining("80"),
    });
    expect(review.hypotheses).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          taskSourceLabel: "ФОТ и смены",
        }),
      ]),
    );
  });

  test("keeps field context visible when several BI hypotheses compete", () => {
    const labor = buildLaborBi({
      shifts: [
        {
          ...shifts[0],
          workers: [
            {
              name: "Официант",
              hours: 8,
              sales: 100000,
            },
          ],
        },
      ],
    });
    const teamTasks: TeamTask[] = [
      {
        id: "task-shift-context",
        title: "Разобрать вечернюю смену",
        source: "copilot",
        sourceLabel: "Выручка и смены",
        priority: "medium",
        status: "in_progress",
        venueId: "venue-1",
        audience: { type: "role", roleId: "venue_manager" },
        dueLabel: "сегодня",
      },
    ];
    const teamComments: TeamTaskComment[] = [
      {
        id: "comment-field-risk",
        venueId: "venue-1",
        taskId: "task-shift-context",
        authorName: "Маша",
        body: "Стоп-лист / закончилось: мята к 21:00, гости жаловались на ожидание.",
        createdAtLabel: "22:30",
      },
    ];

    const review = buildOwnerReview({
      summary,
      dishes,
      categories,
      shifts,
      brief: {
        ...brief,
        revenue: {
          ...brief.revenue,
          previous: 130000,
          deltaPct: -23.1,
        },
      },
      dataQuality: quality,
      dataMode: "live",
      labor,
      margin: buildMenuMarginReadiness({
        dishes,
        products: [],
      }),
      teamTasks,
      teamComments,
    });

    expect(review.hypotheses).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          taskSourceLabel: "Полевой контекст",
          title: "Проверить стоп-лист и потерянные продажи",
          learningChecklistTitle: "Если полевая заметка про стоп-лист",
          briefingQuestion:
            "что закончилось, сколько продаж потеряли и кто отвечает за запас",
        }),
      ]),
    );
    expect(review.tasks).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          title: "Проверить стоп-лист и потерянные продажи",
          sourceLabel: "Полевой контекст",
          roleId: "venue_manager",
          learningChecklistTitle: "Если полевая заметка про стоп-лист",
          contextNote: expect.stringContaining(
            "Вопрос: что закончилось, сколько продаж потеряли и кто отвечает за запас?",
          ),
        }),
      ]),
    );
    expect(review.questions).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          role: "manager",
          text: "что закончилось, сколько продаж потеряли и кто отвечает за запас",
        }),
      ]),
    );
  });

  test("connects sales hypotheses with the upsell learning module", () => {
    const review = buildOwnerReview({
      summary,
      dishes,
      categories,
      shifts,
      brief,
      dataQuality: quality,
      dataMode: "live",
      labor: buildReadyLabor(),
      margin: buildReadyMargin(),
      team: buildReadyTeam(),
      teamTasks: [],
      teamAuditEvents: [],
    });

    expect(review.hypotheses).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          title: "Хит продаж нужно защищать как операционный актив",
          role: "service",
          taskSourceLabel: "Продажи и сервис",
          learningModuleId: "sales-eight-upsell",
          learningModuleTitle: "Восьмерка продаж и апселл в сервисе",
          learningChecklistTitle: "Если BI показал точку для апселла",
        }),
      ]),
    );
    expect(review.tasks).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          title: expect.stringContaining("официанты предлагают рядом"),
          roleId: "service",
          sourceLabel: "Продажи и сервис",
          learningModuleId: "sales-eight-upsell",
          learningModuleTitle: "Восьмерка продаж и апселл в сервисе",
          learningChecklistTitle: "Если BI показал точку для апселла",
          contextNote: expect.stringContaining(
            "Урок для команды: Восьмерка продаж и апселл в сервисе.",
          ),
        }),
      ]),
    );
    expect(review.tasks).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          sourceLabel: "Продажи и сервис",
          contextNote: expect.stringContaining(
            "Чеклист: Если BI показал точку для апселла.",
          ),
        }),
      ]),
    );
  });

  test("connects category margin hypotheses with the tech-card learning module", () => {
    const review = buildOwnerReview({
      summary,
      dishes,
      categories,
      shifts,
      brief,
      dataQuality: quality,
      dataMode: "live",
      labor: buildReadyLabor(),
      margin: buildReadyMargin(),
      team: buildReadyTeam(),
      teamTasks: [],
      teamAuditEvents: [],
    });

    expect(review.hypotheses).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          title: "Категория может держать оборот, но не прибыль",
          role: "chef",
          taskSourceLabel: "Маржа и техкарты",
          learningModuleId: "tech-card-discipline",
          learningModuleTitle: "Техкарта как договор внутри команды",
          learningChecklistTitle: "Если категория держит оборот",
          briefingQuestion:
            "какие позиции категории дают деньги, маржу и риск стоп-листа",
        }),
      ]),
    );
    expect(review.tasks).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          title: expect.stringContaining("Проверить маржу"),
          roleId: "chef",
          sourceLabel: "Маржа и техкарты",
          learningModuleId: "tech-card-discipline",
          learningModuleTitle: "Техкарта как договор внутри команды",
          learningChecklistTitle: "Если категория держит оборот",
          contextNote: expect.stringContaining(
            "Урок для команды: Техкарта как договор внутри команды.",
          ),
        }),
      ]),
    );
    expect(review.tasks).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          sourceLabel: "Маржа и техкарты",
          contextNote: expect.stringContaining(
            "Чеклист: Если категория держит оборот.",
          ),
        }),
      ]),
    );
  });

  test("connects revenue drop hypotheses with the shift control learning module", () => {
    const teamTasks: TeamTask[] = [
      {
        id: "task-shift-context",
        title: "Разобрать вечернюю смену",
        source: "copilot",
        sourceLabel: "Выручка и смены",
        priority: "medium",
        status: "in_progress",
        venueId: "venue-1",
        audience: { type: "role", roleId: "venue_manager" },
        dueLabel: "сегодня",
      },
    ];
    const teamComments: TeamTaskComment[] = [
      {
        id: "comment-field-stock",
        venueId: "venue-1",
        taskId: "task-shift-context",
        authorName: "Маша",
        body: "Стоп-лист / закончилось: мята к 21:00.",
        createdAtLabel: "22:30",
      },
    ];
    const review = buildOwnerReview({
      summary,
      dishes,
      categories,
      shifts: [
        {
          shiftId: "weak-shift",
          openTime: "2026-06-25T12:00:00",
          closeTime: "2026-06-25T22:00:00",
          revenue: 20000,
          items: 40,
          employee: "Слабая смена",
        },
        {
          shiftId: "strong-shift",
          openTime: "2026-06-26T12:00:00",
          closeTime: "2026-06-26T22:00:00",
          revenue: 100000,
          items: 220,
          employee: "Сильная смена",
        },
      ],
      brief: {
        ...brief,
        revenue: {
          ...brief.revenue,
          current: 100000,
          previous: 120000,
          deltaPct: -18,
        },
      },
      dataQuality: quality,
      dataMode: "live",
      labor: buildReadyLabor(),
      margin: buildReadyMargin(),
      team: buildReadyTeam(),
      teamTasks,
      teamComments,
      teamAuditEvents: [],
    });

    expect(review.hypotheses).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          title: "Просадка могла прийти из смены, а не из меню",
          taskTitle: expect.stringContaining("Разобрать просадку смены"),
          role: "manager",
          taskSourceLabel: "Выручка и смены",
          impactLabel: expect.stringMatching(/^20\s000\s₽$/),
          learningModuleId: "shift-open-close",
          learningModuleTitle: "Открытие и закрытие смены без хаоса",
          learningChecklistTitle: "Если BI показал слабую смену",
          why: expect.stringMatching(/Недобор к базе: 20\s000\s₽\./),
          check: expect.stringContaining(
            "Сверить с полевым фактом: Проверить стоп-лист и потерянные продажи.",
          ),
        }),
      ]),
    );
    expect(review.hypotheses).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          title: "Просадка могла прийти из смены, а не из меню",
          why: expect.stringMatching(
            /Недобор слабой смены к средней смене периода: 40\s000\s₽\./,
          ),
        }),
      ]),
    );
    expect(review.tasks).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          title: expect.stringContaining("Разобрать просадку смены"),
          roleId: "venue_manager",
          sourceLabel: "Выручка и смены",
          impactLabel: expect.stringMatching(/^20\s000\s₽$/),
          learningModuleId: "shift-open-close",
          learningModuleTitle: "Открытие и закрытие смены без хаоса",
          learningChecklistTitle: "Если BI показал слабую смену",
          contextNote: expect.stringContaining(
            "Урок для команды: Открытие и закрытие смены без хаоса.",
          ),
        }),
      ]),
    );
    expect(review.tasks).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          sourceLabel: "Выручка и смены",
          contextNote: expect.stringContaining(
            "Чеклист: Если BI показал слабую смену.",
          ),
        }),
      ]),
    );
    expect(review.tasks).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          title: expect.stringContaining("Разобрать просадку смены"),
          contextNote: expect.stringMatching(/Недобор к базе: 20\s000\s₽\./),
        }),
      ]),
    );
    expect(review.tasks).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          sourceLabel: "Выручка и смены",
          contextNote: expect.stringContaining(
            "Сверить с полевым фактом: Проверить стоп-лист и потерянные продажи.",
          ),
        }),
      ]),
    );
  });

  test("connects weak shift hypotheses with the shift control learning module", () => {
    const review = buildOwnerReview({
      summary,
      dishes,
      categories,
      shifts: [
        {
          shiftId: "weak-service",
          openTime: "2026-06-25T12:00:00",
          closeTime: "2026-06-25T22:00:00",
          revenue: 20000,
          items: 40,
          employee: "Слабая смена",
        },
        {
          shiftId: "normal-service",
          openTime: "2026-06-26T12:00:00",
          closeTime: "2026-06-26T22:00:00",
          revenue: 100000,
          items: 220,
          employee: "Сильная смена",
        },
      ],
      brief: {
        ...brief,
        revenue: {
          ...brief.revenue,
          current: 120000,
          previous: 120000,
          deltaPct: 0,
        },
      },
      dataQuality: quality,
      dataMode: "live",
      labor: buildReadyLabor(),
      margin: buildReadyMargin(),
      team: buildReadyTeam(),
      teamTasks: [],
      teamAuditEvents: [],
    });

    expect(review.hypotheses).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          title: "Слабую смену нужно объяснить событием",
          taskTitle: expect.stringContaining("Разобрать слабую смену"),
          role: "manager",
          taskSourceLabel: "Выручка и смены",
          impactLabel: expect.stringMatching(/^40\s000\s₽$/),
          learningModuleId: "shift-open-close",
          learningModuleTitle: "Открытие и закрытие смены без хаоса",
          why: expect.stringMatching(
            /Недобор слабой смены к средней смене периода: 40\s000\s₽\./,
          ),
        }),
      ]),
    );
    expect(review.tasks).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          title: expect.stringContaining("Разобрать слабую смену"),
          roleId: "venue_manager",
          sourceLabel: "Выручка и смены",
          impactLabel: expect.stringMatching(/^40\s000\s₽$/),
          contextNote: expect.stringContaining(
            "Урок для команды: Открытие и закрытие смены без хаоса.",
          ),
        }),
      ]),
    );
    expect(review.tasks).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          sourceLabel: "Выручка и смены",
          contextNote: expect.stringContaining(
            "Чеклист: Если BI показал слабую смену.",
          ),
        }),
      ]),
    );
  });

  test("connects weak day hypotheses with the shift control learning module", () => {
    const review = buildOwnerReview({
      summary: {
        ...summary,
        revenue: 120000,
        points: [
          { date: "2026-06-25", revenue: 20000 },
          { date: "2026-06-26", revenue: 100000 },
        ],
      },
      dishes,
      categories,
      shifts,
      brief,
      dataQuality: quality,
      dataMode: "live",
      labor: buildReadyLabor(),
      margin: buildReadyMargin(),
      team: buildReadyTeam(),
      teamTasks: [],
      teamAuditEvents: [],
    });

    expect(review.hypotheses).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          title: "Слабый день нужно объяснить событием",
          role: "manager",
          taskSourceLabel: "Выручка и смены",
          impactLabel: expect.stringMatching(/^80\s000\s₽$/),
          learningModuleId: "shift-open-close",
          learningModuleTitle: "Открытие и закрытие смены без хаоса",
          why: expect.stringMatching(/Разница дня: 80\s000\s₽\./),
        }),
      ]),
    );
  });

  test("turns revenue growth into a repeatable shift playbook task", () => {
    const review = buildOwnerReview({
      summary: {
        ...summary,
        revenue: 150000,
        points: [
          { date: "2026-06-25", revenue: 70000 },
          { date: "2026-06-26", revenue: 80000 },
        ],
      },
      dishes: [],
      categories: [],
      shifts: [
        {
          shiftId: "growth-1",
          openTime: "2026-06-25T12:00:00",
          closeTime: "2026-06-25T22:00:00",
          revenue: 75000,
          items: 90,
          employee: "День 1",
        },
        {
          shiftId: "growth-2",
          openTime: "2026-06-26T12:00:00",
          closeTime: "2026-06-26T22:00:00",
          revenue: 75000,
          items: 95,
          employee: "День 2",
        },
      ],
      brief: {
        ...brief,
        revenue: {
          ...brief.revenue,
          current: 150000,
          previous: 100000,
          deltaPct: 50,
        },
      },
      dataQuality: quality,
      dataMode: "live",
      teamTasks: [],
      teamAuditEvents: [],
    });

    expect(review.verdict).toContain("Период выглядит сильнее базы");
    expect(review.hypotheses).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          title: "Рост нужно превратить в повторяемый сценарий",
          taskTitle: "Зафиксировать, что сработало в росте выручки",
          role: "manager",
          tone: "good",
          taskSourceLabel: "Выручка и смены",
          learningModuleId: "shift-open-close",
          learningChecklistTitle: "Если период вырос к базе",
          briefingQuestion:
            "что именно сработало и как повторить это в следующей похожей смене",
        }),
      ]),
    );
    expect(review.tasks).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          title: "Зафиксировать, что сработало в росте выручки",
          sourceLabel: "Выручка и смены",
          learningModuleId: "shift-open-close",
          learningChecklistTitle: "Если период вырос к базе",
          contextNote: expect.stringContaining(
            "Вопрос: что именно сработало и как повторить это в следующей похожей смене.",
          ),
        }),
      ]),
    );
    expect(review.tasks).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          sourceLabel: "Выручка и смены",
          contextNote: expect.stringContaining(
            "Чеклист: Если период вырос к базе.",
          ),
        }),
      ]),
    );
  });

  test("marks profit readiness ready when data, economics and loops are closed", () => {
    const review = buildOwnerReview({
      summary,
      dishes,
      categories,
      shifts,
      brief,
      dataQuality: quality,
      dataMode: "live",
      labor: buildReadyLabor(),
      margin: buildReadyMargin(),
      team: buildReadyTeam(),
      teamTasks: [],
      teamAuditEvents: [],
    });

    expect(review.readiness).toEqual({
      status: "ready",
      score: 100,
      title: "Можно считать прибыль",
      detail:
        "Реальные данные iiko, ФОТ, себестоимость и Team OS контуры закрыты.",
      missing: [],
      action: null,
      tone: "good",
    });
  });

  test("does not propose creating a task that is already open in Team OS", () => {
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
    const teamTasks: TeamTask[] = [
      {
        id: "task-learning-open",
        venueId: "venue-1",
        title: "Дожать обучение: Маша: закрыть обязательный модуль роли.",
        source: "copilot",
        priority: "medium",
        status: "accepted",
        audience: { type: "role", roleId: "venue_manager" },
        dueLabel: "сегодня",
      },
    ];

    const review = buildOwnerReview({
      summary,
      dishes,
      categories,
      shifts,
      brief,
      dataQuality: quality,
      dataMode: "live",
      team,
      teamTasks,
    });

    expect(review.actions).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          title: "Дожать обучение",
          target: "team-learning",
        }),
      ]),
    );
    expect(
      review.tasks.some((task) => task.title.startsWith("Дожать обучение")),
    ).toBe(false);
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
      learningModuleId: "restaurant-numbers-basics",
      learningModuleTitle: "Цифры ресторана простым языком",
      learningChecklistTitle: "Если ФОТ не считается полностью",
    });
    expect(review.tasks[0].contextNote).toContain(
      "Вопрос: какая ставка или роль нужна, чтобы корректно посчитать ФОТ смены.",
    );
    expect(review.tasks[0].contextNote).toContain(
      "Чеклист: Если ФОТ не считается полностью.",
    );
  });

  test("explains missing iiko shifts in the FOT setup task", () => {
    const staff = [
      {
        id: "manager",
        name: "Управляющий",
        roleId: "venue_manager" as const,
        venueId: "venue-1",
        status: "active" as const,
        shiftLabel: "iiko",
        hourlyRate: 500,
      },
    ];
    const labor = buildLaborBi({ staff, shifts: [] });
    const laborReadiness = buildTeamLaborReadiness(staff, labor);
    const laborSetupProgress = buildTeamLaborSetupProgress(
      staff,
      laborReadiness,
    );

    const review = buildOwnerReview({
      summary,
      dishes,
      categories,
      shifts: [],
      brief,
      dataQuality: quality,
      dataMode: "live",
      labor,
      laborSetupProgress,
    });

    expect(review.tasks[0]).toMatchObject({
      title: expect.stringContaining("Проверить выгрузку смен iiko"),
      roleId: "operations_manager",
      priority: "high",
      sourceLabel: "ФОТ setup",
      learningModuleId: "iiko-cash-discipline",
      learningModuleTitle: "iiko и кассовая дисциплина на смене",
      learningChecklistTitle: "Если Receptor не видит смены iiko",
    });
    expect(review.tasks[0].contextNote).toContain(
      "Вопрос: каких прав, смен или фильтров iiko не хватает для расчета ФОТ.",
    );
    expect(review.tasks[0].contextNote).toContain(
      "Чеклист: Если Receptor не видит смены iiko.",
    );
  });

  test("uses team comments as field context for owner decisions", () => {
    const teamTasks: TeamTask[] = [
      {
        id: "task-shift-context",
        title: "Разобрать вечернюю смену",
        source: "copilot",
        sourceLabel: "Выручка и смены",
        priority: "medium",
        status: "in_progress",
        venueId: "venue-1",
        audience: { type: "role", roleId: "venue_manager" },
        dueLabel: "сегодня",
      },
    ];
    const teamComments: TeamTaskComment[] = [
      {
        id: "comment-field-1",
        venueId: "venue-1",
        taskId: "task-shift-context",
        authorName: "Маша",
        body: "Был конфликт по ожиданию блюда, гости спрашивали лимонад, мята закончилась.",
        createdAtLabel: "22:30",
      },
      {
        id: "comment-system",
        venueId: "venue-1",
        taskId: "task-shift-context",
        authorName: "Receptor",
        body: "Зачем: понять риск. Урок для команды: Цифры ресторана простым языком.",
        createdAtLabel: "10:00",
      },
    ];

    const review = buildOwnerReview({
      summary,
      dishes,
      categories,
      shifts,
      brief,
      dataQuality: quality,
      dataMode: "live",
      teamTasks,
      teamComments,
    });

    expect(review.evidence).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          label: "Поле",
          value: "3 сигналов",
          detail: expect.stringContaining("Конфликты и жалобы"),
          tone: "risk",
        }),
      ]),
    );
    expect(review.actions).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          title: "Разобрать конфликт смены с цифрами",
          target: "team-actions",
          role: "manager",
          sourceLabel: "Полевой контекст",
          impactLabel: "3 сигнала",
          learningModuleId: "shift-brief",
          learningChecklistTitle: "Если полевая заметка про конфликт",
          briefingQuestion:
            "что стало причиной конфликта и повторяется ли это в сменах",
          detail: expect.stringContaining("Связанные факты:"),
        }),
      ]),
    );
    expect(review.hypotheses).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          title: "Разобрать конфликт смены с цифрами",
          check: expect.stringContaining("возвраты"),
          taskSourceLabel: "Полевой контекст",
          impactLabel: "3 сигнала",
          why: expect.stringContaining("Связанные факты:"),
          learningModuleId: "shift-brief",
          briefingQuestion:
            "что стало причиной конфликта и повторяется ли это в сменах",
        }),
      ]),
    );
    expect(review.questions).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          role: "manager",
          text: "что стало причиной конфликта и повторяется ли это в сменах",
        }),
      ]),
    );
    expect(review.tasks).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          title: "Разобрать конфликт смены с цифрами",
          sourceLabel: "Полевой контекст",
          learningModuleTitle: "Брифинг смены и передача контекста",
          learningChecklistTitle: "Если полевая заметка про конфликт",
          contextNote: expect.stringContaining("Полевой факт: Маша"),
        }),
      ]),
    );
    const fieldTaskContext = review.tasks.find(
      (task) => task.sourceLabel === "Полевой контекст",
    )?.contextNote;
    expect(fieldTaskContext).toContain(
      "Вопрос: что стало причиной конфликта и повторяется ли это в сменах?",
    );
    expect(fieldTaskContext).toContain(
      "Чеклист: Если полевая заметка про конфликт.",
    );
    expect(fieldTaskContext).toContain("Проверка: На брифинге");
    expect(fieldTaskContext).toContain("Связанные факты:");
    expect(fieldTaskContext).toContain("Стоп-лист и заготовки");
  expect(fieldTaskContext).toContain(
    "Зачем: связать факты смены с BI, назначить ответственного и убрать повторяемую причину.",
  );
  });

  test("routes service field notes to the upsell learning checklist", () => {
    const teamTasks: TeamTask[] = [
      {
        id: "task-field",
        title: "Полевой контекст смены",
        source: "manager",
        sourceLabel: "Поле",
        priority: "medium",
        status: "in_progress",
        venueId: "venue-1",
        audience: { type: "role", roleId: "venue_manager" },
        dueLabel: "ежедневно",
      },
    ];
    const teamComments: TeamTaskComment[] = [
      {
        id: "comment-service-field",
        venueId: "venue-1",
        taskId: "task-field",
        authorName: "Оля",
        body: "Сервис / продажи: гости хорошо брали лимонад по рекомендации, но не все официанты предлагали закуску к пиву.",
        createdAtLabel: "22:30",
      },
    ];

    const review = buildOwnerReview({
      summary,
      dishes,
      categories,
      shifts,
      brief,
      dataQuality: quality,
      dataMode: "live",
      teamTasks,
      teamComments,
    });

    expect(review.hypotheses).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          title: "Проверить сервис и допродажи",
          taskSourceLabel: "Полевой контекст",
          learningModuleId: "sales-eight-upsell",
          learningModuleTitle: "Восьмерка продаж и апселл в сервисе",
          learningChecklistTitle: "Если BI показал точку для апселла",
          briefingQuestion:
            "что команда реально рекомендовала гостям и где нужен простой скрипт",
        }),
      ]),
    );
    expect(review.tasks).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          title: "Проверить сервис и допродажи",
          sourceLabel: "Полевой контекст",
          learningModuleId: "sales-eight-upsell",
          learningModuleTitle: "Восьмерка продаж и апселл в сервисе",
          learningChecklistTitle: "Если BI показал точку для апселла",
          contextNote: expect.stringContaining(
            "Урок для команды: Восьмерка продаж и апселл в сервисе.",
          ),
        }),
      ]),
    );
    const fieldTaskContext = review.tasks.find(
      (task) => task.title === "Проверить сервис и допродажи",
    )?.contextNote;
    expect(fieldTaskContext).toContain(
      "Чеклист: Если BI показал точку для апселла.",
    );
  });

  test("turns untagged field notes into a Team OS task to connect them with BI", () => {
    const teamTasks: TeamTask[] = [
      {
        id: "task-shift-context",
        title: "Полевой контекст смены",
        source: "manager",
        sourceLabel: "Поле",
        priority: "medium",
        status: "in_progress",
        venueId: "venue-1",
        audience: { type: "role", roleId: "venue_manager" },
        dueLabel: "ежедневно",
      },
    ];
    const teamComments: TeamTaskComment[] = [
      {
        id: "comment-field-plain",
        venueId: "venue-1",
        taskId: "task-shift-context",
        authorName: "Оля",
        body: "Сегодня есть пара наблюдений для утреннего разбора.",
        createdAtLabel: "23:00",
      },
    ];

    const review = buildOwnerReview({
      summary,
      dishes,
      categories,
      shifts,
      brief,
      dataQuality: quality,
      dataMode: "live",
      teamTasks,
      teamComments,
    });

    expect(review.evidence).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          label: "Поле",
          value: "1 заметка",
          detail: expect.stringContaining("Сегодня есть пара наблюдений"),
          tone: "watch",
        }),
      ]),
    );
    expect(review.actions).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          title: "Связать полевую заметку с цифрами",
          sourceLabel: "Полевой контекст",
          impactLabel: "1 заметка",
          learningModuleId: "shift-brief",
          learningChecklistTitle: "Разбор: факт, вопрос, проверка, действие",
          briefingQuestion:
            "какая цифра подтверждает этот факт: выручка, ФОТ, маржа, стоп-лист или отзывы гостей",
        }),
      ]),
    );
    expect(review.hypotheses).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          title: "Связать полевую заметку с цифрами",
          check: expect.stringContaining("выбрать одну цифру"),
          taskSourceLabel: "Полевой контекст",
          learningChecklistTitle: "Разбор: факт, вопрос, проверка, действие",
        }),
      ]),
    );
    expect(review.tasks).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          title: "Связать полевую заметку с цифрами",
          sourceLabel: "Полевой контекст",
          learningModuleTitle: "Брифинг смены и передача контекста",
          learningChecklistTitle: "Разбор: факт, вопрос, проверка, действие",
          contextNote: expect.stringContaining(
            "Вопрос: какая цифра подтверждает этот факт",
          ),
        }),
      ]),
    );
  });
});
