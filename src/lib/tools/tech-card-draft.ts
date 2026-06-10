import {
  DEFAULT_VENUE_INTELLIGENCE,
  formatVenueProfileForPrompt,
  type VenueIntelligenceProfile,
} from "@/lib/venues/intelligence";
import type { TechCardIngredient, TechCardInput } from "./tech-card";

const OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses";
const DEFAULT_MODEL = process.env.OPENAI_MODEL?.trim() || "gpt-5.5";

export type TechCardDraftInput = {
  idea: string;
  category?: string;
  portions?: number;
  targetFoodCostPercent?: number;
  venueProfile?: VenueIntelligenceProfile;
};

export type TechCardDraftResult = {
  input: TechCardInput;
  provider: "openai" | "fallback";
  note: string;
};

type OpenAITextBlock = { type?: string; text?: string };
type OpenAIResponse = {
  output_text?: string;
  output?: Array<{ content?: OpenAITextBlock[] }>;
};

type RawDraftIngredient = Partial<{
  name: unknown;
  unit: unknown;
  grossQty: unknown;
  netQty: unknown;
  pricePerKg: unknown;
  proteinPer100g: unknown;
  fatPer100g: unknown;
  carbsPer100g: unknown;
  kcalPer100g: unknown;
  article: unknown;
}>;

type RawDraft = Partial<{
  dishName: unknown;
  category: unknown;
  portions: unknown;
  outputWeight: unknown;
  targetFoodCostPercent: unknown;
  process: unknown;
  ingredients: unknown;
}>;

function openAIKey(): string | null {
  const key = process.env.OPENAI_API_KEY?.trim();
  return key ? key : null;
}

function extractOpenAIText(payload: OpenAIResponse): string {
  if (typeof payload.output_text === "string") return payload.output_text;
  return (payload.output ?? [])
    .flatMap((item) => item.content ?? [])
    .map((block) => block.text ?? "")
    .join("\n");
}

function extractJson(text: string): unknown {
  const match = text.match(/\{[\s\S]*\}/);
  if (!match) throw new Error("tech card draft JSON not found");
  return JSON.parse(match[0]) as unknown;
}

function asString(value: unknown, fallback = ""): string {
  return typeof value === "string" && value.trim() ? value.trim() : fallback;
}

function asNumber(value: unknown, fallback = 0): number {
  const parsed =
    typeof value === "number"
      ? value
      : typeof value === "string"
        ? Number(value.replace(",", "."))
        : Number.NaN;
  return Number.isFinite(parsed) && parsed >= 0 ? parsed : fallback;
}

function asUnit(value: unknown): TechCardIngredient["unit"] {
  return value === "ml" || value === "pcs" ? value : "g";
}

function ingredientId(index: number): string {
  return `draft-${index + 1}`;
}

export function normalizeTechCardDraft(
  value: unknown,
  fallback: TechCardDraftInput,
): TechCardInput {
  const raw = (value && typeof value === "object" ? value : {}) as RawDraft;
  const rawIngredients = Array.isArray(raw.ingredients)
    ? raw.ingredients
    : [];
  const ingredients = rawIngredients
    .map((item, index): TechCardIngredient => {
      const ingredient = (item && typeof item === "object"
        ? item
        : {}) as RawDraftIngredient;
      return {
        id: ingredientId(index),
        name: asString(ingredient.name, `Ингредиент ${index + 1}`),
        unit: asUnit(ingredient.unit),
        grossQty: asNumber(ingredient.grossQty),
        netQty: asNumber(ingredient.netQty),
        pricePerKg: asNumber(ingredient.pricePerKg),
        proteinPer100g: asNumber(ingredient.proteinPer100g),
        fatPer100g: asNumber(ingredient.fatPer100g),
        carbsPer100g: asNumber(ingredient.carbsPer100g),
        kcalPer100g: asNumber(ingredient.kcalPer100g),
        article: asString(ingredient.article),
      };
    })
    .filter((ingredient) => ingredient.name.trim().length > 0);

  return {
    dishName: asString(raw.dishName, fallback.idea),
    category: asString(raw.category, fallback.category || "Черновик"),
    portions: Math.max(asNumber(raw.portions, fallback.portions || 1), 1),
    outputWeight: asNumber(raw.outputWeight),
    targetFoodCostPercent: Math.max(
      asNumber(raw.targetFoodCostPercent, fallback.targetFoodCostPercent || 30),
      1,
    ),
    process: asString(raw.process, "Уточните технологию приготовления."),
    ingredients: ingredients.length ? ingredients : fallbackIngredients(fallback.idea),
  };
}

