import { afterEach, describe, expect, test, vi } from "vitest";
import { researchVenue } from "./research";

afterEach(() => {
  vi.unstubAllEnvs();
});

describe("researchVenue", () => {
  test("falls back to a manual profile when no AI key is configured", async () => {
    vi.stubEnv("OPENAI_API_KEY", "");
    vi.stubEnv("OPENROUTER_API_KEY", "");

    const result = await researchVenue({
      name: "Север",
      city: "Иркутск",
      type: "restaurant",
      ownerContext: "Семейный ресторан с сильной кухней и проблемой сервиса.",
    });

    expect(result.provider).toBe("fallback");
    expect(result.profile.researchStatus).toBe("manual");
    expect(result.profile.positioning).toContain("Семейный ресторан");
  });
});
