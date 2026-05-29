/**
 * Mock chat engine — Phase 4 stand-in for Anthropic streaming + tool-calls.
 *
 * Behaviour mirrors what the real Claude loop will do once
 * ANTHROPIC_API_KEY arrives:
 *   1. Inspect user message.
 *   2. Decide which tool to invoke (or none).
 *   3. Run the tool against the iiko client.
 *   4. Stream back a short Russian answer that cites the data.
 *
 * Routing here is keyword-based — naive, but deterministic and demo-safe.
 * The chat UI sees the same NDJSON event stream as it will see from the
 * real Anthropic SSE bridge, so swap-out is local to this file.
 */

import {
  AI_TOOLS,
  getRevenueTool,
  getDishStatisticsTool,
  getShiftsTool,
  comparePeriodsTool,
  searchNomenclatureTool,
} from "./tools";
import { formatRubles, formatInteger } from "@/lib/format";
import type { IikoClient } from "@/lib/iiko/types";
import type { PeriodType } from "@/lib/iiko/models";

// ---------------------------------------------------------------------------
// Stream event shapes (also used by the API route + UI)
// ---------------------------------------------------------------------------

export type ChatEvent =
  | { type: "thinking"; label: string }
  | {
      type: "tool";
      tool: (typeof AI_TOOLS)[number]["name"];
      input: Record<string, unknown>;
      output: unknown;
    }
  | { type: "text"; text: string }
  | { type: "done" };

export type ChatTurnInput = {
  message: string;
  venueName: string;
  venueType: string;
  venueCity: string;
  iikoClient: IikoClient;
};

// ---------------------------------------------------------------------------
// Routing — keyword priority (first match wins)
// ---------------------------------------------------------------------------

type Route =
  | { kind: "compare"; periodA: PeriodType; periodB: PeriodType }
  | { kind: "shifts"; period: PeriodType }
  | { kind: "dishes"; period: PeriodType; topN: number }
  | { kind: "search"; query: string }
  | { kind: "revenue"; period: PeriodType }
  | { kind: "suggest" };

const PERIOD_KEYWORDS: Array<{ rx: RegExp; period: PeriodType }> = [
  { rx: /сегодн/i, period: "TODAY" },
  { rx: /вчера/i, period: "YESTERDAY" },
  { rx: /текущ\w*\s*недел/i, period: "CURRENT_WEEK" },
  { rx: /прошл\w*\s*недел|за\s*недел/i, period: "LAST_WEEK" },
  { rx: /текущ\w*\s*месяц/i, period: "CURRENT_MONTH" },
  { rx: /прошл\w*\s*месяц|за\s*месяц/i, period: "LAST_MONTH" },
];

function pickPeriod(text: string, fallback: PeriodType = "LAST_WEEK"): PeriodType {
  for (const k of PERIOD_KEYWORDS) {
    if (k.rx.test(text)) return k.period;
  }
  return fallback;
}

function pickTopN(text: string, fallback = 5): number {
  const m = text.match(/топ[-\s]*(\d{1,2})/i);
  if (m) {
    const n = parseInt(m[1], 10);
    if (n > 0 && n <= 50) return n;
  }
  return fallback;
}

