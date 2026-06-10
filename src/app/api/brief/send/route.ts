import { NextResponse } from "next/server";
import { z } from "zod";
import { getVenueAccess } from "@/lib/auth/venue-access";
import { buildDailyBrief, renderDailyBriefText } from "@/lib/brief/daily-brief";
import { getDashboardClient } from "@/lib/iiko/config";
import {
  getTelegramConfig,
  sendTelegramMessage,
} from "@/lib/notifications/telegram";

const BodySchema = z.object({
  venueId: z.string().min(1),
  period: z
    .enum([
      "TODAY",
      "YESTERDAY",
      "CURRENT_WEEK",
      "LAST_WEEK",
      "CURRENT_MONTH",
      "LAST_MONTH",
      "CUSTOM",
    ])
    .default("YESTERDAY"),
});

export const runtime = "nodejs";

export async function POST(request: Request) {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json(
      { error: "expected JSON body" },
      { status: 400 },
    );
  }

  const parsed = BodySchema.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json(
      { error: "invalid body", issues: parsed.error.issues },
      { status: 400 },
    );
  }

  const telegram = getTelegramConfig();
  if (!telegram) {
    return NextResponse.json(
      {
        error:
          "telegram is not configured: set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID",
      },
      { status: 503 },
    );
  }

  const access = await getVenueAccess(parsed.data.venueId);
  if (!access.ok) {
    return NextResponse.json(
      { error: access.error },
      { status: access.status },
    );
  }

  const client = getDashboardClient(access.venue);
  const brief = await buildDailyBrief(client, parsed.data.period);
  const text = renderDailyBriefText(brief, { venueName: access.venue.name });
  const sent = await sendTelegramMessage({ ...telegram, text });

  return NextResponse.json(
    {
      ok: true,
      channel: "telegram",
      messageId: sent.messageId,
      venueId: access.venue.id,
      period: brief.period,
    },
    {
      headers: {
        "Cache-Control": "no-store",
      },
    },
  );
}
