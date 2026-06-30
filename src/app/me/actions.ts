"use server";

import { revalidatePath } from "next/cache";
import { z } from "zod";
import { getCurrentUser } from "@/lib/auth/session";
import { getSupabaseAdmin } from "@/lib/db/admin";
import { getServerSupabase } from "@/lib/db/server";

const OwnTaskStatusInput = z.object({
  taskId: z.string().min(1),
  status: z.enum(["accepted", "in_progress", "done"]),
});

const MarkAnnouncementReadInput = z.object({
  announcementId: z.string().min(1),
});

const SubmitFieldNoteInput = z.object({
  body: z.string().trim().min(5).max(1500),
});

export type OwnTaskStatusResult =
  { ok: true; message: string } | { ok: false; error: string };

function missingTeamAnnouncementReadTable(message: string): boolean {
  return /team_announcement_reads|team_announcements|venue_memberships|relation .* does not exist|column .* does not exist/i.test(
    message,
  );
}

function missingFieldNoteTables(message: string): boolean {
  return /venue_memberships|team_tasks|team_task_comments|team_audit_events|source_label|impact_label|relation .* does not exist|column .* does not exist/i.test(
    message,
  );
}

function missingSourceLabelColumn(message: string): boolean {
  return /source_label/i.test(message);
}

function missingImpactLabelColumn(message: string): boolean {
  return /impact_label/i.test(message);
}

export async function updateOwnTaskStatusAction(
  raw: unknown,
): Promise<OwnTaskStatusResult> {
  const parsed = OwnTaskStatusInput.safeParse(raw);
  if (!parsed.success) {
    return { ok: false, error: "Некорректный статус задачи." };
  }

  const user = await getCurrentUser();
  if (!user) return { ok: false, error: "Нужно войти." };
  if (user.isDemo) {
    return { ok: true, message: "Тестовый режим: статус задачи обновлен." };
  }

  const supabase = await getServerSupabase();
  const admin = getSupabaseAdmin();
  if (!supabase || !admin) {
    return { ok: false, error: "Обновление задач не настроено на сервере." };
  }

  const { data: visibleTask, error: visibleError } = await supabase
    .from("team_tasks")
    .select("id")
    .eq("id", parsed.data.taskId)
    .maybeSingle<{ id: string }>();

  if (visibleError) return { ok: false, error: visibleError.message };
  if (!visibleTask) {
    return { ok: false, error: "Задача не найдена или нет доступа." };
  }

  const { error } = await admin
    .from("team_tasks")
    .update({
      status: parsed.data.status,
      updated_at: new Date().toISOString(),
    })
    .eq("id", parsed.data.taskId);

  if (error) return { ok: false, error: error.message };

  revalidatePath("/me");
  return { ok: true, message: "Статус задачи обновлен." };
}

export async function markAnnouncementReadAction(
  raw: unknown,
): Promise<OwnTaskStatusResult> {
  const parsed = MarkAnnouncementReadInput.safeParse(raw);
  if (!parsed.success) {
    return { ok: false, error: "Некорректное объявление." };
  }

  const user = await getCurrentUser();
  if (!user) return { ok: false, error: "Нужно войти." };
  if (user.isDemo) {
    return {
      ok: true,
      message: "Тестовый режим: объявление отмечено как прочитанное.",
    };
  }

  const supabase = await getServerSupabase();
  const admin = getSupabaseAdmin();
  if (!supabase || !admin) {
    return {
      ok: false,
      error: "Подтверждение объявлений не настроено на сервере.",
    };
  }

  const { data: announcement, error: announcementError } = await supabase
    .from("team_announcements")
    .select("id,venue_id")
    .eq("id", parsed.data.announcementId)
    .maybeSingle<{ id: string; venue_id: string }>();

  if (announcementError) {
    if (missingTeamAnnouncementReadTable(announcementError.message)) {
      return {
        ok: false,
        error:
          "В базе нет таблиц объявлений команды. Примените миграции Team OS.",
      };
    }
    return { ok: false, error: announcementError.message };
  }
  if (!announcement) {
    return { ok: false, error: "Объявление не найдено или нет доступа." };
  }

  const { data: membership, error: membershipError } = await admin
    .from("venue_memberships")
    .select("id")
    .eq("venue_id", announcement.venue_id)
    .eq("user_id", user.id)
    .eq("status", "active")
    .maybeSingle<{ id: string }>();

  if (membershipError) {
    if (missingTeamAnnouncementReadTable(membershipError.message)) {
      return {
        ok: false,
        error: "В базе нет таблиц команды. Примените миграции Team OS.",
      };
    }
    return { ok: false, error: membershipError.message };
  }
  if (!membership) {
    return { ok: false, error: "Сотрудник не найден в заведении." };
  }

  const { error } = await admin.from("team_announcement_reads").upsert(
    {
      venue_id: announcement.venue_id,
      announcement_id: announcement.id,
      membership_id: membership.id,
      read_at: new Date().toISOString(),
    },
    { onConflict: "announcement_id,membership_id" },
  );

  if (error) {
    if (missingTeamAnnouncementReadTable(error.message)) {
      return {
        ok: false,
        error:
          "В базе нет таблицы прочтений объявлений. Примените миграцию 0012_team_announcement_reads.sql.",
      };
    }
    return { ok: false, error: error.message };
  }

  revalidatePath("/me");
  revalidatePath("/team");
  revalidatePath(`/dashboard/${announcement.venue_id}`);
  return { ok: true, message: "Объявление отмечено как прочитанное." };
}

