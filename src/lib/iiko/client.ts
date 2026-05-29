/**
 * Unified iiko client facade.
 *
 * Phase 0–3 default to `MockIikoClient` so the dashboard, AI tools, and
 * Михно demo can ship before real apiLogin keys arrive (post-31-May 2026).
 *
 * When `USE_MOCK_IIKO=false` AND a real `channel` is selected, returns
 * the corresponding real client. RMS port is still a placeholder
 * (see `rms-client.ts`).
 *
 * Switching is binary at the env-var level (per-deploy, not per-request)
 * to keep tests deterministic and to avoid leaking mock paths into prod.
 */

import { MockIikoClient } from "./mock-client";
import { CloudIikoClient } from "./cloud-client";
import { RmsIikoClient } from "./rms-client";
import type { IikoClient } from "./types";

export type IikoClientOptions =
  | {
      channel: "cloud";
      apiLogin: string;
      organizationId: string;
      baseUrl?: string;
      today: string;
      fetchImpl?: typeof fetch;
    }
  | {
      channel: "rms";
      host: string;
      login: string;
      password: string;
      today: string;
    };

function shouldUseMock(): boolean {
  const flag = process.env.USE_MOCK_IIKO;
  // Mock is the safe default: only "false" (explicit opt-in to real) flips it.
  return flag !== "false";
}

export function getIikoClient(opts: IikoClientOptions): IikoClient {
  if (shouldUseMock()) {
    return new MockIikoClient({ today: opts.today });
  }

  if (opts.channel === "cloud") {
    return new CloudIikoClient({
      apiLogin: opts.apiLogin,
      organizationId: opts.organizationId,
      baseUrl: opts.baseUrl,
      today: opts.today,
      fetchImpl: opts.fetchImpl,
    });
  }

  return new RmsIikoClient({
    host: opts.host,
    login: opts.login,
    password: opts.password,
    today: opts.today,
  });
}
