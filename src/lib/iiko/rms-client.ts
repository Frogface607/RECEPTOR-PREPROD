/**
 * Minimal iiko RMS Server client.
 *
 * RMS lives on a venue-hosted server (`https://{host}/resto/api/...`) and uses
 * SHA1 password auth + a session key. This implementation covers the BI
 * methods Receptor renders today: revenue, dishes, categories and day shifts.
 */

import { createHash } from "crypto";
import { resolvePeriodToDates } from "./mock-client";
import type { IikoClient } from "./types";
import type {
  Period,
  Product,
  RevenueSummary,
  DishStat,
  CategoryStat,
  ShiftStat,
} from "./models";
import {
  CategoryStatSchema,
  DishStatSchema,
  RevenueSummarySchema,
  ShiftStatSchema,
} from "./models";
import { normalizeIikoProducts, searchIikoProducts } from "./nomenclature";
import {
  mergeProductsWithRmsPrices,
  normalizeRmsPrices,
  type RmsPrice,
} from "./rms-prices";

export interface RmsIikoClientOptions {
  host: string;
  login: string;
  password: string;
  today: string;
  fetchImpl?: typeof fetch;
}

export type RmsOrganization = {
  id: string;
  name: string;
};

type RmsOlapRow = Record<string, unknown>;
type RmsRawRow = Record<string, unknown>;

export type RmsCostFieldProbe = {
  endpoint: string | null;
  costStatus:
    "ready" | "menu-prices-only" | "missing-cost-fields" | "unreadable";
  rawRows: number;
  normalizedProducts: number;
  activeProducts: number;
  normalizedPriceRows: number;
  productsWithCachedCost: number;
  productsWithPurchasePrice: number;
  productsWithMenuPrice: number;
  productsWithTechCardPrice: number;
  costFieldCounts: Record<string, number>;
  menuPriceFieldCounts: Record<string, number>;
  priceFieldCounts: Record<string, number>;
  rawFieldCounts: Record<string, number>;
  error?: string;
};

export type RmsAssemblyChartsProbe = {
  endpoint: string | null;
  status: "ready" | "empty" | "forbidden" | "unreadable";
  dateFrom: string;
  dateTo: string;
  assemblyCharts: number;
  preparedCharts: number;
  normalizedCharts: number;
  chartsWithDishLink: number;
  chartsWithItems: number;
  totalItems: number;
  ingredientRows: number;
  ingredientRowsWithProductLink: number;
  ingredientRowsWithAmount: number;
  ingredientRowsWithUnit: number;
  rawFieldCounts: Record<string, number>;
  ingredientFieldCounts: Record<string, number>;
  error?: string;
};

export type RmsAssemblyChartIngredient = {
  productId?: string;
  productName?: string;
  article?: string;
  amount?: number;
  unit?: string;
  rawField: string;
};

export type RmsAssemblyChart = {
  id?: string;
  productId?: string;
  productName?: string;
  name?: string;
  items: RmsAssemblyChartIngredient[];
};

