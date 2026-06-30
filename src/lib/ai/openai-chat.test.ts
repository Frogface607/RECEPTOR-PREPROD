import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";
import { runOpenAIChatTurn, isOpenAIChatConfigured } from "./openai-chat";
import { MockIikoClient } from "@/lib/iiko/mock-client";
import { DEFAULT_VENUE_INTELLIGENCE } from "@/lib/venues/intelligence";
import { DEMO_CONTEXT_ANSWERS } from "@/lib/venues/context-questionnaire";
import type { RestaurantAdvisorMemory } from "./restaurant-memory";

const ORIGINAL_OPENAI_KEY = process.env.OPENAI_API_KEY;
const ORIGINAL_OPENAI_MODEL = process.env.OPENAI_MODEL;
const ANCHOR = "2026-05-29";
const RESTAURANT_MEMORY: RestaurantAdvisorMemory = {
  teamSummary: "2 активных сотрудников",
  fieldSummary: "Итог смены: ливень, отменили 3 брони после 19:00",
  fieldSignals: ["Погода и внешний контекст: ливень"],
  openTasks: ["Проверить стоп-лист — до 17:00"],
  learningGaps: ["Алина: Как рекомендовать блюдо без давления"],
};

function input(message: string) {
  return {
    message,
    venueName: "Тестовый ресторан",
    venueType: "bar",
    venueCity: "Иркутск",
    venueProfile: DEFAULT_VENUE_INTELLIGENCE,
    venueContext: DEMO_CONTEXT_ANSWERS,
    restaurantMemory: RESTAURANT_MEMORY,
    iikoClient: new MockIikoClient({ today: ANCHOR }),
  };
}

async function collect(message: string) {
  const events = [];
  for await (const event of runOpenAIChatTurn(input(message))) {
    events.push(event);
  }
  return events;
}

beforeEach(() => {
  process.env.OPENAI_API_KEY = "sk-proj-test";
  delete process.env.OPENAI_MODEL;
});

afterEach(() => {
  vi.restoreAllMocks();
  if (ORIGINAL_OPENAI_KEY === undefined) delete process.env.OPENAI_API_KEY;
  else process.env.OPENAI_API_KEY = ORIGINAL_OPENAI_KEY;

  if (ORIGINAL_OPENAI_MODEL === undefined) delete process.env.OPENAI_MODEL;
  else process.env.OPENAI_MODEL = ORIGINAL_OPENAI_MODEL;
});

describe("runOpenAIChatTurn", () => {
  test("false when OPENAI_API_KEY is absent", () => {
    delete process.env.OPENAI_API_KEY;
    expect(isOpenAIChatConfigured()).toBe(false);
  });

  test("runs an OpenAI-selected analytics tool and returns final text", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            id: "resp_1",
            output: [
              {
                type: "function_call",
                name: "get_revenue",
                call_id: "call_1",
                arguments: JSON.stringify({ period: "LAST_WEEK" }),
              },
            ],
          }),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            output_text: "Выручка за прошлую неделю сильная. Проверь пятницу.",
          }),
          { status: 200 },
        ),
      );

    const events = await collect("Какая выручка за прошлую неделю?");
    const tool = events.find((event) => event.type === "tool");
    const text = events.find((event) => event.type === "text");

    expect(fetchMock).toHaveBeenCalledTimes(2);
    const firstBody = JSON.parse(
      String(fetchMock.mock.calls[0]?.[1]?.body),
    ) as { instructions?: string };
    expect(firstBody.instructions).toContain("Контекстная анкета ресторана");
    expect(firstBody.instructions).toContain("POS/back-office: iiko");
    expect(firstBody.instructions).toContain("Ты не отчетчик");
    expect(firstBody.instructions).toContain("Память ресторана");
    expect(firstBody.instructions).toContain("Итог смены: ливень");
    expect(firstBody.instructions).toContain("Учебные пробелы");
    expect(firstBody.instructions).toContain("операционный ритм Receptor");
    expect(firstBody.instructions).toContain("короткий итог смены");
    expect(tool?.tool).toBe("get_revenue");
    expect(text?.text).toContain("Выручка");
    expect(events.at(-1)?.type).toBe("done");
  });

  test("can answer directly when OpenAI does not request a tool", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          output_text: "Спроси меня про выручку, блюда, смены или меню.",
        }),
        { status: 200 },
      ),
    );

    const events = await collect("Привет");

    expect(events.some((event) => event.type === "tool")).toBe(false);
    expect(events.find((event) => event.type === "text")?.text).toContain(
      "выручку",
    );
    expect(events.at(-1)?.type).toBe("done");
  });
});
