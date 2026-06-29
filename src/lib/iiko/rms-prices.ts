import type { Product } from "./models";

type RawRmsPrice = Record<string, unknown>;
type ProductUnit = NonNullable<Product["unit"]>;

export type RmsPrice = {
  skuId: string;
  name: string;
  article?: string;
  unit: ProductUnit;
  originalUnit?: string;
  pricePerUnit: number;
  pricePerKg: number;
  currency: string;
  vatPct: number;
  source: "iiko_rms";
  rawField: string;
  active: boolean;
};

const ARTICLE_FIELDS = [
  "num",
  "article",
  "nomenclatureCode",
  "productCode",
  "itemCode",
] as const;

const NORMALIZED_COST_FIELDS = [
  "purchase_price_per_unit",
  "purchasePricePerUnit",
  "cost_price_per_unit",
  "costPricePerUnit",
  "cost_per_unit",
  "costPerUnit",
  // Legacy RMS cache stores purchase cost in snake_case `price_per_unit`.
  "price_per_unit",
] as const;

const BULK_COST_FIELDS = [
  "purchasePrice",
  "purchase_price",
  "cost",
  "costPrice",
] as const;

const COST_PER_KG_FIELDS = [
  "pricePerKg",
  "price_per_kg",
  "costPerKg",
  "cost_per_kg",
] as const;

const NESTED_NORMALIZED_COST_FIELDS = [
  ...NORMALIZED_COST_FIELDS,
  "pricePerUnit",
] as const;

const COST_CONTAINER_FIELDS = [
  "purchase",
  "purchaseCost",
  "purchase_cost",
  "purchasePrice",
  "purchase_price",
  "cost",
  "costPrice",
  "cost_price",
  "primeCost",
  "prime_cost",
  "lastPurchasePrice",
  "last_purchase_price",
  "averageCost",
  "average_cost",
  "weightedAverageCost",
  "weighted_average_cost",
] as const;

const EXPLICIT_COST_CONTAINER_FIELDS = [
  ...COST_CONTAINER_FIELDS,
  "prices",
  "priceInfo",
  "price_info",
  "costs",
  "purchasePrices",
  "purchase_prices",
] as const;

const NESTED_BULK_COST_FIELDS = [
  ...BULK_COST_FIELDS,
  "price",
  "value",
  "amount",
] as const;

const UNIT_ALIASES: Record<string, ProductUnit> = {
  kg: "g",
  kilogram: "g",
  кг: "g",
  g: "g",
  gram: "g",
  г: "g",
  l: "ml",
  liter: "ml",
  litre: "ml",
  л: "ml",
  ml: "ml",
  milliliter: "ml",
  мл: "ml",
  pcs: "pcs",
  piece: "pcs",
  pieces: "pcs",
  шт: "pcs",
};

export function normalizeRmsPrices(payload: unknown): RmsPrice[] {
  return extractRows(payload)
    .map((row) => normalizeRmsPrice(row))
    .filter((price): price is RmsPrice => price !== null);
}

export function normalizeRmsPrice(raw: RawRmsPrice): RmsPrice | null {
  const skuId = readText(raw, [
    "skuId",
    "id",
    "productId",
    "product.id",
    "nomenclatureId",
    "nomenclature.id",
    "_id",
  ]);
  const name = readText(raw, [
    "name",
    "title",
    "product.name",
    "nomenclature.name",
  ]);
  if (!skuId || !name) return null;

  const originalUnit = readText(raw, [
    "original_unit",
    "originalUnit",
    "unit",
    "measureUnit",
    "measuringUnitName",
  ]);
  const unit = normalizeUnit(originalUnit);
  const cost = readCost(raw, originalUnit, unit);
  if (!cost) return null;

  return {
    skuId,
    name,
    article: readArticle(raw),
    unit,
    originalUnit: originalUnit || undefined,
    pricePerUnit: cost.pricePerUnit,
    pricePerKg: cost.pricePerKg,
    currency: normalizeCurrency(readText(raw, ["currency"])),
    vatPct:
      readNumber(raw, ["vat_pct", "vatPct", "vat", "vatRate", "taxRate"]) ?? 0,
    source: "iiko_rms",
    rawField: cost.rawField,
    active: readBoolean(raw, ["active", "isActive"], true),
  };
}

export function mergeProductsWithRmsPrices(
  products: Product[],
  prices: RmsPrice[],
): Product[] {
  if (prices.length === 0) return products;

  const byId = new Map<string, RmsPrice>();
  const byArticle = new Map<string, RmsPrice>();
  const byName = new Map<string, RmsPrice>();

  prices.forEach((price) => {
    byId.set(price.skuId, price);
    if (price.article) byArticle.set(price.article, price);
    byName.set(normalizeKey(price.name), price);
  });

  return products.map((product) => {
    const price =
      byId.get(product.id) ??
      (product.article ? byArticle.get(product.article) : undefined) ??
      byName.get(normalizeKey(product.name));
    if (!price) return product;

    return {
      ...product,
      article: product.article ?? price.article,
      unit: product.unit ?? price.unit,
      originalUnit: product.originalUnit ?? price.originalUnit,
      purchasePrice: price.pricePerKg,
      purchasePricePerUnit: price.pricePerUnit,
      pricePerKg: price.pricePerKg,
    };
  });
}

