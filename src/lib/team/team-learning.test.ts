import { describe, expect, test } from "vitest";
import {
  calculateLearningScore,
  getLearningItem,
  getLearningItemByTitle,
  learningModuleHref,
  listLearningItemsForRole,
} from "./team-learning";

describe("team learning catalog", () => {
  test("returns role-specific learning items with real lesson content", () => {
    const serviceItems = listLearningItemsForRole("service");

    expect(serviceItems.map((item) => item.id)).toEqual([
      "service-recommendation",
      "sales-eight-upsell",
      "shift-open-close",
      "iiko-cash-discipline",
      "guest-feedback",
      "guest-conflict-service",
    ]);
    expect(serviceItems[0].sections.length).toBeGreaterThan(0);
    expect(serviceItems[0].quiz.length).toBeGreaterThan(0);
  });

  test("includes operational restaurant basics for Learning OS v0", () => {
    const sales = getLearningItem("sales-eight-upsell");
    const cash = getLearningItem("iiko-cash-discipline");
    const numbers = getLearningItem("restaurant-numbers-basics");

    expect(sales).toMatchObject({
      title: "Восьмерка продаж и апселл в сервисе",
      status: "ready",
    });
    expect(sales?.roles).toContain("service");
    expect(cash?.roles).toContain("venue_manager");
    expect(numbers?.roles).toContain("owner");
    expect(numbers?.quiz).toHaveLength(3);
    expect(numbers?.sections).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          title: "Если BI показал перерасход ФОТ",
        }),
      ]),
    );
  });

  test("finds a learning item by id", () => {
    const item = getLearningItem("tech-card-discipline");

    expect(item?.title).toContain("Техкарта");
    expect(item?.roles).toContain("chef");
  });

  test("finds a learning item by title from task context", () => {
    const item = getLearningItem("restaurant-numbers-basics");

    expect(getLearningItemByTitle(item?.title)?.id).toBe(
      "restaurant-numbers-basics",
    );
    expect(getLearningItemByTitle("  ")).toBeUndefined();
  });

  test("includes BI task checklists in linked learning standards", () => {
    const shift = getLearningItem("shift-open-close");
    const techCard = getLearningItem("tech-card-discipline");
    const shiftBrief = getLearningItem("shift-brief");

    expect(shift?.sections).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          title: "Если BI показал слабую смену",
        }),
      ]),
    );
    expect(techCard?.sections).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          title: "Если в техкарте нет цен ингредиентов",
        }),
        expect.objectContaining({
          title: "Если BI показал недобор валовой прибыли",
        }),
      ]),
    );
    expect(shiftBrief?.sections).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          title: "Разбор: факт, вопрос, проверка, действие",
        }),
        expect.objectContaining({
          title: "Если полевая заметка про стоп-лист",
        }),
        expect.objectContaining({
          title: "Если полевая заметка про конфликт",
        }),
        expect.objectContaining({
          title: "Если полевая заметка про сервис или запрос гостей",
        }),
      ]),
    );
  });

  test("builds learning links with focused BI checklist titles", () => {
    expect(
      learningModuleHref(
        "restaurant-numbers-basics",
        "Если BI показал перерасход ФОТ",
      ),
    ).toBe(
      "/me/learning?module=restaurant-numbers-basics&checklist=%D0%95%D1%81%D0%BB%D0%B8+BI+%D0%BF%D0%BE%D0%BA%D0%B0%D0%B7%D0%B0%D0%BB+%D0%BF%D0%B5%D1%80%D0%B5%D1%80%D0%B0%D1%81%D1%85%D0%BE%D0%B4+%D0%A4%D0%9E%D0%A2",
    );
    expect(learningModuleHref("shift-open-close")).toBe(
      "/me/learning?module=shift-open-close",
    );
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
