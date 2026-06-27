import { ProductSchema, type Product } from "./models";

type RawProduct = Record<string, unknown>;

const ARTICLE_FIELDS = [
  "num",
  "article",
  "nomenclatureCode",
  "productCode",
  "itemCode",
] as const;

const UNIT_ALIASES: Record<string, Product["unit"]> = {
  kg: "g",
  kilogram: "g",
  "кг": "g",
  g: "g",
  gram: "g",
  "г": "g",
  l: "ml",
  liter: "ml",
  litre: "ml",
  "л": "ml",
  ml: "ml",
  milliliter: "ml",
  "мл": "ml",
  pcs: "pcs",
  piece: "pcs",
  pieces: "pcs",
  "шт": "pcs",
};

export function normalizeIikoProduct(raw: RawProduct): Product | null {
  const id = readText(raw, ["id", "productId"]);
  const name = readText(raw, ["name", "title"]);
  if (!id || !name) return null;

  const originalUnit = readText(raw, ["unit", "measureUnit", "measuringUnitName"]);
  const unit = normalizeUnit(originalUnit);
  const purchasePrice = readNumber(raw, [
    "purchasePrice",
    "purchase_price",
    "cost",
    "costPrice",
  ]);
  const menuPricePerUnit = readNumber(raw, ["pricePerUnit"]);
  const legacyCostPricePerUnit = readNumber(raw, ["price_per_unit"]);
  const directPricePerUnit = menuPricePerUnit ?? legacyCostPricePerUnit;
  const directPurchasePricePerUnit = readNumber(raw, [
    "purchasePricePerUnit",
    "purchase_price_per_unit",
  ]);
  const menuPrice =
    readNumber(raw, ["price", "currentPrice"]) ??
    readFirstSizePrice(raw);
  const pricePerUnit =
    directPricePerUnit ?? toPricePerUnit(menuPrice, originalUnit, unit);
  const purchasePricePerUnit =
    directPurchasePricePerUnit ??
    toPricePerUnit(purchasePrice, originalUnit, unit);
  const directTechCardPrice = readNumber(raw, [
    "pricePerKg",
    "price_per_kg",
    "costPerKg",
    "cost_per_kg",
  ]);
  const directNormalizedPrice =
    directPurchasePricePerUnit ?? legacyCostPricePerUnit;
  const techCardPricePerKg =
    directTechCardPrice ??
    toTechCardPriceFromNormalizedUnit(directNormalizedPrice, unit) ??
    toTechCardPricePerKg(purchasePrice, originalUnit, unit);

  return ProductSchema.parse({
    id,
    name,
    parentGroupId: readText(raw, ["parentGroupId", "groupId", "group", "category"]),
    sizePrices: menuPrice ? [{ price: { currentPrice: menuPrice } }] : [],
    article: readArticle(raw),
    quickDialCode: readText(raw, ["code", "orderItemId"]),
    unit,
    originalUnit: originalUnit || undefined,
    price: menuPrice,
    purchasePrice,
    pricePerUnit,
    purchasePricePerUnit,
    pricePerKg: techCardPricePerKg,
    active: readBoolean(raw, ["active", "isActive"], true),
    type: readText(raw, ["type", "productType"]),
  });
}

export function normalizeIikoProducts(payload: unknown): Product[] {
  const rows = extractProductRows(payload);
  return rows
    .map((row) => normalizeIikoProduct(row))
    .filter((product): product is Product => product !== null);
}

export function searchIikoProducts(
  products: Product[],
  query: string,
  limit = 20,
): Product[] {
  const normalizedQuery = normalizeSearch(query);
  if (!normalizedQuery) return [];

  return products
    .map((product) => ({
      product,
      score: scoreProduct(product, normalizedQuery),
    }))
    .filter((item) => item.score > 0)
    .sort((a, b) => b.score - a.score || a.product.name.localeCompare(b.product.name))
    .slice(0, limit)
    .map((item) => item.product);
}

function extractProductRows(payload: unknown): RawProduct[] {
  if (Array.isArray(payload)) return payload.filter(isRecord);
  if (!isRecord(payload)) return [];

  for (const key of ["products", "items", "nomenclature", "data"]) {
    const value = payload[key];
    if (Array.isArray(value)) return value.filter(isRecord);
  }

  return [];
}

