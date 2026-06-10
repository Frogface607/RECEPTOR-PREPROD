import { describe, expect, test } from "vitest";
import {
  calculateTechCard,
  createTechCardMarkdown,
  formatRub,
  type TechCardInput,
} from "./tech-card";

const input: TechCardInput = {
  dishName: "Паста с креветками",
  category: "Горячее",
  portions: 2,
  outputWeight: 520,
  targetFoodCostPercent: 30,
  process: "Отварить пасту, прогреть соус, соединить с креветками.",
  ingredients: [
    {
      id: "1",
      name: "Паста",
      unit: "g",
      grossQty: 220,
      netQty: 200,
      pricePerKg: 180,
      proteinPer100g: 12,
      fatPer100g: 1.5,
      carbsPer100g: 70,
      kcalPer100g: 350,
      article: "00001",
    },
    {
      id: "2",
      name: "Креветки",
      unit: "g",
      grossQty: 220,
      netQty: 180,
      pricePerKg: 1100,
      proteinPer100g: 20,
      fatPer100g: 2,
      carbsPer100g: 1,
      kcalPer100g: 100,
    },
  ],
};

describe("calculateTechCard", () => {
  test("calculates cost, recommended price, nutrients and mapping coverage", () => {
    const result = calculateTechCard(input);

    expect(result.totalCost).toBe(234);
    expect(result.costPerPortion).toBe(117);
    expect(result.recommendedPrice).toBe(780);
    expect(result.protein).toBe(60);
    expect(result.kcal).toBe(880);
    expect(result.mappingCoveragePercent).toBe(50);
    expect(result.yieldDelta).toBe(-140);
  });

  test("supports piece-priced ingredients", () => {
    const result = calculateTechCard({
      ...input,
      ingredients: [
        {
          id: "egg",
          name: "Яйцо",
          unit: "pcs",
          grossQty: 2,
          netQty: 2,
          pricePerKg: 14,
          proteinPer100g: 12,
          fatPer100g: 10,
          carbsPer100g: 1,
          kcalPer100g: 155,
        },
      ],
    });

    expect(result.totalCost).toBe(28);
  });
});

describe("tech card formatting", () => {
  test("formats rubles for ru locale", () => {
    expect(formatRub(1234.5)).toBe("1 234,5 ₽");
  });

  test("creates markdown with summary and ingredient table", () => {
    const calculation = calculateTechCard(input);
    const markdown = createTechCardMarkdown(input, calculation);

    expect(markdown).toContain("# Технологическая карта: Паста с креветками");
    expect(markdown).toContain("| Паста | 220 g | 200 g | 9.1% | 36 ₽ | 00001 |");
    expect(markdown).toContain("Покрытие артикулами iiko: 50%");
  });
});
