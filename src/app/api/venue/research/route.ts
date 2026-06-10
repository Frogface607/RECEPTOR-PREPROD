import { NextResponse } from "next/server";
import { z } from "zod";
import { researchVenue } from "@/lib/venues/research";

export const runtime = "nodejs";

const BodySchema = z.object({
  name: z.string().trim().min(1),
  city: z.string().trim().optional().default(""),
  type: z.string().trim().optional(),
  ownerContext: z.string().trim().max(4000).optional().default(""),
});

export async function POST(request: Request) {
  let raw: unknown;
  try {
    raw = await request.json();
  } catch {
    return NextResponse.json({ error: "expected JSON body" }, { status: 400 });
  }

  const parsed = BodySchema.safeParse(raw);
  if (!parsed.success) {
    return NextResponse.json(
      { error: "invalid body", issues: parsed.error.issues },
      { status: 400 },
    );
  }

  const result = await researchVenue(parsed.data);
  return NextResponse.json(result, {
    headers: { "Cache-Control": "no-store" },
  });
}
