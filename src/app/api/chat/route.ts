import { NextResponse } from "next/server";
import { z } from "zod";
import { getDashboardClient, resolveIikoClientConfig } from "@/lib/iiko/config";
import { runMockChatTurn } from "@/lib/ai/mock-chat";
import {
  isOpenAIChatConfigured,
  runOpenAIChatTurn,
} from "@/lib/ai/openai-chat";
import { getVenueAccess } from "@/lib/auth/venue-access";

const BodySchema = z.object({
  venueId: z.string().min(1),
  message: z.string().min(1).max(2000),
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

  const access = await getVenueAccess(parsed.data.venueId);
  if (!access.ok) {
    return NextResponse.json(
      { error: access.error },
      { status: access.status },
    );
  }
  const { venue } = access;

  const iikoClient = getDashboardClient(venue);
  const iikoConfig = resolveIikoClientConfig(
    venue,
    process.env,
    new Date().toISOString().slice(0, 10),
  );
  const useOpenAI = isOpenAIChatConfigured();

  const encoder = new TextEncoder();
  const stream = new ReadableStream<Uint8Array>({
    async start(controller) {
      try {
        const input = {
          message: parsed.data.message,
          venueName: venue.name,
          venueType: venue.type,
          venueCity: venue.city,
          venueProfile: venue.intelligence,
          dataMode: iikoConfig.mode,
          iikoClient,
        };
        const events = useOpenAI
          ? runOpenAIChatTurn(input)
          : runMockChatTurn(input);

        for await (const event of events) {
          controller.enqueue(encoder.encode(JSON.stringify(event) + "\n"));
        }
      } catch (err) {
        if (useOpenAI) {
          for await (const event of runMockChatTurn({
            message: parsed.data.message,
            venueName: venue.name,
            venueType: venue.type,
            venueCity: venue.city,
            venueProfile: venue.intelligence,
            dataMode: iikoConfig.mode,
            iikoClient,
          })) {
            controller.enqueue(encoder.encode(JSON.stringify(event) + "\n"));
          }
        } else {
          controller.enqueue(
            encoder.encode(
              JSON.stringify({
                type: "error",
                message: err instanceof Error ? err.message : "unknown",
              }) + "\n",
            ),
          );
        }
      } finally {
        controller.close();
      }
    },
  });

  return new Response(stream, {
    status: 200,
    headers: {
      "Content-Type": "application/x-ndjson; charset=utf-8",
      "X-Receptor-Backend": useOpenAI ? "openai-chat" : "mock-chat",
      "Cache-Control": "no-store",
    },
  });
}
