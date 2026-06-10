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
  "Что произошло с выручкой за прошлую неделю?",
  "Какие блюда дали максимум денег и порций?",
  "Какая категория меню сейчас тянет зал?",
  "Какие смены стоит проверить в первую очередь?",
  "Что сделать сегодня, чтобы не потерять вечер?",
] as const;
