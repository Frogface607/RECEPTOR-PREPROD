/**
 * AI runner — real Claude execution for the tools showcase.
 *
 * `isAiConfigured()` decides whether `/api/tools/run` calls Claude or falls
 * back to the deterministic mock. The Anthropic SDK is imported lazily so the
 * mock path (and the test suite) never needs the dependency loaded or a key.
 *
 * When Босс pastes `ANTHROPIC_API_KEY` into env, the showcase goes live with
 * zero code change — the route already branches on `isAiConfigured()`.
 */

import type { Tool } from "./catalog";

const PLACEHOLDERS = new Set([
  "your-key-here",
  "your_key_here",
  "changeme",
  "sk-ant-xxx",
  "todo",
]);

/** True only for a plausibly-real Anthropic key. */
export function isAiConfigured(): boolean {
  const key = (process.env.ANTHROPIC_API_KEY ?? "").trim();
  if (!key) return false;
  if (PLACEHOLDERS.has(key.toLowerCase())) return false;
  // Real Anthropic keys start with "sk-ant-".
  return key.startsWith("sk-ant-");
}

const SYSTEM_PROMPT =
  "Ты — Receptor, AI-помощник ресторанного бизнеса. Отвечай по-русски, " +
  "структурно, в markdown. По делу, без воды и без маркетинговой лексики. " +
  "Выводы должны вести к действиям владельца или команды.";

const MODEL = "claude-sonnet-4-6";
const MAX_TOKENS = 2000;

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
    model: MODEL,
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
