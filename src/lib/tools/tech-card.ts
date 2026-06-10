import type { VenueIntelligenceProfile } from "@/lib/venues/intelligence";

export type TechCardIngredient = {
  id: string;
  name: string;
  unit: "g" | "ml" | "pcs";
  grossQty: number;
  netQty: number;
  pricePerKg: number;
  proteinPer100g: number;
  fatPer100g: number;
  carbsPer100g: number;
  kcalPer100g: number;
  article?: string;
};

export type TechCardInput = {
  dishName: string;
  category: string;
  portions: number;
  outputWeight: number;
  targetFoodCostPercent: number;
  process: string;
  ingredients: TechCardIngredient[];
};

export type IngredientCalculation = TechCardIngredient & {
  lossPercent: number;
  cost: number;
  protein: number;
  fat: number;
  carbs: number;
  kcal: number;
};

export type TechCardCalculation = {
  ingredients: IngredientCalculation[];
  totalNetWeight: number;
  totalGrossWeight: number;
  totalCost: number;
  costPerPortion: number;
  recommendedPrice: number;
  foodCostPercent: number;
  protein: number;
  fat: number;
  carbs: number;
  kcal: number;
  proteinPer100g: number;
  fatPer100g: number;
  carbsPer100g: number;
  kcalPer100g: number;
  mappingCoveragePercent: number;
  yieldDelta: number;
};

export type TechCardQualitySeverity = "ok" | "warning" | "critical";

export type TechCardQualityIssue = {
  severity: Exclude<TechCardQualitySeverity, "ok">;
  title: string;
  description: string;
};

export type TechCardQualityReport = {
  status: TechCardQualitySeverity;
  score: number;
  issues: TechCardQualityIssue[];
  nextActions: string[];
};

const round = (value: number, digits = 2): number => {
  if (!Number.isFinite(value)) return 0;
  const factor = 10 ** digits;
  return Math.round(value * factor) / factor;
};

const positive = (value: number): number => {
  if (!Number.isFinite(value) || value < 0) return 0;
  return value;
};

function ingredientCost(ingredient: TechCardIngredient): number {
  const qty = positive(ingredient.netQty);
  if (ingredient.unit === "pcs") return qty * positive(ingredient.pricePerKg);
  return (qty / 1000) * positive(ingredient.pricePerKg);
}

function nutrientFor(ingredient: TechCardIngredient, per100g: number): number {
  return (positive(ingredient.netQty) / 100) * positive(per100g);
}

