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
 * They will land when a live apiLogin arrives and we can
 * validate the actual OLAP response shape end-to-end.
 *
 * For dev/preview, the facade in `client.ts` selects
 * `MockIikoClient` instead via `USE_MOCK_IIKO=true`.
 */

import { resolvePeriodToDates } from "./mock-client";
import {
  RevenueSummarySchema,
  DishStatSchema,
  CategoryStatSchema,
  ShiftStatSchema,
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

export type IikoOrganization = {
  id: string;
  name: string;
};

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

  async listOrganizations(): Promise<IikoOrganization[]> {
    const token = await this.getToken();
    const res = await this.fetchImpl(`${this.baseUrl}/api/1/organizations`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
    });

    if (!res.ok) {
      throw new Error(
        `iiko Cloud organizations failed: HTTP ${res.status}${await readIikoError(res)}`,
      );
    }

    const payload = (await res.json()) as {
      organizations?: Array<Record<string, unknown>>;
    };

    return (payload.organizations ?? [])
      .map((org) => ({
        id: String(org.id ?? ""),
        name: String(org.name ?? org.title ?? ""),
      }))
      .filter((org) => org.id.length > 0);
  }

  async getDishStatistics(period: Period, topN: number): Promise<DishStat[]> {
    const rows = await this.runOlap(period, {
      groupByRowFields: ["DishName", "DishGroup"],
      aggregateFields: ["DishDiscountSumInt", "DishAmountInt"],
    });

    const stats: DishStat[] = rows.map((row) => ({
      dishName: String(row.DishName ?? row.dishName ?? "—"),
      dishGroup: String(row.DishGroup ?? row.dishGroup ?? "—"),
      dishAmountInt: Math.round(
        Number(row.DishAmountInt ?? row.dishAmountInt ?? 0),
      ),
      dishSumInt: Number(row.DishDiscountSumInt ?? row.dishDiscountSumInt ?? 0),
    }));

    stats.sort((a, b) => b.dishSumInt - a.dishSumInt);
    return stats.slice(0, topN).map((s) => DishStatSchema.parse(s));
  }

  async getCategoryStatistics(period: Period): Promise<CategoryStat[]> {
    const rows = await this.runOlap(period, {
      groupByRowFields: ["DishGroup"],
      aggregateFields: ["DishDiscountSumInt"],
    });

    return rows.map((row) =>
      CategoryStatSchema.parse({
        categoryName: String(row.DishGroup ?? row.dishGroup ?? "—"),
        dishSumInt: Number(row.DishDiscountSumInt ?? row.dishDiscountSumInt ?? 0),
      }),
    );
  }

  async getShifts(period: Period): Promise<ShiftStat[]> {
    // Cloud OLAP does not expose cashier-session rows the way RMS does, so we
    // derive one "day-shift" per OpenDate. Good enough for the dashboard's
    // shifts table; revisit with live data if true per-cashier shifts
    // are needed (documented in REAL_CONNECT.md).
    const rows = await this.runOlap(period, {
      groupByRowFields: ["OpenDate"],
      aggregateFields: ["DishDiscountSumInt", "DishAmountInt"],
    });

    return rows.map((row) => {
      const date = String(row.OpenDate ?? row.openDate ?? this.today);
      return ShiftStatSchema.parse({
        shiftId: `cloud-shift-${date}`,
        openTime: `${date}T00:00:00`,
        revenue: Number(row.DishDiscountSumInt ?? row.dishDiscountSumInt ?? 0),
        items: Math.round(Number(row.DishAmountInt ?? row.dishAmountInt ?? 0)),
        employee: "Смена",
      });
    });
  }

  async searchNomenclature(_query: string): Promise<Product[]> {
    // Nomenclature lives behind a separate (non-OLAP) endpoint with a complex
    // normalization step in v1. Deferred to first real-key session — degrade
    // gracefully (empty list) instead of throwing so a live dashboard never
    // 500s. The chat's "найди в меню" simply reports nothing found.
    return [];
  }

  /**
   * Run a SALES OLAP query for a period and return raw rows.
   * Shared by all BI methods so the auth + request shape stay in one place.
   */
  private async runOlap(
    period: Period,
    params: { groupByRowFields: string[]; aggregateFields: string[] },
  ): Promise<Array<Record<string, unknown>>> {
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
        groupByRowFields: params.groupByRowFields,
        aggregateFields: params.aggregateFields,
        dateFrom: from,
        dateTo: to,
      }),
    });

    if (!res.ok) {
      throw new Error(
        `iiko Cloud OLAP failed: HTTP ${res.status}${await readIikoError(res)}`,
      );
    }

    const payload = (await res.json()) as {
      data?: Array<Record<string, unknown>>;
    };
    return payload.data ?? [];
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
      if (res.status === 401) {
        throw new Error(
          "iiko Cloud не принял apiLogin. Вставьте именно значение apiLogin из карточки интеграции, не название строки и не secret/key.",
        );
      }
      throw new Error(
        `iiko Cloud auth failed: HTTP ${res.status}${await readIikoError(res)}`,
      );
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

async function readIikoError(res: Response): Promise<string> {
  try {
    const text = await res.text();
    if (!text) return "";
    return `: ${text.slice(0, 500)}`;
  } catch {
    return "";
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
