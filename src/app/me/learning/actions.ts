"use server";

import { revalidatePath } from "next/cache";
import { z } from "zod";
import { getCurrentUser } from "@/lib/auth/session";
import { getServerSupabase } from "@/lib/db/server";
import {
  calculateLearningScore,
  getLearningItem,
  listLearningItemsForRole,
} from "@/lib/team/team-learning";
import type { TeamRoleId } from "@/lib/team/team-os";
import type { TeamLearningProgressSnapshot } from "@/lib/team/team-learning-progress";

const SaveLearningProgressInput = z.object({
  venueId: z.string().min(1),
  moduleId: z.string().min(1),
  answers: z.array(z.number().int()).min(1).max(24),
});

type MembershipRow = {
  id: string;
  venue_id: string;
  role: string;
  status: string;
};

type ExistingProgressRow = {
  best_percentage: number | null;
};

export type SaveLearningProgressResult =
  | {
      ok: true;
      mode: "saved" | "sandbox" | "local";
      message: string;
      progress: TeamLearningProgressSnapshot;
    }
  | { ok: false; error: string };

function missingLearningTable(message: string): boolean {
  return /team_learning_progress|venue_memberships|relation .* does not exist/i.test(
    message,
  );
}

function snapshotFromScore(input: {
  bestPercentage: number;
  lastPercentage: number;
  correct: number;
  total: number;
  passed: boolean;
  answers: number[];
  completedAt: string;
}): TeamLearningProgressSnapshot {
  return {
    bestPercentage: input.bestPercentage,
    lastPercentage: input.lastPercentage,
    correct: input.correct,
    total: input.total,
    passed: input.passed,
    answers: input.answers,
    completedAt: input.completedAt,
  };
}

export async function saveLearningProgressAction(
  raw: unknown,
): Promise<SaveLearningProgressResult> {
  const parsed = SaveLearningProgressInput.safeParse(raw);
  if (!parsed.success) {
    return { ok: false, error: "Проверьте ответы теста." };
  }

  const item = getLearningItem(parsed.data.moduleId);
  if (!item) {
    return { ok: false, error: "Материал обучения не найден." };
  }

  const score = calculateLearningScore(item, parsed.data.answers);
  const completedAt = new Date().toISOString();
  const localProgress = snapshotFromScore({
    bestPercentage: score.percentage,
    lastPercentage: score.percentage,
    correct: score.correct,
    total: score.total,
    passed: score.passed,
    answers: parsed.data.answers,
    completedAt,
  });

  const user = await getCurrentUser();
  if (!user) return { ok: false, error: "Нужно войти." };
  if (user.isDemo) {
    return {
      ok: true,
      mode: "sandbox",
      message: "Демо: прогресс сохранен локально.",
      progress: localProgress,
    };
  }

  const supabase = await getServerSupabase();
  if (!supabase) {
    return {
      ok: true,
      mode: "local",
      message: "Серверное сохранение недоступно, прогресс оставлен локально.",
      progress: localProgress,
    };
  }

  const membershipResult = await supabase
    .from("venue_memberships")
    .select("id,venue_id,role,status")
    .eq("venue_id", parsed.data.venueId)
    .eq("user_id", user.id)
    .neq("status", "paused")
    .maybeSingle<MembershipRow>();

  if (membershipResult.error) {
    if (missingLearningTable(membershipResult.error.message)) {
      return {
        ok: true,
        mode: "local",
        message: "В базе еще нет таблицы обучения, прогресс оставлен локально.",
        progress: localProgress,
      };
    }
    return { ok: false, error: membershipResult.error.message };
  }

  const membership = membershipResult.data;
  if (!membership) {
    return { ok: false, error: "Нет активной роли в этом заведении." };
  }

  const roleItems = listLearningItemsForRole(membership.role as TeamRoleId);
  if (!roleItems.some((roleItem) => roleItem.id === item.id)) {
    return { ok: false, error: "Этот материал недоступен для вашей роли." };
  }

  const existingResult = await supabase
    .from("team_learning_progress")
    .select("best_percentage")
    .eq("venue_id", membership.venue_id)
    .eq("membership_id", membership.id)
    .eq("module_id", item.id)
    .maybeSingle<ExistingProgressRow>();

  if (existingResult.error && missingLearningTable(existingResult.error.message)) {
    return {
      ok: true,
      mode: "local",
      message: "В базе еще нет таблицы обучения, прогресс оставлен локально.",
      progress: localProgress,
    };
  }
  if (existingResult.error) {
    return { ok: false, error: existingResult.error.message };
  }

  const bestPercentage = Math.max(
    existingResult.data?.best_percentage ?? 0,
    score.percentage,
  );
  const savedProgress = snapshotFromScore({
    bestPercentage,
    lastPercentage: score.percentage,
    correct: score.correct,
    total: score.total,
    passed: bestPercentage >= item.passPercentage,
    answers: parsed.data.answers,
    completedAt,
  });

  const upsertResult = await supabase.from("team_learning_progress").upsert(
    {
      venue_id: membership.venue_id,
      membership_id: membership.id,
      user_id: user.id,
      module_id: item.id,
      best_percentage: bestPercentage,
      last_percentage: score.percentage,
      correct_count: score.correct,
      total_questions: score.total,
      passed: bestPercentage >= item.passPercentage,
      answers: parsed.data.answers,
      completed_at: completedAt,
      updated_at: completedAt,
    },
    { onConflict: "venue_id,membership_id,module_id" },
  );

  if (upsertResult.error) {
    if (missingLearningTable(upsertResult.error.message)) {
      return {
        ok: true,
        mode: "local",
        message: "В базе еще нет таблицы обучения, прогресс оставлен локально.",
        progress: localProgress,
      };
    }
    return { ok: false, error: upsertResult.error.message };
  }

  revalidatePath("/me");
  revalidatePath("/me/learning");
  revalidatePath("/team");
  revalidatePath(`/team?venueId=${encodeURIComponent(membership.venue_id)}`);

  return {
    ok: true,
    mode: "saved",
    message: "Прогресс сохранен.",
    progress: savedProgress,
  };
}
