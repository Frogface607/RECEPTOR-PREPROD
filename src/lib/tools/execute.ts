/**
 * Tool execution orchestrator with graceful degradation.
 *
 * Decides the backend (OpenAI/Claude vs mock) and — critically for a live demo —
 * falls back to the deterministic mock if a real model call fails for any
 * reason (low credits, rate limit, network blip). The user always gets a
 * useful result; they never see a red API error mid-presentation.
 *
 * Dependencies are injected so this is unit-testable without external API keys.
 */

import { runToolMock, validateToolInput } from "./mock-runner";
import { getConfiguredAiBackend, runToolWithAi } from "./ai-runner";
import type { AiBackend, AiToolRunResult } from "./ai-runner";
import type { Tool } from "./catalog";
import type { VenueIntelligenceProfile } from "@/lib/venues/intelligence";

export type ToolResult = {
  markdown: string;
  backend: AiBackend | "mock";
};

export type ExecuteDeps = {
  aiBackend: () => AiBackend | null;
  callAi: (
    tool: Tool,
    values: Record<string, string>,
    venueProfile?: VenueIntelligenceProfile,
  ) => Promise<AiToolRunResult>;
};

const DEFAULT_DEPS: ExecuteDeps = {
  aiBackend: getConfiguredAiBackend,
  callAi: runToolWithAi,
};

export async function executeTool(
  tool: Tool,
  values: Record<string, string>,
  venueProfileOrDeps?: VenueIntelligenceProfile | ExecuteDeps,
  maybeDeps?: ExecuteDeps,
): Promise<ToolResult> {
  const hasDepsAsThirdArg =
    venueProfileOrDeps &&
    "aiBackend" in venueProfileOrDeps &&
    "callAi" in venueProfileOrDeps;
  const venueProfile = hasDepsAsThirdArg
    ? undefined
    : (venueProfileOrDeps as VenueIntelligenceProfile | undefined);
  const deps = hasDepsAsThirdArg
    ? (venueProfileOrDeps as ExecuteDeps)
    : (maybeDeps ?? DEFAULT_DEPS);

  // Validate first — same error contract regardless of backend.
  const validation = validateToolInput(tool, values);
  if (!validation.ok) {
    throw new Error(
      `required fields missing (обязательные поля): ${validation.missing.join(", ")}`,
    );
  }

  const backend = deps.aiBackend();
  if (backend) {
    try {
      return await deps.callAi(tool, values, venueProfile);
    } catch (err) {
      // Demo-safe: never surface the AI error — degrade to the mock preview.
      console.warn(
        `[tools] ${backend} failed for "${tool.id}", falling back to mock:`,
        err instanceof Error ? err.message : err,
      );
    }
  }

  return { markdown: runToolMock(tool.id, values), backend: "mock" };
}
