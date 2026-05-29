/**
 * Shared chat types — mirror the server-side `ChatEvent` shape so the UI
 * can render incoming NDJSON events directly.
 */
export type ChatEvent =
  | { type: "thinking"; label: string }
  | {
      type: "tool";
      tool: string;
      input: Record<string, unknown>;
      output: unknown;
    }
  | { type: "text"; text: string }
  | { type: "done" }
  | { type: "error"; message: string };

export type ChatMessage =
  | { role: "user"; id: string; text: string }
  | {
      role: "assistant";
      id: string;
      text: string;
      toolCalls: Array<{ tool: string; input: Record<string, unknown> }>;
      isStreaming: boolean;
    };

export const SUGGESTED_PROMPTS = [
  "Какая выручка за прошлую неделю?",
  "Покажи топ-5 блюд за месяц",
  "Сравни прошлую и текущую неделю",
  "Сколько сделали смены вчера?",
  "Найди в меню бургер нечто",
] as const;
