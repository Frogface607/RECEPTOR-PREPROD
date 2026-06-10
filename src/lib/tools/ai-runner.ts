/**
 * AI runner — real model execution for the tools showcase.
 *
 * `getConfiguredAiBackend()` decides whether `/api/tools/run` calls OpenAI,
 * Anthropic, or falls back to the deterministic mock.
 *
 * OpenAI is intentionally implemented with fetch instead of the SDK so the
 * project can switch providers without adding a dependency or touching the
 * lockfile.
 */

import type { Tool } from "./catalog";

export type AiBackend = "openai" | "claude";

const PLACEHOLDERS = new Set([
  "your-key-here",
  "your_key_here",
  "changeme",
  "sk-ant-xxx",
  "sk-xxx",
  "todo",
]);

function isUsableKey(key: string): boolean {
  if (!key) return false;
  if (PLACEHOLDERS.has(key.toLowerCase())) return false;
  return true;
}

/** Prefer OpenAI when present; Anthropic remains a compatible fallback. */
export function getConfiguredAiBackend(): AiBackend | null {
  const openaiKey = (process.env.OPENAI_API_KEY ?? "").trim();
  if (isUsableKey(openaiKey) && openaiKey.startsWith("sk-")) {
    return "openai";
  }

  const anthropicKey = (process.env.ANTHROPIC_API_KEY ?? "").trim();
  if (isUsableKey(anthropicKey) && anthropicKey.startsWith("sk-ant-")) {
    return "claude";
  }

  return null;
}

/** Backward-compatible boolean used by older tests and callers. */
export function isAiConfigured(): boolean {
  return getConfiguredAiBackend() !== null;
}

const SYSTEM_PROMPT =
  "Ты — Receptor, AI-помощник ресторанного бизнеса. Отвечай по-русски, " +
  "структурно, в markdown. По делу, без воды и без маркетинговой лексики. " +
  "Выводы должны вести к действиям владельца или команды.";

const CLAUDE_MODEL = "claude-sonnet-4-6";
const OPENAI_MODEL = process.env.OPENAI_MODEL?.trim() || "gpt-5.5";
const MAX_TOKENS = 2000;

export type AiToolRunResult = {
  markdown: string;
  backend: AiBackend;
};

export async function runToolWithAi(
  tool: Tool,
  values: Record<string, string>,
): Promise<AiToolRunResult> {
  const backend = getConfiguredAiBackend();
  if (backend === "openai") {
    return { markdown: await runToolWithOpenAI(tool, values), backend };
  }
  if (backend === "claude") {
    return { markdown: await runToolWithClaude(tool, values), backend };
  }
  throw new Error("AI backend is not configured");
}

type OpenAITextBlock = { type?: string; text?: string };
type OpenAIResponse = {
  output_text?: string;
  output?: Array<{
    content?: OpenAITextBlock[];
  }>;
};

function extractOpenAIText(payload: OpenAIResponse): string {
  if (typeof payload.output_text === "string") {
    return payload.output_text.trim();
  }

  return (payload.output ?? [])
    .flatMap((item) => item.content ?? [])
    .map((block) => block.text ?? "")
    .join("\n")
    .trim();
}

export async function runToolWithOpenAI(
  tool: Tool,
  values: Record<string, string>,
): Promise<string> {
  const apiKey = process.env.OPENAI_API_KEY?.trim();
  if (!apiKey) throw new Error("OPENAI_API_KEY is not set");

  const response = await fetch("https://api.openai.com/v1/responses", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${apiKey}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: OPENAI_MODEL,
      instructions: SYSTEM_PROMPT,
      input: tool.buildPrompt(values),
      max_output_tokens: MAX_TOKENS,
    }),
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`OpenAI failed: HTTP ${response.status} ${detail}`);
  }

  const payload = (await response.json()) as OpenAIResponse;
  const text = extractOpenAIText(payload);
  if (!text) throw new Error("OpenAI returned an empty response");

  return `# ${tool.name}\n\n${text}`;
}

/**
 * Run a tool through Claude using its `buildPrompt`. Lazily imports the SDK
 * so non-AI paths stay dependency-free.
 */
export async function runToolWithClaude(
  tool: Tool,
  values: Record<string, string>,
): Promise<string> {
  const { default: Anthropic } = await import("@anthropic-ai/sdk");
  const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

  const userPrompt = tool.buildPrompt(values);

  const response = await client.messages.create({
    model: CLAUDE_MODEL,
    max_tokens: MAX_TOKENS,
    system: SYSTEM_PROMPT,
    messages: [{ role: "user", content: userPrompt }],
  });

  const text = response.content
    .map((block) => (block.type === "text" ? block.text : ""))
    .join("\n")
    .trim();

  return `# ${tool.name}\n\n${text}`;
}
