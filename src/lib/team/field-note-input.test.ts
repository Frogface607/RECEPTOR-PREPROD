import { describe, expect, test } from "vitest";
import {
  FIELD_NOTE_TEMPLATES,
  hasMeaningfulFieldNoteBody,
} from "./field-note-input";

describe("field note input", () => {
  test("rejects empty guided templates", () => {
    expect(hasMeaningfulFieldNoteBody("Гости спрашивали: ")).toBe(false);
    expect(
      hasMeaningfulFieldNoteBody(
        FIELD_NOTE_TEMPLATES.map((template) => template.text).join("\n"),
      ),
    ).toBe(false);
  });

  test("accepts guided templates with actual shift facts", () => {
    expect(
      hasMeaningfulFieldNoteBody("Гости спрашивали: лимонад без сахара"),
    ).toBe(true);
    expect(
      hasMeaningfulFieldNoteBody(
        "Стоп-лист / закончилось: мята к 21:00\nКоманде мешало: кухня задержала горячее",
      ),
    ).toBe(true);
  });

  test("accepts a free-form short fact without a template", () => {
    expect(hasMeaningfulFieldNoteBody("закончилась мята")).toBe(true);
  });
});
