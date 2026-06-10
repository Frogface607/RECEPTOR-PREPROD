import { afterEach, describe, expect, test, vi } from "vitest";
import {
  getTelegramConfig,
  isTelegramConfigured,
  sendTelegramMessage,
} from "./telegram";

afterEach(() => {
  vi.restoreAllMocks();
});

describe("telegram notification config", () => {
  test("is disabled when token or chat id is missing", () => {
    expect(getTelegramConfig({})).toBeNull();
    expect(
      getTelegramConfig({
        TELEGRAM_BOT_TOKEN: "token",
      }),
    ).toBeNull();
    expect(isTelegramConfigured({})).toBe(false);
  });

  test("returns trimmed config when both values are set", () => {
    expect(
      getTelegramConfig({
        TELEGRAM_BOT_TOKEN: " 123:abc ",
        TELEGRAM_CHAT_ID: " -10042 ",
      }),
    ).toEqual({ botToken: "123:abc", chatId: "-10042" });
  });
});

describe("sendTelegramMessage", () => {
  test("posts plain text to Telegram sendMessage", async () => {
    const fetchImpl = vi.fn(async (...args: Parameters<typeof fetch>) => {
      void args;
      return Response.json({ ok: true, result: { message_id: 77 } });
    });

    await expect(
      sendTelegramMessage({
        botToken: "123:abc",
        chatId: "-10042",
        text: "Daily Brief",
        fetchImpl,
      }),
    ).resolves.toEqual({ messageId: 77 });

    expect(fetchImpl).toHaveBeenCalledWith(
      "https://api.telegram.org/bot123:abc/sendMessage",
      expect.objectContaining({
        method: "POST",
        headers: { "Content-Type": "application/json" },
      }),
    );

    const init = fetchImpl.mock.calls[0][1] as RequestInit;
    expect(JSON.parse(init.body as string)).toEqual({
      chat_id: "-10042",
      text: "Daily Brief",
      disable_web_page_preview: true,
    });
  });

  test("throws Telegram description on API error", async () => {
    const fetchImpl = vi.fn(async (...args: Parameters<typeof fetch>) => {
      void args;
      return Response.json(
        { ok: false, description: "Bad Request: chat not found" },
        { status: 400 },
      );
    });

    await expect(
      sendTelegramMessage({
        botToken: "123:abc",
        chatId: "missing",
        text: "Daily Brief",
        fetchImpl,
      }),
    ).rejects.toThrow("chat not found");
  });
});
