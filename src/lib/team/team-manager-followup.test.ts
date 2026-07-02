import { describe, expect, test } from "vitest";
import { buildLaborBi } from "./labor-bi";
import { buildTeamManagerFollowUp } from "./team-manager-followup";
import type { TeamLaborReadiness } from "./team-labor-readiness";
import type { TeamLearningMemberSummary } from "./team-learning-progress";
import type { TeamShiftPlanVarianceSummary } from "./team-shift-plan-variance";
import type {
  StaffMember,
  TeamAnnouncement,
  TeamAnnouncementRead,
  TeamTask,
} from "./team-os";

const manager: StaffMember = {
  id: "manager-1",
  name: "Мария",
  roleId: "venue_manager",
  venueId: "venue-1",
  status: "active",
  shiftLabel: "зал",
  shiftPay: 5000,
};

const waiter: StaffMember = {
  id: "waiter-1",
  name: "Илья",
  roleId: "service",
  venueId: "venue-1",
  status: "active",
  shiftLabel: "вечер",
};

const readyLabor: TeamLaborReadiness = {
  status: "ready",
  totalStaff: 2,
  activeStaff: 2,
  readyStaff: 2,
  missingStaff: [],
  coveragePct: 100,
  source: "iiko",
  iikoStatus: "ready",
  iikoStaffShifts: 2,
  iikoRevenueCoveragePct: 100,
  iikoUnpricedStaffShifts: 0,
  iikoUnpricedRevenue: 0,
  iikoBlockers: [],
};

const readyVariance: TeamShiftPlanVarianceSummary = {
  plannedShifts: 2,
  actualShifts: 2,
  coveredActualShifts: 2,
  planCoveragePct: 100,
  plannedHours: 16,
  actualHours: 16,
  hoursDelta: 0,
  plannedLaborCost: 10000,
  actualLaborCost: 10000,
  laborDelta: 0,
  unplannedActualShifts: 0,
  missedPlanShifts: 0,
  dayOffWorkedShifts: 0,
  hourVarianceShifts: 0,
  missingRateShifts: 0,
  issues: [],
};

function learningSummary(
  member: StaffMember,
  overrides: Partial<TeamLearningMemberSummary> = {},
): TeamLearningMemberSummary {
  return {
    member,
    items: [],
    totalCount: 0,
    requiredCount: 0,
    requiredMissing: 0,
    completedCount: 0,
    requiredCompleted: 0,
    averageBest: 100,
    status: "complete",
    admissionStatus: "admitted",
    canWorkShift: true,
    nextItem: null,
    lastCompletedAt: "",
    ...overrides,
  };
}