function routeMessage(message: string): Route {
  const t = message.toLowerCase();

  if (/сравн/i.test(t)) {
    const a: PeriodType = /прошл\w*\s*недел/i.test(t) ? "LAST_WEEK" : "LAST_MONTH";
    const b: PeriodType = /текущ\w*\s*недел/i.test(t)
      ? "CURRENT_WEEK"
      : "CURRENT_MONTH";
    return { kind: "compare", periodA: a, periodB: b };
  }

  if (/смен/i.test(t)) {
    return { kind: "shifts", period: pickPeriod(t, "LAST_WEEK") };
  }

  if (/(топ|лучш\w+|ранкинг)/i.test(t) && /(блюд|позиц|пиво|коктейл|сорт)/i.test(t)) {
    return {
      kind: "dishes",
      period: pickPeriod(t, "LAST_WEEK"),
      topN: pickTopN(t, 5),
    };
  }

  if (/(найди|поищ|есть\s+ли|покажи\s+в\s+меню)/i.test(t)) {
    const stripped = message
      .replace(
        /(в\s+меню|найди|поищи|есть\s+ли|покажи|пожалуйста|пж)/gi,
        "",
      )
      .replace(/[?.!]+$/, "")
      .trim();
    if (stripped.length > 0) return { kind: "search", query: stripped };
  }

  if (/(выручк|оборот|сколько\s+денег|сколько\s+сделал)/i.test(t)) {
    return { kind: "revenue", period: pickPeriod(t, "LAST_WEEK") };
  }

  return { kind: "suggest" };
}

// ---------------------------------------------------------------------------
// Per-route formatters — Russian, no emoji, action-oriented.
// ---------------------------------------------------------------------------

const PERIOD_PHRASE: Record<PeriodType, string> = {
  TODAY: "сегодня",
  YESTERDAY: "вчера",
  CURRENT_WEEK: "за эту неделю",
  LAST_WEEK: "за прошлую неделю",
  CURRENT_MONTH: "за этот месяц",
  LAST_MONTH: "за прошлый месяц",
  CUSTOM: "за выбранный период",
};

function formatRevenueAnswer(
  venueName: string,
  out: Awaited<ReturnType<typeof getRevenueTool.handler>>,
  period: PeriodType,
): string {
  const lines = [
    `${venueName} — ${PERIOD_PHRASE[period]}:`,
    "",
    `Выручка: ${formatRubles(out.revenue)}`,
    `Средний чек: ${formatRubles(out.averageCheck)}`,
    `Позиций продано: ${formatInteger(out.itemsSold)}`,
    `Уникальных блюд: ${formatInteger(out.uniqueDishes)}`,
  ];
  if (out.points.length > 1) {
    const last = out.points[out.points.length - 1];
    lines.push(
      "",
      `Последний день в периоде — ${last.date}: ${formatRubles(last.revenue)}.`,
    );
  }
  return lines.join("\n");
}

function formatDishesAnswer(
  out: Awaited<ReturnType<typeof getDishStatisticsTool.handler>>,
  period: PeriodType,
): string {
  const head = `Топ-${out.dishes.length} ${PERIOD_PHRASE[period]}:`;
  const rows = out.dishes
    .map(
      (d, i) =>
        `${i + 1}. ${d.dishName} — ${formatRubles(d.dishSumInt)} ` +
        `(${formatInteger(d.dishAmountInt)} порций)`,
    )
    .join("\n");
  return `${head}\n${rows}`;
}

function formatShiftsAnswer(
  out: Awaited<ReturnType<typeof getShiftsTool.handler>>,
  period: PeriodType,
): string {
  const head = `Смены ${PERIOD_PHRASE[period]}:`;
  const rows = out.shifts
    .map((s) => {
      const date = s.openTime.slice(0, 10);
      return `${date} · ${s.employee} — ${formatRubles(s.revenue)} ` +
        `(${formatInteger(s.items)} поз.)`;
    })
    .join("\n");
  const tail =
    `\nВсего за период: ${formatRubles(out.totalRevenue)} ` +
    `(${formatInteger(out.totalItems)} позиций).`;
  return `${head}\n${rows}${tail}`;
}

function formatCompareAnswer(
  out: Awaited<ReturnType<typeof comparePeriodsTool.handler>>,
): string {
  const sign = out.delta_pct >= 0 ? "+" : "";
  const verdict =
    out.delta_pct >= 0
      ? "В плюс. Если так пойдёт — будет хороший месяц."
      : "В минус. Стоит посмотреть смены и категории-аутсайдеры.";
  return [
    `Сравнение:`,
    "",
    `${PERIOD_PHRASE[out.period_a]}: ${formatRubles(out.revenue_a)}`,
    `${PERIOD_PHRASE[out.period_b]}: ${formatRubles(out.revenue_b)}`,
    `Дельта: ${sign}${out.delta_pct}%`,
    "",
    verdict,
  ].join("\n");
}

