import { NextResponse } from "next/server";
import { z } from "zod";
import { getDashboardClient } from "@/lib/iiko/config";
import { getVenue } from "@/lib/venues/get-venue";
import { runMockChatTurn } from "@/lib/ai/mock-chat";

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

  const venue = getVenue(parsed.data.venueId);
  if (!venue) {
    return NextResponse.json({ error: "venue not found" }, { status: 404 });
  }

  const iikoClient = getDashboardClient(venue);

  const encoder = new TextEncoder();
  const stream = new ReadableStream<Uint8Array>({
    async start(controller) {
      try {
        for await (const event of runMockChatTurn({
          message: parsed.data.message,
          venueName: venue.name,
          venueType: venue.type,
          venueCity: venue.city,
          iikoClient,
        })) {
          controller.enqueue(encoder.encode(JSON.stringify(event) + "\n"));
        }
      } catch (err) {
        controller.enqueue(
          encoder.encode(
            JSON.stringify({
              type: "error",
              message: err instanceof Error ? err.message : "unknown",
            }) + "\n",
          ),
        );
      } finally {
        controller.close();
      }
    },
  });

  return new Response(stream, {
    status: 200,
    headers: {
      "Content-Type": "application/x-ndjson; charset=utf-8",
      "X-Receptor-Backend": "mock-chat",
      "Cache-Control": "no-store",
    },
  });
}