describe("buildTeamManagerFollowUp", () => {
  test("prioritizes urgent tasks and real FOT blockers", () => {
    const tasks: TeamTask[] = [
      {
        id: "task-urgent",
        venueId: "venue-1",
        title: "Проверить стоп-лист перед посадкой",
        source: "copilot",
        priority: "high",
        status: "new",
        audience: { type: "role", roleId: "venue_manager" },
        dueLabel: "сейчас",
      },
    ];
    const labor: TeamLaborReadiness = {
      ...readyLabor,
      status: "partial",
      coveragePct: 55,
      iikoStatus: "partial",
      iikoUnpricedStaffShifts: 1,
      iikoUnpricedRevenue: 80000,
      iikoBlockers: [
        {
          name: "Илья",
          roleId: "service",
          shifts: 1,
          hours: 8,
          sales: 80000,
          reason: "missing-rate",
          action: "set-rate",
        },
      ],
    };

    const followUp = buildTeamManagerFollowUp({
      tasks,
      laborReadiness: labor,
      learningSummaries: [learningSummary(manager), learningSummary(waiter)],
      shiftPlanVariance: readyVariance,
    });

    expect(followUp).toMatchObject({
      status: "blocked",
      urgentTasks: 1,
      laborCoveragePct: 55,
    });
    expect(followUp.items[0]).toMatchObject({
      id: "urgent-tasks",
      title: "Закрыть срочные поручения",
      href: "#team-actions",
      tone: "risk",
    });
    expect(followUp.items[1]).toMatchObject({
      id: "labor-iiko",
      title: "Заполнить ставку ФОТ",
      href: "#labor-rates",
      metric: "55% ФОТ",
      taskDraft: {
        title: "Заполнить ставку ФОТ: Илья",
        roleId: "service",
        priority: "medium",
        sourceLabel: "ФОТ и смены",
        impactLabel: "80 000 ₽",
        learningModuleId: "restaurant-numbers-basics",
        learningChecklistTitle: "Если ФОТ не считается полностью",
        contextNote: expect.stringContaining("80 000 ₽ выручки без точного ФОТ"),
      },
    });
  });

  test("uses impact-aware task queue for the next urgent task", () => {
    const tasks: TeamTask[] = [
      {
        id: "task-small",
        venueId: "venue-1",
        title: "Проверить малую смену",
        source: "copilot",
        sourceLabel: "ФОТ и смены",
        impactLabel: "10 000 ₽",
        priority: "high",
        status: "new",
        audience: { type: "role", roleId: "venue_manager" },
        dueLabel: "сегодня",
      },
      {
        id: "task-large",
        venueId: "venue-1",
        title: "Разобрать дорогую смену",
        source: "copilot",
        sourceLabel: "ФОТ и смены",
        impactLabel: "120 000 ₽",
        priority: "high",
        status: "new",
        audience: { type: "role", roleId: "venue_manager" },
        dueLabel: "сегодня",
      },
    ];

    const followUp = buildTeamManagerFollowUp({
      tasks,
      laborReadiness: readyLabor,
      learningSummaries: [learningSummary(manager), learningSummary(waiter)],
      shiftPlanVariance: readyVariance,
    });

    expect(followUp.items[0]).toMatchObject({
      id: "urgent-tasks",
      detail: expect.stringContaining("Разобрать дорогую смену"),
      taskDraft: expect.objectContaining({
        title: "Разобрать срочное поручение: Разобрать дорогую смену",
      }),
    });
  });

  test("adds learning admission and plan/fact follow-up", () => {
    const variance: TeamShiftPlanVarianceSummary = {
      ...readyVariance,
      planCoveragePct: 50,
      missedPlanShifts: 1,
      issues: [
        {
          id: "waiter-1-2026-06-28-missed",
          member: waiter,
          roleTitle: "Зал",
          dateKey: "2026-06-28",
          dateLabel: "28.06",
          status: "missed_plan",
          tone: "risk",
          plannedShifts: 1,
          actualShifts: 0,
          plannedHours: 8,
          actualHours: 0,
          hoursDelta: -8,
          plannedLaborCost: 4000,
          actualLaborCost: 0,
          laborDelta: -4000,
          revenue: 0,
        },
      ],
    };

    const followUp = buildTeamManagerFollowUp({
      tasks: [],
      laborReadiness: readyLabor,
      learningSummaries: [
        learningSummary(manager),
        learningSummary(waiter, {
          requiredCount: 1,
          requiredMissing: 1,
          averageBest: 0,
          status: "not_started",
          admissionStatus: "not_started",
          canWorkShift: false,
          nextItem: {
            id: "service-standard",
            title: "Стандарт сервиса",
            description: "Короткий материал",
            timeLabel: "5 мин",
            status: "required",
            roles: ["service"],
            passPercentage: 80,
            sections: [],
            quiz: [],
          },
        }),
      ],
      shiftPlanVariance: variance,
    });

    expect(followUp).toMatchObject({
      status: "blocked",
      blockedAdmissions: 1,
      planCoveragePct: 50,
    });
    expect(followUp.items).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          id: "learning-admission",
          title: "Дать допуск к смене",
          href: "#learning-progress",
          taskDraft: expect.objectContaining({
            audienceMemberId: "waiter-1",
            title: expect.stringContaining("Закрыть допуск к смене"),
          }),
        }),
        expect.objectContaining({
          id: "plan-fact",
          title: "Разобрать план/факт",
          href: "#shift-plan-variance",
          tone: "risk",
          taskDraft: expect.objectContaining({
            priority: "high",
            sourceLabel: "План/факт",
            impactLabel: "50% план",
          }),
        }),
      ]),
    );
  });

  test("adds follow-up for unread important announcements", () => {
    const announcements: TeamAnnouncement[] = [
      {
        id: "announcement-service-focus",
        venueId: "venue-1",
        title: "Зал: фокус на вечер",
        body: "Каждый стол получает рекомендацию по ужину.",
        priority: "important",
        audience: { type: "role", roleId: "service" },
        createdByName: "Мария",
        createdAtLabel: "13:00",
      },
    ];
    const announcementReads: TeamAnnouncementRead[] = [
      {
        announcementId: "announcement-service-focus",
        memberId: "waiter-1",
        readAtLabel: "13:05",
      },
    ];
    const secondWaiter: StaffMember = {
      id: "waiter-2",
      name: "Оля",
      roleId: "service",
      venueId: "venue-1",
      status: "active",
      shiftLabel: "вечер",
    };

    const followUp = buildTeamManagerFollowUp({
      staff: [manager, waiter, secondWaiter],
      tasks: [],
      laborReadiness: readyLabor,
      learningSummaries: [
        learningSummary(manager),
        learningSummary(waiter),
        learningSummary(secondWaiter),
      ],
      shiftPlanVariance: readyVariance,
      announcements,
      announcementReads,
    });

    expect(followUp).toMatchObject({
      status: "attention",
      unreadImportantAnnouncements: 1,
    });
    expect(followUp.items[0]).toMatchObject({
      id: "announcement-reads",
      title: "Дожать подтверждение объявления",
      href: "#team-announcement-announcement-service-focus",
      metric: "1 без ответа",
      taskDraft: {
        priority: "medium",
        roleId: "venue_manager",
        sourceLabel: "Связь",
        impactLabel: "1 без ответа",
        title: expect.stringContaining("Зал: фокус на вечер"),
        learningModuleId: "shift-brief",
        learningChecklistTitle: "Если команда не подтвердила важный фокус",
        contextNote: expect.stringContaining("не подтвердили 1 из 2"),
      },
    });
  });

  test("adds follow-up for expensive priced employee shifts", () => {
    const labor = buildLaborBi({
      shifts: [
        {
          shiftId: "shift-expensive-manager",
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

    const followUp = buildTeamManagerFollowUp({
      staff: [manager, waiter],
      tasks: [],
      laborReadiness: readyLabor,
      labor,
      learningSummaries: [learningSummary(manager), learningSummary(waiter)],
      shiftPlanVariance: readyVariance,
    });

    expect(followUp).toMatchObject({
      status: "blocked",
      laborCoveragePct: 100,
    });
    expect(followUp.items[0]).toMatchObject({
      id: "labor-employee-performance",
      title: "Сотрудник дорогой к выручке",
      href: "#labor-member-manager-1",
      metric: "36% ФОТ",
      taskDraft: {
        priority: "high",
        roleId: "venue_manager",
        audienceMemberId: "manager-1",
        audienceMemberName: "Мария",
        sourceLabel: "ФОТ и смены",
        impactLabel: "36% ФОТ",
        learningModuleId: "restaurant-numbers-basics",
        learningChecklistTitle: "Если BI показал перерасход ФОТ",
        contextNote: expect.stringContaining("какая смена, человек или ставка"),
      },
    });
  });

  test("returns a ready follow-up when manager has no blockers", () => {
    const followUp = buildTeamManagerFollowUp({
      tasks: [],
      laborReadiness: readyLabor,
      learningSummaries: [learningSummary(manager), learningSummary(waiter)],
      shiftPlanVariance: readyVariance,
    });

    expect(followUp).toMatchObject({
      status: "ready",
      title: "Команда под контролем",
      openTasks: 0,
      urgentTasks: 0,
      blockedAdmissions: 0,
      laborCoveragePct: 100,
      planCoveragePct: 100,
    });
    expect(followUp.items[0]).toMatchObject({
      id: "ready",
      tone: "good",
      taskDraft: null,
    });
  });
});
