import { describe, expect, test } from "vitest";
import { normalizeTechCardDraft } from "./tech-card-draft";

describe("normalizeTechCardDraft", () => {
  test("normalizes model JSON into editable tech card input", () => {
    const result = normalizeTechCardDraft(
      {
        dishName: "Цезарь с креветками",
        category: "Салаты",
        portions: "2",
        outputWeight: "420",
        targetFoodCostPercent: "28",
        process: "Подготовить салат, обжарить креветки, собрать подачу.",
        ingredients: [
          {
            name: "Креветки",
            unit: "g",
            grossQty: "180",
            netQty: "150",
            pricePerKg: "1100",
            proteinPer100g: "20",
            fatPer100g: "2",
            carbsPer100g: "1",
            kcalPer100g: "100",
          },
        ],
      },
      { idea: "Цезарь", category: "Салаты" },
    );

    expect(result.dishName).toBe("Цезарь с креветками");
    expect(result.portions).toBe(2);
    expect(result.outputWeight).toBe(420);
    expect(result.ingredients[0]).toMatchObject({
      name: "Креветки",
      unit: "g",
      grossQty: 180,
      netQty: 150,
      pricePerKg: 1100,
    });
  });

  test("falls back to safe draft fields when model JSON is incomplete", () => {
    const result = normalizeTechCardDraft({}, { idea: "Стейк", portions: 3 });

    expect(result.dishName).toBe("Стейк");
    expect(result.portions).toBe(3);
    expect(result.ingredients.length).toBeGreaterThan(0);
    expect(result.process.length).toBeGreaterThan(0);
  });

  test("builds a specific fallback for breaded cod with broccoli and bisque", () => {
    const result = normalizeTechCardDraft(
      {},
      { idea: "треска в панировке с брокколи и соусом биск" },
    );

    const names = result.ingredients.map((ingredient) => ingredient.name);
    expect(result.category).toBe("Горячая кухня");
    expect(names).toContain("Филе трески");
    expect(names).toContain("Панировка панко");
    expect(names).toContain("Брокколи");
    expect(names).toContain("Соус биск");
    expect(result.process).toContain("Запанировать");
  });

  test("rejects unsupported units to grams", () => {
    const result = normalizeTechCardDraft(
      {
        ingredients: [{ name: "Соус", unit: "liter", grossQty: 10, netQty: 10 }],
      },
      { idea: "Соус" },
    );

    expect(result.ingredients[0].unit).toBe("g");
  });
});
