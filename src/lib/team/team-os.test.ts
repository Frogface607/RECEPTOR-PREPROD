import { describe, expect, test } from "vitest";
import {
  buildShiftMemoryTaskAnswerComment,
  buildRoleHome,
  countAnnouncementReads,
  getTeamRole,
  hasAnnouncementRead,
  isShiftMemoryFollowUpTask,
  listAnnouncementsForRole,
  listCommentsForTask,
  listRolePermissions,
  listTasksForMember,
  listTasksForRole,
  roleCan,
  taskChecklistHintFromContext,
  taskContextBriefDisplayFromContext,
  taskContextBriefFromContext,
  taskContextWithoutLearningHint,
  taskLearningHintFromContext,
  taskShiftMemoryQuestionFromContext,
} from "./team-os";
import { getFieldNoteReadiness } from "./field-note-input";

describe("Team OS roles and permissions", () => {
  test("keeps owner-level cockpit hidden from service staff", () => {
    expect(roleCan("owner", "view_owner_cockpit")).toBe(true);
    expect(roleCan("service", "view_owner_cockpit")).toBe(false);
    expect(roleCan("service", "complete_own_tasks")).toBe(true);
  });

  test("builds role home from permissions and visible tasks", () => {
    const home = buildRoleHome("venue_manager");

    expect(home.role.title).toBe("Управляющий");
    expect(home.sections).toContain("Задачи");
    expect(home.permissions.map((permission) => permission.id)).toContain(
      "assign_tasks",
    );
    expect(home.visibleTasks.some((task) => task.id === "task-menu-1")).toBe(
      true,
    );
  });

  test("limits line cooks to venue-wide, role and direct tasks", () => {
    const cookTasks = listTasksForMember("staff-cook");

    expect(cookTasks.map((task) => task.id)).toEqual([
      "task-cook-1",
      "task-venue-1",
    ]);
    expect(listTasksForRole("line_cook").map((task) => task.id)).toEqual([
      "task-venue-1",
    ]);
  });

  test("throws for unknown roles", () => {
    expect(() => getTeamRole("bad" as never)).toThrow("Unknown team role");
  });

  test("returns readable permission descriptions", () => {
    const permissions = listRolePermissions("chef");

    expect(permissions.map((permission) => permission.title)).toContain("Меню");
  });

  test("lists comments for a concrete task", () => {
    const comments = listCommentsForTask("task-menu-1");

    expect(comments).toHaveLength(1);
    expect(comments[0]?.authorName).toBe("Роман");
  });

  test("extracts learning hint from BI task context", () => {
    const context =
      "ФОТ 36%. Урок для команды: Цифры ресторана простым языком. Чеклист: Если BI показал перерасход ФОТ.";

    expect(taskLearningHintFromContext(context)).toBe(
      "Цифры ресторана простым языком",
    );
    expect(taskChecklistHintFromContext(context)).toBe(
      "Если BI показал перерасход ФОТ",
    );
    expect(taskLearningHintFromContext("Без учебного стандарта")).toBeNull();
    expect(taskContextWithoutLearningHint(context)).toBe("ФОТ 36%.");
  });

  test("extracts standard hint from new BI task context", () => {
    const context =
      "ФОТ 36%. Стандарт: Цифры ресторана простым языком. Чеклист: Если BI показал перерасход ФОТ.";

    expect(taskLearningHintFromContext(context)).toBe(
      "Цифры ресторана простым языком",
    );
    expect(taskChecklistHintFromContext(context)).toBe(
      "Если BI показал перерасход ФОТ",
    );
    expect(taskContextWithoutLearningHint(context)).toBe("ФОТ 36%.");
  });

  test("keeps dots inside learning standard titles", () => {
    const context =
      "Проверьте кассовую дисциплину. Стандарт: iiko 2.0 и кассовая дисциплина.";

    expect(taskLearningHintFromContext(context)).toBe(
      "iiko 2.0 и кассовая дисциплина",
    );
    expect(taskContextWithoutLearningHint(context)).toBe(
      "Проверьте кассовую дисциплину.",
    );
  });

  test("extracts field briefing sections from task context", () => {
    const context =
      "Полевой факт: Маша: Выручка и смены — закончилась мята к 21:00. Вопрос: что в смене объясняет эту цифру? Проверка: Сверить стоп-лист и потерянные продажи. Зачем: связать факты смены с BI. Стандарт: Брифинг смены и передача контекста. Чеклист: После смены собери полевой факт.";

    expect(taskContextBriefFromContext(context)).toEqual({
      fieldFact:
        "Полевой факт: Маша: Выручка и смены — закончилась мята к 21:00.",
      question: "Вопрос: что в смене объясняет эту цифру?",
      check: "Проверка: Сверить стоп-лист и потерянные продажи.",
      reason: "Зачем: связать факты смены с BI.",
    });
    expect(taskContextWithoutLearningHint(context)).toBe(
      "Полевой факт: Маша: Выручка и смены — закончилась мята к 21:00. Вопрос: что в смене объясняет эту цифру? Проверка: Сверить стоп-лист и потерянные продажи. Зачем: связать факты смены с BI.",
    );
    expect(taskContextBriefDisplayFromContext(context)).toEqual({
      fieldFact: "Маша: Выручка и смены — закончилась мята к 21:00.",
      question: "что в смене объясняет эту цифру?",
      check: "Сверить стоп-лист и потерянные продажи.",
      reason: "связать факты смены с BI.",
    });
  });

  test("extracts shift memory task question and formats answer as field memory", () => {
    const context =
      "Проверка: советнику не хватает живого контекста смены.\nЧто уже есть: Трение в команде: Маша — было странно\nВопросы для управляющего:\n- Почему это повлияло на гостей, продажи или команду?\n- Когда это случилось и сколько гостей, столов, позиций или денег затронуло?\nЗачем: без этих ответов владелец видит цифры, но не понимает причину смены.";
    const question = taskShiftMemoryQuestionFromContext(context);
    const comment = buildShiftMemoryTaskAnswerComment({
      question,
      answer:
        "Из-за ливня после 19:00 отменили 3 брони, зал предложил посадку у бара, утром проверить стоп-лист и обзвонить отмененные брони.",
    });

    expect(question).toBe(
      "Почему это повлияло на гостей, продажи или команду?",
    );
    expect(comment).toContain("Итог смены:");
    expect(comment).toContain("Из-за ливня после 19:00");
    expect(getFieldNoteReadiness(comment)).toMatchObject({
      hasFact: true,
      hasContext: true,
      hasScale: true,
      hasAction: true,
      score: 4,
    });
    expect(
      isShiftMemoryFollowUpTask({
        id: "shift-memory",
        venueId: "venue",
        title: "Уточнить итог смены",
        source: "copilot",
        sourceLabel: "Память смены",
        learningChecklistTitle: "Если итог смены неполный",
        priority: "medium",
        status: "new",
        audience: { type: "role", roleId: "venue_manager" },
        dueLabel: "до утреннего разбора",
      }),
    ).toBe(true);
  });

  test("filters announcements by role visibility", () => {
    const serviceAnnouncements = listAnnouncementsForRole("service");
    const chefAnnouncements = listAnnouncementsForRole("chef");

    expect(serviceAnnouncements.map((item) => item.id)).toEqual([
      "announcement-venue-1",
      "announcement-service-1",
    ]);
    expect(chefAnnouncements.map((item) => item.id)).toContain(
      "announcement-kitchen-1",
    );
  });

  test("counts and detects announcement reads", () => {
    const reads = [
      {
        announcementId: "announcement-venue-1",
        memberId: "staff-service",
        readAtLabel: "12:00",
      },
      {
        announcementId: "announcement-venue-1",
        memberId: "staff-chef",
        readAtLabel: "12:05",
      },
    ];

    expect(countAnnouncementReads("announcement-venue-1", reads)).toBe(2);
    expect(
      hasAnnouncementRead("announcement-venue-1", "staff-service", reads),
    ).toBe(true);
    expect(
      hasAnnouncementRead("announcement-venue-1", "staff-cook", reads),
    ).toBe(false);
  });
});
