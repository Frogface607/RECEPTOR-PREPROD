export type TelegramConfig = {
  botToken: string;
  chatId: string;
};

export type SendTelegramMessageInput = TelegramConfig & {
  text: string;
  fetchImpl?: typeof fetch;
};

export type SendTelegramMessageResult = {
  messageId?: number;
};

function isRealValue(value: string | undefined): value is string {
  if (!value) return false;
  const normalized = value.trim().toLowerCase();
  return (
    normalized.length > 0 &&
    !normalized.includes("your-") &&
    !normalized.includes("replace")
  );
}

export function getTelegramConfig(
  env: Record<string, string | undefined> = process.env,
): TelegramConfig | null {
  const botToken = env.TELEGRAM_BOT_TOKEN;
  const chatId = env.TELEGRAM_CHAT_ID;
  if (!isRealValue(botToken) || !isRealValue(chatId)) return null;
  return { botToken: botToken.trim(), chatId: chatId.trim() };
}

export function isTelegramConfigured(
  env: Record<string, string | undefined> = process.env,
): boolean {
  return getTelegramConfig(env) !== null;
}

export async function sendTelegramMessage({
  botToken,
  chatId,
  text,
  fetchImpl = fetch,
}: SendTelegramMessageInput): Promise<SendTelegramMessageResult> {
  const response = await fetchImpl(
    `https://api.telegram.org/bot${botToken}/sendMessage`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        chat_id: chatId,
        text,
        disable_web_page_preview: true,
      }),
    },
  );

  const payload = (await response.json().catch(() => null)) as {
    ok?: boolean;
    description?: string;
    result?: { message_id?: number };
  } | null;

  if (!response.ok || payload?.ok === false) {
    throw new Error(
      payload?.description ?? `Telegram API returned HTTP ${response.status}`,
    );
  }

  return { messageId: payload?.result?.message_id };
}
