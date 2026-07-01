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
  "Что мне проверить сегодня утром?",
  "Почему смена могла просесть и что спросить у управляющего?",
  "Что сказать команде перед вечерней посадкой?",
  "Какие блюда поставить в фокус официантам сегодня?",
  "Где цифры выглядят странно и какой итог смены нужен?",
  "Дай одно действие на сегодня без лишней воды.",
] as const;
