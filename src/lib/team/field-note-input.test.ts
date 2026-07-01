import { describe, expect, test } from "vitest";
import {
  FIELD_NOTE_CLOSED_LOOP_COPY,
  FIELD_NOTE_MEMORY_LINK_COPY,
  FIELD_NOTE_MEMORY_PROMPTS,
  FIELD_NOTE_SAVED_MEMORY_COPY,
  FIELD_NOTE_TEMPLATES,
  buildFieldNoteFollowUpQuestions,
  buildFieldNoteFollowUpTaskDraft,
  fieldNoteReadinessHint,
  getFieldNoteReadiness,
  hasMeaningfulFieldNoteBody,
  isFieldNoteClosedLearningAdoptionMessage,
  summarizeFieldNoteReadiness,
} from "./field-note-input";

describe("field note input", () => {
  test("keeps shift memory form copy aligned with restaurant memory", () => {
    expect(FIELD_NOTE_MEMORY_LINK_COPY).toMatchObject({
      label: "Что связываем в памяти",
      title: "Собрать итог",
      action: "Сохранить связь",
    });
    expect(FIELD_NOTE_MEMORY_LINK_COPY.detail).toContain("человека");
    expect(FIELD_NOTE_MEMORY_LINK_COPY.detail).toContain("задачи");
    expect(FIELD_NOTE_MEMORY_LINK_COPY.detail).toContain("утренний разбор");
    expect(FIELD_NOTE_SAVED_MEMORY_COPY.title).toContain("память ресторана");
    expect(FIELD_NOTE_SAVED_MEMORY_COPY.detail).toContain("задачах");
    expect(FIELD_NOTE_SAVED_MEMORY_COPY.detail).toContain("обучении");
    expect(FIELD_NOTE_SAVED_MEMORY_COPY.detail).toContain("цифрах");
    expect(FIELD_NOTE_CLOSED_LOOP_COPY.title).toContain("Стандарт");
    expect(FIELD_NOTE_CLOSED_LOOP_COPY.detail).toContain("стандарт");
    expect(FIELD_NOTE_CLOSED_LOOP_COPY.detail).toContain("память ресторана");
  });

  test("detects when a saved shift note closed a learning adoption loop", () => {
    expect(
      isFieldNoteClosedLearningAdoptionMessage(
        "Заметка смены сохранена. Задача внедрения стандарта закрыта.",
      ),
    ).toBe(true);

    expect(
      isFieldNoteClosedLearningAdoptionMessage(
        "Заметка смены сохранена. Receptor учтет ее в советах.",
      ),
    ).toBe(false);
  });

  test("rejects empty guided templates", () => {
    expect(hasMeaningfulFieldNoteBody(FIELD_NOTE_TEMPLATES[0].text)).toBe(
      false,
    );
    expect(
      hasMeaningfulFieldNoteBody(
        FIELD_NOTE_TEMPLATES.map((template) => template.text).join("\n"),
      ),
    ).toBe(false);
  });

  test("accepts guided templates with actual shift facts", () => {
    expect(FIELD_NOTE_TEMPLATES[0]).toMatchObject({
      label: "Итог смены",
    });
    expect(FIELD_NOTE_TEMPLATES[0].text).toContain("Контекст / причина");
    expect(FIELD_NOTE_TEMPLATES[0].text).toContain("Что проверить утром");
    expect(FIELD_NOTE_MEMORY_PROMPTS.map((prompt) => prompt.label)).toEqual([
      "Факт",
      "Контекст",
      "Масштаб",
      "Действие",
    ]);
    expect(
      hasMeaningfulFieldNoteBody(
        "Гости спрашивали:\nКонтекст / почему важно: часто просили без сахара\nСколько раз / когда: 4 раза после 21:00\nЧто ответили: предложили лимонад без сахара",
      ),
    ).toBe(true);
    expect(
      hasMeaningfulFieldNoteBody(
        "Стоп-лист / закончилось: мята\nКогда заметили: к 21:00\nЧто заменили или потеряли: не продали 6 лимонадов\nКоманде мешало: кухня задержала горячее",
      ),
    ).toBe(true);
    expect(
      hasMeaningfulFieldNoteBody(
        "Маржа / ФОТ: ФОТ 34%, дорогая смена\nЧто продавали или не продавали: маржинальные закуски почти не предлагали\nЧто проверить утром: дать фокус на апсейл",
      ),
    ).toBe(true);
  });

  test("accepts a free-form short fact without a template", () => {
    expect(hasMeaningfulFieldNoteBody("закончилась мята")).toBe(true);
  });

  test("scores field notes by fact, context, scale and action", () => {
    expect(
      getFieldNoteReadiness(
        "Стоп-лист / закончилось: мята\nКонтекст / причина: поставка не пришла, зал терял лимонады\nКогда заметили: к 21:00\nЧто заменили или потеряли: не продали 6 лимонадов\nЧто проверить утром: заказ мяты",
      ),
    ).toMatchObject({
      hasFact: true,
      hasContext: true,
      hasScale: true,
      hasAction: true,
      score: 4,
      missing: [],
    });

    expect(getFieldNoteReadiness("закончилась мята")).toMatchObject({
      hasFact: true,
      hasContext: true,
      hasScale: false,
      hasAction: false,
      score: 2,
      missing: ["когда/сколько", "что сделали или проверить"],
    });

    expect(
      getFieldNoteReadiness(
        "Было странно и неприятно. Надо обсудить.",
      ),
    ).toMatchObject({
      hasFact: true,
      hasContext: false,
      hasScale: false,
      hasAction: true,
      score: 2,
      missing: ["контекст/причина", "когда/сколько"],
    });
  });

  test("treats weather and briefing context as a useful shift note", () => {
    expect(
      getFieldNoteReadiness(
        "Итог смены:\nПосадка / гости / погода: ливень, отменили 3 брони после 19:00\nЧто повлияло на выручку: меньше посадка\nЧто проверить утром: стоп-лист и замену лимонада\nЧто сказать на брифе: предлагать горячие напитки",
      ),
    ).toMatchObject({
      hasFact: true,
      hasContext: true,
      hasScale: true,
      hasAction: true,
      score: 4,
      missing: [],
    });
  });

  test("explains what the shift note still needs", () => {
    expect(
      fieldNoteReadinessHint(getFieldNoteReadiness(FIELD_NOTE_TEMPLATES[0].text)),
    ).toContain("Начните с одного факта");

    expect(
      fieldNoteReadinessHint(getFieldNoteReadiness("закончилась мята")),
    ).toContain("когда/сколько");

    expect(
      fieldNoteReadinessHint(
        getFieldNoteReadiness(
          "Стоп-лист: к 21:00 закончилась мята. Утром проверить заказ и дать замену лимонада.",
        ),
      ),
    ).toContain("память смены");
  });

  test("summarizes completed shift memory notes", () => {
    expect(
      summarizeFieldNoteReadiness([
        "Было странно и неприятно. Надо обсудить.",
        "Итог смены: к 21:00 закончилась мята. Контекст: ливень, гости просили лимонады. Масштаб: 6 отказов. Действие: утром проверить заказ мяты.",
      ]),
    ).toMatchObject({
      total: 2,
      complete: 1,
      bestScore: 4,
      bestMissing: [],
      followUpQuestions: ["Что важно запомнить из смены для утреннего разбора?"],
    });

    expect(summarizeFieldNoteReadiness([])).toMatchObject({
      total: 0,
      complete: 0,
      bestScore: 0,
      followUpQuestions: [
        "Что конкретно произошло в смене?",
        "Почему это повлияло на гостей, продажи или команду?",
        "Когда это случилось и сколько гостей, столов, позиций или денег затронуло?",
        "Что команда уже сделала и что управляющему проверить утром?",
      ],
    });
  });

  test("turns missing shift memory parts into concrete manager questions", () => {
    expect(
      buildFieldNoteFollowUpQuestions(["контекст/причина", "когда/сколько"]),
    ).toEqual([
      "Почему это повлияло на гостей, продажи или команду?",
      "Когда это случилось и сколько гостей, столов, позиций или денег затронуло?",
    ]);

    expect(
      summarizeFieldNoteReadiness(["Итог смены: было странно. Надо обсудить."])
        .followUpQuestions,
    ).toEqual([
      "Почему это повлияло на гостей, продажи или команду?",
      "Когда это случилось и сколько гостей, столов, позиций или денег затронуло?",
    ]);
  });

  test("builds a manager task draft from incomplete shift memory", () => {
    const readiness = summarizeFieldNoteReadiness([
      "Итог смены: было странно. Надо обсудить.",
    ]);
    const draft = buildFieldNoteFollowUpTaskDraft({
      readiness,
      signalSummary: "Трение в команде: Маша — было странно",
    });

    expect(draft).toMatchObject({
      title: "Уточнить итог смены: контекст/причина, когда/сколько",
      priority: "medium",
      roleId: "venue_manager",
      dueLabel: "до утреннего разбора",
      sourceLabel: "Память смены",
      impactLabel: "не хватает: контекст/причина, когда/сколько",
      learningModuleId: "shift-brief",
      learningChecklistTitle: "Если итог смены неполный",
    });
    expect(draft?.contextNote).toContain(
      "Почему это повлияло на гостей, продажи или команду?",
    );
    expect(draft?.contextNote).toContain("Что уже есть: Трение в команде");

    expect(
      buildFieldNoteFollowUpTaskDraft({
        readiness: summarizeFieldNoteReadiness([
          "Итог смены: ливень, отменили 3 брони после 19:00. Утром проверить стоп-лист.",
        ]),
      }),
    ).toBeNull();
  });
});
