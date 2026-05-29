/**
 * AI tools — Claude tool-calling surface for the Receptor chat.
 *
 * Each tool ships in two parts:
 *   - `name + description + input_schema` — exactly the shape Anthropic's
 *     `tools` parameter expects (JSON Schema).
 *   - `handler(input, client)` — server-side dispatch that calls
 *     `MockIikoClient` (Phase 4) or a real iiko client (Phase 5).
 *
 * Tools are pure functions of `(input, client)`. They never touch
 * `process.env`, never call `Date.now()`, never randomise. Determinism is
 * what lets the Михно demo screenshot reliably.
 */

import { z } from "zod";
import {
  PeriodTypeSchema,
  type PeriodType,
  type Period,
  type IikoClientWithTools,
} from "./types";
import { formatRubles, formatInteger } from "@/lib/format";
import type { IikoClient } from "@/lib/iiko/types";

// ---------------------------------------------------------------------------
// Shared shapes
// ---------------------------------------------------------------------------

const PERIOD_PROP_SCHEMA = {
  type: "string" as const,
  enum: [
    "TODAY",
    "YESTERDAY",
    "CURRENT_WEEK",
    "LAST_WEEK",
    "CURRENT_MONTH",
    "LAST_MONTH",
  ],
  description:
    "Период анализа. Используй пресеты, а не произвольные даты.",
};

function asPeriod(type: PeriodType): Period {
  // CUSTOM is intentionally not exposed to AI tools in Phase 4 to keep
  // demo deterministic; AI can only ask for presets.
  return { type: type as Exclude<PeriodType, "CUSTOM"> };
}

/** Anthropic-shaped tool descriptor. */
export type AnthropicTool = {
  name: string;
  description: string;
  input_schema: {
    type: "object";
    properties: Record<string, unknown>;
    required?: string[];
  };
};

export type ToolDefinition<TInput, TOutput> = AnthropicTool & {
  handler: (input: TInput, client: IikoClient) => Promise<TOutput>;
};

// ---------------------------------------------------------------------------
// Tools
// ---------------------------------------------------------------------------

const GetRevenueInput = z.object({
  period: PeriodTypeSchema.exclude(["CUSTOM"]),
});

export const getRevenueTool: ToolDefinition<
  { period: PeriodType },
  {
    revenue: number;
    averageCheck: number;
    itemsSold: number;
    uniqueDishes: number;
    points: { date: string; revenue: number }[];
    summary: string;
  }
> = {
  name: "get_revenue",
  description:
    "Выручка заведения за период. Возвращает итог по периоду, средний чек, " +
    "продано позиций, уникальных блюд и распределение по дням.",
  input_schema: {
    type: "object",
    properties: { period: PERIOD_PROP_SCHEMA },
    required: ["period"],
  },
  handler: async (raw, client) => {
    const { period } = GetRevenueInput.parse(raw);
    const s = await client.getRevenueSummary(asPeriod(period));
    const days = s.points.length;
    return {
      revenue: s.revenue,
      averageCheck: s.averageCheck,
      itemsSold: s.itemsSold,
      uniqueDishes: s.uniqueDishes,
      points: s.points,
      summary:
        `За ${days} дней выручка ${formatRubles(s.revenue)}, ` +
        `средний чек ${formatRubles(s.averageCheck)}, ` +
        `продано ${formatInteger(s.itemsSold)} позиций.`,
    };
  },
};

const GetDishStatisticsInput = z.object({
  period: PeriodTypeSchema.exclude(["CUSTOM"]),
  top_n: z.number().int().positive().max(50).optional(),
});

export const getDishStatisticsTool: ToolDefinition<
  { period: PeriodType; top_n?: number },
  {
    dishes: {
      dishName: string;
      dishGroup: string;
      dishAmountInt: number;
      dishSumInt: number;
    }[];
    summary: string;
  }
> = {
  name: "get_dish_statistics",
  description:
    "Топ-N блюд по выручке за период. Используй когда спрашивают про " +
    "«какие блюда продаются», «топ позиций», «что тянет вниз».",
  input_schema: {
    type: "object",
    properties: {
      period: PERIOD_PROP_SCHEMA,
      top_n: {
        type: "integer",
        minimum: 1,
        maximum: 50,
        default: 10,
        description: "Сколько позиций вернуть (1–50, по умолчанию 10).",
      },
    },
    required: ["period"],
  },
  handler: async (raw, client) => {
    const { period, top_n } = GetDishStatisticsInput.parse(raw);
    const topN = top_n ?? 10;
    const dishes = await client.getDishStatistics(asPeriod(period), topN);
    const top = dishes[0];
    return {
      dishes,
      summary: top
        ? `Топ-${dishes.length}: лидер — «${top.dishName}» ` +
          `(${formatRubles(top.dishSumInt)}).`
        : "Нет данных.",
    };
  },
};