const SESSION_TTL_MS = 115 * 60 * 1000;
const RMS_REVENUE_FIELD = "DishDiscountSumInt";
const RMS_ORDER_COUNT_FIELD = "UniqOrderId";
const RMS_NOMENCLATURE_ENDPOINTS = [
  "/resto/api/v2/entities/products/list",
  "/resto/api/products/list",
  "/resto/api/menu/list",
  "/resto/api/nomenclature/list",
] as const;
const RMS_TOP_LEVEL_COST_FIELD_ALIASES = [
  "purchasePrice",
  "purchase_price",
  "purchasePricePerUnit",
  "purchase_price_per_unit",
  "cost_price_per_unit",
  "costPricePerUnit",
  "cost_per_unit",
  "costPerUnit",
  "cost",
  "costPrice",
  "costPerKg",
  "cost_per_kg",
  "price_per_unit",
  "pricePerKg",
  "price_per_kg",
] as const;
const RMS_NESTED_COST_FIELD_ALIASES = [
  "purchase.pricePerUnit",
  "purchase.price_per_unit",
  "purchase.purchasePricePerUnit",
  "purchase.purchase_price_per_unit",
  "purchase.pricePerKg",
  "purchase.price_per_kg",
  "purchase.price",
  "purchase.value",
  "purchase.amount",
  "purchasePrice.price",
  "purchasePrice.value",
  "purchase_price.price",
  "purchase_price.value",
  "purchaseCost.price",
  "purchaseCost.value",
  "cost.pricePerUnit",
  "cost.price_per_unit",
  "cost.costPricePerUnit",
  "cost.cost_price_per_unit",
  "cost.pricePerKg",
  "cost.price_per_kg",
  "cost.price",
  "cost.value",
  "cost.amount",
  "costPrice.price",
  "costPrice.value",
  "cost_price.price",
  "cost_price.value",
  "primeCost.price",
  "primeCost.value",
  "averageCost.price",
  "averageCost.value",
  "lastPurchasePrice.price",
  "lastPurchasePrice.value",
  "prices.purchasePrice",
  "prices.purchase_price",
  "prices.purchasePricePerUnit",
  "prices.purchase_price_per_unit",
  "prices.costPrice",
  "prices.cost_price",
  "prices.costPerUnit",
  "prices.cost_per_unit",
  "prices.pricePerKg",
  "prices.price_per_kg",
  "priceInfo.purchasePrice",
  "priceInfo.costPrice",
  "costs.purchasePrice",
  "costs.costPrice",
  "purchasePrices.purchasePrice",
  "purchasePrices.costPrice",
] as const;
const RMS_COST_FIELD_ALIASES = [
  ...RMS_TOP_LEVEL_COST_FIELD_ALIASES,
  ...RMS_NESTED_COST_FIELD_ALIASES,
] as const;
const RMS_MENU_PRICE_FIELD_ALIASES = [
  "price",
  "currentPrice",
  "pricePerUnit",
  "sizePrices",
  "prices.price",
  "prices.currentPrice",
] as const;
const RMS_PRICE_FIELD_ALIASES = [
  ...RMS_COST_FIELD_ALIASES,
  ...RMS_MENU_PRICE_FIELD_ALIASES,
  "vat",
  "vatRate",
  "tax",
  "taxRate",
] as const;
const RMS_SHIFT_FIELD_SETS = [
  [
    "Session.Id",
    "SessionOpenDate.Typed",
    "SessionCloseDate.Typed",
    "CashierName",
  ],
  [
    "Session.Id",
    "SessionOpenDate.Typed",
    "SessionCloseDate.Typed",
    "WaiterName",
  ],
  ["Session.Id", "SessionOpenDate.Typed", "SessionCloseDate.Typed"],
  ["CashSessionOpenDate.Typed", "CashSessionCloseDate.Typed", "CashierName"],
  ["SessionDate.Typed", "CashierName"],
  ["OpenDate.Typed"],
] as const;
const RMS_SHIFT_EMPLOYEE_FIELDS = [
  "CashierName",
  "WaiterName",
  "UserName",
  "EmployeeName",
  "User.Name",
  "AuthUserName",
] as const;
const RMS_ASSEMBLY_CHART_ITEM_ARRAY_PATHS = [
  "items",
  "ingredients",
  "components",
  "products",
  "rows",
  "recipeItems",
  "ingredientRows",
  "composition",
  "composition.items",
  "recipe.items",
  "technologicalCardItems",
] as const;
const RMS_ASSEMBLY_CHART_ID_PATHS = [
  "id",
  "assemblyChartId",
  "chartId",
  "_id",
] as const;
const RMS_ASSEMBLY_CHART_PRODUCT_ID_PATHS = [
  "productId",
  "product.id",
  "dishId",
  "dish.id",
  "itemId",
  "nomenclatureId",
  "nomenclature.id",
] as const;
const RMS_ASSEMBLY_CHART_NAME_PATHS = [
  "productName",
  "product.name",
  "dishName",
  "dish.name",
  "name",
  "title",
] as const;
const RMS_ASSEMBLY_INGREDIENT_PRODUCT_ID_PATHS = [
  "productId",
  "product.id",
  "ingredientId",
  "ingredient.id",
  "nomenclatureId",
  "nomenclature.id",
  "skuId",
  "itemId",
  "item.id",
  "goodsId",
  "id",
] as const;
const RMS_ASSEMBLY_INGREDIENT_NAME_PATHS = [
  "productName",
  "product.name",
  "ingredientName",
  "ingredient.name",
  "nomenclatureName",
  "nomenclature.name",
  "itemName",
  "item.name",
  "name",
  "title",
] as const;
const RMS_ASSEMBLY_INGREDIENT_ARTICLE_PATHS = [
  "article",
  "num",
  "code",
  "product.article",
  "product.num",
  "product.code",
  "ingredient.article",
  "ingredient.num",
  "nomenclature.article",
  "nomenclature.num",
  "nomenclatureCode",
  "productCode",
] as const;
const RMS_ASSEMBLY_INGREDIENT_AMOUNT_PATHS = [
  "amount",
  "quantity",
  "qty",
  "netto",
  "nettoQty",
  "weight",
  "value",
  "amountIn",
] as const;
const RMS_ASSEMBLY_INGREDIENT_UNIT_PATHS = [
  "unit",
  "unit.name",
  "measureUnit",
  "measureUnit.name",
  "amountUnit",
  "amountUnit.name",
  "product.unit",
  "product.unit.name",
  "ingredient.unit",
  "nomenclature.unit",
] as const;

