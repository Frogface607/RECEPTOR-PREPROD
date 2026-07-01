import { describe, expect, test } from "vitest";
import {
  buildRestaurantAdvisorMemory,
  formatRestaurantAdvisorMemoryForAnswer,
  formatRestaurantAdvisorMemoryForPrompt,
} from "./restaurant-memory";
import type {
  StaffMember,
  TeamAuditEvent,
  TeamTask,
  TeamTaskComment,
} from "@/lib/team/team-os";

const staff: StaffMember[] = [
  {
    id: "manager",
    name: "Маша",
    roleId: "venue_manager",
    venueId: "venue",
    status: "active",
    shiftLabel: "зал",
  },
  {
    id: "service",
    name: "Алина",
    roleId: "service",
    venueId: "venue",
    status: "active",
    shiftLabel: "вечер",
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
  {
    id: "stock",
    title: "Проверить стоп-лист",
    source: "manager",
    sourceLabel: "Кухня",
    impactLabel: "вечерняя выручка",
    priority: "high",
    status: "new",
    venueId: "venue",
    audience: { type: "role", roleId: "chef" },
    dueLabel: "до 17:00",
  },
  {
    id: "shift-memory",
    title: "Уточнить итог смены: контекст/причина, когда/сколько",
    source: "copilot",
    sourceLabel: "Память смены",
    learningChecklistTitle: "Если итог смены неполный",
    priority: "medium",
    status: "in_progress",
    venueId: "venue",
    audience: { type: "role", roleId: "venue_manager" },
    dueLabel: "до утреннего разбора",
  },
];

const comments: TeamTaskComment[] = [
  {
    id: "note",
    venueId: "venue",
    taskId: "field",
    authorName: "Маша",
    body:
      "Итог смены: ливень, отменили 3 брони после 19:00. Гости спрашивали безалкогольные коктейли. Утром проверить стоп-лист.",
    createdAtLabel: "22:30",
  },
];

describe("restaurant advisor memory", () => {
  test("builds compact restaurant memory from team workspace", () => {
    const memory = buildRestaurantAdvisorMemory({
      staff,
      tasks,
      comments,
      learningProgress: [],
      learningStandards: [],
    });

    expect(memory.teamSummary).toContain("2 активных сотрудников");
    expect(memory.teamSummary).toContain("Управляющий: 1");
    expect(memory.teamSummary).toContain("Официант: 1");
    expect(memory.fieldSummary).toContain("Итог смены");
    expect(memory.fieldMemoryQuality).toBe("полных итогов смены: 1/1");
    expect(memory.fieldMemoryTaskStatus).toContain("Уточнить итог смены");
    expect(memory.fieldMemoryTaskStatus).toContain("в работе");
    expect(memory.fieldMemoryFollowUpQuestions).toEqual([]);
    expect(memory.memberSignals.join("\n")).toContain("Маша");
    expect(memory.memberSignals.join("\n")).toContain("итоги смены: 1/1");
    expect(memory.memberSignals.join("\n")).toContain("Алина");
    expect(memory.memberSignals.join("\n")).toContain("нет итога смены");
    expect(memory.fieldSignals.join("\n")).toContain("Погода");
    expect(memory.openTasks[0]).toContain("Проверить стоп-лист");
    expect(memory.learningGaps[0]).toContain("Маша");
    expect(memory.learningAdoptionGaps).toEqual([]);
    expect(memory.closedStandardFollowUps).toEqual([]);
    expect(memory.memoryGraph.join("\n")).toContain("Маша -> роль");
    expect(memory.memoryGraph.join("\n")).toContain("оставил(а) итог смены");
    expect(memory.memoryGraphMarkdown).toContain("# Карта памяти ресторана");
    expect(memory.memoryGraphMarkdown).toContain("person:маша");
    expect(memory.memoryGraphTrace?.join("\n")).toContain("Люди: Маша");
    expect(memory.memoryGraphTrace?.join("\n")).not.toContain("->");
    expect(memory.memoryGraphBrief).toMatchObject({
      status: "ready",
      sourceLabels: ["люди", "смена", "задачи"],
      missingLabels: [],
    });
  });

  test("suggests briefing questions when shift memory is incomplete and not assigned", () => {
    const memory = buildRestaurantAdvisorMemory({
      staff,
      tasks: tasks.filter((task) => task.id !== "shift-memory"),
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
      learningProgress: [],
      learningStandards: [],
    });

    expect(memory.fieldMemoryQuality).toContain("память смены неполная");
    expect(memory.fieldMemoryTaskStatus).toBeNull();
    expect(memory.fieldMemoryFollowUpQuestions).toEqual([
      "Почему это повлияло на гостей, продажи или команду?",
      "Когда это случилось и сколько гостей, столов, позиций или денег затронуло?",
    ]);
  });

  test("tracks passed standards that have not returned a shift-memory fact", () => {
    const memory = buildRestaurantAdvisorMemory({
      staff,
      tasks,
      comments,
      learningProgress: [
        {
          venueId: "venue",
          membershipId: "service",
          userId: "user-service",
          moduleId: "service-recommendation",
          bestPercentage: 100,
          lastPercentage: 100,
          correct: 3,
          total: 3,
          passed: true,
          answers: [1, 0, 2],
          completedAt: "2026-06-26T10:00:00.000Z",
          updatedAt: "2026-06-26T10:00:00.000Z",
        },
      ],
      learningStandards: [],
    });

    expect(memory.learningAdoptionGaps).toEqual([
      "Алина: Как рекомендовать блюдо без давления сдан, нужен факт смены после практики",
    ]);
    expect(memory.memoryGraph.join("\n")).toContain(
      "Алина -> стандарт ждет факт смены -> Как рекомендовать блюдо без давления",
    );
    expect(memory.memoryGraphTrace?.join("\n")).toContain("Стандарты: Алина");
    expect(memory.memoryGraphBrief).toMatchObject({
      status: "work",
      sourceLabels: ["люди", "смена", "стандарты", "задачи"],
      nextAction: "добрать факт стандарта из смены",
    });
  });

  test("feeds closed standards into advisor memory as shift fact follow-ups", () => {
    const auditEvents: TeamAuditEvent[] = [
      {
        id: "audit-standard-closed",
        venueId: "venue",
        type: "task_status_updated",
        sourceLabel: "Стандарт",
        impactLabel: "1 допуск",
        targetType: "task",
        targetId: "admission-task",
        summary:
          "Автоматически закрыта задача стандарта после сдачи: Как рекомендовать блюдо без давления.",
        createdAtLabel: "12:10",
      },
    ];

    const memory = buildRestaurantAdvisorMemory({
      staff,
      tasks: [
        ...tasks,
        {
          id: "admission-task",
          title: "Пройти стандарт: Как рекомендовать блюдо без давления",
          source: "manager",
          sourceLabel: "Стандарт",
          priority: "medium",
          status: "done",
          venueId: "venue",
          audience: { type: "member", memberId: "service" },
          dueLabel: "до смены",
        },
      ],
      comments,
      auditEvents,
      learningProgress: [],
      learningStandards: [],
    });

    expect(memory.closedStandardFollowUps).toEqual([
      "Алина: Как рекомендовать блюдо без давления закрыт; после смены нужен факт: где применили стандарт, что изменилось и что проверить утром",
    ]);
  });

  test("formats memory for advisor prompt", () => {
    const text = formatRestaurantAdvisorMemoryForPrompt({
      teamSummary: "2 активных сотрудников",
      fieldSummary: "Память смены: ливень и стоп-лист",
      fieldSignals: ["Погода: ливень"],
      fieldMemoryQuality: "полных итогов смены: 1/1",
      fieldMemoryTaskStatus:
        "Уточнить итог смены: контекст/причина (в работе, до утреннего разбора)",
      fieldMemoryFollowUpQuestions: [],
      memberSignals: ["Маша (Управляющий): итоги смены: 1/1"],
      openTasks: ["Проверить стоп-лист — до 17:00"],
      learningGaps: ["Алина: Как рекомендовать блюдо без давления"],
      learningAdoptionGaps: [
        "Алина: Как рекомендовать блюдо без давления сдан, нужен факт смены после практики",
      ],
      closedStandardFollowUps: [
        "Алина: Как рекомендовать блюдо без давления закрыт; после смены нужен факт",
      ],
      memoryGraph: [
        "Маша -> оставил(а) итог смены -> Поле: ливень и стоп-лист",
      ],
      memoryGraphTrace: [
        "Люди: Маша — Управляющий.",
        "Смена: Маша дал(а) контекст — ливень и стоп-лист.",
      ],
      memoryGraphBrief: {
        relationCount: 3,
        sourceLabels: ["люди", "смена", "задачи"],
        missingLabels: [],
        status: "ready",
        summary: "3 связей: люди, смена, задачи",
        nextAction: "можно спрашивать советника о причинах и действиях",
      },
    });

    expect(text).toContain("Память ресторана");
    expect(text).toContain("Сигналы с поля");
    expect(text).toContain("Качество памяти смены");
    expect(text).toContain("Добор памяти смены уже поставлен");
    expect(text).toContain("Люди и допуск");
    expect(text).toContain("Учебные пробелы");
    expect(text).toContain("Стандарты без факта смены");
    expect(text).toContain("Закрытые стандарты ждут факта смены");
    expect(text).toContain("Связи памяти");
    expect(text).toContain("Карта памяти");
    expect(text).toContain("Почему так думаю");
    expect(text).toContain("Маша -> оставил(а) итог смены");
  });

  test("formats shift memory follow-up questions for advisor prompt", () => {
    const text = formatRestaurantAdvisorMemoryForPrompt({
      teamSummary: "2 активных сотрудника",
      fieldSummary: "Итог смены: было странно",
      fieldSignals: [],
      fieldMemoryQuality: "память смены неполная: не хватает контекста",
      fieldMemoryTaskStatus: null,
      fieldMemoryFollowUpQuestions: [
        "Почему это повлияло на гостей, продажи или команду?",
      ],
      memberSignals: [],
      openTasks: [],
      learningGaps: [],
      learningAdoptionGaps: [],
      closedStandardFollowUps: [],
      memoryGraph: [],
    });

    expect(text).toContain("Вопросы для добора памяти смены");
    expect(text).toContain("Почему это повлияло");
  });

  test("formats a compact memory summary for user-facing answers", () => {
    const text = formatRestaurantAdvisorMemoryForAnswer({
      teamSummary: "2 активных сотрудников",
      fieldSummary: "Итог смены: ливень и стоп-лист",
      fieldSignals: ["Погода: ливень", "Стоп-лист: мята"],
      fieldMemoryQuality: "память смены неполная: не хватает контекста, когда/сколько",
      fieldMemoryTaskStatus:
        "Уточнить итог смены: контекст/причина (в работе, до утреннего разбора)",
      fieldMemoryFollowUpQuestions: [],
      memberSignals: ["Маша (Управляющий): итог неполный"],
      openTasks: ["Проверить стоп-лист — до 17:00"],
      learningGaps: ["Алина: Как рекомендовать блюдо без давления"],
      learningAdoptionGaps: [
        "Алина: Как рекомендовать блюдо без давления сдан, нужен факт смены после практики",
      ],
      closedStandardFollowUps: [
        "Алина: Как рекомендовать блюдо без давления закрыт; после смены нужен факт",
      ],
      memoryGraph: ["Маша -> оставил(а) итог смены -> Поле: ливень"],
      memoryGraphTrace: [
        "Люди: Маша — Управляющий.",
        "Смена: Маша дал(а) контекст — ливень.",
      ],
      memoryGraphBrief: {
        relationCount: 3,
        sourceLabels: ["люди", "смена", "задачи"],
        missingLabels: [],
        status: "ready",
        summary: "3 связей: люди, смена, задачи",
        nextAction: "можно спрашивать советника о причинах и действиях",
      },
    });

    expect(text).toContain("Что уже знаю");
    expect(text).toContain("Последняя память смены");
    expect(text).toContain("Память смены неполная");
    expect(text).toContain("Добор памяти уже в работе");
    expect(text).toContain("Карта памяти");
    expect(text).toContain("Почему так думаю");
    expect(text).toContain("Стандарт нужно проверить в смене");
    expect(text).toContain("Закрытый стандарт ждет факт смены");
    expect(text).toContain("Первый учебный пробел");
    expect(text).not.toContain("Сигналы с поля");
    expect(text).not.toContain("Открытые действия:");
    expect(text).not.toContain("->");
  });

  test("formats next briefing question when no shift memory task is open", () => {
    const text = formatRestaurantAdvisorMemoryForAnswer({
      teamSummary: "2 активных сотрудника",
      fieldSummary: "Итог смены: было странно",
      fieldSignals: [],
      fieldMemoryQuality: "память смены неполная: не хватает контекста",
      fieldMemoryTaskStatus: null,
      fieldMemoryFollowUpQuestions: [
        "Почему это повлияло на гостей, продажи или команду?",
      ],
      memberSignals: [],
      openTasks: [],
      learningGaps: [],
      learningAdoptionGaps: [],
      closedStandardFollowUps: [],
      memoryGraph: [],
    });

    expect(text).toContain("Следующий вопрос для брифа");
    expect(text).toContain("Почему это повлияло");
  });
});
