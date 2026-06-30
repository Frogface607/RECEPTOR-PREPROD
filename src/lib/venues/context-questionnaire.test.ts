import { describe, expect, test } from "vitest";
import {
  buildContextMemoryReadiness,
  calculateContextCompletion,
  DEMO_CONTEXT_ANSWERS,
  formatContextAnswersForPrompt,
  listRequiredContextQuestionIds,
  normalizeContextAnswers,
  VENUE_CONTEXT_QUESTIONNAIRE,
} from "./context-questionnaire";

describe("venue context questionnaire", () => {
  test("defines required context questions", () => {
    expect(VENUE_CONTEXT_QUESTIONNAIRE.length).toBeGreaterThanOrEqual(6);
    expect(listRequiredContextQuestionIds()).toEqual(
      expect.arrayContaining([
        "format",
        "positioning",
        "audience",
        "owner_goals",
        "pos_system",
        "ai_provider_policy",
      ]),
    );
  });

  test("normalizes answer payloads", () => {
    const answers = normalizeContextAnswers({
      format: "  bar  ",
      audience: [" вечер ", "", "компании"],
      empty: "   ",
      count: 80,
    });

    expect(answers).toEqual({
      format: "bar",
      audience: ["вечер", "компании"],
      count: "80",
    });
  });

  test("calculates completion", () => {
    const completion = calculateContextCompletion(DEMO_CONTEXT_ANSWERS);

    expect(completion.percentage).toBe(100);
    expect(completion.requiredPercentage).toBe(100);
    expect(completion.missingRequired).toEqual([]);
  });

  test("formats context for Copilot prompts", () => {
    const prompt = formatContextAnswersForPrompt({
      format: "ресторан",
      owner_goals: ["видеть риски", "экономить время"],
      daily_pains: ["новички не понимают стандарты"],
      shift_summary_rules: "управляющий пишет итог смены после закрытия",
    });

    expect(prompt).toContain("Идентичность заведения");
    expect(prompt).toContain("Формат: ресторан");
    expect(prompt).toContain("Цели владельца: видеть риски; экономить время");
    expect(prompt).toContain("Как ресторан живет на самом деле");
    expect(prompt).toContain("Главные боли: новички не понимают стандарты");
    expect(prompt).toContain(
      "Итог смены: управляющий пишет итог смены после закрытия",
    );
  });

  test("asks the first missing restaurant memory question", () => {
    const readiness = buildContextMemoryReadiness({});

    expect(readiness.status).toBe("starter");
    expect(readiness.percentage).toBe(0);
    expect(readiness.nextQuestion).toMatchObject({
      id: "format",
      label: "Формат",
      sectionTitle: "Идентичность заведения",
    });
  });

  test("prioritizes operating reality before secondary setup details", () => {
    const readiness = buildContextMemoryReadiness({
      format: "бар",
      positioning: "локальный craft bar",
      audience: ["постоянные гости"],
      owner_goals: ["понять смену утром"],
      decision_metrics: ["выручка"],
    });

    expect(readiness.nextQuestion).toMatchObject({
      id: "daily_pains",
      sectionTitle: "Как ресторан живет на самом деле",
    });
    expect(readiness.nextQuestion?.reason).toContain("реальность");
  });

  test("marks demo context as strong restaurant memory", () => {
    const readiness = buildContextMemoryReadiness(DEMO_CONTEXT_ANSWERS);

    expect(readiness.status).toBe("strong");
    expect(readiness.percentage).toBe(100);
    expect(readiness.nextQuestion).toBeNull();
    expect(readiness.summary).toContain("итоги смен");
  });
});
