import { describe, expect, test } from "vitest";
import {
  FIELD_NOTE_TEMPLATES,
  getFieldNoteReadiness,
  hasMeaningfulFieldNoteBody,
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
      text: expect.stringContaining("Что проверить утром"),
    });
    expect(
      hasMeaningfulFieldNoteBody(
        "Гости спрашивали:\nСколько раз / когда: 4 раза после 21:00\nЧто ответили: предложили лимонад без сахара",
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

  test("scores field notes by fact, scale and action", () => {
    expect(
      getFieldNoteReadiness(
        "Стоп-лист / закончилось: мята\nКогда заметили: к 21:00\nЧто заменили или потеряли: не продали 6 лимонадов\nЧто проверить утром: заказ мяты",
      ),
    ).toMatchObject({
      hasFact: true,
      hasScale: true,
      hasAction: true,
      score: 3,
      missing: [],
    });

    expect(getFieldNoteReadiness("закончилась мята")).toMatchObject({
      hasFact: true,
      hasScale: false,
      hasAction: false,
      score: 1,
      missing: ["когда/сколько", "что сделали или проверить"],
    });
  });

  test("treats weather and briefing context as a useful shift note", () => {
    expect(
      getFieldNoteReadiness(
        "Итог смены:\nПосадка / гости / погода: ливень, отменили 3 брони после 19:00\nЧто повлияло на выручку: меньше посадка\nЧто проверить утром: стоп-лист и замену лимонада\nЧто сказать на брифе: предлагать горячие напитки",
      ),
    ).toMatchObject({
      hasFact: true,
      hasScale: true,
      hasAction: true,
      score: 3,
      missing: [],
    });
  });
});
