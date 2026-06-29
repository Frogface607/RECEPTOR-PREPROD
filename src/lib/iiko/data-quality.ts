import { resolvePeriodToDates } from "./mock-client";
import type { Period, RevenueSummary } from "./models";

export type DataMode = "live" | "mock";
export type DataQualityStatus = "ok" | "watch" | "risk";

export type RevenueDataQuality = {
  status: DataQualityStatus;
  requestedDays: number;
  activeDays: number;
  missingDays: number;
  coveragePct: number;
  firstDataDate: string | null;
  lastDataDate: string | null;
  basis: string;
  summary: string;
  warnings: string[];
};

export function buildRevenueDataQuality(
  period: Period,
  summary: RevenueSummary,
  options: { today: string; dataMode: DataMode },
): RevenueDataQuality {
  const requestedDates = resolvePeriodToDates(period, options.today);
  const requestedDays = requestedDates.length;
  const positivePointDates = summary.points
    .filter((point) => point.revenue > 0)
    .map((point) => point.date)
    .sort();
  const positiveDateSet = new Set(positivePointDates);
  const activeDays = requestedDates.filter((date) =>
    positiveDateSet.has(date),
  ).length;
  const missingDays = Math.max(0, requestedDays - activeDays);
  const coveragePct =
    requestedDays > 0 ? Math.round((activeDays / requestedDays) * 100) : 0;
  const warnings: string[] = [];

  if (options.dataMode === "mock") {
    warnings.push(
      "Показаны тестовые данные. Для решений подключите реальные данные iiko.",
    );
  }

  if (summary.revenue <= 0 || activeDays === 0) {
    warnings.push("За выбранный период нет продаж в BI-выгрузке.");
  } else if (requestedDays >= 7 && coveragePct < 85) {
    warnings.push(
      `В периоде есть продажи только за ${activeDays} из ${requestedDays} дней. Сравнения и выводы могут быть неполными.`,
    );
  }

  if (options.dataMode === "live" && summary.revenue > 0) {
    if (summary.averageCheck <= 0) {
      warnings.push(
        "Средний чек не рассчитан: источник не отдал количество заказов.",
      );
    }
    if (summary.uniqueDishes <= 0) {
      warnings.push(
        "Меню не детализировано: источник не отдал блюда с продажами.",
      );
    }
  }

  const status = resolveStatus({
    dataMode: options.dataMode,
    revenue: summary.revenue,
    requestedDays,
    activeDays,
    coveragePct,
    warnings,
  });

  return {
    status,
    requestedDays,
    activeDays,
    missingDays,
    coveragePct,
    firstDataDate: positivePointDates[0] ?? null,
    lastDataDate: positivePointDates[positivePointDates.length - 1] ?? null,
    basis:
      options.dataMode === "live"
        ? "Выручка после скидок, по продажам iiko"
        : "Демо-выручка для знакомства с кабинетом",
    summary: buildSummary(activeDays, requestedDays, coveragePct),
    warnings,
  };
}

function resolveStatus({
  dataMode,
  revenue,
  requestedDays,
  activeDays,
  coveragePct,
  warnings,
}: {
  dataMode: DataMode;
  revenue: number;
  requestedDays: number;
  activeDays: number;
  coveragePct: number;
  warnings: string[];
}): DataQualityStatus {
  if (revenue <= 0 || activeDays === 0) return "risk";
  if (requestedDays >= 7 && coveragePct < 50) return "risk";
  if (dataMode === "mock") return "watch";
  if (requestedDays >= 7 && coveragePct < 85) return "watch";
  if (warnings.length > 0) return "watch";
  return "ok";
}

function buildSummary(
  activeDays: number,
  requestedDays: number,
  coveragePct: number,
): string {
  if (requestedDays <= 0) return "Период не выбран";
  if (activeDays === requestedDays) {
    return `Полное покрытие: ${activeDays} из ${requestedDays} дней`;
  }
  return `${activeDays} из ${requestedDays} дней с продажами (${coveragePct}%)`;
}
