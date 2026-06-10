import { describe, expect, test, vi } from "vitest";
import { executeTool } from "./execute";
import { getToolById } from "./catalog";

const tool = getToolById("promo-idea")!;
const values = { venue: "Кофейня, утренний трафик" };

describe("executeTool — backend selection + fallback", () => {
  test("uses mock when AI is not configured", async () => {
    const res = await executeTool(tool, values, {
      aiBackend: () => null,
      callAi: async () => ({
        markdown: "SHOULD NOT BE CALLED",
        backend: "openai",
      }),
    });
    expect(res.backend).toBe("mock");
    expect(res.markdown).toContain("# Идея акции");
  });

  test("uses OpenAI when configured and the call succeeds", async () => {
    const res = await executeTool(tool, values, {
      aiBackend: () => "openai",
      callAi: async () => ({
        markdown: "# Идея акции\n\nЖивой ответ OpenAI",
        backend: "openai",
      }),
    });
    expect(res.backend).toBe("openai");
    expect(res.markdown).toContain("Живой ответ OpenAI");
  });

  test("falls back to mock when the configured AI throws (credits/rate-limit/network)", async () => {
    const callAi = vi.fn(async () => {
      throw new Error("credit balance is too low");
    });
    const res = await executeTool(tool, values, {
      aiBackend: () => "claude",
      callAi,
    });
    expect(callAi).toHaveBeenCalledOnce();
    expect(res.backend).toBe("mock");
    expect(res.markdown).toContain("# Идея акции");
  });

  test("still validates required fields before any backend runs", async () => {
    await expect(
      executeTool(tool, {}, {
        aiBackend: () => "openai",
        callAi: async () => ({ markdown: "x", backend: "openai" }),
      }),
    ).rejects.toThrow(/required|обязател/i);
  });
});
