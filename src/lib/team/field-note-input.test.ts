import { describe, expect, test } from "vitest";
import {
  FIELD_NOTE_MEMORY_PROMPTS,
  FIELD_NOTE_TEMPLATES,
  fieldNoteReadinessHint,
  getFieldNoteReadiness,
  hasMeaningfulFieldNoteBody,
  summarizeFieldNoteReadiness,
} from "./field-note-input";

describe("field note input", () => {
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
    });

    expect(summarizeFieldNoteReadiness([])).toMatchObject({
      total: 0,
      complete: 0,
      bestScore: 0,
    });
  });
});
