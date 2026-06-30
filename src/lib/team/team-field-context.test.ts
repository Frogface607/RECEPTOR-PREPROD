import { describe, expect, test } from "vitest";
import { buildTeamFieldContextDigest } from "./team-field-context";
import type { TeamTask, TeamTaskComment } from "./team-os";

const tasks: TeamTask[] = [
  {
    id: "task-service",
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

describe("buildTeamFieldContextDigest", () => {
  test("extracts field signals from team comments", () => {
    const comments: TeamTaskComment[] = [
      {
        id: "comment-1",
        venueId: "venue-1",
        taskId: "task-service",
        authorName: "Маша",
        body: "Гости спрашивали безалкогольный коктейль, а еще закончилась мята.",
        createdAtLabel: "22:10",
      },
      {
        id: "comment-2",
        venueId: "venue-1",
        taskId: "task-service",
        authorName: "Игорь",
        body: "Был конфликт по ожиданию блюда, долго отдавали кухней.",
        createdAtLabel: "22:30",
      },
    ];

    const digest = buildTeamFieldContextDigest({ comments, tasks });

    expect(digest).toMatchObject({
      totalNotes: 2,
      signalCount: 4,
      signals: expect.arrayContaining([
        expect.objectContaining({
          kind: "conflict",
          title: "Конфликты и жалобы",
          detail: expect.stringContaining("Игорь: Выручка и смены"),
        }),
        expect.objectContaining({
          kind: "stock",
          title: "Стоп-лист и заготовки",
          detail: expect.stringContaining("закончилась мята"),
        }),
      ]),
    });
  });

  test("ignores Receptor system task context", () => {
    const digest = buildTeamFieldContextDigest({
      comments: [
        {
          id: "comment-system",
          venueId: "venue-1",
          taskId: "task-service",
          authorName: "Receptor",
          body: "ФОТ 36%. Зачем: понять риск. Урок для команды: Цифры ресторана простым языком. Чеклист: Если BI показал перерасход ФОТ.",
          createdAtLabel: "10:00",
        },
      ],
      tasks,
    });

    expect(digest).toBeNull();
  });

  test("recognizes guided field note templates", () => {
    const comments: TeamTaskComment[] = [
      {
        id: "comment-event",
        venueId: "venue-1",
        taskId: "task-service",
        authorName: "Маша",
        body: "Событие / посадка: было 36 гостей и плотная бронь.",
        createdAtLabel: "21:40",
      },
      {
        id: "comment-team",
        venueId: "venue-1",
        taskId: "task-service",
        authorName: "Игорь",
        body: "Команде мешало: кухня задержала два стола на горячем.",
        createdAtLabel: "22:20",
      },
      {
        id: "comment-sales",
        venueId: "venue-1",
        taskId: "task-service",
        authorName: "Оля",
        body: "Сервис / продажи: гости хорошо брали лимонад по рекомендации.",
        createdAtLabel: "22:30",
      },
    ];

    const digest = buildTeamFieldContextDigest({ comments, tasks });

    expect(digest).toMatchObject({
      totalNotes: 3,
      signals: expect.arrayContaining([
        expect.objectContaining({ kind: "event" }),
        expect.objectContaining({ kind: "team" }),
        expect.objectContaining({ kind: "service" }),
      ]),
    });
  });
});
