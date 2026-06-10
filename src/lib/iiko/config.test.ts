import { describe, expect, test } from "vitest";
import { resolveIikoClientConfig, DEMO_ANCHOR } from "./config";
import type { ResolvedVenue } from "@/lib/venues/get-venue";

const venue: ResolvedVenue = {
  id: "edison-demo",
  name: "Edison Bar",
  city: "Иркутск",
  type: "bar",
  timezone: "Asia/Irkutsk",
  iiko: { channel: "cloud", organizationId: "edison-org" },
};

describe("resolveIikoClientConfig", () => {
  test("stored venue apiLogin selects real mode without env flags", () => {
    const cfg = resolveIikoClientConfig(
      {
        ...venue,
        iiko: { ...venue.iiko, apiLogin: "stored-login" },
      },
      {},
      "2026-06-03",
    );
    expect(cfg.mode).toBe("real");
    if (cfg.mode === "real") {
      expect(cfg.apiLogin).toBe("stored-login");
      expect(cfg.organizationId).toBe("edison-org");
    }
  });

  test("mock mode when USE_MOCK_IIKO unset → deterministic anchor", () => {
    const cfg = resolveIikoClientConfig(venue, {}, "2026-06-03");
    expect(cfg.mode).toBe("mock");
    if (cfg.mode === "mock") {
      expect(cfg.today).toBe(DEMO_ANCHOR);
    }
  });

  test("mock mode when USE_MOCK_IIKO=true explicitly", () => {
    const cfg = resolveIikoClientConfig(
      venue,
      { USE_MOCK_IIKO: "true" },
      "2026-06-03",
    );
    expect(cfg.mode).toBe("mock");
  });

  test("real mode requires USE_MOCK_IIKO=false AND an apiLogin", () => {
    const cfg = resolveIikoClientConfig(
      venue,
      { USE_MOCK_IIKO: "false", EDISON_IIKO_API_LOGIN: "real-login-123" },
      "2026-06-03",
    );
    expect(cfg.mode).toBe("real");
    if (cfg.mode === "real") {
      expect(cfg.apiLogin).toBe("real-login-123");
      expect(cfg.organizationId).toBe("edison-org");
      // real client uses the actual current date, not the demo anchor
      expect(cfg.today).toBe("2026-06-03");
    }
  });

  test("falls back to mock when real requested but apiLogin missing", () => {
    const cfg = resolveIikoClientConfig(
      venue,
      { USE_MOCK_IIKO: "false" },
      "2026-06-03",
    );
    expect(cfg.mode).toBe("mock");
  });

  test("generic IIKO_API_LOGIN works for any venue when venue-specific absent", () => {
    const cfg = resolveIikoClientConfig(
      venue,
      { USE_MOCK_IIKO: "false", IIKO_API_LOGIN: "global-login" },
      "2026-06-03",
    );
    expect(cfg.mode).toBe("real");
    if (cfg.mode === "real") {
      expect(cfg.apiLogin).toBe("global-login");
    }
  });

  test("venue-specific key takes precedence over generic", () => {
    const cfg = resolveIikoClientConfig(
      venue,
      {
        USE_MOCK_IIKO: "false",
        IIKO_API_LOGIN: "global",
        EDISON_IIKO_API_LOGIN: "venue-specific",
      },
      "2026-06-03",
    );
    if (cfg.mode === "real") {
      expect(cfg.apiLogin).toBe("venue-specific");
    }
  });
});
