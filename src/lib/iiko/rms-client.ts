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

const SESSION_TTL_MS = 115 * 60 * 1000;

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

function periodToRange(period: Period, today: string): { from: string; to: string } {
  const dates = resolvePeriodToDates(period, today);
  if (dates.length === 0) return { from: today, to: today };
  return { from: dates[0], to: dates[dates.length - 1] };
}

async function readResponseText(res: Response): Promise<string> {
  try {
    return await res.text();
  } catch {
    return "";
  }
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
      aggregateFields: ["DishAmountInt", "DishSumInt", "DiscountSum"],
    });

    const points = rows.map((row) => ({
      date: readText(row, "OpenDate.Typed", this.today),
      revenue: readNumber(row, "DishSumInt"),
    }));
    points.sort((a, b) => a.date.localeCompare(b.date));

    const revenue = points.reduce((sum, point) => sum + point.revenue, 0);
    const itemsSold = Math.round(
      rows.reduce((sum, row) => sum + readNumber(row, "DishAmountInt"), 0),
    );

    return RevenueSummarySchema.parse({
      revenue,
      averageCheck: itemsSold > 0 ? Math.round(revenue / itemsSold) : 0,
      itemsSold,
      uniqueDishes: 0,
      points,
    });
  }

  async getDishStatistics(
    period: Period,
    topN: number,
  ): Promise<DishStat[]> {
    const rows = await this.runOlap(period, {
      groupByRowFields: ["DishName", "DishGroup"],
      aggregateFields: ["DishAmountInt", "DishSumInt", "DiscountSum"],
    });

    const stats = rows.map((row) =>
      DishStatSchema.parse({
        dishName: readText(row, "DishName"),
        dishGroup: readText(row, "DishGroup"),
        dishAmountInt: Math.round(readNumber(row, "DishAmountInt")),
        dishSumInt: readNumber(row, "DishSumInt"),
      }),
    );

    stats.sort((a, b) => b.dishSumInt - a.dishSumInt);
    return stats.slice(0, topN);
  }

  async getCategoryStatistics(period: Period): Promise<CategoryStat[]> {
    const rows = await this.runOlap(period, {
      groupByRowFields: ["DishGroup"],
      aggregateFields: ["DishSumInt", "DiscountSum"],
    });

    return rows.map((row) =>
      CategoryStatSchema.parse({
        categoryName: readText(row, "DishGroup"),
        dishSumInt: readNumber(row, "DishSumInt"),
      }),
    );
  }

  async getShifts(period: Period): Promise<ShiftStat[]> {
    const rows = await this.runOlap(period, {
      groupByRowFields: ["OpenDate.Typed"],
      aggregateFields: ["DishAmountInt", "DishSumInt"],
    });

    return rows.map((row) => {
      const date = readText(row, "OpenDate.Typed", this.today);
      return ShiftStatSchema.parse({
        shiftId: `rms-shift-${date}`,
        openTime: `${date}T00:00:00`,
        revenue: readNumber(row, "DishSumInt"),
        items: Math.round(readNumber(row, "DishAmountInt")),
        employee: "Смена",
      });
    });
  }

  async searchNomenclature(): Promise<Product[]> {
    return [];
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
          | { organizations?: Array<Record<string, unknown>>; data?: Array<Record<string, unknown>>; items?: Array<Record<string, unknown>> };
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

  private async runOlap(
    period: Period,
    params: { groupByRowFields: string[]; aggregateFields: string[] },
  ): Promise<RmsOlapRow[]> {
    const key = await this.getSessionKey();
    const { from, to } = periodToRange(period, this.today);
    const res = await this.fetchImpl(this.url("/resto/api/v2/reports/olap", { key }), {
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
    });

    if (!res.ok) {
      throw new Error(
        `iiko RMS OLAP failed: HTTP ${res.status}: ${(await readResponseText(res)).slice(0, 500)}`,
      );
    }

    const payload = (await res.json()) as { data?: RmsOlapRow[] };
    return payload.data ?? [];
  }

  private async getSessionKey(forceRefresh = false): Promise<string> {
    if (!forceRefresh && this.sessionKey && Date.now() < this.sessionExpiresAt) {
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
