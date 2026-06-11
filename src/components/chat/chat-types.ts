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
  "Дай короткий разбор для владельца: что происходит и что делать сегодня?",
  "Где мы теряем деньги или маржу за выбранный период?",
  "Какие блюда и категории сейчас реально тянут продажи?",
  "Какие смены стоит разобрать управляющему в первую очередь?",
  "Что поставить в фокус официантам на ближайший вечер?",
  "Сформируй 3 действия на сегодня без лишней воды.",
] as const;
