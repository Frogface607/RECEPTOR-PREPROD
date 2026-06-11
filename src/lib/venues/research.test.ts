import { afterEach, describe, expect, test, vi } from "vitest";
import { researchVenue } from "./research";

afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
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

  test("uses OpenAI web search when an OpenAI key is configured", async () => {
    vi.stubEnv("OPENAI_API_KEY", "sk-test");
    vi.stubEnv("OPENROUTER_API_KEY", "");

    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        output_text: JSON.stringify({
          format: "ресторан",
          positioning: "Ресторан с авторской кухней и сильной вечерней посадкой.",
          audience: ["гости на ужин"],
          strengths: ["сильная кухня"],
          guestPains: ["ожидание"],
          ownerGoals: ["системность"],
          operatingRisks: ["просадка среднего чека"],
          decisionRules: ["отделять факт от гипотезы"],
          recommendedFocus: ["анализ продаж по категориям"],
          researchStatus: "researched",
        }),
      }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const result = await researchVenue({
      name: "Премьера",
      city: "Иркутск",
      type: "restaurant",
    });

    const body = JSON.parse(String(fetchMock.mock.calls[0]?.[1]?.body)) as {
      tools?: Array<{ type?: string; search_context_size?: string }>;
      tool_choice?: string;
    };

    expect(result.provider).toBe("openai");
    expect(result.profile.researchStatus).toBe("researched");
    expect(result.summary).toContain("web research");
    expect(body.tools?.[0]).toMatchObject({
      type: "web_search",
      search_context_size: "high",
    });
    expect(body.tool_choice).toBe("required");
  });
});
