import { describe, expect, test } from "vitest";
import { buildDailyBrief, renderDailyBriefText } from "./daily-brief";
import { MockIikoClient } from "@/lib/iiko/mock-client";

describe("buildDailyBrief", () => {
  test("builds a deterministic owner brief from iiko data", async () => {
    const brief = await buildDailyBrief(
      new MockIikoClient({ today: "2026-05-29" }),
      "LAST_WEEK",
    );

    expect(brief.period).toBe("LAST_WEEK");
    expect(brief.comparisonPeriod).toBe("LAST_MONTH");
    expect(brief.headline).toMatch(/Выручка/);
    expect(brief.highlights).toHaveLength(3);
    expect(brief.actions).toHaveLength(3);
    expect(brief.revenue.current).toBeGreaterThan(0);
  });

  test("renders a plain-text brief for delivery channels", async () => {
    const brief = await buildDailyBrief(
      new MockIikoClient({ today: "2026-05-29" }),
      "YESTERDAY",
    );

    const text = renderDailyBriefText(brief, {
      venueName: "Edison",
      generatedAt: new Date("2026-05-30T06:00:00.000Z"),
    });

    expect(text).toContain("Receptor Daily Brief: Edison");
    expect(text).toContain("Главное:");
    expect(text).toContain("Что сделать сегодня:");
    expect(text).toContain(brief.headline);
  });
});
