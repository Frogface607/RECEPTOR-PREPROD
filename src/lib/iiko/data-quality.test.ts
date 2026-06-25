import { describe, expect, test } from "vitest";
import { buildRevenueDataQuality } from "./data-quality";
import type { RevenueSummary } from "./models";

const baseSummary: RevenueSummary = {
  revenue: 300000,
  averageCheck: 1500,
  itemsSold: 200,
  uniqueDishes: 12,
  points: [
    { date: "2026-05-01", revenue: 100000 },
    { date: "2026-05-02", revenue: 100000 },
    { date: "2026-05-03", revenue: 100000 },
  ],
};

describe("buildRevenueDataQuality", () => {
  test("marks a fully covered live period as ok", () => {
    const quality = buildRevenueDataQuality(
      { type: "CUSTOM", from: "2026-05-01", to: "2026-05-03" },
      baseSummary,
      { today: "2026-05-10", dataMode: "live" },
    );

    expect(quality.status).toBe("ok");
    expect(quality.activeDays).toBe(3);
    expect(quality.requestedDays).toBe(3);
    expect(quality.coveragePct).toBe(100);
    expect(quality.warnings).toEqual([]);
  });

  test("warns when a long period has incomplete live coverage", () => {
    const quality = buildRevenueDataQuality(
      { type: "CUSTOM", from: "2026-01-01", to: "2026-01-10" },
      baseSummary,
      { today: "2026-05-10", dataMode: "live" },
    );

    expect(quality.status).toBe("risk");
    expect(quality.activeDays).toBe(0);
    expect(quality.requestedDays).toBe(10);
    expect(quality.warnings[0]).toContain("нет продаж");
  });

  test("flags partial history without hiding the numbers", () => {
    const quality = buildRevenueDataQuality(
      { type: "CUSTOM", from: "2026-05-01", to: "2026-05-10" },
      baseSummary,
      { today: "2026-05-10", dataMode: "live" },
    );

    expect(quality.status).toBe("risk");
    expect(quality.activeDays).toBe(3);
    expect(quality.missingDays).toBe(7);
    expect(quality.coveragePct).toBe(30);
    expect(quality.summary).toBe("3 из 10 дней с продажами (30%)");
  });

  test("marks mock data as watch even with full coverage", () => {
    const quality = buildRevenueDataQuality(
      { type: "CUSTOM", from: "2026-05-01", to: "2026-05-03" },
      baseSummary,
      { today: "2026-05-10", dataMode: "mock" },
    );

    expect(quality.status).toBe("watch");
    expect(quality.warnings[0]).toContain("демо-данные");
  });
});
