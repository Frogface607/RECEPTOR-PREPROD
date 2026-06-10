/**
 * Period <-> URL search-param helpers for the dashboard.
 *
 * State is intentionally URL-driven: shareable links, server-renderable,
 * and `?period=` becomes the canonical source of truth.
 */

import type { Period, PeriodType } from "@/lib/iiko/models";

const PRESETS: PeriodType[] = [
  "TODAY",
  "YESTERDAY",
  "CURRENT_WEEK",
  "LAST_WEEK",
  "CURRENT_MONTH",
  "LAST_MONTH",
];

export const PERIOD_LABELS_RU: Record<PeriodType, string> = {
  TODAY: "Сегодня",
  YESTERDAY: "Вчера",
  CURRENT_WEEK: "Текущая неделя",
  LAST_WEEK: "Прошлая неделя",
  CURRENT_MONTH: "Текущий месяц",
  LAST_MONTH: "Прошлый месяц",
  CUSTOM: "Произвольный",
};

/** Default period when none is set in the URL. */
export const DEFAULT_PERIOD: Period = { type: "LAST_WEEK" };

/** Parse `?period=...` (and `?from=`, `?to=` for CUSTOM) into a Period. */
export function parsePeriodSearchParams(
  params: Record<string, string | string[] | undefined>,
): Period {
  const raw = typeof params.period === "string" ? params.period : "";
  if (PRESETS.includes(raw as PeriodType)) {
    return { type: raw as Exclude<PeriodType, "CUSTOM"> };
  }
  if (raw === "CUSTOM") {
    const from = typeof params.from === "string" ? params.from : "";
    const to = typeof params.to === "string" ? params.to : "";
    if (
      /^\d{4}-\d{2}-\d{2}$/.test(from) &&
      /^\d{4}-\d{2}-\d{2}$/.test(to) &&
      from <= to
    ) {
      return { type: "CUSTOM", from, to };
    }
  }
  return DEFAULT_PERIOD;
}

/** Serialise a Period back into search-param shape. */
export function periodToSearchParams(period: Period): Record<string, string> {
  if (period.type === "CUSTOM") {
    return { period: "CUSTOM", from: period.from, to: period.to };
  }
  return { period: period.type };
}

export function formatPeriodLabel(period: Period): string {
  if (period.type !== "CUSTOM") {
    return PERIOD_LABELS_RU[period.type];
  }

  return `${formatDateRu(period.from)} - ${formatDateRu(period.to)}`;
}

function formatDateRu(value: string): string {
  const [year, month, day] = value.split("-");
  return `${day}.${month}.${year}`;
}