export async function submitFieldNoteAction(
  raw: unknown,
): Promise<OwnTaskStatusResult> {
  const parsed = SubmitFieldNoteInput.safeParse(raw);
  if (!parsed.success) {
    return { ok: false, error: "Опишите, что важного было на смене." };
  }

  const user = await getCurrentUser();
  if (!user) return { ok: false, error: "Нужно войти." };
  if (user.isDemo) {
    return {
      ok: true,
      message: "Тестовый режим: заметка после смены сохранена.",
    };
  }

  const admin = getSupabaseAdmin();
  if (!admin) {
    return {
      ok: false,
      error: "Полевые заметки не настроены на сервере.",
    };
  }

  const { data: membership, error: membershipError } = await admin
    .from("venue_memberships")
    .select("id,venue_id")
    .eq("user_id", user.id)
    .eq("status", "active")
    .order("created_at", { ascending: true })
    .limit(1)
    .maybeSingle<{ id: string; venue_id: string }>();

  if (membershipError) {
    if (missingFieldNoteTables(membershipError.message)) {
      return {
        ok: false,
        error: "В базе нет таблиц команды. Примените миграции Team OS.",
      };
    }
    return { ok: false, error: membershipError.message };
  }

  if (!membership) {
    return { ok: false, error: "Сотрудник не найден в заведении." };
  }

  const { data: existingTask, error: taskLookupError } = await admin
    .from("team_tasks")
    .select("id,audience_type,audience_role")
    .eq("venue_id", membership.venue_id)
    .eq("title", "Полевой контекст смены")
    .in("status", ["new", "accepted", "in_progress"])
    .order("created_at", { ascending: false })
    .limit(1)
    .maybeSingle<{
      id: string;
      audience_type: string | null;
      audience_role: string | null;
    }>();

  if (taskLookupError) {
    if (missingFieldNoteTables(taskLookupError.message)) {
      return {
        ok: false,
        error: "В базе нет таблиц задач и комментариев Team OS.",
      };
    }
    return { ok: false, error: taskLookupError.message };
  }

  let taskId = existingTask?.id ?? null;
  if (
    existingTask &&
    (existingTask.audience_type !== "role" ||
      existingTask.audience_role !== "venue_manager")
  ) {
    const { error: updateAudienceError } = await admin
      .from("team_tasks")
      .update({
        audience_type: "role",
        audience_member_id: null,
        audience_role: "venue_manager",
        updated_at: new Date().toISOString(),
      })
      .eq("id", existingTask.id)
      .eq("venue_id", membership.venue_id);

    if (
      updateAudienceError &&
      !missingFieldNoteTables(updateAudienceError.message)
    ) {
      return { ok: false, error: updateAudienceError.message };
    }
  }

  if (!taskId) {
    const insert = {
      venue_id: membership.venue_id,
      title: "Полевой контекст смены",
      source: "manager",
      priority: "medium",
      status: "in_progress",
      audience_type: "role",
      audience_member_id: null,
      audience_role: "venue_manager",
      due_label: "ежедневно",
      source_label: "Поле",
      impact_label: "Контекст смены",
      created_by: user.id,
    };

    let taskResult = await admin
      .from("team_tasks")
      .insert(insert)
      .select("id")
      .maybeSingle<{ id: string }>();

    if (
      taskResult.error &&
      missingImpactLabelColumn(taskResult.error.message)
    ) {
      const fallbackInsert = { ...insert };
      delete (fallbackInsert as { impact_label?: string | null }).impact_label;
      taskResult = await admin
        .from("team_tasks")
        .insert(fallbackInsert)
        .select("id")
        .maybeSingle<{ id: string }>();
    }

    if (
      taskResult.error &&
      missingSourceLabelColumn(taskResult.error.message)
    ) {
      const legacyInsert = { ...insert };
      delete (legacyInsert as { source_label?: string | null }).source_label;
      delete (legacyInsert as { impact_label?: string | null }).impact_label;
      taskResult = await admin
        .from("team_tasks")
        .insert(legacyInsert)
        .select("id")
        .maybeSingle<{ id: string }>();
    }

    if (taskResult.error) {
      if (missingFieldNoteTables(taskResult.error.message)) {
        return {
          ok: false,
          error: "В базе нет таблиц задач Team OS.",
        };
      }
      return { ok: false, error: taskResult.error.message };
    }

    taskId = taskResult.data?.id ?? null;
  }

  if (!taskId) {
    return { ok: false, error: "Не удалось создать задачу для заметок." };
  }

  const { data: comment, error: commentError } = await admin
    .from("team_task_comments")
    .insert({
      venue_id: membership.venue_id,
      task_id: taskId,
      author_membership_id: membership.id,
      author_user_id: user.id,
      body: parsed.data.body,
    })
    .select("id")
    .maybeSingle<{ id: string }>();

  if (commentError) {
    if (missingFieldNoteTables(commentError.message)) {
      return {
        ok: false,
        error: "В базе нет таблицы комментариев Team OS.",
      };
    }
    return { ok: false, error: commentError.message };
  }

  await admin.from("team_audit_events").insert({
    venue_id: membership.venue_id,
    actor_user_id: user.id,
    actor_membership_id: membership.id,
    event_type: "comment_added",
    target_type: "comment",
    target_id: comment?.id ?? null,
    summary: "Добавлен полевой контекст смены.",
    metadata: {
      taskId,
      sourceLabel: "Поле",
      impactLabel: "Контекст смены",
    },
  });

  revalidatePath("/me");
  revalidatePath("/team");
  revalidatePath(`/dashboard/${membership.venue_id}`);
  return {
    ok: true,
    message: "Заметка смены сохранена. Receptor учтет ее в советах.",
  };
}
