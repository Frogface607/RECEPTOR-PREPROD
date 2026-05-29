import { describe, expect, test } from "vitest";
import { RmsIikoClient } from "./rms-client";

/**
 * RMS Server port is deferred to Phase 1.5. RMS is only used by chain
 * restaurants (think Edison + 4 more locations under one corporate iiko Office).
 * We have zero chain pilots in the pipeline, so porting OLAP-on-RMS is
 * effort-without-customer.
 *
 * For Phase 1 we expose the surface (the class exists, methods exist with
 * the right signatures so the facade compiles), but every method throws
 * a clear deferral error.
 */

const HOST = "edison-bar.iiko.it";
const LOGIN = "Sergey";
const PASSWORD = "secret";
const ANCHOR = "2026-05-29";

describe("RmsIikoClient — all methods deferred to Phase 1.5", () => {
  const client = new RmsIikoClient({
    host: HOST,
    login: LOGIN,
    password: PASSWORD,
    today: ANCHOR,
  });

  test.each([
    ["getRevenueSummary", () => client.getRevenueSummary({ type: "TODAY" })],
    [
      "getDishStatistics",
      () => client.getDishStatistics({ type: "TODAY" }, 10),
    ],
    [
      "getCategoryStatistics",
      () => client.getCategoryStatistics({ type: "TODAY" }),
    ],
    ["getShifts", () => client.getShifts({ type: "TODAY" })],
    ["searchNomenclature", () => client.searchNomenclature("burger")],
  ])("%s throws explicit deferral error", async (_label, call) => {
    await expect(call()).rejects.toThrow(/RMS|not yet implemented|deferred/i);
  });

  test("constructor stores credentials but does not authenticate eagerly", () => {
    // No exception should escape construction even with bad creds — we
    // defer all network I/O until a method is invoked.
    expect(() => new RmsIikoClient({
      host: HOST,
      login: LOGIN,
      password: PASSWORD,
      today: ANCHOR,
    })).not.toThrow();
  });
});
