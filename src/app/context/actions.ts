"use server";

import { z } from "zod";
import { getCurrentUser } from "@/lib/auth/session";
import { getServerSupabase } from "@/lib/db/server";
import {
  calculateContextCompletion,
  normalizeContextAnswers,
  type VenueContextAnswers,
} from "@/lib/venues/context-questionnaire";

const UpdateVenueContextInput = z.object({
  venueId: z.string().min(1),
  answers: z.unknown(),
});

export type UpdateVenueContextResult =
  | {
      ok: true;
      mode: "saved" | "sandbox";
      answers: VenueContextAnswers;
      completion: ReturnType<typeof calculateContextCompletion>;
    }
  | { ok: false; error: string };

export async function updateVenueContextAction(
  raw: unknown,
): Promise<UpdateVenueContextResult> {
  const parsed = UpdateVenueContextInput.safeParse(raw);
  if (!parsed.success) {
    return { ok: false, error: "Некорректные данные анкеты." };
  }

  const user = await getCurrentUser();
  if (!user) {
    return { ok: false, error: "Нужно войти, чтобы сохранить контекст." };
  }

  const answers = normalizeContextAnswers(parsed.data.answers);
  const completion = calculateContextCompletion(answers);
  const supabase = await getServerSupabase();

  if (!supabase || user.isDemo) {
    return { ok: true, mode: "sandbox", answers, completion };
  }

  const { data, error } = await supabase
    .from("venues")
    .update({ context_profile: answers })
    .eq("id", parsed.data.venueId)
    .eq("owner_user_id", user.id)
    .select("id")
    .maybeSingle();

  if (error) {
    if (/context_profile/i.test(error.message)) {
      return {
        ok: false,
        error:
          "В базе нет context_profile. Примените миграцию 0003_venue_context_profile.sql.",
      };
    }
    return { ok: false, error: error.message };
  }

  if (!data) {
    return { ok: false, error: "Заведение не найдено или нет доступа." };
  }

  return { ok: true, mode: "saved", answers, completion };
}
