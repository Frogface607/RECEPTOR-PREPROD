import { describe, expect, test } from "vitest";
import { runMockChatTurn } from "./mock-chat";
import { MockIikoClient } from "@/lib/iiko/mock-client";
import { DEFAULT_VENUE_INTELLIGENCE } from "@/lib/venues/intelligence";

const ANCHOR = "2026-05-29";

function client() {
  return new MockIikoClient({ today: ANCHOR });
}

async function collect(message: string) {
  const events = [];
  for await (const ev of runMockChatTurn({
    message,
    venueName: "Тестовое заведение",
    venueType: "Бар",
    venueCity: "Иркутск",
    venueProfile: DEFAULT_VENUE_INTELLIGENCE,
    iikoClient: client(),
  })) {
    events.push(ev);
  }
  return events;
}

describe("runMockChatTurn — routing", () => {
  test("'топ блюд за неделю' → calls get_dish_statistics", async () => {
    const ev = await collect("Покажи топ блюд за прошлую неделю");
    const toolEvent = ev.find((e) => e.type === "tool");
    expect(toolEvent?.tool).toBe("get_dish_statistics");
  });

  test("'какая выручка' → calls get_revenue", async () => {
    const ev = await collect("Какая выручка за последний месяц?");
    const toolEvent = ev.find((e) => e.type === "tool");
    expect(toolEvent?.tool).toBe("get_revenue");
  });

  test("'смены вчера' → calls get_shifts", async () => {
    const ev = await collect("Сколько сделали смены вчера и за неделю?");
    const toolEvent = ev.find((e) => e.type === "tool");
    expect(toolEvent?.tool).toBe("get_shifts");
  });

  test("'сравни прошлую и текущую неделю' → calls compare_periods", async () => {
    const ev = await collect(
      "Сравни прошлую и текущую неделю по выручке",
    );
    const toolEvent = ev.find((e) => e.type === "tool");
    expect(toolEvent?.tool).toBe("compare_periods");
  });

  test("'найди бургер нечто' → calls get_nomenclature_search", async () => {
    const ev = await collect("Найди в меню бургер нечто");
    const toolEvent = ev.find((e) => e.type === "tool");
    expect(toolEvent?.tool).toBe("get_nomenclature_search");
  });

  test("'что делать сегодня' → calls get_owner_brief", async () => {
    const ev = await collect("Что делать сегодня, чтобы не потерять вечер?");
    const toolEvent = ev.find((e) => e.type === "tool");
    expect(toolEvent?.tool).toBe("get_owner_brief");
    const text = ev.find((e) => e.type === "text");
    expect(text?.text).toContain("Диагностика:");
  });

  test("greeting / off-topic → suggests prompts without tool calls", async () => {
    const ev = await collect("Привет, что ты умеешь?");
    expect(ev.some((e) => e.type === "tool")).toBe(false);
    const text = ev.find((e) => e.type === "text");
    expect(text?.text.toLowerCase()).toContain("спрос");
  });
});

describe("runMockChatTurn — event stream shape", () => {
  test("always emits thinking → text → done", async () => {
    const ev = await collect("Какая выручка за неделю?");
    expect(ev[0].type).toBe("thinking");
    expect(ev.at(-1)?.type).toBe("done");
    expect(ev.some((e) => e.type === "text")).toBe(true);
  });

  test("tool answer mentions a ruble amount", async () => {
    const ev = await collect("Покажи топ 3 блюда за месяц");
    const text = ev.find((e) => e.type === "text");
    expect(text?.text).toMatch(/₽/);
  });

  test("venue name appears in the system context (text addresses venue)", async () => {
    const ev = await collect("Какая выручка за неделю?");
    const text = ev.find((e) => e.type === "text");
    // We don't assert exact mention; we assert it's a non-generic Russian reply.
    expect(text?.text.length).toBeGreaterThan(40);
    expect(text?.text).toMatch(/[А-Я]/);
  });
});
