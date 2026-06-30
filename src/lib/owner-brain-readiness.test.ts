import { describe, expect, test } from "vitest";
import { DEMO_CONTEXT_ANSWERS } from "@/lib/venues/context-questionnaire";
import type { TeamLearningMemberSummary } from "@/lib/team/team-learning-progress";
import type { StaffMember, TeamTask, TeamTaskComment } from "@/lib/team/team-os";
import { buildOwnerBrainReadiness } from "./owner-brain-readiness";

const staff: StaffMember[] = [
  {
    id: "manager",
    name: "Маша",
    roleId: "venue_manager",
    venueId: "venue",
    status: "active",
    shiftLabel: "вечер",
  },
  {
    id: "service",
    name: "Алина",
    roleId: "service",
    venueId: "venue",
    status: "active",
    shiftLabel: "зал",
  },
];

const tasks: TeamTask[] = [
  {
    id: "field",
    title: "Полевой контекст смены",
    source: "manager",
    sourceLabel: "Поле",
    priority: "medium",
    status: "in_progress",
    venueId: "venue",
    audience: { type: "venue", venueId: "venue" },
    dueLabel: "после смены",
  },
];

const comments: TeamTaskComment[] = [
  {
    id: "note",
    venueId: "venue",
    taskId: "field",
    authorName: "Маша",
    body:
      "Итог смены: ливень, гости отменяли брони, закончилась мята, утром проверить стоп-лист.",
    createdAtLabel: "22:30",
  },
];

function learningSummary(
  member: StaffMember,
  canWorkShift = true,
): TeamLearningMemberSummary {
  return {
    member,
    items: [],
    totalCount: 1,
    requiredCount: 1,
    requiredMissing: canWorkShift ? 0 : 1,
    completedCount: canWorkShift ? 1 : 0,
    requiredCompleted: canWorkShift ? 1 : 0,
    averageBest: canWorkShift ? 100 : 0,
    status: canWorkShift ? "complete" : "not_started",
    admissionStatus: canWorkShift ? "admitted" : "not_started",
    canWorkShift,
    nextItem: null,
    lastCompletedAt: canWorkShift ? "2026-06-30T10:00:00.000Z" : "",
  };
}

