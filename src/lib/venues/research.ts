import {
  DEFAULT_VENUE_INTELLIGENCE,
  normalizeVenueProfile,
  type VenueIntelligenceProfile,
} from "./intelligence";

const OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses";
const OPENROUTER_CHAT_URL = "https://openrouter.ai/api/v1/chat/completions";
const DEFAULT_OPENAI_MODEL = "gpt-5.5";
const DEFAULT_OPENROUTER_MODEL = "perplexity/sonar-pro";
const RESEARCH_FETCH_TIMEOUT_MS = 18_000;

export type VenueResearchInput = {
  name: string;
  city: string;
  type?: string;
  ownerContext?: string;
};

export type VenueResearchResult = {
  profile: VenueIntelligenceProfile;
  provider: "openai" | "openrouter" | "fallback";
  summary: string;
  diagnostics?: string[];
};

type OpenAIResponse = {
  output_text?: string;
  output?: Array<{ content?: Array<{ text?: string }> }>;
};

type OpenRouterResponse = {
  choices?: Array<{ message?: { content?: string } }>;
};

function openAIKey(): string | null {
  const key = process.env.OPENAI_API_KEY?.trim();
  return key ? key : null;
}

function openRouterKey(): string | null {
  const key = process.env.OPENROUTER_API_KEY?.trim();
  return key ? key : null;
}

function researchInstructions(): string {
  return `Ты — ресторанный бизнес-аналитик Receptor.

Задача: изучить заведение и собрать профиль для BI + AI-помощника владельца.
Обязательно используй web search, если он доступен: сайт, соцсети, карты,
отзывы, меню, позиционирование, новости и упоминания. Если публичных данных
мало, честно дополни профиль по названию, городу, типу и контексту владельца.

Верни только JSON:
{
  "format": "формат заведения",
  "positioning": "позиционирование и концепция",
  "audience": ["сегмент гостей"],
  "strengths": ["сильная сторона"],
  "guestPains": ["частая боль гостей из отзывов или типовая боль"],
  "ownerGoals": ["что важно владельцу"],
  "operatingRisks": ["операционный риск"],
  "decisionRules": ["как AI-помощник должен делать выводы"],
  "recommendedFocus": ["что анализировать в первую очередь"],
  "researchStatus": "researched"
}

Правила:
- Не выдумывай точные рейтинги и факты, если не нашёл их уверенно.
- Не называй источник, если не уверен, что видел его в поиске.
- Если публичных данных мало, делай аккуратный профиль по названию/городу/контексту владельца.
- Пиши по-русски, конкретно для ресторатора.`;
}

function userPrompt(input: VenueResearchInput): string {
  return [
    `Заведение: ${input.name}`,
    `Город: ${input.city || "не указан"}`,
    `Тип: ${input.type || "restaurant"}`,
    input.ownerContext
      ? `Контекст владельца, концепция, боли: ${input.ownerContext}`
      : "",
  ]
    .filter(Boolean)
    .join("\n");
}

function extractJson(text: string): unknown {
  const match = text.match(/\{[\s\S]*\}/);
  if (!match) throw new Error("research JSON not found");
  return JSON.parse(match[0]) as unknown;
}

function researchFetchSignal(): AbortSignal {
  return AbortSignal.timeout(RESEARCH_FETCH_TIMEOUT_MS);
}

function fallbackProfile(input: VenueResearchInput): VenueIntelligenceProfile {
  const typeLabel =
    input.type === "bar"
      ? "бар"
      : input.type === "cafe"
        ? "кафе"
        : input.type === "coffee"
          ? "кофейня"
          : input.type === "chain"
            ? "сеть заведений"
            : "ресторан";

  return {
    ...DEFAULT_VENUE_INTELLIGENCE,
    format: `${typeLabel} в городе ${input.city || "не указан"}`,
    positioning: input.ownerContext?.trim()
      ? input.ownerContext.trim()
      : `Заведение «${input.name}» с фокусом на управляемость, продажи, сервис и повторные визиты.`,
    researchStatus: "manual",
  };
}

function extractOpenAIText(response: OpenAIResponse): string {
  if (response.output_text) return response.output_text;
  return (response.output ?? [])
    .flatMap((item) => item.content ?? [])
    .map((block) => block.text ?? "")
    .join("\n");
}

