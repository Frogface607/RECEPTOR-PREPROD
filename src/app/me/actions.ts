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

export type OwnTaskStatusResult =
  { ok: true; message: string } | { ok: false; error: string };

function missingTeamAnnouncementReadTable(message: string): boolean {
  return /team_announcement_reads|team_announcements|venue_memberships|relation .* does not exist|column .* does not exist/i.test(
    message,
  );
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
