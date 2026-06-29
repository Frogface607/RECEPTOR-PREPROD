"use server";

import { revalidatePath } from "next/cache";
import { z } from "zod";
import { getCurrentUser } from "@/lib/auth/session";
import { getServerSupabase } from "@/lib/db/server";
import {
  calculateLearningScore,
  getLearningItem,
} from "@/lib/team/team-learning";
import {
  listLearningItemsForRoleWithStandards,
  normalizeLearningStandardStatus,
  type TeamLearningStandardOverride,
} from "@/lib/team/team-learning-standards";
import type { TeamRoleId } from "@/lib/team/team-os";
import type { TeamLearningProgressSnapshot } from "@/lib/team/team-learning-progress";
import { selectLearningAdmissionTasksToClose } from "@/lib/team/team-task-autoresolve";

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

type LearningTaskRow = {
  id: string;
  title: string;
  status: "new" | "accepted" | "in_progress" | "done" | "verified";
  audience_member_id: string | null;
};

type DbLearningStandard = {
  venue_id: string;
  role: string;
  module_id: string;
  status: string | null;
  updated_at: string | null;
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
  return /team_learning_progress|team_learning_standards|venue_memberships|team_tasks|team_audit_events|relation .* does not exist/i.test(
    message,
  );
}

const OPEN_TASK_STATUSES = ["new", "accepted", "in_progress"] as const;

function mapLearningStandard(
  row: DbLearningStandard,
): TeamLearningStandardOverride {
  return {
    venueId: row.venue_id,
    roleId: row.role as TeamRoleId,
    moduleId: row.module_id,
    status: normalizeLearningStandardStatus(row.status),
    updatedAt: row.updated_at ?? "",
  };
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

async function closeLearningAdmissionTasks(input: {
  supabase: NonNullable<Awaited<ReturnType<typeof getServerSupabase>>>;
  venueId: string;
  memberId: string;
  moduleTitle: string;
  userId: string;
}): Promise<string[]> {
  const { supabase, venueId, memberId, moduleTitle, userId } = input;

  const { data, error } = await supabase
    .from("team_tasks")
    .select("id,title,status,audience_member_id")
    .eq("venue_id", venueId)
    .eq("audience_type", "member")
    .eq("audience_member_id", memberId)
    .in("status", OPEN_TASK_STATUSES);

  if (error) {
    if (missingLearningTable(error.message)) return [];
    throw new Error(error.message);
  }

  const taskIds = selectLearningAdmissionTasksToClose(
    ((data ?? []) as LearningTaskRow[]).map((task) => ({
      id: task.id,
      title: task.title,
      status: task.status,
      audience: { type: "member", memberId: task.audience_member_id ?? "" },
    })),
    { memberId, moduleTitle },
  ).map((task) => task.id);

  if (taskIds.length === 0) return [];

  const updatedAt = new Date().toISOString();
  const { error: updateError } = await supabase
    .from("team_tasks")
    .update({ status: "done", updated_at: updatedAt })
    .eq("venue_id", venueId)
    .in("id", taskIds);

  if (updateError) {
    if (missingLearningTable(updateError.message)) return [];
    throw new Error(updateError.message);
  }

  const auditResult = await supabase.from("team_audit_events").insert({
    venue_id: venueId,
    actor_user_id: userId,
    actor_membership_id: memberId,
    event_type: "task_status_updated",
    target_type: "task",
    target_id: taskIds[0] ?? null,
    summary: `Автоматически закрыта задача обучения после сдачи модуля: ${moduleTitle}.`,
    metadata: {
      taskIds,
      memberId,
      moduleTitle,
      status: "done",
      sourceLabel: "Обучение",
      impactLabel: `${taskIds.length} допуск`,
    },
  });

  if (auditResult.error && !missingLearningTable(auditResult.error.message)) {
    console.warn(
      "Failed to write learning admission task audit:",
      auditResult.error.message,
    );
  }

  return taskIds;
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
      message: "Тестовый режим: прогресс сохранен локально.",
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

  const standardsResult = await supabase
    .from("team_learning_standards")
    .select("venue_id,role,module_id,status,updated_at")
    .eq("venue_id", membership.venue_id);

  const standards =
    standardsResult.error && missingLearningTable(standardsResult.error.message)
      ? []
      : ((standardsResult.data ?? []) as DbLearningStandard[]).map(
          mapLearningStandard,
        );

  const roleItems = listLearningItemsForRoleWithStandards(
    membership.role as TeamRoleId,
    standards,
  );
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

  if (
    existingResult.error &&
    missingLearningTable(existingResult.error.message)
  ) {
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

  let closedTaskIds: string[] = [];
  let taskCloseWarning = false;
  if (savedProgress.passed) {
    try {
      closedTaskIds = await closeLearningAdmissionTasks({
        supabase,
        venueId: membership.venue_id,
        memberId: membership.id,
        moduleTitle: item.title,
        userId: user.id,
      });
    } catch (error) {
      taskCloseWarning = true;
      console.warn("Failed to auto-close learning admission task:", error);
    }
  }

  revalidatePath("/me");
  revalidatePath("/me/learning");
  revalidatePath("/team");
  revalidatePath(`/team?venueId=${encodeURIComponent(membership.venue_id)}`);
  revalidatePath(`/dashboard/${membership.venue_id}`);

  return {
    ok: true,
    mode: "saved",
    message:
      closedTaskIds.length > 0
        ? "Прогресс сохранен, задача обучения закрыта."
        : taskCloseWarning
          ? "Прогресс сохранен. Задача обучения не закрылась автоматически."
          : "Прогресс сохранен.",
    progress: savedProgress,
  };
}
