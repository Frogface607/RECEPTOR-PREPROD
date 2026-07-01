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
            title: "Закрыть стандарт",
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
          practiceAction:
            "На смене предложить подходящую пару к заказу гостя.",
          memoryPrompt:
            "После смены зафиксировать, что спрашивали гости и что сработало.",
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
      reason: "Память команды показывает: 1 срочно нужно закрыть до смены.",
      tone: "risk",
    });
    expect(steps[1]).toMatchObject({
      title: "Усилить сервис и продажи: Официант",
      detail:
        "В смене: На смене предложить подходящую пару к заказу гостя. После: После смены зафиксировать, что спрашивали гости и что сработало.",
      reason:
        "После обучения ждем короткий итог смены: После смены зафиксировать, что спрашивали гости и что сработало.",
      tone: "work",
    });
    expect(steps[2]).toMatchObject({
      title: "Разобрать факты смены",
      href: "#shift-summary",
      reason:
        "Память смены уже дала контекст, его надо связать с утренним решением.",
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
      reason: "Без короткого итога советник видит цифры, но не причину смены.",
      tone: "risk",
    });
    expect(steps[3]).toMatchObject({
      title: "Дать один фокус",
      reason:
        "Память собрана достаточно, чтобы дать один фокус без лишнего шума.",
      tone: "ready",
    });
  });

  test("prioritizes a passed standard that still needs shift evidence", () => {
    const steps = buildTeamDailyWorkflow({
      opsReadiness: {
        score: 92,
        status: "ready",
        roleCoveragePct: 100,
        laborCoveragePct: 100,
        learningAdmissionPct: 100,
        learningAveragePct: 92,
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
      learningFocus: [
        {
          id: "ready-service",
          title: "Официант: развитие команды",
          detail: "Можно усилить следующий стандарт.",
          reason: "Блокеров нет.",
          roleTitle: "Официант",
          moduleTitle: "Восьмерка продаж и апселл в сервисе",
          practiceAction: "На смене предложить пару к заказу.",
          memoryPrompt: "После смены зафиксировать, что сработало.",
          href: "#learning-progress",
          tone: "ready",
        },
      ],
      learningAdoptionFocus: {
        title: "Попросить итог по стандарту",
        detail:
          "Маша: Как рекомендовать блюдо без давления — назначьте один итог смены после практики.",
        reason:
          "Тест не показывает, как человек работает в зале или на кухне. Нужен короткий итог из смены.",
        href: "#learning-progress",
        tone: "risk",
      },
      fieldContext: null,
    });

    expect(steps[1]).toMatchObject({
      title: "Попросить итог по стандарту",
      detail:
        "Маша: Как рекомендовать блюдо без давления — назначьте один итог смены после практики.",
      href: "#learning-progress",
      tone: "risk",
    });
    expect(steps[1].reason).toContain("Нужен короткий итог из смены");
  });
});
