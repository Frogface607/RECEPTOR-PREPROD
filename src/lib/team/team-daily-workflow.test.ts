import { describe, expect, test } from "vitest";
import { buildTeamDailyWorkflow } from "./team-daily-workflow";

describe("buildTeamDailyWorkflow", () => {
  test("builds a daily loop from manager focus, learning and field context", () => {
    const steps = buildTeamDailyWorkflow({
      opsReadiness: {
        score: 62,
        status: "attention",
        roleCoveragePct: 80,
        laborCoveragePct: 50,
        learningAdmissionPct: 75,
        learningAveragePct: 68,
        actions: [
          {
            id: "learning",
            title: "Дожать обучение",
            detail: "Маша: Как рекомендовать блюдо без давления.",
            href: "#learning-progress",
            tone: "watch",
          },
        ],
      },
      managerFollowUp: {
        status: "attention",
        title: "Есть что закрыть",
        detail: "Перед сменой есть блокеры.",
        openTasks: 2,
        urgentTasks: 1,
        blockedAdmissions: 1,
        laborCoveragePct: 50,
        planCoveragePct: 80,
        unreadImportantAnnouncements: 0,
        items: [
          {
            id: "urgent-tasks",
            title: "Закрыть срочные задачи",
            detail: "Разобрать жалобу гостя.",
            tone: "risk",
            href: "#team-actions",
            metric: "1 срочно",
            taskDraft: null,
          },
        ],
      },
      learningFocus: [
        {
          id: "field-service",
          title: "Усилить сервис и продажи: Официант",
          detail: "Гости просили безалкогольный коктейль.",
          reason: "Команда должна знать, что рекомендовать.",
          roleTitle: "Официант",
          moduleTitle: "Как рекомендовать блюдо без давления",
          href: "#learning-progress",
          tone: "field",
        },
      ],
      fieldContext: {
        totalNotes: 1,
        signalCount: 1,
        summary: "Сервис и продажи: гости просили безалкогольный коктейль.",
        signals: [],
      },
    });

    expect(steps.map((step) => step.id)).toEqual([
      "before_shift",
      "training",
      "field_note",
      "owner_decision",
    ]);
    expect(steps[0]).toMatchObject({
      title: "Закрыть срочные задачи",
      tone: "risk",
    });
    expect(steps[1]).toMatchObject({
      title: "Усилить сервис и продажи: Официант",
      tone: "work",
    });
    expect(steps[2]).toMatchObject({
      title: "Разобрать факты смены",
      href: "#shift-summary",
      tone: "work",
    });
  });

  test("asks for a shift summary when field context is missing", () => {
    const steps = buildTeamDailyWorkflow({
      opsReadiness: {
        score: 90,
        status: "ready",
        roleCoveragePct: 100,
        laborCoveragePct: 100,
        learningAdmissionPct: 100,
        learningAveragePct: 90,
        actions: [],
      },
      managerFollowUp: {
        status: "ready",
        title: "Готово",
        detail: "Блокеров нет.",
        openTasks: 0,
        urgentTasks: 0,
        blockedAdmissions: 0,
        laborCoveragePct: 100,
        planCoveragePct: 100,
        unreadImportantAnnouncements: 0,
        items: [],
      },
      learningFocus: [],
      fieldContext: null,
    });

    expect(steps[2]).toMatchObject({
      title: "Собрать итог смены",
      href: "#shift-summary",
      tone: "risk",
    });
    expect(steps[3]).toMatchObject({
      title: "Дать один фокус",
      tone: "ready",
    });
  });
});