function readCost(
  raw: RawRmsPrice,
  originalUnit: string | undefined,
  unit: ProductUnit,
): { pricePerUnit: number; pricePerKg: number; rawField: string } | null {
  const normalized =
    readNumberWithField(raw, NORMALIZED_COST_FIELDS) ??
    readNestedNumberWithField(
      raw,
      EXPLICIT_COST_CONTAINER_FIELDS,
      NESTED_NORMALIZED_COST_FIELDS,
    );
  if (normalized) {
    return {
      pricePerUnit: normalized.value,
      pricePerKg: toReferencePrice(normalized.value, unit),
      rawField: normalized.field,
    };
  }

  const perKg =
    readNumberWithField(raw, COST_PER_KG_FIELDS) ??
    readNestedNumberWithField(
      raw,
      EXPLICIT_COST_CONTAINER_FIELDS,
      COST_PER_KG_FIELDS,
    );
  if (perKg) {
    return {
      pricePerUnit: unit === "pcs" ? perKg.value : perKg.value / 1000,
      pricePerKg: perKg.value,
      rawField: perKg.field,
    };
  }

  const bulk =
    readNumberWithField(raw, BULK_COST_FIELDS) ??
    readNestedNumberWithField(
      raw,
      COST_CONTAINER_FIELDS,
      NESTED_BULK_COST_FIELDS,
    ) ??
    readNestedNumberWithField(
      raw,
      EXPLICIT_COST_CONTAINER_FIELDS,
      BULK_COST_FIELDS,
    );
  if (!bulk) return null;

  return {
    pricePerUnit: toPricePerUnit(bulk.value, originalUnit, unit),
    pricePerKg: toPricePerKg(bulk.value, originalUnit, unit),
    rawField: bulk.field,
  };
}

function extractRows(payload: unknown): RawRmsPrice[] {
  if (Array.isArray(payload)) return payload.filter(isRecord);
  if (!isRecord(payload)) return [];

  for (const key of ["prices", "products", "items", "nomenclature", "data"]) {
    const value = payload[key];
    if (Array.isArray(value)) return value.filter(isRecord);
  }

  return [];
}

function readArticle(raw: RawRmsPrice): string | undefined {
  return readText(raw, [...ARTICLE_FIELDS]);
}

function readText(raw: RawRmsPrice, keys: string[]): string | undefined {
  for (const key of keys) {
    const value = readPath(raw, key);
    if (value === null || value === undefined) continue;
    const text = String(value).trim();
    if (text) return text;
  }
  return undefined;
}

function readNumber(raw: RawRmsPrice, keys: string[]): number | undefined {
  return readNumberWithField(raw, keys)?.value;
}

function readNumberWithField(
  raw: RawRmsPrice,
  keys: readonly string[],
): { field: string; value: number } | undefined {
  for (const key of keys) {
    const value = toNumber(readPath(raw, key));
    if (value !== undefined && value > 0) return { field: key, value };
  }
  return undefined;
}

function readNestedNumberWithField(
  raw: RawRmsPrice,
  containers: readonly string[],
  keys: readonly string[],
): { field: string; value: number } | undefined {
  for (const container of containers) {
    const value = readPath(raw, container);

    if (isRecord(value)) {
      const nested = readNumberWithField(value, keys);
      if (nested) {
        return {
          field: `${container}.${nested.field}`,
          value: nested.value,
        };
      }
    }

    for (const key of keys) {
      const field = `${container}.${key}`;
      const flattened = toNumber(readPath(raw, field));
      if (flattened !== undefined && flattened > 0) {
        return { field, value: flattened };
      }
    }
  }

  return undefined;
}

function readPath(raw: RawRmsPrice, key: string): unknown {
  if (Object.prototype.hasOwnProperty.call(raw, key)) return raw[key];
  if (!key.includes(".")) return undefined;

  return key.split(".").reduce<unknown>((current, part) => {
    if (!isRecord(current)) return undefined;
    return current[part];
  }, raw);
}

function readBoolean(
  raw: RawRmsPrice,
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

function normalizeUnit(unit?: string): ProductUnit {
  if (!unit) return "pcs";
  return UNIT_ALIASES[unit.trim().toLowerCase()] ?? "pcs";
}

function normalizeCurrency(currency?: string): string {
  if (!currency) return "RUB";
  const normalized = currency.trim().toUpperCase();
  return normalized === "РУБ" || normalized === "РУБЛЕЙ" ? "RUB" : normalized;
}

function toPricePerUnit(
  price: number,
  originalUnit: string | undefined,
  unit: ProductUnit,
): number {
  if (unit === "pcs") return price;
  return isBulkUnit(originalUnit) ? price / 1000 : price;
}

function toPricePerKg(
  price: number,
  originalUnit: string | undefined,
  unit: ProductUnit,
): number {
  if (unit === "pcs") return price;
  return isSmallUnit(originalUnit) ? price * 1000 : price;
}

function toReferencePrice(pricePerUnit: number, unit: ProductUnit): number {
  return unit === "pcs" ? pricePerUnit : pricePerUnit * 1000;
}

function isBulkUnit(unit?: string): boolean {
  const normalized = unit?.trim().toLowerCase();
  return (
    normalized === "kg" ||
    normalized === "кг" ||
    normalized === "l" ||
    normalized === "л"
  );
}

function isSmallUnit(unit?: string): boolean {
  const normalized = unit?.trim().toLowerCase();
  return (
    normalized === "g" ||
    normalized === "г" ||
    normalized === "ml" ||
    normalized === "мл"
  );
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

function normalizeKey(value: string): string {
  return value
    .trim()
    .toLowerCase()
    .replace(/[^\p{L}\p{N}\s]/gu, " ")
    .replace(/\s+/g, " ");
}

function isRecord(value: unknown): value is RawRmsPrice {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
