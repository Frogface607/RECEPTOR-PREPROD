import { formatInteger, formatRubles } from "@/lib/format";
import type { IikoClient } from "@/lib/iiko/types";
import type { Period, PeriodType } from "@/lib/iiko/models";
import { PERIOD_LABELS_RU } from "@/lib/venues/period";

export type DailyBrief = {
  period: PeriodType;
  comparisonPeriod: PeriodType;
  headline: string;
  revenue: {
    current: number;
    previous: number;
    deltaPct: number;
  };
  highlights: string[];
  actions: string[];
};

export type RenderDailyBriefOptions = {
  venueName: string;
  generatedAt?: Date;
};

const COMPARISON_PERIOD: Record<PeriodType, PeriodType> = {
  TODAY: "YESTERDAY",
  YESTERDAY: "LAST_WEEK",
  CURRENT_WEEK: "LAST_WEEK",
  LAST_WEEK: "LAST_MONTH",
  CURRENT_MONTH: "LAST_MONTH",
  LAST_MONTH: "CURRENT_MONTH",
  CUSTOM: "CUSTOM",
};

function asPeriod(type: PeriodType): Period {
  if (type === "CUSTOM") return { type: "LAST_WEEK" };
  return { type };
}

function deltaPct(current: number, previous: number): number {
  if (previous <= 0) return current > 0 ? 100 : 0;
  return Number((((current - previous) / previous) * 100).toFixed(1));
}

function deltaPhrase(delta: number): string {
  if (delta > 0) return `выше на ${Math.abs(delta)}%`;
  if (delta < 0) return `ниже на ${Math.abs(delta)}%`;
  return "на уровне сравнения";
}

function periodTitle(period: PeriodType): string {
  const titles: Record<PeriodType, string> = {
    TODAY: "сегодня",
    YESTERDAY: "вчера",
    CURRENT_WEEK: "на этой неделе",
    LAST_WEEK: "на прошлой неделе",
    CURRENT_MONTH: "в этом месяце",
    LAST_MONTH: "в прошлом месяце",
    CUSTOM: "за выбранный период",
  };
  return titles[period];
}

export async function buildDailyBrief(
  client: IikoClient,
  period: PeriodType = "YESTERDAY",
): Promise<DailyBrief> {
  const comparisonPeriod = COMPARISON_PERIOD[period] ?? "LAST_WEEK";
  const [current, previous, dishes, categories] = await Promise.all([
    client.getRevenueSummary(asPeriod(period)),
    client.getRevenueSummary(asPeriod(comparisonPeriod)),
    client.getDishStatistics(asPeriod(period), 5),
    client.getCategoryStatistics(asPeriod(period)),
  ]);

  const delta = deltaPct(current.revenue, previous.revenue);
  const topDish = dishes[0];
  const topCategory = categories.sort((a, b) => b.dishSumInt - a.dishSumInt)[0];

  const highlights = [
    `Деньги ${periodTitle(period)}: ${formatRubles(current.revenue)} — ${deltaPhrase(delta)}.`,
    topDish
      ? `Главное блюдо периода: ${topDish.dishName} (${formatRubles(topDish.dishSumInt)}, ${formatInteger(topDish.dishAmountInt)} порций).`
      : "Нет данных по блюдам за период.",
    topCategory
      ? `Категория, которая держит выручку: ${topCategory.categoryName} (${formatRubles(topCategory.dishSumInt)}).`
      : "Нет данных по категориям за период.",
  ];

  const actions = [
    delta < 0
      ? "Начни с просевших смен и категорий: найди, где потеряли деньги, а не просто констатируй падение."
      : "Зафиксируй, что сработало: расписание, промо, погода, посадка, команда на смене.",
    topDish
      ? `Дай официантам фокус на ${topDish.dishName} и проверь стоп-лист/заготовки до вечерней посадки.`
      : "Проверь корректность выгрузки блюд из iiko.",
    topCategory
      ? `Разбери маржинальность категории ${topCategory.categoryName}: высокая выручка не всегда означает прибыль.`
      : "Проверь категории меню и настройки номенклатуры.",
  ];

  return {
    period,
    comparisonPeriod,
    headline:
      delta < 0
        ? `Выручка ${periodTitle(period)} просела: ${formatRubles(current.revenue)}.`
        : `Выручка ${periodTitle(period)} в плюсе: ${formatRubles(current.revenue)}.`,
    revenue: {
      current: current.revenue,
      previous: previous.revenue,
      deltaPct: delta,
    },
    highlights,
    actions,
  };
}

export function renderDailyBriefText(
  brief: DailyBrief,
  options: RenderDailyBriefOptions,
): string {
  const generatedAt = options.generatedAt ?? new Date();
  const date = new Intl.DateTimeFormat("ru-RU", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(generatedAt);

  return [
    `Receptor Daily Brief: ${options.venueName}`,
    `${PERIOD_LABELS_RU[brief.period]} · ${date}`,
    "",
    brief.headline,
    "",
    "Главное:",
    ...brief.highlights.map((item) => `- ${item}`),
    "",
    "Что сделать сегодня:",
    ...brief.actions.map((item, index) => `${index + 1}. ${item}`),
  ].join("\n");
}
