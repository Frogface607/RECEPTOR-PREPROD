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

export type OwnTaskStatusResult =
  | { ok: true; message: string }
  | { ok: false; error: string };

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
    return { ok: true, message: "Демо: статус задачи обновлен." };
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
