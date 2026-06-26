/**
 * Mock implementation of `IikoClient` backed by deterministic sandbox fixtures.
 *
 * Used in dev/preview while real iiko keys are pending (Phase 0–3), and as
 * the fallback backend while real iiko credentials are absent.
 *
 * Determinism guarantees:
 *  - Same anchor date + same period → same numbers, every run.
 *  - No `Math.random()`, no `Date.now()` (other than constructor-injected `today`).
 *  - Safe for screenshot tests and SSR caching.
 */

import {
  SANDBOX_CATEGORY_MIX,
  SANDBOX_DISHES,
  SANDBOX_PRODUCTS,
  SANDBOX_SHIFT_EMPLOYEES,
  sandboxDailyRevenue,
} from "@/lib/mock/sandbox-fixtures";

import type { IikoClient } from "./types";
import type {
  Period,
  Product,
  RevenueSummary,
  RevenuePoint,
  DishStat,
  CategoryStat,
  ShiftStat,
} from "./models";

/** Average ticket size used to derive items_sold from revenue. */
const AVG_TICKET_RUBLES = 1700;

export interface MockIikoClientOptions {
  /** ISO date (YYYY-MM-DD) treated as "today" for period resolution. */
  today: string;
}

export class MockIikoClient implements IikoClient {
  private readonly today: string;

  constructor(options: MockIikoClientOptions) {
    this.today = options.today;
  }

  async getRevenueSummary(period: Period): Promise<RevenueSummary> {
    const dates = resolvePeriodToDates(period, this.today);
    const points: RevenuePoint[] = dates.map((date) => ({
      date,
      revenue: sandboxDailyRevenue(date),
    }));

    const revenue = points.reduce((sum, p) => sum + p.revenue, 0);
    const itemsSold = points.reduce(
      (sum, p) => sum + dailyItemsSold(p.revenue),
      0,
    );
    const averageCheck = itemsSold > 0 ? Math.round(revenue / itemsSold) : 0;
    const uniqueDishes = Math.min(SANDBOX_DISHES.length, 60 + dates.length);

    return {
      revenue,
      averageCheck,
      itemsSold,
      uniqueDishes,
      points,
    };
  }

  async getDishStatistics(
    period: Period,
    topN: number,
  ): Promise<DishStat[]> {
    const dates = resolvePeriodToDates(period, this.today);
    const totalRevenue = dates.reduce((s, d) => s + sandboxDailyRevenue(d), 0);

    const stats: DishStat[] = SANDBOX_DISHES.map((dish) => {
      const categoryShare = SANDBOX_CATEGORY_MIX[dish.category] ?? 0;
      const dishRevenue = totalRevenue * categoryShare * dish.weight;
      const dishSumInt = Math.round(dishRevenue);
      const dishAmountInt = Math.round(dishRevenue / dish.price);
      return {
        dishName: dish.name,
        dishGroup: dish.category,
        dishAmountInt,
        dishSumInt,
      };
    });

    stats.sort((a, b) => b.dishSumInt - a.dishSumInt);
    return stats.slice(0, topN);
  }

  async getCategoryStatistics(period: Period): Promise<CategoryStat[]> {
    const dates = resolvePeriodToDates(period, this.today);
    const totalRevenue = dates.reduce((s, d) => s + sandboxDailyRevenue(d), 0);

    return Object.entries(SANDBOX_CATEGORY_MIX).map(([categoryName, share]) => ({
      categoryName,
      dishSumInt: Math.round(totalRevenue * share),
    }));
  }

  async getShifts(period: Period): Promise<ShiftStat[]> {
    const dates = resolvePeriodToDates(period, this.today);
    return dates.map((date, idx) => {
      const revenue = sandboxDailyRevenue(date);
      const items = dailyItemsSold(revenue);
      const employee =
        SANDBOX_SHIFT_EMPLOYEES[idx % SANDBOX_SHIFT_EMPLOYEES.length];
      const next = addDays(date, 1);
      return {
        shiftId: `shift-${date}`,
        openTime: `${date}T18:00:00`,
        closeTime: `${next}T03:00:00`,
        revenue,
        items,
        employee,
      };
    });
  }

  async fetchNomenclature(): Promise<Product[]> {
    return SANDBOX_PRODUCTS;
  }

  async searchNomenclature(query: string): Promise<Product[]> {
    const q = query.trim().toLowerCase();
    if (!q) return [];
    return SANDBOX_PRODUCTS.filter((p) => p.name.toLowerCase().includes(q));
  }
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function dailyItemsSold(revenue: number): number {
  return Math.round(revenue / AVG_TICKET_RUBLES);
}

function addDays(isoDate: string, days: number): string {
  const d = new Date(isoDate + "T00:00:00Z");
  d.setUTCDate(d.getUTCDate() + days);
  return d.toISOString().slice(0, 10);
}

function startOfWeekMonday(isoDate: string): string {
  const d = new Date(isoDate + "T00:00:00Z");
  const day = d.getUTCDay(); // 0=Sun .. 6=Sat
  const offset = day === 0 ? 6 : day - 1; // back to Monday
  d.setUTCDate(d.getUTCDate() - offset);
  return d.toISOString().slice(0, 10);
}

function startOfMonth(isoDate: string): string {
  const d = new Date(isoDate + "T00:00:00Z");
  return `${d.getUTCFullYear()}-${String(d.getUTCMonth() + 1).padStart(2, "0")}-01`;
}

function endOfPreviousMonth(isoDate: string): string {
  const d = new Date(isoDate + "T00:00:00Z");
  d.setUTCDate(0); // moves to last day of previous month
  return d.toISOString().slice(0, 10);
}

function startOfPreviousMonth(isoDate: string): string {
  const d = new Date(isoDate + "T00:00:00Z");
  d.setUTCDate(1);
  d.setUTCMonth(d.getUTCMonth() - 1);
  return d.toISOString().slice(0, 10);
}

/** Inclusive date range "from..to" → array of ISO date strings. */
function datesBetween(from: string, to: string): string[] {
  const out: string[] = [];
  let cur = from;
  while (cur <= to) {
    out.push(cur);
    cur = addDays(cur, 1);
  }
  return out;
}

/**
 * Resolve a `Period` against a fixed anchor day ("today") into a list of
 * ISO dates. Centralised so both the iiko clients and the AI tools share
 * one notion of what "LAST_WEEK" means.
 */
export function resolvePeriodToDates(period: Period, today: string): string[] {
  switch (period.type) {
    case "TODAY":
      return [today];
    case "YESTERDAY":
      return [addDays(today, -1)];
    case "CURRENT_WEEK": {
      const from = startOfWeekMonday(today);
      return datesBetween(from, today);
    }
    case "LAST_WEEK": {
      // 7 days ending yesterday
      const to = addDays(today, -1);
      const from = addDays(to, -6);
      return datesBetween(from, to);
    }
    case "CURRENT_MONTH": {
      const from = startOfMonth(today);
      return datesBetween(from, today);
    }
    case "LAST_MONTH": {
      const from = startOfPreviousMonth(today);
      const to = endOfPreviousMonth(today);
      return datesBetween(from, to);
    }
    case "CUSTOM":
      return datesBetween(period.from, period.to);
  }
}
