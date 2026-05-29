/**
 * Real iiko Cloud API client — port of `iiko_client.py` from v1.
 *
 * Scope of this Phase 1 port:
 *  - Token acquisition via POST /api/1/access_token { apiLogin }
 *  - In-memory token cache (TTL 14 min — iiko tokens nominally 15 min)
 *  - getRevenueSummary via POST /api/v2/reports/olap (SALES report)
 *
 * Methods not yet ported (`getDishStatistics`, `getCategoryStatistics`,
 * `getShifts`, `searchNomenclature`) throw a clear deferral error.
 * They will land when Edison apiLogin arrives (post-31-May 2026) and we can
 * validate the actual OLAP response shape end-to-end.
 *
 * For dev/preview/Михно demo, the facade in `client.ts` selects
 * `MockIikoClient` instead via `USE_MOCK_IIKO=true`.
 */

import { resolvePeriodToDates } from "./mock-client";
import {
  RevenueSummarySchema,
} from "./models";
import type { IikoClient } from "./types";
import type {
  Period,
  Product,
  RevenueSummary,
  DishStat,
  CategoryStat,
  ShiftStat,
} from "./models";

const DEFAULT_BASE_URL = "https://api-ru.iiko.services";
const TOKEN_TTL_MS = 14 * 60 * 1000; // 14 minutes — iiko tokens live ~15

export interface CloudIikoClientOptions {
  apiLogin: string;
  organizationId: string;
  baseUrl?: string;
  /** ISO date treated as "today" for relative period resolution. */
  today: string;
  /** Allow injecting a fetch implementation (tests, edge runtime). */
  fetchImpl?: typeof fetch;
}

export class CloudIikoClient implements IikoClient {
  private readonly apiLogin: string;
  private readonly organizationId: string;
  private readonly baseUrl: string;
  private readonly today: string;
  private readonly fetchImpl: typeof fetch;
  private cachedToken: string | null = null;
  private tokenExpiresAt = 0;

  constructor(opts: CloudIikoClientOptions) {
    this.apiLogin = opts.apiLogin;
    this.organizationId = opts.organizationId;
    this.baseUrl = (opts.baseUrl ?? DEFAULT_BASE_URL).replace(/\/$/, "");
    this.today = opts.today;
    this.fetchImpl = opts.fetchImpl ?? globalThis.fetch.bind(globalThis);
  }

  async getRevenueSummary(period: Period): Promise<RevenueSummary> {
    const { from, to } = periodToRange(period, this.today);
    const token = await this.getToken();

    const res = await this.fetchImpl(`${this.baseUrl}/api/v2/reports/olap`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        organizationIds: [this.organizationId],
        reportType: "SALES",
        groupByRowFields: ["OpenDate"],
        aggregateFields: ["DishDiscountSumInt"],
        dateFrom: from,
        dateTo: to,
      }),
    });

    if (!res.ok) {
      throw new Error(`iiko Cloud OLAP failed: HTTP ${res.status}`);
    }

    const payload = (await res.json()) as { data?: Array<Record<string, unknown>> };
    const rows = payload.data ?? [];

    const points = rows.map((row) => ({
      date: String(row.OpenDate ?? row.openDate ?? ""),
      revenue: Number(row.DishDiscountSumInt ?? row.dishDiscountSumInt ?? 0),
    }));

    const revenue = points.reduce((s, p) => s + p.revenue, 0);
    const itemsSold = 0; // not derivable from this OLAP query — populated in Phase 1.5
    const averageCheck = 0;
    const uniqueDishes = 0;

    const summary: RevenueSummary = {
      revenue,
      averageCheck,
      itemsSold,
      uniqueDishes,
      points,
    };

    return RevenueSummarySchema.parse(summary);
  }

  async getDishStatistics(_period: Period, _topN: number): Promise<DishStat[]> {
    throw new Error(
      "CloudIikoClient.getDishStatistics: deferred — not yet implemented. Use USE_MOCK_IIKO=true or wait for Phase 1.5 port.",
    );
  }

  async getCategoryStatistics(_period: Period): Promise<CategoryStat[]> {
    throw new Error(
      "CloudIikoClient.getCategoryStatistics: deferred — not yet implemented. Use USE_MOCK_IIKO=true or wait for Phase 1.5 port.",
    );
  }

  async getShifts(_period: Period): Promise<ShiftStat[]> {
    throw new Error(
      "CloudIikoClient.getShifts: deferred — not yet implemented. Use USE_MOCK_IIKO=true or wait for Phase 1.5 port.",
    );
  }

  async searchNomenclature(_query: string): Promise<Product[]> {
    throw new Error(
      "CloudIikoClient.searchNomenclature: deferred — not yet implemented. Use USE_MOCK_IIKO=true or wait for Phase 1.5 port.",
    );
  }

  // -------------------------------------------------------------------------
  // Internal — token handling
  // -------------------------------------------------------------------------

  private async getToken(): Promise<string> {
    if (this.cachedToken && Date.now() < this.tokenExpiresAt) {
      return this.cachedToken;
    }

    const res = await this.fetchImpl(`${this.baseUrl}/api/1/access_token`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ apiLogin: this.apiLogin }),
    });

    if (!res.ok) {
      throw new Error(`iiko Cloud auth failed: HTTP ${res.status}`);
    }

    const payload = (await res.json()) as { token?: string };
    if (!payload.token) {
      throw new Error("iiko Cloud auth: token missing in response");
    }

    this.cachedToken = payload.token;
    this.tokenExpiresAt = Date.now() + TOKEN_TTL_MS;
    return payload.token;
  }
}

/**
 * Collapse a `Period` into a `{from, to}` date range (ISO YYYY-MM-DD).
 * Wraps `resolvePeriodToDates` from the mock client so both code paths agree
 * on what "LAST_WEEK" means.
 */
function periodToRange(period: Period, today: string): { from: string; to: string } {
  const dates = resolvePeriodToDates(period, today);
  if (dates.length === 0) {
    return { from: today, to: today };
  }
  return { from: dates[0], to: dates[dates.length - 1] };
}
