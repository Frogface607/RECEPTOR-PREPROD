/**
 * OpenAI-backed chat loop for the dashboard drawer.
 *
 * The UI consumes the same NDJSON event shape as the mock chat. OpenAI only
 * chooses which analytics tool to call; all sensitive iiko data is fetched
 * server-side through the existing tool handlers.
 */

import { AI_TOOLS } from "./tools";
import type { ChatEvent, ChatTurnInput } from "./mock-chat";
import type { IikoClient } from "@/lib/iiko/types";

const OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses";
const DEFAULT_MODEL = "gpt-5.5";
const MAX_OUTPUT_TOKENS = 1200;

type OpenAIContentBlock = {
  type?: string;
  text?: string;
};

type OpenAIOutputItem = {
  type?: string;
  name?: string;
  call_id?: string;
  arguments?: string;
  content?: OpenAIContentBlock[];
};

type OpenAIResponse = {
  id?: string;
  output_text?: string;
  output?: OpenAIOutputItem[];
};

type OpenAIRequestBody = {
  model: string;
  instructions: string;
  input: unknown;
  tools?: unknown[];
  previous_response_id?: string;
  max_output_tokens: number;
};

type RuntimeTool = {
  handler: (input: unknown, client: IikoClient) => Promise<unknown>;
};

function openAIModel(): string {
  return process.env.OPENAI_MODEL?.trim() || DEFAULT_MODEL;
}

function openAIKey(): string | null {
  const key = process.env.OPENAI_API_KEY?.trim();
  return key ? key : null;
}

function systemPrompt(input: ChatTurnInput): string {
  return [
    `Ты — Receptor, AI-копайлот владельца заведения ${input.venueName}.`,
    `Тип: ${input.venueType}. Город: ${input.venueCity}.`,
    "Отвечай по-русски, коротко и управленчески: цифры, вывод, действие.",
    "Если вопрос про выручку, блюда, смены, сравнение периодов или меню — обязательно вызови подходящий инструмент.",
    "Не выдумывай метрики. Используй только данные, которые вернул инструмент.",
  ].join("\n");
}

function openAITools() {
  return AI_TOOLS.map((tool) => ({
    type: "function",
    name: tool.name,
    description: tool.description,
    parameters: tool.input_schema,
  }));
}

async function callOpenAI(body: OpenAIRequestBody): Promise<OpenAIResponse> {
  const key = openAIKey();
  if (!key) throw new Error("OPENAI_API_KEY is not set");

  const response = await fetch(OPENAI_RESPONSES_URL, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${key}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`OpenAI chat failed: HTTP ${response.status} ${detail}`);
  }

  return (await response.json()) as OpenAIResponse;
}

function extractText(response: OpenAIResponse): string {
  if (typeof response.output_text === "string") {
    return response.output_text.trim();
  }

  return (response.output ?? [])
    .flatMap((item) => item.content ?? [])
    .map((block) => block.text ?? "")
    .join("\n")
    .trim();
}

function firstFunctionCall(response: OpenAIResponse): OpenAIOutputItem | null {
  return (
    response.output?.find(
      (item) => item.type === "function_call" && item.name && item.call_id,
    ) ?? null
  );
}

function parseArgs(raw: string | undefined): Record<string, unknown> {
  if (!raw) return {};
  const parsed = JSON.parse(raw) as unknown;
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
    return {};
  }
  return parsed as Record<string, unknown>;
}

async function runToolByName(
  name: string,
  args: Record<string, unknown>,
  iikoClient: IikoClient,
): Promise<unknown> {
  switch (name) {
    case "get_revenue":
      return (AI_TOOLS[0] as RuntimeTool).handler(args, iikoClient);
    case "get_dish_statistics":
      return (AI_TOOLS[1] as RuntimeTool).handler(args, iikoClient);
    case "get_shifts":
      return (AI_TOOLS[2] as RuntimeTool).handler(args, iikoClient);
    case "compare_periods":
      return (AI_TOOLS[3] as RuntimeTool).handler(args, iikoClient);
    case "get_nomenclature_search":
      return (AI_TOOLS[4] as RuntimeTool).handler(args, iikoClient);
    default:
      throw new Error(`Unsupported OpenAI tool call: ${name}`);
  }
}

export function isOpenAIChatConfigured(): boolean {
  const key = openAIKey();
  return Boolean(key && key.startsWith("sk-"));
}

export async function* runOpenAIChatTurn(
  input: ChatTurnInput,
): AsyncGenerator<ChatEvent> {
  yield { type: "thinking", label: "Спрашиваю OpenAI и готовлю данные iiko" };

  const first = await callOpenAI({
    model: openAIModel(),
    instructions: systemPrompt(input),
    input: [{ role: "user", content: input.message }],
    tools: openAITools(),
    max_output_tokens: MAX_OUTPUT_TOKENS,
  });

  const toolCall = firstFunctionCall(first);
  if (!toolCall) {
    const text = extractText(first);
    yield {
      type: "text",
      text:
        text ||
        "Спроси про выручку, топ блюд, смены, сравнение периодов или поиск по меню.",
    };
    yield { type: "done" };
    return;
  }

  const tool = AI_TOOLS.find((candidate) => candidate.name === toolCall.name);
  if (!tool) {
    throw new Error(`Unsupported OpenAI tool call: ${toolCall.name}`);
  }

  const toolInput = parseArgs(toolCall.arguments);
  const toolOutput = await runToolByName(tool.name, toolInput, input.iikoClient);
  yield {
    type: "tool",
    tool: tool.name,
    input: toolInput,
    output: toolOutput,
  };

  const final = await callOpenAI({
    model: openAIModel(),
    instructions: systemPrompt(input),
    previous_response_id: first.id,
    input: [
      {
        type: "function_call_output",
        call_id: toolCall.call_id,
        output: JSON.stringify(toolOutput),
      },
    ],
    max_output_tokens: MAX_OUTPUT_TOKENS,
  });

  const text = extractText(final);
  yield {
    type: "text",
    text:
      text ||
      (typeof toolOutput === "object" && toolOutput && "summary" in toolOutput
        ? String(toolOutput.summary)
        : "Данные получил, но модель не вернула текстовый ответ."),
  };
  yield { type: "done" };
}
