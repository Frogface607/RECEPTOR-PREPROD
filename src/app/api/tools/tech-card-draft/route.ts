import { NextResponse } from "next/server";
import { z } from "zod";
import { generateTechCardDraft } from "@/lib/tools/tech-card-draft";
import {
  normalizeVenueProfile,
  VenueIntelligenceSchema,
} from "@/lib/venues/intelligence";

export const runtime = "nodejs";

const BodySchema = z.object({
  idea: z.string().trim().min(2),
  category: z.string().trim().optional().default(""),
  portions: z.number().positive().optional().default(1),
  targetFoodCostPercent: z.number().positive().optional().default(30),
  venueProfile: VenueIntelligenceSchema.optional(),
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

  const body = parsed.data;
  const result = await generateTechCardDraft({
    idea: body.idea,
    category: body.category,
    portions: body.portions,
    targetFoodCostPercent: body.targetFoodCostPercent,
    venueProfile: body.venueProfile
      ? normalizeVenueProfile(body.venueProfile)
      : undefined,
  });

  return NextResponse.json(result, {
    headers: { "Cache-Control": "no-store" },
  });
}