function scoreProduct(product: Product, normalizedQuery: string): number {
  const name = normalizeSearch(product.name);
  const article = normalizeSearch(product.article ?? "");
  const quickDialCode = normalizeSearch(product.quickDialCode ?? "");

  if (article && article === normalizedQuery) return 100;
  if (name === normalizedQuery) return 90;
  if (article && article.includes(normalizedQuery)) return 80;
  if (name.startsWith(normalizedQuery)) return 70;
  if (name.includes(normalizedQuery)) return 50;
  if (quickDialCode && quickDialCode.includes(normalizedQuery)) return 30;
  return 0;
}

function readArticle(raw: RawProduct): string | undefined {
  for (const field of ARTICLE_FIELDS) {
    const value = raw[field];
    if (value === null || value === undefined) continue;
    const article = String(value).trim();
    if (article && article !== "0") return article;
  }
  return undefined;
}

function readFirstSizePrice(raw: RawProduct): number | undefined {
  const sizePrices = raw.sizePrices;
  if (!Array.isArray(sizePrices)) return undefined;
  for (const item of sizePrices) {
    if (!isRecord(item)) continue;
    const price = item.price;
    if (!isRecord(price)) continue;
    const currentPrice = toNumber(price.currentPrice);
    if (currentPrice !== undefined) return currentPrice;
  }
  return undefined;
}

function readText(raw: RawProduct, keys: string[]): string | undefined {
  for (const key of keys) {
    const value = raw[key];
    if (value === null || value === undefined) continue;
    const text = String(value).trim();
    if (text) return text;
  }
  return undefined;
}

function readNumber(raw: RawProduct, keys: string[]): number | undefined {
  for (const key of keys) {
    const value = toNumber(raw[key]);
    if (value !== undefined) return value;
  }
  return undefined;
}

function readBoolean(
  raw: RawProduct,
  keys: string[],
  fallback: boolean,
): boolean {
  for (const key of keys) {
    const value = raw[key];
    if (typeof value === "boolean") return value;
    if (typeof value === "string") {
      if (value.toLowerCase() === "true") return true;
      if (value.toLowerCase() === "false") return false;
    }
  }
  return fallback;
}

function normalizeUnit(unit?: string): Product["unit"] {
  if (!unit) return "pcs";
  return UNIT_ALIASES[unit.trim().toLowerCase()] ?? "pcs";
}

function toPricePerUnit(
  price: number | undefined,
  originalUnit: string | undefined,
  unit: Product["unit"],
): number | undefined {
  if (price === undefined) return undefined;
  if (unit === "pcs") return price;
  return isBulkUnit(originalUnit) ? price / 1000 : price;
}

function toTechCardPricePerKg(
  price: number | undefined,
  originalUnit: string | undefined,
  unit: Product["unit"],
): number | undefined {
  if (price === undefined) return undefined;
  if (unit === "pcs") return price;
  return isSmallUnit(originalUnit) ? price * 1000 : price;
}

function toTechCardPriceFromNormalizedUnit(
  price: number | undefined,
  unit: Product["unit"],
): number | undefined {
  if (price === undefined) return undefined;
  if (unit === "pcs") return price;
  return price * 1000;
}

function isBulkUnit(unit?: string): boolean {
  const normalized = unit?.trim().toLowerCase();
  return normalized === "kg" || normalized === "кг" || normalized === "l" || normalized === "л";
}

function isSmallUnit(unit?: string): boolean {
  const normalized = unit?.trim().toLowerCase();
  return normalized === "g" || normalized === "г" || normalized === "ml" || normalized === "мл";
}

function toNumber(value: unknown): number | undefined {
  if (typeof value === "number" && Number.isFinite(value) && value >= 0) {
    return value;
  }
  if (typeof value === "string" && value.trim()) {
    const parsed = Number(value.replace(",", "."));
    if (Number.isFinite(parsed) && parsed >= 0) return parsed;
  }
  return undefined;
}

function normalizeSearch(value: string): string {
  return value
    .trim()
    .toLowerCase()
    .replace(/\s+/g, " ");
}

function isRecord(value: unknown): value is RawProduct {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
