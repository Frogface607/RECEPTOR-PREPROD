"use server";

import { z } from "zod";
import { getCurrentUser } from "@/lib/auth/session";
import { getVenueAccess } from "@/lib/auth/venue-access";
import { getServerSupabase } from "@/lib/db/server";
import {
  calculateContextCompletion,
  formatContextAnswersForPrompt,
  normalizeContextAnswers,
  type VenueContextAnswers,
} from "@/lib/venues/context-questionnaire";
import type { VenueIntelligenceProfile } from "@/lib/venues/intelligence";
import { researchVenue } from "@/lib/venues/research";

const UpdateVenueContextInput = z.object({
  venueId: z.string().min(1),
  answers: z.unknown(),
});

const ResearchVenueContextInput = UpdateVenueContextInput;

export type UpdateVenueContextResult =
  | {
      ok: true;
      mode: "saved" | "sandbox";
      answers: VenueContextAnswers;
      completion: ReturnType<typeof calculateContextCompletion>;
    }
  | { ok: false; error: string };

export type ResearchVenueContextResult =
  | {
      ok: true;
      mode: "saved" | "sandbox";
      answers: VenueContextAnswers;
      completion: ReturnType<typeof calculateContextCompletion>;
      profile: VenueIntelligenceProfile;
      provider: "openai" | "openrouter" | "fallback";
      summary: string;
      diagnostics: string[];
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

export async function researchVenueContextAction(
  raw: unknown,
): Promise<ResearchVenueContextResult> {
  const parsed = ResearchVenueContextInput.safeParse(raw);
  if (!parsed.success) {
    return { ok: false, error: "Некорректные данные анкеты." };
  }

  const access = await getVenueAccess(parsed.data.venueId);
  if (!access.ok) {
    return {
      ok: false,
      error:
        access.status === 401
          ? "Нужно войти, чтобы собрать профиль заведения."
          : "Заведение не найдено или нет доступа.",
    };
  }

  const answers = normalizeContextAnswers(parsed.data.answers);
  const completion = calculateContextCompletion(answers);
  const ownerContext =
    formatContextAnswersForPrompt(answers) ||
    formatContextAnswersForPrompt(access.venue.context) ||
    access.venue.intelligence.positioning;

  const research = await researchVenue({
    name: access.venue.name,
    city: access.venue.city,
    type: access.venue.type,
    ownerContext,
  });

  const supabase = await getServerSupabase();
  if (!supabase || access.user.isDemo) {
    return {
      ok: true,
      mode: "sandbox",
      answers,
      completion,
      profile: research.profile,
      provider: research.provider,
      summary: research.summary,
      diagnostics: research.diagnostics ?? [],
    };
  }

  const { data, error } = await supabase
    .from("venues")
    .update({
      context_profile: answers,
      intelligence_profile: research.profile,
    })
    .eq("id", parsed.data.venueId)
    .eq("owner_user_id", access.user.id)
    .select("id")
    .maybeSingle();

  if (error) {
    if (/(intelligence_profile|context_profile)/i.test(error.message)) {
      return {
        ok: false,
        error:
          "В базе нет полей context_profile или intelligence_profile. Примените миграции 0002 и 0003.",
      };
    }
    return { ok: false, error: error.message };
  }

  if (!data) {
    return { ok: false, error: "Заведение не найдено или нет доступа." };
  }

  return {
    ok: true,
    mode: "saved",
    answers,
    completion,
    profile: research.profile,
    provider: research.provider,
    summary: research.summary,
    diagnostics: research.diagnostics ?? [],
  };
}