export function calculateTechCard(input: TechCardInput): TechCardCalculation {
  const ingredients = input.ingredients.map((ingredient) => {
    const gross = positive(ingredient.grossQty);
    const net = positive(ingredient.netQty);
    const lossPercent = gross > 0 ? ((gross - net) / gross) * 100 : 0;

    return {
      ...ingredient,
      grossQty: gross,
      netQty: net,
      pricePerKg: positive(ingredient.pricePerKg),
      proteinPer100g: positive(ingredient.proteinPer100g),
      fatPer100g: positive(ingredient.fatPer100g),
      carbsPer100g: positive(ingredient.carbsPer100g),
      kcalPer100g: positive(ingredient.kcalPer100g),
      lossPercent: round(lossPercent, 1),
      cost: round(ingredientCost(ingredient), 2),
      protein: round(nutrientFor(ingredient, ingredient.proteinPer100g), 2),
      fat: round(nutrientFor(ingredient, ingredient.fatPer100g), 2),
      carbs: round(nutrientFor(ingredient, ingredient.carbsPer100g), 2),
      kcal: round(nutrientFor(ingredient, ingredient.kcalPer100g), 0),
    };
  });

  const totalNetWeight = round(
    ingredients.reduce((sum, ingredient) => sum + ingredient.netQty, 0),
    1,
  );
  const totalGrossWeight = round(
    ingredients.reduce((sum, ingredient) => sum + ingredient.grossQty, 0),
    1,
  );
  const totalCost = round(
    ingredients.reduce((sum, ingredient) => sum + ingredient.cost, 0),
    2,
  );
  const portions = Math.max(positive(input.portions), 1);
  const targetFoodCostPercent = Math.max(
    positive(input.targetFoodCostPercent),
    1,
  );
  const outputWeight = positive(input.outputWeight);
  const mappedCount = ingredients.filter((ingredient) =>
    ingredient.article?.trim(),
  ).length;

  const protein = round(
    ingredients.reduce((sum, ingredient) => sum + ingredient.protein, 0),
    2,
  );
  const fat = round(
    ingredients.reduce((sum, ingredient) => sum + ingredient.fat, 0),
    2,
  );
  const carbs = round(
    ingredients.reduce((sum, ingredient) => sum + ingredient.carbs, 0),
    2,
  );
  const kcal = round(
    ingredients.reduce((sum, ingredient) => sum + ingredient.kcal, 0),
    0,
  );

  return {
    ingredients,
    totalNetWeight,
    totalGrossWeight,
    totalCost,
    costPerPortion: round(totalCost / portions, 2),
    recommendedPrice: round(totalCost / (targetFoodCostPercent / 100), 0),
    foodCostPercent: targetFoodCostPercent,
    protein,
    fat,
    carbs,
    kcal,
    proteinPer100g: outputWeight ? round((protein / outputWeight) * 100, 2) : 0,
    fatPer100g: outputWeight ? round((fat / outputWeight) * 100, 2) : 0,
    carbsPer100g: outputWeight ? round((carbs / outputWeight) * 100, 2) : 0,
    kcalPer100g: outputWeight ? round((kcal / outputWeight) * 100, 0) : 0,
    mappingCoveragePercent: ingredients.length
      ? round((mappedCount / ingredients.length) * 100, 0)
      : 0,
    yieldDelta: round(totalNetWeight - outputWeight, 1),
  };
}

export function formatRub(value: number): string {
  return `${round(value, 2).toLocaleString("ru-RU")} ₽`;
}

export function evaluateTechCardQuality(
  input: TechCardInput,
  calculation: TechCardCalculation,
): TechCardQualityReport {
  const issues: TechCardQualityIssue[] = [];
  const filledIngredients = input.ingredients.filter((ingredient) =>
    ingredient.name.trim(),
  );

  if (!input.dishName.trim()) {
    issues.push({
      severity: "critical",
      title: "Нет названия блюда",
      description: "Без названия техкарту нельзя нормально сохранить, печатать или маппить в iiko.",
    });
  }

  if (filledIngredients.length === 0) {
    issues.push({
      severity: "critical",
      title: "Нет ингредиентов",
      description: "Добавьте хотя бы один ингредиент с нетто, ценой и КБЖУ.",
    });
  }

  const missingQty = filledIngredients.filter(
    (ingredient) => ingredient.netQty <= 0 || ingredient.grossQty <= 0,
  );
  if (missingQty.length > 0) {
    issues.push({
      severity: "critical",
      title: "Не заполнены брутто/нетто",
      description: `${missingQty.length} ингредиент(а) без корректного количества. Расчёт себестоимости и выхода будет неточным.`,
    });
  }

  const missingPrices = filledIngredients.filter(
    (ingredient) => ingredient.pricePerKg <= 0,
  );
  if (missingPrices.length > 0) {
    issues.push({
      severity: "warning",
      title: "Не заполнены цены",
      description: `${missingPrices.length} ингредиент(а) без цены. Фудкост и рекомендуемая цена занижены.`,
    });
  }

  const missingNutrition = filledIngredients.filter(
    (ingredient) =>
      ingredient.kcalPer100g <= 0 &&
      ingredient.proteinPer100g <= 0 &&
      ingredient.fatPer100g <= 0 &&
      ingredient.carbsPer100g <= 0,
  );
  if (missingNutrition.length > 0) {
    issues.push({
      severity: "warning",
      title: "Не заполнено КБЖУ",
      description: `${missingNutrition.length} ингредиент(а) без пищевой ценности. КБЖУ на 100 г будет неполным.`,
    });
  }

  const excessiveLoss = calculation.ingredients.filter(
    (ingredient) => ingredient.name.trim() && ingredient.lossPercent > 45,
  );
  if (excessiveLoss.length > 0) {
    issues.push({
      severity: "warning",
      title: "Высокие потери",
      description: `${excessiveLoss.length} ингредиент(а) с потерями выше 45%. Проверьте брутто/нетто или технологию обработки.`,
    });
  }

  if (input.outputWeight > 0 && Math.abs(calculation.yieldDelta) > 20) {
    issues.push({
      severity: "warning",
      title: "Выход не сходится",
      description: `Сумма нетто отличается от указанного выхода на ${calculation.yieldDelta} г. Для печати и iiko лучше выровнять.`,
    });
  }

  if (
    filledIngredients.length > 0 &&
    calculation.mappingCoveragePercent < 80
  ) {
    issues.push({
      severity: "warning",
      title: "Мало iiko-артикулов",
      description: `Покрытие артикулами: ${calculation.mappingCoveragePercent}%. Для iiko-экспорта нужно довести маппинг почти до 100%.`,
    });
  }

  const criticalCount = issues.filter(
    (issue) => issue.severity === "critical",
  ).length;
  const warningCount = issues.filter(
    (issue) => issue.severity === "warning",
  ).length;
  const score = Math.max(0, 100 - criticalCount * 28 - warningCount * 12);
  const status: TechCardQualitySeverity =
    criticalCount > 0 ? "critical" : warningCount > 0 ? "warning" : "ok";

  const nextActions =
    issues.length === 0
      ? [
          "Можно печатать PDF или переходить к iiko-маппингу.",
          "Перед продажей проверьте фактические цены поставщиков.",
        ]
      : issues.slice(0, 4).map((issue) => issue.title);

  return { status, score, issues, nextActions };
}

