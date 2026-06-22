/**
 * RMS Server iiko client — placeholder.
 *
 * RMS (`/resto/api/...` endpoints on a venue-hosted `*.iiko.it` server) is
 * used by chain restaurants that run their own iiko Office. We have no
 * chain deployments in the pipeline for v2. Porting the 1094-line v1 RMS
 * client (`docs/v1-iiko-reference/iiko_rms_client.py`) is real work
 * without a customer to validate against.
 *
 * Phase 1.5 — port when the first chain customer signs.
 *
 * Until then, this class exists so the facade (`client.ts`) and the
 * settings UI (`iiko_credentials.channel = 'rms'`) can reference it,
 * but every method throws a clear deferral error.
 */

import type { IikoClient } from "./types";
import type {
  Period,
  Product,
  RevenueSummary,
  DishStat,
  CategoryStat,
  ShiftStat,
} from "./models";

export interface RmsIikoClientOptions {
  host: string;
  login: string;
  password: string;
  today: string;
}

function deferred(method: string): Error {
  return new Error(
    `RmsIikoClient.${method}: RMS port deferred to Phase 1.5 (first chain customer). Use Cloud channel or USE_MOCK_IIKO=true.`,
  );
}

export class RmsIikoClient implements IikoClient {
  private readonly host: string;
  private readonly login: string;
  private readonly password: string;
  private readonly today: string;

  constructor(opts: RmsIikoClientOptions) {
    this.host = opts.host;
    this.login = opts.login;
    this.password = opts.password;
    this.today = opts.today;
  }

  async getRevenueSummary(_period: Period): Promise<RevenueSummary> {
    throw deferred("getRevenueSummary");
  }

  async getDishStatistics(
    _period: Period,
    _topN: number,
  ): Promise<DishStat[]> {
    throw deferred("getDishStatistics");
  }

  async getCategoryStatistics(_period: Period): Promise<CategoryStat[]> {
    throw deferred("getCategoryStatistics");
  }

  async getShifts(_period: Period): Promise<ShiftStat[]> {
    throw deferred("getShifts");
  }

  async searchNomenclature(_query: string): Promise<Product[]> {
    throw deferred("searchNomenclature");
  }
}