describe("owner brain readiness", () => {
  test("asks for restaurant profile first when the advisor has no context", () => {
    const readiness = buildOwnerBrainReadiness({
      context: {},
      staff: [],
      tasks: [],
      comments: [],
      learningSummaries: [],
      dataMode: "mock",
    });

    expect(readiness.tone).toBe("risk");
    expect(readiness.nextSource.id).toBe("context");
    expect(readiness.summary).toContain("живой контекст");
    expect(readiness.memoryGraph).toMatchObject({
      tone: "risk",
      summary: "связей пока нет",
      actionLabel: "Нужно связать",
    });
    expect(readiness.fieldMemory).toMatchObject({
      status: "missing",
      title: "Итог смены еще не собран",
      actionLabel: "Поставить задачу",
      nextQuestion: "Что конкретно произошло в смене?",
    });
    expect(readiness.snapshot).toMatchObject([
      {
        id: "known",
        value: "пока ничего надежного",
        tone: "risk",
      },
      {
        id: "missing",
        tone: "watch",
      },
      {
        id: "next",
        sourceId: "context",
      },
    ]);
  });

  test("marks the restaurant brain usable when context, field notes and team are present", () => {
    const readiness = buildOwnerBrainReadiness({
      context: DEMO_CONTEXT_ANSWERS,
      staff,
      tasks,
      comments,
      learningSummaries: staff.map((member) => learningSummary(member)),
      dataMode: "live",
    });

    expect(readiness.score).toBeGreaterThanOrEqual(80);
    expect(readiness.tone).toBe("good");
    expect(readiness.nextSource.id).toBe("context");
    expect(readiness.memoryGraph).toMatchObject({
      tone: "good",
      actionLabel: "Связано",
      detail: "Люди, смена и задачи уже связаны в памяти советника.",
    });
    expect(readiness.memoryGraph.summary).toContain("люди, смена, задачи");
    expect(readiness.sources.find((source) => source.id === "field")?.status).toBe(
      "ready",
    );
    expect(readiness.fieldMemory).toMatchObject({
      status: "ready",
      title: "Последний итог смены",
      value: "1/1",
      actionLabel: "Открыть",
      nextQuestion: null,
      followUpQuestions: [],
      followUpTask: null,
    });
    expect(readiness.fieldMemory.detail).toContain("ливень");
    expect(readiness.snapshot[0]).toMatchObject({
      id: "known",
      value: "Профиль, Люди, Смена, Допуск, Факты",
      tone: "good",
    });
    expect(readiness.snapshot[1]).toMatchObject({
      id: "missing",
      value: "критичных пробелов нет",
      tone: "good",
    });
    expect(readiness.snapshot[2]).toMatchObject({
      id: "next",
      label: "Готово к вопросам",
      tone: "good",
    });
  });

  test("shows learning as the next source when staff is not admitted to shifts", () => {
    const readiness = buildOwnerBrainReadiness({
      context: DEMO_CONTEXT_ANSWERS,
      staff,
      tasks,
      comments,
      learningSummaries: staff.map((member, index) =>
        learningSummary(member, index === 0),
      ),
      dataMode: "live",
    });

    expect(readiness.nextSource.id).toBe("learning");
    expect(readiness.nextSource.detail).toContain("Не допущены");
    expect(readiness.snapshot[1].value).toContain("Допуск: нужно дописать");
    expect(readiness.snapshot[2]).toMatchObject({
      sourceId: "learning",
      value: "Допуск: 1/2",
    });
  });

  test("keeps shift memory in progress when the note has no context or scale", () => {
    const readiness = buildOwnerBrainReadiness({
      context: DEMO_CONTEXT_ANSWERS,
      staff,
      tasks,
      comments: [
        {
          id: "weak-note",
          venueId: "venue",
          taskId: "field",
          authorName: "Маша",
          body: "Итог смены: было странно. Надо обсудить.",
          createdAtLabel: "22:10",
        },
      ],
      learningSummaries: staff.map((member) => learningSummary(member)),
      dataMode: "live",
    });

    const field = readiness.sources.find((source) => source.id === "field");

    expect(field).toMatchObject({
      status: "work",
      value: "0/1",
    });
    expect(field?.detail).toContain("не хватает");
    expect(readiness.fieldMemory).toMatchObject({
      status: "work",
      title: "Итог смены нужно уточнить",
      value: "0/1",
      actionLabel: "Поставить задачу",
      nextQuestion: "Почему это повлияло на гостей, продажи или команду?",
      followUpQuestions: [
        "Почему это повлияло на гостей, продажи или команду?",
        "Когда это случилось и сколько гостей, столов, позиций или денег затронуло?",
      ],
      followUpTask: null,
    });
    expect(readiness.nextSource.id).toBe("field");
    expect(readiness.snapshot[1].value).toContain("Смена: нужно дописать");
    expect(readiness.snapshot[2]).toMatchObject({
      sourceId: "field",
      value: "Смена: 0/1",
    });
  });

  test("shows when missing shift memory is already assigned as a task", () => {
    const readiness = buildOwnerBrainReadiness({
      context: DEMO_CONTEXT_ANSWERS,
      staff,
      tasks: [
        ...tasks,
        {
          id: "shift-memory-task-done",
          venueId: "venue",
          title: "Старая задача по памяти смены",
          source: "copilot",
          sourceLabel: "Память смены",
          learningChecklistTitle: "Если итог смены неполный",
          priority: "medium",
          status: "done",
          audience: { type: "role", roleId: "venue_manager" },
          dueLabel: "вчера",
        },
        {
          id: "shift-memory-task-open",
          venueId: "venue",
          title: "Уточнить итог смены: контекст/причина, когда/сколько",
          source: "copilot",
          sourceLabel: "Память смены",
          learningChecklistTitle: "Если итог смены неполный",
          priority: "medium",
          status: "in_progress",
          audience: { type: "role", roleId: "venue_manager" },
          dueLabel: "до утреннего разбора",
        },
      ],
      comments: [
        {
          id: "weak-note",
          venueId: "venue",
          taskId: "field",
          authorName: "Маша",
          body: "Итог смены: было странно. Надо обсудить.",
          createdAtLabel: "22:10",
        },
      ],
      learningSummaries: staff.map((member) => learningSummary(member)),
      dataMode: "live",
    });

    expect(readiness.fieldMemory).toMatchObject({
      status: "work",
      actionLabel: "Открыть задачу",
      nextQuestion: null,
      followUpTask: {
        title: "Уточнить итог смены: контекст/причина, когда/сколько",
        statusLabel: "в работе",
        dueLabel: "до утреннего разбора",
      },
    });
  });

  test("shows when shift memory answer was received from a follow-up task", () => {
    const readiness = buildOwnerBrainReadiness({
      context: DEMO_CONTEXT_ANSWERS,
      staff,
      tasks: [
        ...tasks,
        {
          id: "shift-memory-task-done",
          venueId: "venue",
          title: "Уточнить итог смены: контекст/причина, когда/сколько",
          source: "copilot",
          sourceLabel: "Память смены",
          learningChecklistTitle: "Если итог смены неполный",
          priority: "medium",
          status: "done",
          audience: { type: "role", roleId: "venue_manager" },
          dueLabel: "до утреннего разбора",
        },
      ],
      comments: [
        {
          id: "weak-note",
          venueId: "venue",
          taskId: "field",
          authorName: "Маша",
          body: "Итог смены: было странно. Надо обсудить.",
          createdAtLabel: "22:10",
        },
        {
          id: "answer",
          venueId: "venue",
          taskId: "shift-memory-task-done",
          authorName: "Маша",
          body:
            "Итог смены: ливень начался после 19:00, отменили 3 брони, гости просили горячие напитки, утром проверить мяту и стоп-лист.",
          createdAtLabel: "22:40",
        },
      ],
      learningSummaries: staff.map((member) => learningSummary(member)),
      dataMode: "live",
    });

    expect(readiness.fieldMemory.detail).toContain("Ответ по задаче получен");
    expect(readiness.fieldMemory).toMatchObject({
      status: "ready",
      actionLabel: "Открыть",
      followUpTask: null,
      answerSource: {
        title: "Уточнить итог смены: контекст/причина, когда/сколько",
        statusLabel: "сделана",
        dueLabel: "до утреннего разбора",
        done: true,
        verified: false,
      },
    });
  });
});
