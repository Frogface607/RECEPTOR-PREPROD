import { describe, expect, test } from "vitest";
import type { StaffMember, TeamTask, TeamTaskComment } from "./team-os";
import {
  buildTeamLearningAdoptionNextMove,
  buildTeamLearningAdoptionRows,
  buildTeamLearningAdoptionSignal,
  buildTeamLearningAdoptionTaskDraft,
  findOpenLearningAdoptionTask,
  pickTeamLearningAdoptionFocus,
} from "./team-learning-adoption";
import {
  buildTeamLearningSummaries,
  type TeamLearningProgress,
} from "./team-learning-progress";

const staff: StaffMember[] = [
  {
    id: "service-1",
    name: "Маша",
    roleId: "service",
    venueId: "venue-1",
    status: "active",
    shiftLabel: "зал",
  },
  {
    id: "chef-1",
    name: "Роман",
    roleId: "chef",
    venueId: "venue-1",
    status: "active",
    shiftLabel: "кухня",
  },
];

const serviceProgress: TeamLearningProgress = {
  venueId: "venue-1",
  membershipId: "service-1",
  userId: "user-1",
  moduleId: "service-recommendation",
  bestPercentage: 100,
  lastPercentage: 100,
  correct: 3,
  total: 3,
  passed: true,
  answers: [1, 0, 2],
  completedAt: "2026-06-26T10:00:00.000Z",
  updatedAt: "2026-06-26T10:00:00.000Z",
};

const matchingComment: TeamTaskComment = {
  id: "comment-1",
  venueId: "venue-1",
  taskId: "field-note",
  authorName: "Маша",
  body: 'Итог смены по стандарту "Как рекомендовать блюдо без давления": факт - гости чаще спрашивали лимонад; контекст - жара; когда/сколько - вечер; что проверить - апселл десерта.',
  createdAtLabel: "21:40",
};

describe("team learning adoption", () => {
  test("marks a passed standard as returned when a shift-memory note exists", () => {
    const [summary] = buildTeamLearningSummaries(staff, [serviceProgress]);

    const signal = buildTeamLearningAdoptionSignal({
      summary,
      progress: [serviceProgress],
      comments: [matchingComment],
    });

    expect(signal).toMatchObject({
      status: "returned_memory",
      label: "Стандарт работает",
      moduleId: "service-recommendation",
      memoryCommentId: "comment-1",
      evidenceLabel: "Открыть память смены",
      evidenceHref: "#shift-summary",
    });
    expect(signal.detail).toContain("Receptor запомнил");
  });

  test("asks for a shift fact when the latest passed standard has no memory", () => {
    const [summary] = buildTeamLearningSummaries(staff, [serviceProgress]);

    const signal = buildTeamLearningAdoptionSignal({
      summary,
      progress: [serviceProgress],
      comments: [],
    });

    expect(signal).toMatchObject({
      status: "needs_memory",
      label: "Стандарт сдан — нужен итог",
      moduleId: "service-recommendation",
      memoryCommentId: null,
    });
    expect(signal.detail).toContain("попробовать это в смене");
    expect(signal.detail).toContain("где применил");
  });

  test("waits for learning before asking for operational adoption", () => {
    const [, summary] = buildTeamLearningSummaries(staff, []);

    const signal = buildTeamLearningAdoptionSignal({
      summary,
      progress: [],
      comments: [],
    });

    expect(signal).toMatchObject({
      status: "not_ready",
      moduleId: "kitchen-stop-list",
      memoryCommentId: null,
    });
  });

  test("builds a task draft to return a passed standard to shift memory", () => {
    const [summary] = buildTeamLearningSummaries(staff, [serviceProgress]);
    const signal = buildTeamLearningAdoptionSignal({
      summary,
      progress: [serviceProgress],
      comments: [],
    });

    const draft = buildTeamLearningAdoptionTaskDraft(summary, signal);

    expect(draft).toMatchObject({
      title:
        "Оставить итог смены: Маша — Как рекомендовать блюдо без давления",
      audienceType: "member",
      audienceMemberId: "service-1",
      moduleId: "service-recommendation",
      checklistTitle: "Если стандарт сдан, но нет итога смены",
      dueLabel: "после ближайшей смены",
    });
    expect(draft?.contextNote).toContain("не оставил(а) итог");
    expect(draft?.contextNote).toContain("В память:");
  });

  test("turns adoption signals into one manager next move", () => {
    const [summary] = buildTeamLearningSummaries(staff, [serviceProgress]);
    const needsMemory = buildTeamLearningAdoptionSignal({
      summary,
      progress: [serviceProgress],
      comments: [],
    });
    const returnedMemory = buildTeamLearningAdoptionSignal({
      summary,
      progress: [serviceProgress],
      comments: [matchingComment],
    });

    expect(
      buildTeamLearningAdoptionNextMove({ signal: needsMemory }),
    ).toMatchObject({
      label: "Нужен короткий итог",
      action: "assign_fact",
      actionLabel: "Поручить итог",
    });
    expect(
      buildTeamLearningAdoptionNextMove({
        signal: needsMemory,
        taskExists: true,
      }),
    ).toMatchObject({
      label: "Ждем итог смены",
      action: "none",
    });
    expect(
      buildTeamLearningAdoptionNextMove({ signal: returnedMemory }),
    ).toMatchObject({
      label: "Стандарт работает",
      action: "open_evidence",
      actionLabel: "Открыть итог",
    });
  });

  test("finds an existing open adoption task for the same member and standard", () => {
    const [summary] = buildTeamLearningSummaries(staff, [serviceProgress]);
    const signal = buildTeamLearningAdoptionSignal({
      summary,
      progress: [serviceProgress],
      comments: [],
    });
    const draft = buildTeamLearningAdoptionTaskDraft(summary, signal);
    expect(draft).not.toBeNull();

    const tasks: TeamTask[] = [
      {
        id: "task-1",
        title:
          "Вернуть факт смены: Маша — Как рекомендовать блюдо без давления",
        source: "manager",
        priority: "medium",
        status: "in_progress",
        venueId: "venue-1",
        audience: { type: "member", memberId: "service-1" },
        dueLabel: "после ближайшей смены",
      },
    ];

    expect(findOpenLearningAdoptionTask(tasks, draft!)).toMatchObject({
      id: "task-1",
    });
  });

  test("builds shared adoption rows and picks the owner-visible next focus", () => {
    const summaries = buildTeamLearningSummaries(staff, [serviceProgress]);

    const rows = buildTeamLearningAdoptionRows({
      summaries,
      progress: [serviceProgress],
      comments: [],
      tasks: [],
    });
    const focus = pickTeamLearningAdoptionFocus(rows);

    expect(rows).toHaveLength(2);
    expect(focus).toMatchObject({
      summary: { member: { id: "service-1" } },
      signal: { status: "needs_memory" },
      move: {
        label: "Нужен короткий итог",
        action: "assign_fact",
      },
    });
  });
});