function fallbackIngredients(idea: string): TechCardIngredient[] {
  const lower = idea.toLowerCase();
  const base =
    lower.includes("салат") || lower.includes("цезар")
      ? [
          ["Лист салата", 90, 80, 450, 1.4, 0.2, 2.9, 17],
          ["Белковый ингредиент", 110, 100, 950, 20, 4, 0, 120],
          ["Соус", 45, 40, 620, 2, 35, 4, 340],
          ["Сыр", 25, 22, 1100, 25, 28, 1.5, 360],
        ]
      : [
          ["Основной продукт", 220, 200, 800, 18, 8, 0, 160],
          ["Гарнир", 180, 160, 180, 3, 1, 22, 120],
          ["Соус", 45, 40, 520, 2, 24, 5, 250],
          ["Декор / зелень", 12, 10, 700, 2, 0.5, 3, 25],
        ];

  return base.map((item, index) => ({
    id: ingredientId(index),
    name: item[0] as string,
    unit: "g",
    grossQty: item[1] as number,
    netQty: item[2] as number,
    pricePerKg: item[3] as number,
    proteinPer100g: item[4] as number,
    fatPer100g: item[5] as number,
    carbsPer100g: item[6] as number,
    kcalPer100g: item[7] as number,
    article: "",
  }));
}

function fallbackDraft(input: TechCardDraftInput): TechCardInput {
  const ingredients = fallbackIngredients(input.idea);
  const outputWeight = ingredients.reduce(
    (sum, ingredient) => sum + ingredient.netQty,
    0,
  );

  return {
    dishName: input.idea,
    category: input.category || "Черновик",
    portions: Math.max(input.portions || 1, 1),
    outputWeight,
    targetFoodCostPercent: input.targetFoodCostPercent || 30,
    process:
      "Подготовить ингредиенты, обработать основной продукт, соединить компоненты, довести вкус, оформить подачу. Уточните технологию под фактическую кухню и оборудование.",
    ingredients,
  };
}

function systemPrompt(): string {
  return `Ты — Receptor, AI-шеф и технолог ресторанного бизнеса.

Собери черновик технологической карты для дальнейшего редактирования.
Верни только JSON без markdown:
{
  "dishName": "название блюда",
  "category": "категория меню",
  "portions": 1,
  "outputWeight": 350,
  "targetFoodCostPercent": 30,
  "process": "технология приготовления, подача, контрольные точки",
  "ingredients": [
    {
      "name": "ингредиент",
      "unit": "g",
      "grossQty": 100,
      "netQty": 90,
      "pricePerKg": 500,
      "proteinPer100g": 10,
      "fatPer100g": 5,
      "carbsPer100g": 20,
      "kcalPer100g": 160,
      "article": ""
    }
  ]
}

Правила:
- unit только "g", "ml" или "pcs".
- Количества и КБЖУ должны быть реалистичными черновыми оценками.
- pricePerKg указывай как грубую рыночную оценку в рублях.
- article оставляй пустым: iiko-артикулы появятся после маппинга.
- Не притворяйся, что это финальная утверждённая ТТК.`;
}

function userPrompt(input: TechCardDraftInput): string {
  const profile = input.venueProfile ?? DEFAULT_VENUE_INTELLIGENCE;
  return [
    `Идея блюда: ${input.idea}`,
    input.category ? `Категория: ${input.category}` : "",
    `Порций: ${input.portions || 1}`,
    `Целевой фудкост: ${input.targetFoodCostPercent || 30}%`,
    "",
    "Контекст заведения:",
    formatVenueProfileForPrompt(profile),
  ]
    .filter(Boolean)
    .join("\n");
}

async function draftWithOpenAI(input: TechCardDraftInput): Promise<TechCardInput> {
  const key = openAIKey();
  if (!key) throw new Error("OPENAI_API_KEY is not set");

  const response = await fetch(OPENAI_RESPONSES_URL, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${key}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: DEFAULT_MODEL,
      instructions: systemPrompt(),
      input: userPrompt(input),
      max_output_tokens: 2600,
    }),
  });

  if (!response.ok) {
    throw new Error(`OpenAI tech-card draft failed: HTTP ${response.status}`);
  }

  const data = (await response.json()) as OpenAIResponse;
  return normalizeTechCardDraft(extractJson(extractOpenAIText(data)), input);
}

export async function generateTechCardDraft(
  input: TechCardDraftInput,
): Promise<TechCardDraftResult> {
  if (openAIKey()) {
    try {
      return {
        input: await draftWithOpenAI(input),
        provider: "openai",
        note: "Черновик собран через OpenAI с учётом профиля заведения.",
      };
    } catch (err) {
      console.warn("[tech-card-draft] OpenAI failed:", err);
    }
  }

  return {
    input: fallbackDraft(input),
    provider: "fallback",
    note: "Черновик собран локально. Уточните ингредиенты, цены и технологию перед использованием.",
  };
}
