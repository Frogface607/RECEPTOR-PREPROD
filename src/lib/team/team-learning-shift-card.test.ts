import { describe, expect, test } from "vitest";
import { getLearningItem } from "./team-learning";
import { buildTeamLearningShiftCard } from "./team-learning-shift-card";

describe("team learning shift card", () => {
  test("turns service learning into a practical shift action", () => {
    const item = getLearningItem("service-recommendation");
    expect(item).toBeTruthy();

    const card = buildTeamLearningShiftCard(item!);

    expect(card.reason).toContain("деньги");
    expect(card.action).toContain("предложи");
    expect(card.fieldNote).toContain("гости");
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

  test("explains iiko learning as data discipline", () => {
    const item = getLearningItem("iiko-cash-discipline");
    expect(item).toBeTruthy();

    const card = buildTeamLearningShiftCard(item!);

    expect(card.reason).toContain("управленческие цифры");
    expect(card.action).toContain("скидки");
    expect(card.fieldNote).toContain("спорные операции");
  });
});
