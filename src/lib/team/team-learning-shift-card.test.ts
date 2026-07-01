import { describe, expect, test } from "vitest";
import { getLearningItem } from "./team-learning";
import {
  buildTeamLearningOperatingStandard,
  buildTeamLearningShiftCard,
} from "./team-learning-shift-card";

describe("team learning shift card", () => {
  test("turns service learning into a practical shift action", () => {
    const item = getLearningItem("service-recommendation");
    expect(item).toBeTruthy();

    const card = buildTeamLearningShiftCard(item!);

    expect(card.reason).toContain("деньги");
    expect(card.action).toContain("предложи");
    expect(card.fieldNote).toContain("гости");
    expect(card.fieldNoteTemplate).toContain(
      'Итог смены по стандарту "Как рекомендовать блюдо без давления"',
    );
    expect(card.fieldNoteTemplate).toContain("факт");
    expect(card.fieldNoteTemplate).toContain("что проверить");
  });

  test("uses checklist title as the shift focus", () => {
    const item = getLearningItem("shift-brief");
    expect(item).toBeTruthy();

    const card = buildTeamLearningShiftCard(
      item!,
      "Если полевая заметка про стоп-лист",
    );

    expect(card.title).toBe("Фокус смены: Если полевая заметка про стоп-лист");
    expect(card.checklistLabel).toBe("Если полевая заметка про стоп-лист");
    expect(card.fieldNote).toContain("короткий итог");
  });

  test("turns a learning item into an operating standard route", () => {
    const item = getLearningItem("service-recommendation");
    expect(item).toBeTruthy();

    const standard = buildTeamLearningOperatingStandard(item!);

    expect(standard).toMatchObject({
      label: "Операционный стандарт роли",
      title: "Как рекомендовать блюдо без давления",
    });
    expect(standard.promise).toContain("реальной смене");
    expect(standard.promise).toContain("память ресторана");
    expect(standard.steps.map((step) => step.title)).toEqual([
      "Понять правило",
      "Применить в смене",
      "Оставить итог",
      "Закрыть проверку",
    ]);
    expect(standard.steps[1]?.detail).toContain("предложи");
    expect(standard.steps[2]?.detail).toContain("После смены");
    expect(standard.steps[3]?.detail).toContain("80%");
  });

  test("explains iiko learning as data discipline", () => {
    const item = getLearningItem("iiko-cash-discipline");
    expect(item).toBeTruthy();

    const card = buildTeamLearningShiftCard(item!);

    expect(card.reason).toContain("управленческие цифры");
    expect(card.action).toContain("скидки");
    expect(card.fieldNote).toContain("спорные операции");
  });
});
