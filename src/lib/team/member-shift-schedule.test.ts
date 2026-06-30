import { describe, expect, test } from "vitest";
import { buildLaborBi } from "./labor-bi";
import {
  buildMemberDailyRoute,
  buildMemberOperationPlan,
  buildMemberSecondBrainProfile,
  buildMemberLaborProfile,
  buildMemberShiftSchedule,
} from "./member-shift-schedule";
import type { TeamLearningMemberSummary } from "./team-learning-progress";
import type { StaffMember, TeamAnnouncement, TeamTask } from "./team-os";

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

  test("adds unread important announcements before regular tasks", () => {
    const plan = buildMemberOperationPlan({
      member,
      tasks: [
        buildTask({
          id: "task-medium",
          priority: "medium",
          title: "Проверить витрину перед сменой",
        }),
      ],
      schedule: [],
      laborProfile: null,
      learning: buildLearningSummary({ canWorkShift: true }),
      announcements: [
        buildAnnouncement({
          id: "announcement-service",
          title: "Новый стоп-лист на вечер",
          priority: "important",
          audience: { type: "role", roleId: "service" },
        }),
      ],
      announcementReads: [],
    });

    expect(plan.map((item) => item.id)).toEqual([
      "announcement-announcement-service",
      "task-task-medium",
    ]);
    expect(plan[0]).toMatchObject({
      title: "Подтвердить важное объявление",
      detail: "Новый стоп-лист на вечер",
      href: "#team-announcement-announcement-service",
      tone: "work",
      announcementId: "announcement-service",
    });
  });

  test("skips important announcements already read by the member", () => {
    const plan = buildMemberOperationPlan({
      member,
      tasks: [
        buildTask({
          id: "task-medium",
          priority: "medium",
          title: "Проверить витрину перед сменой",
        }),
      ],
      schedule: [],
      laborProfile: null,
      learning: buildLearningSummary({ canWorkShift: true }),
      announcements: [
        buildAnnouncement({
          id: "announcement-service",
          priority: "important",
          audience: { type: "role", roleId: "service" },
        }),
      ],
      announcementReads: [
        {
          announcementId: "announcement-service",
          memberId: member.id,
          readAtLabel: "12:00",
        },
      ],
    });

    expect(plan[0]).toMatchObject({
      id: "task-task-medium",
      taskId: "task-medium",
    });
  });

  test("builds a shift route that starts with unread briefing", () => {
    const route = buildMemberDailyRoute({
      member,
      tasks: [],
      comments: [],
      learning: buildLearningSummary({ canWorkShift: true }),
      announcements: [
        buildAnnouncement({
          id: "announcement-service",
          title: "Сегодня продаем лимонад без мяты",
          priority: "important",
          audience: { type: "role", roleId: "service" },
        }),
      ],
      announcementReads: [],
    });

    expect(route.readyCount).toBe(2);
    expect(route.totalCount).toBe(4);
    expect(route.focus).toMatchObject({
      id: "briefing",
      title: "Прочитать бриф",
      action: "Подтвердить",
      href: "#team-announcement-announcement-service",
    });
    expect(route.items.map((item) => item.id)).toEqual([
      "briefing",
      "learning",
      "task",
      "shift_memory",
    ]);
  });

  test("routes the employee to shift memory after briefing, learning and tasks", () => {
    const route = buildMemberDailyRoute({
      member,
      tasks: [],
      comments: [],
      learning: buildLearningSummary({ canWorkShift: true }),
      announcements: [],
      announcementReads: [],
    });

    expect(route.focus).toMatchObject({
      id: "shift_memory",
      status: "нет итога",
      href: "#shift-summary",
    });
    expect(route.headline).toContain("память ресторана");
  });

  test("marks the route complete when the employee left a shift note", () => {
    const route = buildMemberDailyRoute({
      member,
      tasks: [],
      comments: [
        {
          id: "comment-field",
          venueId: "dev-venue",
          taskId: "task-field",
          authorName: "Маша",
          body: "Итог смены: гости просили безалкогольный коктейль, утром проверить мяту.",
          createdAtLabel: "23:10",
        },
      ],
      learning: buildLearningSummary({ canWorkShift: true }),
      announcements: [],
      announcementReads: [],
    });

    expect(route.readyCount).toBe(4);
    expect(route.headline).toContain("закрыта");
    expect(route.focus.id).toBe("shift_memory");
    expect(route.focus.action).toBe("Дополнить");
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

  test("builds a second-brain profile from learning, tasks and field notes", () => {
    const profile = buildMemberSecondBrainProfile({
      member,
      tasks: [
        buildTask({
          id: "task-high",
          priority: "high",
          title: "Разобрать жалобу гостя",
        }),
      ],
      comments: [
        {
          id: "comment-field",
          venueId: "dev-venue",
          taskId: "task-high",
          authorName: "Маша",
          body: "Итог смены: гости просили безалкогольный коктейль, к 21:00 закончилась мята.",
          createdAtLabel: "23:10",
        },
      ],
      schedule: [],
      laborProfile: null,
      learning: buildLearningSummary({ canWorkShift: false }),
      nextLearning: {
        title: "Как рекомендовать блюдо",
        timeLabel: "7 минут",
      },
    });

    expect(profile).toMatchObject({
      title: "Маша: рабочий контекст",
      tags: expect.arrayContaining(["Service", "активен", "нужен допуск", "есть поле"]),
      nextQuestion: "Что мешает пройти стандарт «Как рекомендовать блюдо» до смены?",
    });
    expect(profile.facts).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          label: "Обучение",
          value: "не начато",
          tone: "risk",
        }),
        expect.objectContaining({
          label: "Поле",
          value: "1",
          detail: expect.stringContaining("Итог смены"),
        }),
      ]),
    );
  });

  test("asks for a shift summary when the member has no field context", () => {
    const profile = buildMemberSecondBrainProfile({
      member,
      tasks: [],
      comments: [],
      schedule: [],
      laborProfile: null,
      learning: buildLearningSummary({ canWorkShift: true }),
    });

    expect(profile.facts).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          label: "Поле",
          value: "нет итога",
          tone: "setup",
        }),
      ]),
    );
    expect(profile.nextQuestion).toContain("Что произошло на последней смене");
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

function buildAnnouncement(
  overrides: Partial<TeamAnnouncement>,
): TeamAnnouncement {
  return {
    id: "announcement",
    venueId: "dev-venue",
    title: "Объявление",
    body: "Текст объявления",
    priority: "normal",
    audience: { type: "venue", venueId: "dev-venue" },
    createdByName: "Управляющий",
    createdAtLabel: "12:00",
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
