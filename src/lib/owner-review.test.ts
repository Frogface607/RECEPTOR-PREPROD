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
        }),
      ]),
    );
    expect(review.tasks[0]).toMatchObject({
      title: expect.stringContaining("Сотрудник дорогой к выручке"),
      priority: "high",
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

  test("shows operational proof from open tasks and recently closed loops", () => {
    const teamTasks: TeamTask[] = [
      {
        id: "task-open",
        venueId: "venue-1",
        title: "Разобрать дорогую смену",
        source: "copilot",
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
      ]),
    );
    expect(review.operationalPulse).toMatchObject({
      title: "Есть срочные действия команды",
      tone: "risk",
      openTasks: 1,
      urgentOpenTasks: 1,
      closedLoops: 1,
      recentEvents: [
        expect.objectContaining({
          label: "Закрыто",
          summary: expect.stringContaining("Автоматически закрыта задача"),
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
    expect(review.readiness.detail).toContain("1 открытая задача Team OS");
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
      detail: "Live-данные, ФОТ, себестоимость и Team OS контуры закрыты.",
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
    });
  });
});
