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

export type TechCardExportDocument = {
  schema: "receptor.tech-card";
  version: 1;
  exportedAt: string;
  input: TechCardInput;
  venueProfile?: VenueIntelligenceProfile;
};

export type TechCardLaunchPack = {
  menuDescription: string;
  waiterPitch: string;
  upsellIdeas: string[];
  ownerNotes: string[];
  markdown: string;
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

export function createTechCardExportDocument(
  input: TechCardInput,
  venueProfile?: VenueIntelligenceProfile,
  exportedAt = new Date().toISOString(),
): TechCardExportDocument {
  return {
    schema: "receptor.tech-card",
    version: 1,
    exportedAt,
    input,
    venueProfile,
  };
}

export function serializeTechCard(
  input: TechCardInput,
  venueProfile?: VenueIntelligenceProfile,
): string {
  return JSON.stringify(
    createTechCardExportDocument(input, venueProfile),
    null,
    2,
  );
}

function isObject(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function parseIngredient(
  value: unknown,
  index: number,
): TechCardIngredient | null {
  if (!isObject(value)) return null;

  const unit = value.unit === "ml" || value.unit === "pcs" ? value.unit : "g";
  return {
    id:
      typeof value.id === "string" && value.id.trim()
        ? value.id
        : `import-${index + 1}`,
    name: typeof value.name === "string" ? value.name : "",
    unit,
    grossQty: positive(Number(value.grossQty)),
    netQty: positive(Number(value.netQty)),
    pricePerKg: positive(Number(value.pricePerKg)),
    proteinPer100g: positive(Number(value.proteinPer100g)),
    fatPer100g: positive(Number(value.fatPer100g)),
    carbsPer100g: positive(Number(value.carbsPer100g)),
    kcalPer100g: positive(Number(value.kcalPer100g)),
    article: typeof value.article === "string" ? value.article : "",
  };
}

function parseTechCardInput(value: unknown): TechCardInput {
  if (!isObject(value)) {
    throw new Error("Некорректный файл техкарты: input должен быть объектом.");
  }

  const ingredients = Array.isArray(value.ingredients)
    ? value.ingredients
        .map((ingredient, index) => parseIngredient(ingredient, index))
        .filter((ingredient): ingredient is TechCardIngredient =>
          Boolean(ingredient),
        )
    : [];

  return {
    dishName: typeof value.dishName === "string" ? value.dishName : "",
    category: typeof value.category === "string" ? value.category : "",
    portions: Math.max(positive(Number(value.portions)), 1),
    outputWeight: positive(Number(value.outputWeight)),
    targetFoodCostPercent: Math.max(
      positive(Number(value.targetFoodCostPercent)),
      1,
    ),
    process: typeof value.process === "string" ? value.process : "",
    ingredients,
  };
}

export function parseTechCardExportDocument(
  json: string,
): TechCardExportDocument {
  const parsed = JSON.parse(json) as unknown;
  if (!isObject(parsed)) {
    throw new Error("Некорректный файл техкарты.");
  }
  if (parsed.schema !== "receptor.tech-card" || parsed.version !== 1) {
    throw new Error("Неподдерживаемый формат техкарты Receptor.");
  }

  return {
    schema: "receptor.tech-card",
    version: 1,
    exportedAt:
      typeof parsed.exportedAt === "string"
        ? parsed.exportedAt
        : new Date().toISOString(),
    input: parseTechCardInput(parsed.input),
    venueProfile: isObject(parsed.venueProfile)
      ? (parsed.venueProfile as VenueIntelligenceProfile)
      : undefined,
  };
}

function topCostIngredients(calculation: TechCardCalculation): string[] {
  return [...calculation.ingredients]
    .filter((ingredient) => ingredient.name.trim())
    .sort((a, b) => b.cost - a.cost)
    .slice(0, 3)
    .map((ingredient) => ingredient.name);
}

function dishBase(input: TechCardInput): string {
  return input.dishName.trim() || "Новое блюдо";
}

function humanList(items: string[]): string {
  if (items.length === 0) return "";
  if (items.length === 1) return items[0];
  if (items.length === 2) return `${items[0]} и ${items[1]}`;
  return `${items.slice(0, -1).join(", ")} и ${items[items.length - 1]}`;
}

function isSupportingIngredient(name: string): boolean {
  return /сливк|масл|сыр|пармезан|паниров|соль|сахар|мук|зелень|декор|вода|соус/i.test(name);
}

function heroIngredients(calculation: TechCardCalculation): string[] {
  const named = [...calculation.ingredients].filter((ingredient) =>
    ingredient.name.trim(),
  );
  const heroes = named
    .filter((ingredient) => !isSupportingIngredient(ingredient.name))
    .sort((a, b) => b.netQty - a.netQty)
    .slice(0, 2)
    .map((ingredient) => ingredient.name);

  if (heroes.length > 0) return heroes;
  return named
    .sort((a, b) => b.netQty - a.netQty)
    .slice(0, 2)
    .map((ingredient) => ingredient.name);
}

function dishTone(input: TechCardInput, keyIngredients: string[]): string {
  const text = `${input.dishName} ${input.category} ${keyIngredients.join(" ")}`.toLowerCase();
  if (/треск|рыб|кревет|морепродукт|биск/.test(text)) {
    return "хрустящая рыба, мягкий гарнир и насыщенный соус";
  }
  if (/паст|ризот|слив|пармезан|мортадел/.test(text)) {
    return "плотная паста с мягкой солёностью и ресторанной подачей";
  }
  if (/стейк|говядин|утк|томл/.test(text)) {
    return "насыщенный мясной вкус, сочность и понятная ресторанная подача";
  }
  if (/салат|зелень|овощ/.test(text)) {
    return "свежесть, лёгкая текстура и чистый вкус ингредиентов";
  }
  if (/десерт|шоколад|медов|фондан/.test(text)) {
    return "выразительная сладость, понятная текстура и финальный акцент после основного блюда";
  }
  return "понятный вкус, аккуратная подача и стабильное качество";
}

function pairingIdeas(input: TechCardInput): string[] {
  const text = `${input.dishName} ${input.category}`.toLowerCase();
  if (/треск|рыб|кревет|морепродукт|биск/.test(text)) {
    return [
      "Предложить бокал сухого белого вина или безалкогольный цитрусовый лимонад.",
      "Добавить лёгкую закуску перед блюдом, если гость выбирает полноценный ужин.",
      "После блюда предложить десерт с мягкой кислотностью или кофе.",
    ];
  }
  if (/паст|ризот|слив|пармезан|мортадел/.test(text)) {
    return [
      "Предложить бокал белого или лёгкого красного вина под сливочную основу.",
      "Добавить салат или овощную закуску, чтобы сбалансировать плотное блюдо.",
      "Предложить десерт или эспрессо после основного блюда.",
    ];
  }
  return [
    "Предложить напиток, который усиливает основной вкус блюда.",
    "Предложить лёгкую закуску или салат, если блюдо берут как основное.",
    "Предложить десерт или кофе после блюда, если чек нужно мягко поднять.",
  ];
}

export function createTechCardLaunchPack(
  input: TechCardInput,
  calculation: TechCardCalculation,
  quality: TechCardQualityReport,
  venueProfile?: VenueIntelligenceProfile,
): TechCardLaunchPack {
  const dish = dishBase(input);
  const keyIngredients = topCostIngredients(calculation);
  const heroes = heroIngredients(calculation);
  const heroText = heroes.length ? humanList(heroes) : "понятная основа блюда";
  const tone = dishTone(input, [...keyIngredients, ...heroes]);
  const priceHint = calculation.recommendedPrice
    ? `Рекомендуемая цена при целевом фудкосте: ${formatRub(calculation.recommendedPrice)}.`
    : "Рекомендуемую цену стоит уточнить после заполнения цен.";
  const profileFocus = venueProfile?.ownerGoals[0]
    ? `Фокус владельца: ${venueProfile.ownerGoals[0]}.`
    : "Фокус владельца: проверить цену, выход и стабильность приготовления.";

  const menuDescription = `${dish} — ${tone}.`;
  const waiterPitch = `Рекомендуйте ${dish.toLowerCase()} как понятное горячее блюдо: ${heroText}, аккуратная подача, вкус без лишней сложности.`;
  const upsellIdeas = pairingIdeas(input);
  const ownerNotes = [
    priceHint,
    `Preflight score: ${quality.score}. ${quality.status === "ok" ? "Блокеров нет." : "Перед запуском стоит закрыть замечания preflight."}`,
    calculation.mappingCoveragePercent < 100
      ? "iiko-маппинг появится после подключения номенклатуры и артикулов."
      : "iiko-маппинг заполнен.",
    profileFocus,
  ];

  const markdown = `# Launch Pack: ${dish}

## Описание для меню

${menuDescription}

## Скрипт официанта

${waiterPitch}

## Upsell

${upsellIdeas.map((idea) => `- ${idea}`).join("\n")}

## Заметки владельца

${ownerNotes.map((note) => `- ${note}`).join("\n")}
`;

  return {
    menuDescription,
    waiterPitch,
    upsellIdeas,
    ownerNotes,
    markdown,
  };
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