function normalizeHost(host: string): string {
  return host
    .trim()
    .replace(/^https?:\/\//i, "")
    .replace(/\/+$/, "");
}

function sha1Hex(value: string): string {
  return createHash("sha1").update(value, "utf8").digest("hex");
}

function readNumber(row: RmsOlapRow, key: string): number {
  return Number(row[key] ?? 0);
}

function readText(row: RmsOlapRow, key: string, fallback = "—"): string {
  const value = row[key];
  if (value === null || value === undefined || value === "") return fallback;
  return String(value);
}

function readFirstText(
  row: RmsOlapRow,
  keys: readonly string[],
  fallback = "—",
): string {
  for (const key of keys) {
    const value = readText(row, key, "");
    if (value) return value;
  }
  return fallback;
}

function toIsoDateTime(value: string, fallbackTime: string): string {
  const text = value.trim();
  if (/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/.test(text)) return text;
  if (/^\d{4}-\d{2}-\d{2}$/.test(text)) return `${text}T${fallbackTime}`;
  return `${text.slice(0, 10)}T${fallbackTime}`;
}

function readOptionalShiftCloseTime(
  row: RmsOlapRow,
  fields: readonly string[],
): string | undefined {
  const shouldReadClose =
    fields.includes("SessionCloseDate.Typed") ||
    fields.includes("CashSessionCloseDate.Typed");
  if (!shouldReadClose) return undefined;

  const closeTime = readFirstText(
    row,
    ["SessionCloseDate.Typed", "CashSessionCloseDate.Typed"],
    "",
  );
  return closeTime ? toIsoDateTime(closeTime, "23:59:59") : undefined;
}

function periodToRange(
  period: Period,
  today: string,
): { from: string; to: string } {
  const dates = resolvePeriodToDates(period, today);
  if (dates.length === 0) return { from: today, to: today };
  return { from: dates[0], to: dates[dates.length - 1] };
}

function addDays(date: string, days: number): string {
  const parsed = new Date(`${date}T00:00:00.000Z`);
  if (Number.isNaN(parsed.getTime())) return date;
  parsed.setUTCDate(parsed.getUTCDate() + days);
  return parsed.toISOString().slice(0, 10);
}

async function readResponseText(res: Response): Promise<string> {
  try {
    return await res.text();
  } catch {
    return "";
  }
}

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

export class RmsIikoClient implements IikoClient {
  private readonly host: string;
  private readonly login: string;
  private readonly password: string;
  private readonly today: string;
  private readonly fetchImpl: typeof fetch;
  private sessionKey: string | null = null;
  private sessionExpiresAt = 0;

  constructor(opts: RmsIikoClientOptions) {
    this.host = normalizeHost(opts.host);
    this.login = opts.login;
    this.password = opts.password;
    this.today = opts.today;
    this.fetchImpl = opts.fetchImpl ?? globalThis.fetch.bind(globalThis);
  }

  async getRevenueSummary(period: Period): Promise<RevenueSummary> {
    const rows = await this.runOlap(period, {
      groupByRowFields: ["OpenDate.Typed"],
      aggregateFields: [
        "DishAmountInt",
        RMS_REVENUE_FIELD,
        RMS_ORDER_COUNT_FIELD,
      ],
    });

    const points = rows.map((row) => ({
      date: readText(row, "OpenDate.Typed", this.today),
      revenue: readNumber(row, RMS_REVENUE_FIELD),
    }));
    points.sort((a, b) => a.date.localeCompare(b.date));

    const revenue = points.reduce((sum, point) => sum + point.revenue, 0);
    const itemsSold = Math.round(
      rows.reduce((sum, row) => sum + readNumber(row, "DishAmountInt"), 0),
    );
    const orderCount = Math.round(
      rows.reduce(
        (sum, row) => sum + readNumber(row, RMS_ORDER_COUNT_FIELD),
        0,
      ),
    );
    const uniqueDishes = await this.getUniqueDishesCount(period);

    return RevenueSummarySchema.parse({
      revenue,
      averageCheck: orderCount > 0 ? Math.round(revenue / orderCount) : 0,
      itemsSold,
      uniqueDishes,
      points,
    });
  }

  async getDishStatistics(period: Period, topN: number): Promise<DishStat[]> {
    const rows = await this.runOlap(period, {
      groupByRowFields: ["DishName", "DishGroup"],
      aggregateFields: ["DishAmountInt", RMS_REVENUE_FIELD],
    });

    const stats = rows.map((row) =>
      DishStatSchema.parse({
        dishName: readText(row, "DishName"),
        dishGroup: readText(row, "DishGroup"),
        dishAmountInt: Math.round(readNumber(row, "DishAmountInt")),
        dishSumInt: readNumber(row, RMS_REVENUE_FIELD),
      }),
    );

    stats.sort((a, b) => b.dishSumInt - a.dishSumInt);
    return stats.slice(0, topN);
  }

  async getCategoryStatistics(period: Period): Promise<CategoryStat[]> {
    const rows = await this.runOlap(period, {
      groupByRowFields: ["DishGroup"],
      aggregateFields: [RMS_REVENUE_FIELD],
    });

    return rows.map((row) =>
      CategoryStatSchema.parse({
        categoryName: readText(row, "DishGroup"),
        dishSumInt: readNumber(row, RMS_REVENUE_FIELD),
      }),
    );
  }

  async getShifts(period: Period): Promise<ShiftStat[]> {
    const { rows, fields } = await this.runShiftOlap(period);

    return rows.map((row, index) => {
      const date = readFirstText(
        row,
        [
          "SessionOpenDate.Typed",
          "CashSessionOpenDate.Typed",
          "SessionDate.Typed",
          "OpenDate.Typed",
        ],
        this.today,
      );
      const sessionId = readFirstText(row, ["Session.Id"], "");
      const employee = readFirstText(row, RMS_SHIFT_EMPLOYEE_FIELDS, "Смена");
      return ShiftStatSchema.parse({
        shiftId: sessionId
          ? `rms-shift-${sessionId}`
          : `rms-shift-${date}-${index}`,
        openTime: toIsoDateTime(date, "00:00:00"),
        closeTime: readOptionalShiftCloseTime(row, fields),
        revenue: readNumber(row, RMS_REVENUE_FIELD),
        items: Math.round(readNumber(row, "DishAmountInt")),
        employee,
      });
    });
  }

  async fetchNomenclature(): Promise<Product[]> {
    const key = await this.getSessionKey();

    const errors: string[] = [];
    for (const endpoint of RMS_NOMENCLATURE_ENDPOINTS) {
      const res = await this.fetchImpl(this.url(endpoint, { key }), {
        method: "GET",
        headers: {
          Accept: "application/json",
          "User-Agent": "Receptor-iiko-RMS-Client/2.0",
        },
      });

      const text = await readResponseText(res);
      if (!res.ok) {
        errors.push(`${endpoint}: HTTP ${res.status}`);
        continue;
      }

      try {
        const payload = JSON.parse(text) as unknown;
        const prices = normalizeRmsPrices(payload);
        const products = mergeProductsWithRmsPrices(
          normalizeIikoProducts(payload),
          prices,
        ).filter((product) => product.active !== false);
        if (products.length > 0) return products;
      } catch {
        errors.push(`${endpoint}: invalid JSON`);
      }
    }

    throw new Error(
      `iiko RMS nomenclature failed: ${errors.join("; ") || "no products returned"}`,
    );
  }

  async fetchPrices(): Promise<RmsPrice[]> {
    const key = await this.getSessionKey();
    const errors: string[] = [];

    for (const endpoint of RMS_NOMENCLATURE_ENDPOINTS) {
      const res = await this.fetchImpl(this.url(endpoint, { key }), {
        method: "GET",
        headers: {
          Accept: "application/json",
          "User-Agent": "Receptor-iiko-RMS-Client/2.0",
        },
      });

      const text = await readResponseText(res);
      if (!res.ok) {
        errors.push(`${endpoint}: HTTP ${res.status}`);
        continue;
      }

      try {
        const prices = normalizeRmsPrices(JSON.parse(text) as unknown);
        if (prices.length > 0) return prices;
        errors.push(`${endpoint}: no cost fields`);
      } catch {
        errors.push(`${endpoint}: invalid JSON`);
      }
    }

    throw new Error(
      `iiko RMS prices failed: ${errors.join("; ") || "no prices returned"}`,
    );
  }

  async probeCostFields(): Promise<RmsCostFieldProbe> {
    const key = await this.getSessionKey();
    const errors: string[] = [];

    for (const endpoint of RMS_NOMENCLATURE_ENDPOINTS) {
      const res = await this.fetchImpl(this.url(endpoint, { key }), {
        method: "GET",
        headers: {
          Accept: "application/json",
          "User-Agent": "Receptor-iiko-RMS-Client/2.0",
        },
      });
      const text = await readResponseText(res);
      if (!res.ok) {
        errors.push(`${endpoint}: HTTP ${res.status}`);
        continue;
      }

      try {
        const payload = JSON.parse(text) as unknown;
        const rows = extractRmsRows(payload);
        if (rows.length === 0) {
          errors.push(`${endpoint}: no product rows`);
          continue;
        }

        const prices = normalizeRmsPrices(payload);
        const costFieldCounts = countFields(rows, RMS_COST_FIELD_ALIASES);
        const menuPriceFieldCounts = countFields(
          rows,
          RMS_MENU_PRICE_FIELD_ALIASES,
        );
        const costStatus =
          prices.length > 0
            ? ("ready" as const)
            : Object.keys(menuPriceFieldCounts).length > 0
              ? ("menu-prices-only" as const)
              : ("missing-cost-fields" as const);
        const products = mergeProductsWithRmsPrices(
          normalizeIikoProducts(payload),
          prices,
        );
        return {
          endpoint,
          costStatus,
          rawRows: rows.length,
          normalizedProducts: products.length,
          activeProducts: products.filter((product) => product.active !== false)
            .length,
          normalizedPriceRows: prices.length,
          productsWithCachedCost: products.filter((product) =>
            Boolean(product.pricePerKg || product.purchasePricePerUnit),
          ).length,
          productsWithPurchasePrice: products.filter((product) =>
            Boolean(product.purchasePrice || product.purchasePricePerUnit),
          ).length,
          productsWithMenuPrice: products.filter((product) =>
            Boolean(product.price || product.pricePerUnit),
          ).length,
          productsWithTechCardPrice: prices.length,
          costFieldCounts,
          menuPriceFieldCounts,
          priceFieldCounts: countFields(rows, RMS_PRICE_FIELD_ALIASES),
          rawFieldCounts: topFieldCounts(rows, 30),
        };
      } catch {
        errors.push(`${endpoint}: invalid JSON`);
      }
    }

    return {
      endpoint: null,
      costStatus: "unreadable",
      rawRows: 0,
      normalizedProducts: 0,
      activeProducts: 0,
      normalizedPriceRows: 0,
      productsWithCachedCost: 0,
      productsWithPurchasePrice: 0,
      productsWithMenuPrice: 0,
      productsWithTechCardPrice: 0,
      costFieldCounts: {},
      menuPriceFieldCounts: {},
      priceFieldCounts: {},
      rawFieldCounts: {},
      error: errors.join("; ") || "no RMS nomenclature response",
    };
  }

  async probeAssemblyCharts(): Promise<RmsAssemblyChartsProbe> {
    const endpoint = "/resto/api/v2/assemblyCharts/getAll";
    const key = await this.getSessionKey();
    const dateFrom = addDays(this.today, -365);
    const dateTo = addDays(this.today, 365);

    const res = await this.fetchImpl(
      this.url(endpoint, {
        key,
        dateFrom,
        dateTo,
        includeDeletedProducts: "true",
        includePreparedCharts: "false",
      }),
      {
        method: "GET",
        headers: {
          Accept: "application/json",
          "User-Agent": "Receptor-iiko-RMS-Client/2.0",
        },
      },
    );

    const text = await readResponseText(res);
    if (!res.ok) {
      return {
        endpoint,
        status: res.status === 403 ? "forbidden" : "unreadable",
        dateFrom,
        dateTo,
        assemblyCharts: 0,
        preparedCharts: 0,
        normalizedCharts: 0,
        chartsWithDishLink: 0,
        chartsWithItems: 0,
        totalItems: 0,
        ingredientRows: 0,
        ingredientRowsWithProductLink: 0,
        ingredientRowsWithAmount: 0,
        ingredientRowsWithUnit: 0,
        rawFieldCounts: {},
        ingredientFieldCounts: {},
        error: `HTTP ${res.status}: ${text.slice(0, 300)}`,
      };
    }

    try {
      const payload = JSON.parse(text) as unknown;
      const assemblyCharts = extractAssemblyCharts(payload);
      const preparedCharts = extractPreparedCharts(payload);
      const normalizedCharts = assemblyCharts.map(normalizeAssemblyChart);
      const ingredientRows = normalizedCharts.flatMap((chart) => chart.items);
      const rawIngredientRows = assemblyCharts.flatMap((chart) =>
        extractAssemblyChartItemRows(chart).map(({ row }) => row),
      );

      return {
        endpoint,
        status: assemblyCharts.length > 0 ? "ready" : "empty",
        dateFrom,
        dateTo,
        assemblyCharts: assemblyCharts.length,
        preparedCharts: preparedCharts.length,
        normalizedCharts: normalizedCharts.length,
        chartsWithDishLink: normalizedCharts.filter((chart) =>
          Boolean(chart.productId),
        ).length,
        chartsWithItems: normalizedCharts.filter(
          (chart) => chart.items.length > 0,
        ).length,
        totalItems: ingredientRows.length,
        ingredientRows: ingredientRows.length,
        ingredientRowsWithProductLink: ingredientRows.filter((item) =>
          Boolean(item.productId),
        ).length,
        ingredientRowsWithAmount: ingredientRows.filter(
          (item) => item.amount !== undefined,
        ).length,
        ingredientRowsWithUnit: ingredientRows.filter((item) =>
          Boolean(item.unit),
        ).length,
        rawFieldCounts: topFieldCounts(assemblyCharts, 30),
        ingredientFieldCounts: topFieldCounts(rawIngredientRows, 30),
      };
    } catch {
      return {
        endpoint,
        status: "unreadable",
        dateFrom,
        dateTo,
        assemblyCharts: 0,
        preparedCharts: 0,
        normalizedCharts: 0,
        chartsWithDishLink: 0,
        chartsWithItems: 0,
        totalItems: 0,
        ingredientRows: 0,
        ingredientRowsWithProductLink: 0,
        ingredientRowsWithAmount: 0,
        ingredientRowsWithUnit: 0,
        rawFieldCounts: {},
        ingredientFieldCounts: {},
        error: "invalid JSON",
      };
    }
  }

  async fetchAssemblyCharts(): Promise<RmsAssemblyChart[]> {
    const endpoint = "/resto/api/v2/assemblyCharts/getAll";
    const key = await this.getSessionKey();
    const dateFrom = addDays(this.today, -365);
    const dateTo = addDays(this.today, 365);

    const res = await this.fetchImpl(
      this.url(endpoint, {
        key,
        dateFrom,
        dateTo,
        includeDeletedProducts: "true",
        includePreparedCharts: "false",
      }),
      {
        method: "GET",
        headers: {
          Accept: "application/json",
          "User-Agent": "Receptor-iiko-RMS-Client/2.0",
        },
      },
    );

    const text = await readResponseText(res);
    if (!res.ok) {
      throw new Error(
        `iiko RMS assembly charts failed: HTTP ${res.status}: ${text.slice(0, 500)}`,
      );
    }

    try {
      const payload = JSON.parse(text) as unknown;
      return extractAssemblyCharts(payload).map(normalizeAssemblyChart);
    } catch {
      throw new Error("iiko RMS assembly charts failed: invalid JSON");
    }
  }

  async searchNomenclature(query: string): Promise<Product[]> {
    try {
      return searchIikoProducts(await this.fetchNomenclature(), query);
    } catch {
      return [];
    }
  }

  async listOrganizations(): Promise<RmsOrganization[]> {
    const key = await this.getSessionKey();
    const endpoints = [
      "/resto/api/v2/entities/organizations/list",
      "/resto/api/corporation/organizations",
      "/resto/api/organizations",
      "/resto/api/v2/corporation",
    ];

    for (const endpoint of endpoints) {
      const url = this.url(endpoint, { key });
      const res = await this.fetchImpl(url, {
        method: "GET",
        headers: { "User-Agent": "Receptor-iiko-RMS-Client/2.0" },
      });
      if (!res.ok) continue;
      const text = await readResponseText(res);
      try {
        const payload = JSON.parse(text) as
          | Array<Record<string, unknown>>
          | {
              organizations?: Array<Record<string, unknown>>;
              data?: Array<Record<string, unknown>>;
              items?: Array<Record<string, unknown>>;
            };
        const rows = Array.isArray(payload)
          ? payload
          : (payload.organizations ?? payload.data ?? payload.items ?? []);
        const organizations = rows
          .map((row) => ({
            id: String(row.id ?? ""),
            name: String(row.name ?? row.title ?? ""),
          }))
          .filter((org) => org.id && org.name);
        if (organizations.length > 0) return organizations;
      } catch {
        // Some RMS endpoints return XML/HTML depending on server version.
      }
    }

    return [{ id: "default", name: this.host }];
  }

  async probe(): Promise<void> {
    await this.getSessionKey(true);
  }

  private async getUniqueDishesCount(period: Period): Promise<number> {
    const rows = await this.runOlap(period, {
      groupByRowFields: ["DishName"],
      aggregateFields: [RMS_REVENUE_FIELD],
    });

    return rows.filter(
      (row) =>
        readText(row, "DishName", "").trim().length > 0 &&
        readNumber(row, RMS_REVENUE_FIELD) > 0,
    ).length;
  }

  private async runShiftOlap(
    period: Period,
  ): Promise<{ rows: RmsOlapRow[]; fields: readonly string[] }> {
    const errors: string[] = [];

    for (const fields of RMS_SHIFT_FIELD_SETS) {
      const groupByRowFields: readonly string[] = fields;
      try {
        const rows = await this.runOlap(period, {
          groupByRowFields: [...groupByRowFields],
          aggregateFields: ["DishAmountInt", RMS_REVENUE_FIELD],
        });
        if (rows.length > 0 || groupByRowFields.includes("OpenDate.Typed")) {
          return { rows, fields: groupByRowFields };
        }
      } catch (error) {
        errors.push(`${groupByRowFields.join("+")}: ${errorMessage(error)}`);
      }
    }

    throw new Error(
      `iiko RMS shifts failed: ${errors.join("; ") || "no shift rows returned"}`,
    );
  }

  private async runOlap(
    period: Period,
    params: { groupByRowFields: string[]; aggregateFields: string[] },
  ): Promise<RmsOlapRow[]> {
    const key = await this.getSessionKey();
    const { from, to } = periodToRange(period, this.today);
    const res = await this.fetchImpl(
      this.url("/resto/api/v2/reports/olap", { key }),
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json; charset=utf-8",
          Accept: "application/json",
          "User-Agent": "Receptor-iiko-RMS-Client/2.0",
        },
        body: JSON.stringify({
          reportType: "SALES",
          buildSummary: true,
          groupByRowFields: params.groupByRowFields,
          groupByColFields: [],
          aggregateFields: params.aggregateFields,
          filters: {
            "OpenDate.Typed": {
              filterType: "DateRange",
              periodType: "CUSTOM",
              from,
              to,
              includeLow: true,
              includeHigh: true,
            },
          },
        }),
      },
    );

    if (!res.ok) {
      throw new Error(
        `iiko RMS OLAP failed: HTTP ${res.status}: ${(await readResponseText(res)).slice(0, 500)}`,
      );
    }

    const payload = (await res.json()) as { data?: RmsOlapRow[] };
    return payload.data ?? [];
  }

  private async getSessionKey(forceRefresh = false): Promise<string> {
    if (
      !forceRefresh &&
      this.sessionKey &&
      Date.now() < this.sessionExpiresAt
    ) {
      return this.sessionKey;
    }

    const res = await this.fetchImpl(
      this.url("/resto/api/auth", {
        login: this.login,
        pass: sha1Hex(this.password),
      }),
      {
        method: "GET",
        headers: { "User-Agent": "Receptor-iiko-RMS-Client/2.0" },
      },
    );

    const text = (await readResponseText(res)).trim();
    if (!res.ok) {
      throw new Error(
        `iiko RMS auth failed: HTTP ${res.status}: ${text.slice(0, 300)}`,
      );
    }
    if (!text || text.length < 10) {
      throw new Error("iiko RMS auth: invalid session key response");
    }

    this.sessionKey = text;
    this.sessionExpiresAt = Date.now() + SESSION_TTL_MS;
    return text;
  }

  private url(path: string, query: Record<string, string>): string {
    const search = new URLSearchParams(query);
    return `https://${this.host}${path}?${search.toString()}`;
  }
}