const GetShiftsInput = z.object({
  period: PeriodTypeSchema.exclude(["CUSTOM"]),
});

export const getShiftsTool: ToolDefinition<
  { period: PeriodType },
  {
    shifts: {
      shiftId: string;
      openTime: string;
      closeTime?: string;
      revenue: number;
      items: number;
      employee: string;
    }[];
    totalRevenue: number;
    totalItems: number;
    summary: string;
  }
> = {
  name: "get_shifts",
  description:
    "Кассовые смены за период. Возвращает каждую смену с временем " +
    "открытия/закрытия, выручкой, числом позиций и сотрудником.",
  input_schema: {
    type: "object",
    properties: { period: PERIOD_PROP_SCHEMA },
    required: ["period"],
  },
  handler: async (raw, client) => {
    const { period } = GetShiftsInput.parse(raw);
    const shifts = await client.getShifts(asPeriod(period));
    const totalRevenue = shifts.reduce((s, x) => s + x.revenue, 0);
    const totalItems = shifts.reduce((s, x) => s + x.items, 0);
    return {
      shifts,
      totalRevenue,
      totalItems,
      summary:
        `${shifts.length} смен, выручка ${formatRubles(totalRevenue)}, ` +
        `${formatInteger(totalItems)} позиций.`,
    };
  },
};

const ComparePeriodsInput = z.object({
  period_a: PeriodTypeSchema.exclude(["CUSTOM"]),
  period_b: PeriodTypeSchema.exclude(["CUSTOM"]),
});

export const comparePeriodsTool: ToolDefinition<
  { period_a: PeriodType; period_b: PeriodType },
  {
    period_a: PeriodType;
    period_b: PeriodType;
    revenue_a: number;
    revenue_b: number;
    delta_pct: number;
    summary: string;
  }
> = {
  name: "compare_periods",
  description:
    "Сравнивает выручку двух периодов. Используй для «сравни прошлую и " +
    "текущую неделю», «насколько хуже вчера, чем позавчера».",
  input_schema: {
    type: "object",
    properties: {
      period_a: PERIOD_PROP_SCHEMA,
      period_b: PERIOD_PROP_SCHEMA,
    },
    required: ["period_a", "period_b"],
  },
  handler: async (raw, client) => {
    const { period_a, period_b } = ComparePeriodsInput.parse(raw);
    const [a, b] = await Promise.all([
      client.getRevenueSummary(asPeriod(period_a)),
      client.getRevenueSummary(asPeriod(period_b)),
    ]);
    const deltaPct =
      a.revenue > 0 ? ((b.revenue - a.revenue) / a.revenue) * 100 : 0;
    const sign = deltaPct >= 0 ? "+" : "";
    return {
      period_a,
      period_b,
      revenue_a: a.revenue,
      revenue_b: b.revenue,
      delta_pct: Number(deltaPct.toFixed(1)),
      summary:
        `Период ${period_a}: ${formatRubles(a.revenue)}. ` +
        `Период ${period_b}: ${formatRubles(b.revenue)}. ` +
        `Дельта: ${sign}${deltaPct.toFixed(1)}%.`,
    };
  },
};

const SearchNomenclatureInput = z.object({
  query: z.string().min(1),
});

export const searchNomenclatureTool: ToolDefinition<
  { query: string },
  {
    products: { id: string; name: string; price: number }[];
    summary: string;
  }
> = {
  name: "get_nomenclature_search",
  description:
    "Поиск блюда в меню по частичному совпадению названия (case-insensitive). " +
    "Возвращает id, название и текущую цену.",
  input_schema: {
    type: "object",
    properties: {
      query: {
        type: "string",
        minLength: 1,
        description: "Часть названия блюда: «бургер», «крафт ipa», «нечто».",
      },
    },
    required: ["query"],
  },
  handler: async (raw, client) => {
    const { query } = SearchNomenclatureInput.parse(raw);
    const products = await client.searchNomenclature(query);
    return {
      products: products.map((p) => ({
        id: p.id,
        name: p.name,
        price: p.sizePrices[0]?.price.currentPrice ?? 0,
      })),
      summary:
        products.length > 0
          ? `Найдено ${products.length} позиций по запросу «${query}».`
          : `По запросу «${query}» ничего не нашлось.`,
    };
  },
};

export const AI_TOOLS = [
  getRevenueTool,
  getDishStatisticsTool,
  getShiftsTool,
  comparePeriodsTool,
  searchNomenclatureTool,
] as const;
