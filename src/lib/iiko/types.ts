/**
 * Contract every iiko client (mock or real) must satisfy.
 *
 * The dashboard, AI tools, and automation surfaces all talk
 * to this surface — never to a concrete client directly.
 *
 * Real implementations live in `cloud-client.ts` / `rms-client.ts`.
 * The mock implementation lives in `mock-client.ts`.
 * The runtime switch (USE_MOCK_IIKO) lives in `client.ts`.
 */

import type {
  Period,
  Product,
  RevenueSummary,
  DishStat,
  CategoryStat,
  ShiftStat,
} from "./models";

export interface IikoClient {
  /** Aggregate revenue for a period: totals + daily breakdown. */
  getRevenueSummary(period: Period): Promise<RevenueSummary>;

  /** Top-N dishes by revenue inside a period, sorted desc. */
  getDishStatistics(period: Period, topN: number): Promise<DishStat[]>;

  /** Revenue grouped by menu category for a period. */
  getCategoryStatistics(period: Period): Promise<CategoryStat[]>;

  /** Cashier-shift breakdown for a period (1+ shifts per day). */
  getShifts(period: Period): Promise<ShiftStat[]>;

  /** Full venue nomenclature when the current iiko channel exposes it. */
  fetchNomenclature?(): Promise<Product[]>;

  /** Case-insensitive substring search across the venue's nomenclature. */
  searchNomenclature(query: string): Promise<Product[]>;
}