function extractRmsRows(payload: unknown): RmsRawRow[] {
  if (Array.isArray(payload)) return payload.filter(isRecord);
  if (!isRecord(payload)) return [];

  for (const key of ["items", "products", "nomenclature", "data"]) {
    const value = payload[key];
    if (Array.isArray(value)) return value.filter(isRecord);
  }

  return [];
}

function extractAssemblyCharts(payload: unknown): RmsRawRow[] {
  if (Array.isArray(payload)) return payload.filter(isRecord);
  if (!isRecord(payload)) return [];

  for (const key of ["assemblyCharts", "charts", "items", "data"]) {
    const value = payload[key];
    if (Array.isArray(value)) return value.filter(isRecord);
  }

  return [];
}

function extractPreparedCharts(payload: unknown): RmsRawRow[] {
  if (!isRecord(payload)) return [];
  const value = payload.preparedCharts;
  return Array.isArray(value) ? value.filter(isRecord) : [];
}

function normalizeAssemblyChart(chart: RmsRawRow): RmsAssemblyChart {
  const productId = readFirstStringPath(
    chart,
    RMS_ASSEMBLY_CHART_PRODUCT_ID_PATHS,
  );
  const productName = readFirstStringPath(chart, RMS_ASSEMBLY_CHART_NAME_PATHS);

  return {
    id: readFirstStringPath(chart, RMS_ASSEMBLY_CHART_ID_PATHS),
    productId,
    productName,
    name: productName,
    items: extractAssemblyChartItemRows(chart)
      .map(({ row, field }) => normalizeAssemblyChartIngredient(row, field))
      .filter((item): item is RmsAssemblyChartIngredient => item !== null),
  };
}

