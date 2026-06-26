import { describe, expect, test } from "vitest";
import {
  calculateLearningScore,
  getLearningItem,
  listLearningItemsForRole,
} from "./team-learning";

describe("team learning catalog", () => {
  test("returns role-specific learning items with real lesson content", () => {
    const serviceItems = listLearningItemsForRole("service");

    expect(serviceItems.map((item) => item.id)).toEqual([
      "service-recommendation",
      "guest-feedback",
    ]);
    expect(serviceItems[0].sections.length).toBeGreaterThan(0);
    expect(serviceItems[0].quiz.length).toBeGreaterThan(0);
  });

  test("finds a learning item by id", () => {
    const item = getLearningItem("tech-card-discipline");

    expect(item?.title).toContain("Техкарта");
    expect(item?.roles).toContain("chef");
  });

  test("calculates pass/fail score from selected answers", () => {
    const item = getLearningItem("owner-morning");
    expect(item).toBeDefined();

    const passed = calculateLearningScore(item!, [0, 0, 0]);
    const failed = calculateLearningScore(item!, [1, 2, 1]);

    expect(passed).toEqual({
      correct: 3,
      total: 3,
      percentage: 100,
      passed: true,
    });
    expect(failed).toMatchObject({
      correct: 0,
      total: 3,
      percentage: 0,
      passed: false,
    });
  });
});