function formatSearchAnswer(
  out: Awaited<ReturnType<typeof searchNomenclatureTool.handler>>,
  query: string,
): string {
  if (out.products.length === 0) {
    return `По запросу «${query}» ничего в меню не нашлось.`;
  }
  const rows = out.products
    .slice(0, 10)
    .map((p) => `• ${p.name} — ${formatRubles(p.price)}`)
    .join("\n");
  return `Нашёл ${out.products.length} позиций по «${query}»:\n${rows}`;
}

function formatSuggestAnswer(venueName: string): string {
  return [
    `Я Receptor — кулинарный копайлот ${venueName}. Спроси меня:`,
    "",
    "• какая выручка за прошлую неделю?",
    "• покажи топ-5 блюд за месяц",
    "• сравни прошлую и текущую неделю",
    "• сколько сделали смены вчера?",
    "• найди в меню бургер нечто",
  ].join("\n");
}

// ---------------------------------------------------------------------------
// The stream
// ---------------------------------------------------------------------------

export async function* runMockChatTurn(
  input: ChatTurnInput,
): AsyncGenerator<ChatEvent> {
  const route = routeMessage(input.message);

  // 1. Thinking event — UI shows a status pill while we hit iiko.
  yield {
    type: "thinking",
    label:
      route.kind === "suggest"
        ? "Подбираю ответ"
        : `Запрашиваю iiko · ${routeLabel(route)}`,
  };

  switch (route.kind) {
    case "revenue": {
      const output = await getRevenueTool.handler(
        { period: route.period },
        input.iikoClient,
      );
      yield {
        type: "tool",
        tool: "get_revenue",
        input: { period: route.period },
        output,
      };
      yield {
        type: "text",
        text: formatRevenueAnswer(input.venueName, output, route.period),
      };
      break;
    }

    case "dishes": {
      const output = await getDishStatisticsTool.handler(
        { period: route.period, top_n: route.topN },
        input.iikoClient,
      );
      yield {
        type: "tool",
        tool: "get_dish_statistics",
        input: { period: route.period, top_n: route.topN },
        output,
      };
      yield { type: "text", text: formatDishesAnswer(output, route.period) };
      break;
    }

    case "shifts": {
      const output = await getShiftsTool.handler(
        { period: route.period },
        input.iikoClient,
      );
      yield {
        type: "tool",
        tool: "get_shifts",
        input: { period: route.period },
        output,
      };
      yield { type: "text", text: formatShiftsAnswer(output, route.period) };
      break;
    }

    case "compare": {
      const output = await comparePeriodsTool.handler(
        { period_a: route.periodA, period_b: route.periodB },
        input.iikoClient,
      );
      yield {
        type: "tool",
        tool: "compare_periods",
        input: { period_a: route.periodA, period_b: route.periodB },
        output,
      };
      yield { type: "text", text: formatCompareAnswer(output) };
      break;
    }

    case "search": {
      const output = await searchNomenclatureTool.handler(
        { query: route.query },
        input.iikoClient,
      );
      yield {
        type: "tool",
        tool: "get_nomenclature_search",
        input: { query: route.query },
        output,
      };
      yield { type: "text", text: formatSearchAnswer(output, route.query) };
      break;
    }

    case "suggest": {
      yield { type: "text", text: formatSuggestAnswer(input.venueName) };
      break;
    }
  }

  yield { type: "done" };
}

function routeLabel(r: Route): string {
  switch (r.kind) {
    case "revenue":
      return "выручка";
    case "dishes":
      return "топ блюд";
    case "shifts":
      return "смены";
    case "compare":
      return "сравнение периодов";
    case "search":
      return "поиск в меню";
    case "suggest":
      return "подсказки";
  }
}