async function researchWithOpenAI(
  input: VenueResearchInput,
  options: { webSearch: boolean },
): Promise<VenueIntelligenceProfile> {
  const key = openAIKey();
  if (!key) throw new Error("OPENAI_API_KEY is not set");

  const body: Record<string, unknown> = {
    model: process.env.OPENAI_RESEARCH_MODEL?.trim() || DEFAULT_OPENAI_MODEL,
    instructions: researchInstructions(),
    input: [{ role: "user", content: userPrompt(input) }],
    max_output_tokens: 2200,
  };

  if (options.webSearch) {
    body.tools = [{ type: "web_search", search_context_size: "high" }];
    body.tool_choice = "required";
  }

  const response = await fetch(OPENAI_RESPONSES_URL, {
    method: "POST",
    signal: researchFetchSignal(),
    headers: {
      Authorization: `Bearer ${key}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    throw new Error(`OpenAI research failed: HTTP ${response.status}`);
  }

  const data = (await response.json()) as OpenAIResponse;
  return normalizeVenueProfile(extractJson(extractOpenAIText(data)));
}

async function researchWithOpenRouter(
  input: VenueResearchInput,
): Promise<VenueIntelligenceProfile> {
  const key = openRouterKey();
  if (!key) throw new Error("OPENROUTER_API_KEY is not set");

  const response = await fetch(OPENROUTER_CHAT_URL, {
    method: "POST",
    signal: researchFetchSignal(),
    headers: {
      Authorization: `Bearer ${key}`,
      "Content-Type": "application/json",
      "HTTP-Referer": process.env.NEXT_PUBLIC_APP_URL || "https://receptor.ai",
      "X-Title": "Receptor",
    },
    body: JSON.stringify({
      model: process.env.OPENROUTER_RESEARCH_MODEL?.trim() || DEFAULT_OPENROUTER_MODEL,
      messages: [
        { role: "system", content: researchInstructions() },
        { role: "user", content: userPrompt(input) },
      ],
      temperature: 0.25,
      max_tokens: 1800,
    }),
  });

  if (!response.ok) {
    throw new Error(`OpenRouter research failed: HTTP ${response.status}`);
  }

  const data = (await response.json()) as OpenRouterResponse;
  const text = data.choices?.[0]?.message?.content ?? "";
  return normalizeVenueProfile(extractJson(text));
}

export async function researchVenue(
  input: VenueResearchInput,
): Promise<VenueResearchResult> {
  const diagnostics: string[] = [];

  if (openRouterKey()) {
    try {
      const profile = await researchWithOpenRouter(input);
      return {
        profile: { ...profile, researchStatus: "researched" },
        provider: "openrouter",
        summary: "Профиль собран через web research.",
        diagnostics,
      };
    } catch (err) {
      console.warn("[venue-research] OpenRouter failed:", err);
      diagnostics.push(formatResearchFailure("OpenRouter", err));
    }
  }

  if (openAIKey()) {
    try {
      const profile = await researchWithOpenAI(input, { webSearch: true });
      return {
        profile: { ...profile, researchStatus: "researched" },
        provider: "openai",
        summary: "Профиль собран через OpenAI web research.",
        diagnostics,
      };
    } catch (err) {
      console.warn("[venue-research] OpenAI web research failed:", err);
      diagnostics.push(formatResearchFailure("OpenAI web research", err));
    }
  }

  if (openAIKey()) {
    try {
      const profile = await researchWithOpenAI(input, { webSearch: false });
      return {
        profile: { ...profile, researchStatus: "manual" },
        provider: "openai",
        summary: "Web research не сработал, собран черновик через OpenAI по анкете.",
        diagnostics,
      };
    } catch (err) {
      console.warn("[venue-research] OpenAI fallback failed:", err);
      diagnostics.push(formatResearchFailure("OpenAI profile draft", err));
    }
  }

  const noAiKey = !openAIKey() && !openRouterKey();
  return {
    profile: fallbackProfile(input),
    provider: "fallback",
    summary: noAiKey
      ? "AI-ключ для исследования не настроен. Добавьте OPENAI_API_KEY в Vercel, чтобы Receptor искал публичный контекст."
      : "AI-исследование не сработало. Профиль создан из анкеты, его можно уточнить вручную.",
    diagnostics,
  };
}

function formatResearchFailure(provider: string, err: unknown): string {
  const message = err instanceof Error ? err.message : String(err);
  return `${provider}: ${message}`;
}
