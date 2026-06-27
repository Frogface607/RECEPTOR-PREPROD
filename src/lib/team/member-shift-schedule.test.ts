import { describe, expect, test } from "vitest";
import { buildLaborBi } from "./labor-bi";
import {
  buildMemberOperationPlan,
  buildMemberLaborProfile,
  buildMemberShiftSchedule,
} from "./member-shift-schedule";
import type { TeamLearningMemberSummary } from "./team-learning-progress";
import type { StaffMember, TeamTask } from "./team-os";

const member: StaffMember = {
  id: "staff-service",
  name: "Маша",
  roleId: "service",
  venueId: "dev-venue",
  status: "active",
  shiftLabel: "зал",
  hourlyRate: 350,
};

describe("buildMemberShiftSchedule", () => {
  test("matches plain iiko employee shifts by staff name", () => {
    const schedule = buildMemberShiftSchedule({
      member,
      shifts: [
        {
          shiftId: "shift-1",
          openTime: "2026-06-26T16:00:00",
          closeTime: "2026-06-27T00:00:00",
          revenue: 90000,
          items: 160,
          employee: "Маша",
        },
      ],
    });

    expect(schedule).toMatchObject([
      {
        shiftId: "shift-1",
        dateKey: "2026-06-26",
        revenue: 90000,
        items: 160,
        hours: 8,
      },
    ]);
    expect(schedule[0]?.timeLabel).toContain("16:00");
  });

  test("matches worker rows by member id and uses worker sales and hours", () => {
    const schedule = buildMemberShiftSchedule({
      member,
      shifts: [
        {
          shiftId: "shift-2",
          openTime: "2026-06-26T12:00:00",
          closeTime: "2026-06-26T22:00:00",
          revenue: 120000,
          items: 220,
          employee: "Смена",
          workers: [
            {
              memberId: "staff-service",
              name: "Мария",
              hours: 7.5,
              sales: 45000,
            },
            {
              memberId: "staff-cook",
              name: "Илья",
              hours: 10,
              sales: 75000,
            },
          ],
        },
      ],
    });

    expect(schedule[0]).toMatchObject({
      shiftId: "shift-2",
      revenue: 45000,
      hours: 7.5,
    });
  });

  test("sorts shifts and skips unrelated employees", () => {
    const schedule = buildMemberShiftSchedule({
      member,
      shifts: [
        {
          shiftId: "late",
          openTime: "2026-06-28T18:00:00",
          closeTime: "2026-06-29T03:00:00",
          revenue: 70000,
          items: 120,
          employee: "Маша",
        },
        {
          shiftId: "other",
          openTime: "2026-06-27T18:00:00",
          closeTime: "2026-06-28T03:00:00",
          revenue: 80000,
          items: 140,
          employee: "Илья",
        },
        {
          shiftId: "early",
          openTime: "2026-06-26T18:00:00",
          closeTime: "2026-06-27T03:00:00",
          revenue: 90000,
          items: 150,
          employee: "Маша",
        },
      ],
    });

    expect(schedule.map((item) => item.shiftId)).toEqual(["early", "late"]);
  });

  test("builds member labor profile from labor BI", () => {
    const labor = buildLaborBi({
      staff: [member],
      shifts: [
        {
          shiftId: "shift-1",
          openTime: "2026-06-26T16:00:00",
          closeTime: "2026-06-27T00:00:00",
          revenue: 90000,
          items: 160,
          employee: "Маша",
        },
      ],
    });

    expect(buildMemberLaborProfile({ member, labor })).toMatchObject({
      status: "ready",
      shifts: 1,
      hours: 8,
      sales: 90000,
      laborCost: 2800,
      revenuePerHour: 11250,
      laborCostPct: 3.1,
      missingRate: false,
    });
  });

  test("marks member labor profile when rate is missing", () => {
    const noRateMember: StaffMember = {
      ...member,
      hourlyRate: undefined,
    };
    const labor = buildLaborBi({
      staff: [noRateMember],
      shifts: [
        {
          shiftId: "shift-1",
          openTime: "2026-06-26T16:00:00",
          closeTime: "2026-06-27T00:00:00",
          revenue: 90000,
          items: 160,
          employee: "Маша",
        },
      ],
    });

    expect(
      buildMemberLaborProfile({ member: noRateMember, labor }),
    ).toMatchObject({
      status: "missing_rate",
      shifts: 1,
      laborCost: 0,
      missingRate: true,
    });
  });

  test("returns an empty labor profile when employee has no shifts", () => {
    expect(buildMemberLaborProfile({ member, labor: null })).toMatchObject({
      status: "no_shifts",
      shifts: 0,
      sales: 0,
      laborCost: 0,
      revenuePerHour: null,
      laborCostPct: null,
    });
  });

  test("builds a personal operation plan from FOT, learning and tasks", () => {
    const plan = buildMemberOperationPlan({
      member,
      tasks: [
        buildTask({
          id: "task-low",
          priority: "medium",
          title: "Проверить фокус продаж",
        }),
        buildTask({
          id: "task-high",
          priority: "high",
          title: "Закрыть жалобу гостя",
        }),
      ],
      schedule: [],
      laborProfile: {
        status: "missing_rate",
        shifts: 2,
        hours: 16,
        sales: 180000,
        laborCost: 0,
        revenuePerHour: 11250,
        laborCostPct: null,
        missingRate: true,
      },
      learning: buildLearningSummary({ canWorkShift: false }),
      nextLearning: { title: "Как рекомендовать блюдо", timeLabel: "7 минут" },
    });

    expect(plan.map((item) => item.id)).toEqual([
      "labor-rate",
      "learning-admission",
      "task-task-high",
    ]);
    expect(plan[0]).toMatchObject({
      title: "Заполнить ставку ФОТ",
      href: "#labor-member-staff-service",
      tone: "risk",
    });
    expect(plan[1]?.detail).toContain("Как рекомендовать блюдо");
    expect(plan[2]?.detail).toBe("Закрыть жалобу гостя");
  });

  test("adds the next shift when the member has no blockers", () => {
    const plan = buildMemberOperationPlan({
      member,
      tasks: [],
      schedule: [
        {
          shiftId: "shift-1",
          dateKey: "2026-06-26",
          dayLabel: "пт, 26.06",
          timeLabel: "16:00 - 00:00",
          revenue: 90000,
          items: 160,
          hours: 8,
        },
      ],
      laborProfile: {
        status: "ready",
        shifts: 1,
        hours: 8,
        sales: 90000,
        laborCost: 2800,
        revenuePerHour: 11250,
        laborCostPct: 3.1,
        missingRate: false,
      },
      learning: buildLearningSummary({ canWorkShift: true }),
    });

    expect(plan).toMatchObject([
      {
        id: "shift-shift-1",
        title: "Проверить смену периода",
        tone: "ready",
      },
    ]);
    expect(plan[0]?.detail).toMatch(/90\s000 ₽/);
  });

  test("shows iiko shift matching as the next action without schedule", () => {
    const plan = buildMemberOperationPlan({
      member,
      tasks: [],
      schedule: [],
      laborProfile: {
        status: "no_shifts",
        shifts: 0,
        hours: 0,
        sales: 0,
        laborCost: 0,
        revenuePerHour: null,
        laborCostPct: null,
        missingRate: false,
      },
      learning: buildLearningSummary({ canWorkShift: true }),
    });

    expect(plan[0]).toMatchObject({
      id: "shift-match",
      href: "#iiko-shift-diagnostics",
      tone: "setup",
    });
  });
});

function buildTask(overrides: Partial<TeamTask>): TeamTask {
  return {
    id: "task",
    title: "Задача",
    source: "manager",
    priority: "medium",
    status: "new",
    venueId: "dev-venue",
    audience: { type: "member", memberId: member.id },
    dueLabel: "сегодня",
    ...overrides,
  };
}

function buildLearningSummary(
  overrides: Partial<TeamLearningMemberSummary>,
): TeamLearningMemberSummary {
  return {
    member,
    items: [],
    totalCount: 1,
    requiredCount: 1,
    requiredMissing: overrides.canWorkShift === false ? 1 : 0,
    completedCount: overrides.canWorkShift === false ? 0 : 1,
    requiredCompleted: overrides.canWorkShift === false ? 0 : 1,
    averageBest: overrides.canWorkShift === false ? 0 : 100,
    status: overrides.canWorkShift === false ? "not_started" : "complete",
    admissionStatus:
      overrides.canWorkShift === false ? "not_started" : "admitted",
    canWorkShift: true,
    nextItem: null,
    lastCompletedAt: "",
    ...overrides,
  };
}
