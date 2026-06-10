import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";
import { runOpenAIChatTurn, isOpenAIChatConfigured } from "./openai-chat";
import { MockIikoClient } from "@/lib/iiko/mock-client";

const ORIGINAL_OPENAI_KEY = process.env.OPENAI_API_KEY;
const ORIGINAL_OPENAI_MODEL = process.env.OPENAI_MODEL;
const ANCHOR = "2026-05-29";

function input(message: string) {
  return {
    message,
    venueName: "Ресторан Премьера",
    venueType: "bar",
    venueCity: "Иркутск",
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
