import { describe, expect, test } from "vitest";
import {
  calculateTechCard,
  createTechCardLaunchPack,
  createTechCardMarkdown,
  evaluateTechCardQuality,
  formatRub,
  parseTechCardExportDocument,
  serializeTechCard,
  type TechCardInput,
} from "./tech-card";
import { DEFAULT_VENUE_INTELLIGENCE } from "@/lib/venues/intelligence";

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

describe("evaluateTechCardQuality", () => {
  test("returns ok for a filled and mapped tech card", () => {
    const filled: TechCardInput = {
      ...input,
      outputWeight: 380,
      ingredients: input.ingredients.map((ingredient, index) => ({
        ...ingredient,
        article: `0000${index + 1}`,
      })),
    };
    const calculation = calculateTechCard(filled);
    const quality = evaluateTechCardQuality(filled, calculation);

    expect(quality.status).toBe("ok");
    expect(quality.score).toBe(100);
    expect(quality.issues).toHaveLength(0);
  });

  test("marks missing core fields as critical", () => {
    const empty: TechCardInput = {
      dishName: "",
      category: "",
      portions: 1,
      outputWeight: 0,
      targetFoodCostPercent: 30,
      process: "",
      ingredients: [],
    };
    const quality = evaluateTechCardQuality(empty, calculateTechCard(empty));

    expect(quality.status).toBe("critical");
    expect(quality.issues.some((issue) => issue.title === "Нет названия блюда")).toBe(true);
    expect(quality.issues.some((issue) => issue.title === "Нет ингредиентов")).toBe(true);
  });

  test("warns about missing prices, nutrition and output mismatch", () => {
    const draft: TechCardInput = {
      ...input,
      outputWeight: 1000,
      ingredients: [
        {
          ...input.ingredients[0],
          pricePerKg: 0,
          proteinPer100g: 0,
          fatPer100g: 0,
          carbsPer100g: 0,
          kcalPer100g: 0,
          article: "",
        },
      ],
    };
    const quality = evaluateTechCardQuality(draft, calculateTechCard(draft));

    expect(quality.status).toBe("warning");
    expect(quality.issues.map((issue) => issue.title)).toEqual(
      expect.arrayContaining([
        "Не заполнены цены",
        "Не заполнено КБЖУ",
        "Выход не сходится",
      ]),
    );
  });
});

describe("tech card JSON export", () => {
  test("serializes and parses a tech card with venue profile", () => {
    const json = serializeTechCard(input, DEFAULT_VENUE_INTELLIGENCE);
    const document = parseTechCardExportDocument(json);

    expect(document.schema).toBe("receptor.tech-card");
    expect(document.version).toBe(1);
    expect(document.input.dishName).toBe(input.dishName);
    expect(document.input.ingredients[0].name).toBe("Паста");
    expect(document.venueProfile?.format).toBe(DEFAULT_VENUE_INTELLIGENCE.format);
  });

  test("rejects unsupported import format", () => {
    expect(() =>
      parseTechCardExportDocument(JSON.stringify({ schema: "unknown", version: 1 })),
    ).toThrow(/Неподдерживаемый формат/);
  });
});

describe("createTechCardLaunchPack", () => {
  test("creates menu, waiter and owner materials from a tech card", () => {
    const calculation = calculateTechCard(input);
    const quality = evaluateTechCardQuality(input, calculation);
    const pack = createTechCardLaunchPack(
      input,
      calculation,
      quality,
      DEFAULT_VENUE_INTELLIGENCE,
    );

    expect(pack.menuDescription).toContain(input.dishName);
    expect(pack.menuDescription).not.toContain("Городское заведение");
    expect(pack.menuDescription).not.toContain("формата");
    expect(pack.waiterPitch).toContain("Рекомендуйте");
    expect(pack.waiterPitch).toContain("вкус без лишней сложности");
    expect(pack.upsellIdeas.length).toBeGreaterThanOrEqual(3);
    expect(pack.ownerNotes.join("\n")).toContain("Проверка качества");
    expect(pack.markdown).toContain("# Запуск блюда");
  });

  test("creates dish-specific launch copy for fish dishes", () => {
    const fishInput: TechCardInput = {
      ...input,
      dishName: "Треска в панировке с брокколи и соусом биск",
      category: "Горячая кухня",
      ingredients: [
        {
          ...input.ingredients[0],
          id: "cod",
          name: "Филе трески",
          pricePerKg: 980,
        },
        {
          ...input.ingredients[1],
          id: "bisque",
          name: "Соус биск",
          pricePerKg: 780,
        },
      ],
    };
    const calculation = calculateTechCard(fishInput);
    const quality = evaluateTechCardQuality(fishInput, calculation);
    const pack = createTechCardLaunchPack(
      fishInput,
      calculation,
      quality,
      DEFAULT_VENUE_INTELLIGENCE,
    );

    expect(pack.menuDescription).toContain("хрустящая рыба");
    expect(pack.waiterPitch).toContain("Филе трески");
    expect(pack.upsellIdeas.join("\n")).toContain("белого вина");
  });

  test("does not overexplain supporting ingredients in menu copy", () => {
    const pastaInput: TechCardInput = {
      ...input,
      dishName: "Паста с мортаделлой в сливочном соусе",
      ingredients: [
        { ...input.ingredients[0], name: "Мортаделла", netQty: 90, pricePerKg: 900 },
        { ...input.ingredients[1], name: "Сливки 33%", netQty: 80, pricePerKg: 420 },
        {
          ...input.ingredients[1],
          id: "cheese",
          name: "Пармезан или твердый выдержанный сыр",
          netQty: 24,
          pricePerKg: 1400,
        },
      ],
    };
    const calculation = calculateTechCard(pastaInput);
    const quality = evaluateTechCardQuality(pastaInput, calculation);
    const pack = createTechCardLaunchPack(
      pastaInput,
      calculation,
      quality,
      DEFAULT_VENUE_INTELLIGENCE,
    );

    expect(pack.menuDescription).not.toContain("Сливки");
    expect(pack.menuDescription).not.toContain("Пармезан");
    expect(pack.waiterPitch).toContain("Мортаделла");
  });
});
