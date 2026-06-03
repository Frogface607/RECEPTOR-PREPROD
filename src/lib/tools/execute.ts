/**
 * Tool execution orchestrator with graceful degradation.
 *
 * Decides the backend (Claude vs mock) and — critically for a live demo —
 * falls back to the deterministic mock if a real Claude call fails for any
 * reason (low credits, rate limit, network blip). The user always gets a
 * useful result; they never see a red API error mid-presentation.
 *
 * Dependencies are injected so this is unit-testable without the Anthropic
 * SDK or a key. The route passes the real wiring.
 */

import { runToolMock, validateToolInput } from "./mock-runner";
import { isAiConfigured } from "./ai-runner";
import { runToolWithClaude } from "./ai-runner";
import type { Tool } from "./catalog";

export type ToolResult = {
  markdown: string;
  backend: "claude" | "mock";
};

export type ExecuteDeps = {
  aiConfigured: () => boolean;
  callClaude: (tool: Tool, values: Record<string, string>) => Promise<string>;
};

const DEFAULT_DEPS: ExecuteDeps = {
  aiConfigured: isAiConfigured,
  callClaude: runToolWithClaude,
};

export async function executeTool(
  tool: Tool,
  values: Record<string, string>,
  deps: ExecuteDeps = DEFAULT_DEPS,
): Promise<ToolResult> {
  // Validate first — same error contract regardless of backend.
  const validation = validateToolInput(tool, values);
  if (!validation.ok) {
    throw new Error(
      `required fields missing (обязательные поля): ${validation.missing.join(", ")}`,
    );
  }

  if (deps.aiConfigured()) {
    try {
      const markdown = await deps.callClaude(tool, values);
      return { markdown, backend: "claude" };
    } catch (err) {
      // Demo-safe: never surface the AI error — degrade to the mock preview.
      console.warn(
        `[tools] Claude failed for "${tool.id}", falling back to mock:`,
        err instanceof Error ? err.message : err,
      );
    }
  }

  return { markdown: runToolMock(tool.id, values), backend: "mock" };
}
