import { describe, expect, test, beforeEach, afterEach } from "vitest";
import { getIikoClient } from "./client";
import { MockIikoClient } from "./mock-client";
import { CloudIikoClient } from "./cloud-client";
import { RmsIikoClient } from "./rms-client";

const ORIGINAL_FLAG = process.env.USE_MOCK_IIKO;

beforeEach(() => {
  delete process.env.USE_MOCK_IIKO;
});

afterEach(() => {
  if (ORIGINAL_FLAG === undefined) {
    delete process.env.USE_MOCK_IIKO;
  } else {
    process.env.USE_MOCK_IIKO = ORIGINAL_FLAG;
  }
});

describe("getIikoClient facade", () => {
  test("USE_MOCK_IIKO=true → returns MockIikoClient regardless of channel", () => {
    process.env.USE_MOCK_IIKO = "true";
    const cloud = getIikoClient({
      channel: "cloud",
      apiLogin: "x",
      organizationId: "o",
      today: "2026-05-29",
    });
    const rms = getIikoClient({
      channel: "rms",
      host: "h",
      login: "l",
      password: "p",
      today: "2026-05-29",
    });
    expect(cloud).toBeInstanceOf(MockIikoClient);
    expect(rms).toBeInstanceOf(MockIikoClient);
  });

  test("when flag absent → defaults to mock (safe default for Phase 0–3)", () => {
    const c = getIikoClient({
      channel: "cloud",
      apiLogin: "x",
      organizationId: "o",
      today: "2026-05-29",
    });
    expect(c).toBeInstanceOf(MockIikoClient);
  });

  test("USE_MOCK_IIKO=false + channel=cloud → returns CloudIikoClient", () => {
    process.env.USE_MOCK_IIKO = "false";
    const c = getIikoClient({
      channel: "cloud",
      apiLogin: "x",
      organizationId: "o",
      today: "2026-05-29",
    });
    expect(c).toBeInstanceOf(CloudIikoClient);
  });

  test("USE_MOCK_IIKO=false + channel=rms → returns RmsIikoClient", () => {
    process.env.USE_MOCK_IIKO = "false";
    const c = getIikoClient({
      channel: "rms",
      host: "h",
      login: "l",
      password: "p",
      today: "2026-05-29",
    });
    expect(c).toBeInstanceOf(RmsIikoClient);
  });

  test("mock client returned by facade still satisfies IikoClient contract", async () => {
    process.env.USE_MOCK_IIKO = "true";
    const c = getIikoClient({
      channel: "cloud",
      apiLogin: "x",
      organizationId: "o",
      today: "2026-05-29",
    });
    const summary = await c.getRevenueSummary({ type: "TODAY" });
    expect(summary.points).toHaveLength(1);
  });
});
