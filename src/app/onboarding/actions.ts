"use server";

import { z } from "zod";
import { getServerSupabase } from "@/lib/db/server";
import { getCurrentUser } from "@/lib/auth/session";

const VenueInput = z.object({
  name: z.string().min(1).max(120),
  type: z.enum(["restaurant", "cafe", "coffee", "bar", "chain", "other"]),
  city: z.string().max(120).optional().default(""),
});

export type OnboardingResult =
  | { ok: true; mode: "saved" | "demo"; venueId: string }
  | { ok: false; error: string };

/**
 * Persist the onboarding venue.
 *
 * - Real mode (Supabase configured + logged in): insert into `venues`,
 *   return the new id.
 * - Demo mode: nothing to persist — return the demo venue id so the wizard
 *   still completes and lands the user on the Edison dashboard.
 *
 * Wrapped defensively: a DB hiccup never blocks the user from reaching the
 * dashboard during a demo.
 */
export async function createVenueAction(
  raw: unknown,
): Promise<OnboardingResult> {
  const parsed = VenueInput.safeParse(raw);
  if (!parsed.success) {
    return { ok: false, error: "Проверьте поля заведения." };
  }

  const user = await getCurrentUser();
  const supabase = await getServerSupabase();

  // Demo mode (or unauthenticated demo): skip persistence, proceed.
  if (!supabase || !user || user.isDemo) {
    return { ok: true, mode: "demo", venueId: "edison-demo" };
  }

  try {
    const { data, error } = await supabase
      .from("venues")
      .insert({
        owner_user_id: user.id,
        name: parsed.data.name,
        type: parsed.data.type,
        city: parsed.data.city || null,
      })
      .select("id")
      .single();

    if (error || !data) {
      return { ok: false, error: error?.message ?? "Не удалось сохранить." };
    }
    return { ok: true, mode: "saved", venueId: data.id as string };
  } catch (err) {
    return {
      ok: false,
      error: err instanceof Error ? err.message : "Ошибка сохранения.",
    };
  }
}
