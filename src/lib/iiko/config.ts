/**
 * iiko client configuration resolver.
 *
 * Single source of truth for "which iiko backend does this venue use right
 * now" — real integration credentials first, env fallback for dev/demo.
 * The dashboard, chat, and tools all resolve through here.
 *
 * Pure + env-injected so it's fully testable. The thin builder
 * `getDashboardClient` wires it to real clients.
 */

import { getIikoClient } from "./client";
import type { IikoClient } from "./types";
import type { ResolvedVenue } from "@/lib/venues/get-venue";

/**
 * Frozen "today" for mock mode — keeps demo numbers and screenshots stable.
 * Real mode uses the actual current date instead.
 */
export const DEMO_ANCHOR = "2026-05-29";

export type IikoClientConfig =
  | { mode: "mock"; today: string; organizationId: string }
  | {
      mode: "real";
      today: string;
      apiLogin: string;
      organizationId: string;
    };

/**
 * Resolve the iiko config for a venue given an env bag and the current date.
 *
 * Real mode is selected when a venue carries a stored apiLogin. Env keys remain
 * a dev fallback and require `USE_MOCK_IIKO=false`.
 */
export function resolveIikoClientConfig(
  venue: ResolvedVenue,
  env: Record<string, string | undefined>,
  today: string,
): IikoClientConfig {
  if (venue.iiko.apiLogin?.trim()) {
    return {
      mode: "real",
      today,
      apiLogin: venue.iiko.apiLogin.trim(),
      organizationId: venue.iiko.organizationId,
    };
  }

  const wantReal = env.USE_MOCK_IIKO === "false";

  if (wantReal) {
    const apiLogin = env.IIKO_API_LOGIN?.trim() || "";

    if (apiLogin) {
      return {
        mode: "real",
        today,
        apiLogin,
        organizationId: venue.iiko.organizationId,
      };
    }
  }

  return {
    mode: "mock",
    today: DEMO_ANCHOR,
    organizationId: venue.iiko.organizationId,
  };
}

/** Current date as ISO YYYY-MM-DD (UTC). Real mode only. */
function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}

/**
 * Build a ready-to-use iiko client for a venue based on resolved config.
 * This is what the dashboard / chat / tools call.
 */
export function getDashboardClient(venue: ResolvedVenue): IikoClient {
  const cfg = resolveIikoClientConfig(venue, process.env, todayIso());

  if (cfg.mode === "real") {
    return getIikoClient({
      channel: "cloud",
      apiLogin: cfg.apiLogin,
      organizationId: cfg.organizationId,
      today: cfg.today,
      forceReal: true,
    });
  }

  // Mock path: facade also returns MockIikoClient, but we pass through the
  // anchor explicitly so determinism does not depend on env ordering.
  return getIikoClient({
    channel: "cloud",
    apiLogin: "",
    organizationId: cfg.organizationId,
    today: cfg.today,
  });
}