function extractAssemblyChartItemRows(
  chart: RmsRawRow,
): Array<{ row: RmsRawRow; field: string }> {
  for (const path of RMS_ASSEMBLY_CHART_ITEM_ARRAY_PATHS) {
    const value = readPath(chart, path);
    if (!Array.isArray(value)) continue;

    const rows = value.filter(isRecord);
    if (rows.length === 0) continue;
    return rows.map((row) => ({ row, field: path }));
  }

  return [];
}

function normalizeAssemblyChartIngredient(
  row: RmsRawRow,
  rawField: string,
): RmsAssemblyChartIngredient | null {
  const productId = readFirstStringPath(
    row,
    RMS_ASSEMBLY_INGREDIENT_PRODUCT_ID_PATHS,
  );
  const productName = readFirstStringPath(
    row,
    RMS_ASSEMBLY_INGREDIENT_NAME_PATHS,
  );
  const article = readFirstStringPath(
    row,
    RMS_ASSEMBLY_INGREDIENT_ARTICLE_PATHS,
  );
  const amount = readFirstPositiveNumberPath(
    row,
    RMS_ASSEMBLY_INGREDIENT_AMOUNT_PATHS,
  );
  const unit = readFirstStringPath(row, RMS_ASSEMBLY_INGREDIENT_UNIT_PATHS);

  if (!productId && !productName && !article && amount === undefined && !unit) {
    return null;
  }

  return {
    productId,
    productName,
    article,
    amount,
    unit,
    rawField,
  };
}