export function createTechCardMarkdown(
  input: TechCardInput,
  calculation: TechCardCalculation,
  venueProfile?: VenueIntelligenceProfile,
): string {
  const rows = calculation.ingredients
    .map(
      (ingredient) =>
        `| ${ingredient.name || "Ингредиент"} | ${ingredient.grossQty} ${ingredient.unit} | ${ingredient.netQty} ${ingredient.unit} | ${ingredient.lossPercent}% | ${formatRub(ingredient.cost)} | ${ingredient.article || "-"} |`,
    )
    .join("\n");

  const venueBlock = venueProfile
    ? `
## Контекст заведения

- Формат: ${venueProfile.format}
- Позиционирование: ${venueProfile.positioning}
- Фокус владельца: ${venueProfile.ownerGoals.slice(0, 3).join("; ")}
`
    : "";

  return `# Технологическая карта: ${input.dishName || "Новое блюдо"}

**Категория:** ${input.category || "-"}
**Порций:** ${input.portions || 1}
**Выход:** ${input.outputWeight || calculation.totalNetWeight} г
**Целевой фудкост:** ${input.targetFoodCostPercent || calculation.foodCostPercent}%
${venueBlock}

## Сводка

- Себестоимость блюда: ${formatRub(calculation.totalCost)}
- Себестоимость порции: ${formatRub(calculation.costPerPortion)}
- Рекомендуемая цена: ${formatRub(calculation.recommendedPrice)}
- КБЖУ на 100 г: ${calculation.kcalPer100g} ккал / Б ${calculation.proteinPer100g} / Ж ${calculation.fatPer100g} / У ${calculation.carbsPer100g}
- Покрытие артикулами iiko: ${calculation.mappingCoveragePercent}%

## Ингредиенты

| Ингредиент | Брутто | Нетто | Потери | Стоимость | Артикул iiko |
| --- | ---: | ---: | ---: | ---: | --- |
${rows}

## Технология

${input.process || "Опишите технологию приготовления, подачу и условия хранения."}
`;
}
