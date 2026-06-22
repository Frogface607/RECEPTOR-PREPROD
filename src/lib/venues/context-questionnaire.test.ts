import { describe, expect, test } from "vitest";
import {
  calculateContextCompletion,
  DEMO_CONTEXT_ANSWERS,
  formatContextAnswersForPrompt,
  listRequiredContextQuestionIds,
  normalizeContextAnswers,
  VENUE_CONTEXT_QUESTIONNAIRE,
} from "./context-questionnaire";

describe("venue context questionnaire", () => {
  test("defines required context questions", () => {
    expect(VENUE_CONTEXT_QUESTIONNAIRE.length).toBeGreaterThanOrEqual(5);
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
    });

    expect(prompt).toContain("Идентичность заведения");
    expect(prompt).toContain("Формат: ресторан");
    expect(prompt).toContain("Цели владельца: видеть риски; экономить время");
  });
});