function readFirstStringPath(
  row: RmsRawRow,
  paths: readonly string[],
): string | undefined {
  for (const path of paths) {
    const value = readPath(row, path);
    if (!hasMeaningfulValue(value)) continue;
    if (typeof value === "object") continue;

    const text = String(value).trim();
    if (text) return text;
  }

  return undefined;
}

function readFirstPositiveNumberPath(
  row: RmsRawRow,
  paths: readonly string[],
): number | undefined {
  for (const path of paths) {
    const value = readPath(row, path);
    if (!hasMeaningfulValue(value)) continue;

    const parsed =
      typeof value === "number"
        ? value
        : Number(String(value).replace(",", "."));
    if (Number.isFinite(parsed) && parsed > 0) return parsed;
  }

  return undefined;
}

function countFields(
  rows: RmsRawRow[],
  fields: readonly string[],
): Record<string, number> {
  const counts: Record<string, number> = {};
  for (const field of fields) {
    const count = rows.filter((row) =>
      hasMeaningfulValue(readPath(row, field)),
    ).length;
    if (count > 0) counts[field] = count;
  }
  return counts;
}

function readPath(row: RmsRawRow, path: string): unknown {
  if (Object.prototype.hasOwnProperty.call(row, path)) return row[path];
  if (!path.includes(".")) return row[path];

  let current: unknown = row;
  for (const part of path.split(".")) {
    if (!isRecord(current)) return undefined;
    current = current[part];
  }
  return current;
}

function topFieldCounts(
  rows: RmsRawRow[],
  limit: number,
): Record<string, number> {
  const counts = new Map<string, number>();
  rows.forEach((row) => {
    Object.keys(row).forEach((field) => {
      if (!hasMeaningfulValue(row[field])) return;
      counts.set(field, (counts.get(field) ?? 0) + 1);
    });
  });

  return Object.fromEntries(
    [...counts.entries()]
      .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
      .slice(0, limit),
  );
}

function hasMeaningfulValue(value: unknown): boolean {
  if (value === null || value === undefined) return false;
  if (typeof value === "string") return value.trim().length > 0;
  if (Array.isArray(value)) return value.length > 0;
  return true;
}

function isRecord(value: unknown): value is RmsRawRow {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
