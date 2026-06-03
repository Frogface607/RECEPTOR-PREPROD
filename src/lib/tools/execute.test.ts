import { describe, expect, test, vi } from "vitest";
import { executeTool } from "./execute";
import { getToolById } from "./catalog";

const tool = getToolById("promo-idea")!;
const values = { venue: "Кофейня, утренний трафик" };

describe("executeTool — backend selection + fallback", () => {
  test("uses mock when AI is not configured", async () => {
    const res = await executeTool(tool, values, {
      aiConfigured: () => false,
      callClaude: async () => "SHOULD NOT BE CALLED",
    });
    expect(res.backend).toBe("mock");
    expect(res.markdown).toContain("# Идея акции");
  });

  test("uses Claude when configured and the call succeeds", async () => {
    const res = await executeTool(tool, values, {
      aiConfigured: () => true,
      callClaude: async () => "# Идея акции\n\nЖивой ответ Claude",
    });
    expect(res.backend).toBe("claude");
    expect(res.markdown).toContain("Живой ответ Claude");
  });

  test("falls back to mock when Claude throws (credits/rate-limit/network)", async () => {
    const callClaude = vi.fn(async () => {
      throw new Error("credit balance is too low");
    });
    const res = await executeTool(tool, values, {
      aiConfigured: () => true,
      callClaude,
    });
    expect(callClaude).toHaveBeenCalledOnce();
    expect(res.backend).toBe("mock");
    expect(res.markdown).toContain("# Идея акции");
  });

  test("still validates required fields before any backend runs", async () => {
    await expect(
      executeTool(tool, {}, {
        aiConfigured: () => true,
        callClaude: async () => "x",
      }),
    ).rejects.toThrow(/required|обязател/i);
  });
});
