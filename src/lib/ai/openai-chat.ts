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
import { formatVenueProfileForPrompt } from "@/lib/venues/intelligence";
import { formatContextAnswersForPrompt } from "@/lib/venues/context-questionnaire";

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
  const dataModeNote =
    input.dataMode === "mock"
      ? "Важно: профиль заведения может быть реальным, но BI/iiko-цифры сейчас тестовые sandbox-данные до подключения активного iiko Cloud API. Не выдавай их за реальные показатели заведения."
      : "BI/iiko-цифры получены из подключенного источника данных заведения.";

  return [
    `Ты — Receptor, AI-помощник владельца заведения ${input.venueName}.`,
    `Тип: ${input.venueType}. Город: ${input.venueCity}.`,
    dataModeNote,
    "Профиль заведения:",
    formatVenueProfileForPrompt(input.venueProfile),
    input.venueContext && Object.keys(input.venueContext).length > 0
      ? ["Контекстная анкета ресторана:", formatContextAnswersForPrompt(input.venueContext)].join("\n")
      : "Контекстная анкета ресторана: пока не заполнена.",
    "Отвечай по-русски, коротко и управленчески: факт, вывод, действие.",
    "Если вопрос про выручку, блюда, смены, сравнение периодов или меню — обязательно вызови подходящий инструмент.",
    "Если вопрос про общий разбор, совет владельцу, просадку, риски или что делать сегодня — используй get_owner_brief.",
    "Не выдумывай метрики. Используй только данные, которые вернул инструмент.",
    "Если данных не хватает, явно скажи, какой доступ или отчёт нужен.",
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
  const tool = AI_TOOLS.find((candidate) => candidate.name === name);
  if (!tool) {
    throw new Error(`Unsupported OpenAI tool call: ${name}`);
  }
  return (tool as RuntimeTool).handler(args, iikoClient);
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
