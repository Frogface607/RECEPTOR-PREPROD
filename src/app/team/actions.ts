"use server";

import { revalidatePath } from "next/cache";
import { z } from "zod";
import { getCurrentUser } from "@/lib/auth/session";
import { normalizeStaffLoginToEmail } from "@/lib/auth/staff-login";
import { getSupabaseAdmin } from "@/lib/db/admin";
import { getServerSupabase } from "@/lib/db/server";
import {
  TEAM_ROLES,
  type TeamRoleId,
  type TeamTask,
} from "@/lib/team/team-os";

const TeamRoleIdSchema = z.enum(
  TEAM_ROLES.map((role) => role.id) as [TeamRoleId, ...TeamRoleId[]],
);

const TaskPrioritySchema = z.enum(["high", "medium", "low"]);
const TaskStatusSchema = z.enum([
  "new",
  "accepted",
  "in_progress",
  "done",
  "verified",
]);
const TaskAudienceTypeSchema = z.enum(["member", "role", "venue"]);
const AnnouncementAudienceTypeSchema = z.enum(["role", "venue"]);
const AnnouncementPrioritySchema = z.enum(["normal", "important"]);
const MemberStatusSchema = z.enum(["active", "paused"]);

const InviteMemberInput = z.object({
  venueId: z.string().min(1),
  fullName: z.string().trim().min(2).max(120),
  email: z.string().trim().email().optional().or(z.literal("")),
  phone: z.string().trim().max(40).optional().or(z.literal("")),
  login: z.string().trim().max(80).optional().or(z.literal("")),
  password: z.string().min(6).max(72).optional().or(z.literal("")),
  role: TeamRoleIdSchema,
  shiftLabel: z.string().trim().max(120).optional().or(z.literal("")),
});

const CreateTeamTaskInput = z
  .object({
    venueId: z.string().min(1),
    title: z.string().trim().min(3).max(240),
    priority: TaskPrioritySchema.default("medium"),
    audienceType: TaskAudienceTypeSchema,
    audienceMemberId: z.string().trim().optional().or(z.literal("")),
    audienceRole: TeamRoleIdSchema.optional(),
    dueLabel: z.string().trim().max(120).optional().or(z.literal("")),
  })
  .superRefine((value, ctx) => {
    if (value.audienceType === "member" && !value.audienceMemberId) {
      ctx.addIssue({
        code: "custom",
        path: ["audienceMemberId"],
        message: "Выберите сотрудника.",
      });
    }
    if (value.audienceType === "role" && !value.audienceRole) {
      ctx.addIssue({
        code: "custom",
        path: ["audienceRole"],
        message: "Выберите роль.",
      });
    }
  });

const UpdateTaskStatusInput = z.object({
  venueId: z.string().min(1),
  taskId: z.string().min(1),
  status: TaskStatusSchema,
});

const UpdateTeamMemberStatusInput = z.object({
  venueId: z.string().min(1),
  memberId: z.string().min(1),
  status: MemberStatusSchema,
});

const ResetTeamMemberPasswordInput = z.object({
  venueId: z.string().min(1),
  memberId: z.string().min(1),
  password: z.string().min(6).max(72),
});

const AddTaskCommentInput = z.object({
  venueId: z.string().min(1),
  taskId: z.string().min(1),
  body: z.string().trim().min(2).max(1000),
});

const CreateAnnouncementInput = z
  .object({
    venueId: z.string().min(1),
    title: z.string().trim().min(2).max(160),
    body: z.string().trim().min(2).max(1200),
    priority: AnnouncementPrioritySchema.default("normal"),
    audienceType: AnnouncementAudienceTypeSchema,
    audienceRole: TeamRoleIdSchema.optional(),
  })
  .superRefine((value, ctx) => {
    if (value.audienceType === "role" && !value.audienceRole) {
      ctx.addIssue({
        code: "custom",
        path: ["audienceRole"],
        message: "Выберите роль.",
      });
    }
  });

export type TeamActionResult =
  | { ok: true; mode: "saved" | "sandbox"; message: string }
  | { ok: false; error: string };

type WritableTeamContext = Extract<
  Awaited<ReturnType<typeof getWritableTeamContext>>,
  { ok: true }
>;

type TeamAuditEventInput = {
  venueId: string;
  type:
    | "member_invited"
    | "member_status_updated"
    | "member_password_reset"
    | "task_created"
    | "task_status_updated"
    | "comment_added"
    | "announcement_created";
  targetType: "member" | "task" | "comment" | "announcement";
  targetId?: string | null;
  summary: string;
  metadata?: Record<string, unknown>;
};

function missingTeamTables(message: string): boolean {
  return /venue_memberships|team_tasks|team_task_comments|team_announcements|team_audit_events|relation .* does not exist/i.test(
    message,
  );
}

async function getWritableTeamContext(): Promise<
  | {
      ok: true;
      mode: "saved" | "sandbox";
      userId: string;
      supabase: Awaited<ReturnType<typeof getServerSupabase>>;
    }
  | { ok: false; error: string }
> {
  const user = await getCurrentUser();
  if (!user) return { ok: false, error: "Нужно войти, чтобы работать с командой." };

  const supabase = await getServerSupabase();
  if (!supabase || user.isDemo) {
    return { ok: true, mode: "sandbox", userId: user.id, supabase: null };
  }

  return { ok: true, mode: "saved", userId: user.id, supabase };
}

async function writeTeamAuditEvent(
  ctx: WritableTeamContext,
  event: TeamAuditEventInput,
): Promise<void> {
  if (ctx.mode === "sandbox" || !ctx.supabase) return;

  const { data: membership } = await ctx.supabase
    .from("venue_memberships")
    .select("id")
    .eq("venue_id", event.venueId)
    .eq("user_id", ctx.userId)
    .maybeSingle<{ id: string }>();

  const { error } = await ctx.supabase.from("team_audit_events").insert({
    venue_id: event.venueId,
    actor_user_id: ctx.userId,
    actor_membership_id: membership?.id ?? null,
    event_type: event.type,
    target_type: event.targetType,
    target_id: event.targetId ?? null,
    summary: event.summary,
    metadata: event.metadata ?? {},
  });

  if (error && !missingTeamTables(error.message)) {
    console.warn("Failed to write team audit event:", error.message);
  }
}

export async function inviteTeamMemberAction(
  raw: unknown,
): Promise<TeamActionResult> {
  const parsed = InviteMemberInput.safeParse(raw);
  if (!parsed.success) {
    return { ok: false, error: "Проверьте данные сотрудника." };
  }

  const ctx = await getWritableTeamContext();
  if (!ctx.ok) return ctx;

  if (ctx.mode === "sandbox" || !ctx.supabase) {
    return {
      ok: true,
      mode: "sandbox",
      message: "Sandbox: сотрудник добавлен в демо-режиме.",
    };
  }

  const wantsCredentials = Boolean(parsed.data.login || parsed.data.password);
  const loginEmail = wantsCredentials
    ? normalizeStaffLoginToEmail(parsed.data.login || parsed.data.email || "")
    : null;

  if (wantsCredentials && (!loginEmail || !parsed.data.password)) {
    return {
      ok: false,
      error:
        "Для доступа сотрудника укажите короткий логин/email и временный пароль от 6 символов.",
    };
  }

  let createdUserId: string | null = null;
  if (wantsCredentials && loginEmail && parsed.data.password) {
    const admin = getSupabaseAdmin();
    if (!admin) {
      return {
        ok: false,
        error:
          "На сервере не настроен SUPABASE_SERVICE_ROLE_KEY для создания логинов сотрудников.",
      };
    }

    const { data, error } = await admin.auth.admin.createUser({
      email: loginEmail,
      password: parsed.data.password,
      email_confirm: true,
      user_metadata: {
        full_name: parsed.data.fullName,
        venue_id: parsed.data.venueId,
        role: parsed.data.role,
      },
    });

    if (error || !data.user) {
      return {
        ok: false,
        error: error?.message ?? "Не удалось создать логин сотрудника.",
      };
    }

    createdUserId = data.user.id;
  }

  const { data: member, error } = await ctx.supabase
    .from("venue_memberships")
    .insert({
      venue_id: parsed.data.venueId,
      user_id: createdUserId,
      full_name: parsed.data.fullName,
      email: loginEmail || parsed.data.email || null,
      phone: parsed.data.phone || null,
      role: parsed.data.role,
      status: createdUserId || !parsed.data.email ? "active" : "invited",
      shift_label: parsed.data.shiftLabel || "",
      created_by: ctx.userId,
    })
    .select("id")
    .maybeSingle<{ id: string }>();

  if (error) {
    if (createdUserId) {
      await getSupabaseAdmin()?.auth.admin.deleteUser(createdUserId);
    }
    if (missingTeamTables(error.message)) {
      return {
        ok: false,
        error: "В базе нет таблиц команды. Примените миграцию 0004_team_os.sql.",
      };
    }
    return { ok: false, error: error.message };
  }

  await writeTeamAuditEvent(ctx, {
    venueId: parsed.data.venueId,
    type: "member_invited",
    targetType: "member",
    targetId: member?.id ?? null,
    summary: `Создан доступ для ${parsed.data.fullName}.`,
    metadata: {
      role: parsed.data.role,
      hasLogin: Boolean(createdUserId),
      email: loginEmail || parsed.data.email || null,
    },
  });

  revalidatePath("/team");
  return {
    ok: true,
    mode: "saved",
    message: createdUserId
      ? `Сотрудник добавлен. Логин: ${loginEmail}.`
      : "Сотрудник добавлен.",
  };
}

export async function updateTeamMemberStatusAction(
  raw: unknown,
): Promise<TeamActionResult> {
  const parsed = UpdateTeamMemberStatusInput.safeParse(raw);
  if (!parsed.success) {
    return { ok: false, error: "Некорректный статус сотрудника." };
  }

  const ctx = await getWritableTeamContext();
  if (!ctx.ok) return ctx;

  if (ctx.mode === "sandbox" || !ctx.supabase) {
    return {
      ok: true,
      mode: "sandbox",
      message: "Sandbox: статус доступа обновлен.",
    };
  }

  const { data, error } = await ctx.supabase
    .from("venue_memberships")
    .update({
      status: parsed.data.status,
      updated_at: new Date().toISOString(),
    })
    .eq("id", parsed.data.memberId)
    .eq("venue_id", parsed.data.venueId)
    .select("id")
    .maybeSingle();

  if (error) {
    if (missingTeamTables(error.message)) {
      return {
        ok: false,
        error: "В базе нет таблиц команды. Примените миграцию 0004_team_os.sql.",
      };
    }
    return { ok: false, error: error.message };
  }

  if (!data) {
    return { ok: false, error: "Сотрудник не найден или нет доступа." };
  }

  await writeTeamAuditEvent(ctx, {
    venueId: parsed.data.venueId,
    type: "member_status_updated",
    targetType: "member",
    targetId: parsed.data.memberId,
    summary:
      parsed.data.status === "active"
        ? "Доступ сотрудника активирован."
        : "Доступ сотрудника поставлен на паузу.",
    metadata: { status: parsed.data.status },
  });

  revalidatePath("/team");
  revalidatePath("/me");
  return {
    ok: true,
    mode: "saved",
    message:
      parsed.data.status === "active"
        ? "Доступ сотрудника активирован."
        : "Доступ сотрудника поставлен на паузу.",
  };
}

export async function resetTeamMemberPasswordAction(
  raw: unknown,
): Promise<TeamActionResult> {
  const parsed = ResetTeamMemberPasswordInput.safeParse(raw);
  if (!parsed.success) {
    return { ok: false, error: "Пароль должен быть не короче 6 символов." };
  }

  const ctx = await getWritableTeamContext();
  if (!ctx.ok) return ctx;

  if (ctx.mode === "sandbox" || !ctx.supabase) {
    return {
      ok: true,
      mode: "sandbox",
      message: "Sandbox: пароль сотрудника обновлен.",
    };
  }

  const { data: member, error: memberError } = await ctx.supabase
    .from("venue_memberships")
    .select("id,user_id,email")
    .eq("id", parsed.data.memberId)
    .eq("venue_id", parsed.data.venueId)
    .maybeSingle<{ id: string; user_id: string | null; email: string | null }>();

  if (memberError) return { ok: false, error: memberError.message };
  if (!member) {
    return { ok: false, error: "Сотрудник не найден или нет доступа." };
  }
  if (!member.user_id) {
    return {
      ok: false,
      error: "У сотрудника нет созданного логина. Создайте доступ заново.",
    };
  }

  const admin = getSupabaseAdmin();
  if (!admin) {
    return {
      ok: false,
      error:
        "На сервере не настроен SUPABASE_SERVICE_ROLE_KEY для сброса пароля.",
    };
  }

  const { error } = await admin.auth.admin.updateUserById(member.user_id, {
    password: parsed.data.password,
  });

  if (error) return { ok: false, error: error.message };

  await writeTeamAuditEvent(ctx, {
    venueId: parsed.data.venueId,
    type: "member_password_reset",
    targetType: "member",
    targetId: parsed.data.memberId,
    summary: `Пароль сотрудника обновлен${member.email ? `: ${member.email}` : ""}.`,
    metadata: { email: member.email },
  });

  revalidatePath("/team");
  return {
    ok: true,
    mode: "saved",
    message: `Пароль обновлен${member.email ? ` для ${member.email}` : ""}.`,
  };
}

export async function createTeamTaskAction(
  raw: unknown,
): Promise<TeamActionResult> {
  const parsed = CreateTeamTaskInput.safeParse(raw);
  if (!parsed.success) {
    return { ok: false, error: "Проверьте задачу и получателя." };
  }

  const ctx = await getWritableTeamContext();
  if (!ctx.ok) return ctx;

  if (ctx.mode === "sandbox" || !ctx.supabase) {
    return {
      ok: true,
      mode: "sandbox",
      message: "Sandbox: задача создана в демо-режиме.",
    };
  }

  const audienceType = parsed.data.audienceType;
  const insert = {
    venue_id: parsed.data.venueId,
    title: parsed.data.title,
    source: "manager" satisfies TeamTask["source"],
    priority: parsed.data.priority,
    status: "new" satisfies TeamTask["status"],
    audience_type: audienceType,
    audience_member_id:
      audienceType === "member" ? parsed.data.audienceMemberId : null,
    audience_role: audienceType === "role" ? parsed.data.audienceRole : null,
    due_label: parsed.data.dueLabel || "",
    created_by: ctx.userId,
  };

  const { data: task, error } = await ctx.supabase
    .from("team_tasks")
    .insert(insert)
    .select("id")
    .maybeSingle<{ id: string }>();

  if (error) {
    if (missingTeamTables(error.message)) {
      return {
        ok: false,
        error: "В базе нет таблиц команды. Примените миграцию 0004_team_os.sql.",
      };
    }
    return { ok: false, error: error.message };
  }

  await writeTeamAuditEvent(ctx, {
    venueId: parsed.data.venueId,
    type: "task_created",
    targetType: "task",
    targetId: task?.id ?? null,
    summary: `Создана задача: ${parsed.data.title}.`,
    metadata: {
      priority: parsed.data.priority,
      audienceType,
      audienceMemberId:
        audienceType === "member" ? parsed.data.audienceMemberId : null,
      audienceRole: audienceType === "role" ? parsed.data.audienceRole : null,
    },
  });

  revalidatePath("/team");
  return { ok: true, mode: "saved", message: "Задача создана." };
}

export async function updateTeamTaskStatusAction(
  raw: unknown,
): Promise<TeamActionResult> {
  const parsed = UpdateTaskStatusInput.safeParse(raw);
  if (!parsed.success) {
    return { ok: false, error: "Некорректный статус задачи." };
  }

  const ctx = await getWritableTeamContext();
  if (!ctx.ok) return ctx;

  if (ctx.mode === "sandbox" || !ctx.supabase) {
    return {
      ok: true,
      mode: "sandbox",
      message: "Sandbox: статус задачи обновлен в демо-режиме.",
    };
  }

  const { data, error } = await ctx.supabase
    .from("team_tasks")
    .update({ status: parsed.data.status, updated_at: new Date().toISOString() })
    .eq("id", parsed.data.taskId)
    .eq("venue_id", parsed.data.venueId)
    .select("id")
    .maybeSingle();

  if (error) {
    if (missingTeamTables(error.message)) {
      return {
        ok: false,
        error: "В базе нет таблиц команды. Примените миграцию 0004_team_os.sql.",
      };
    }
    return { ok: false, error: error.message };
  }

  if (!data) {
    return { ok: false, error: "Задача не найдена или нет доступа." };
  }

  await writeTeamAuditEvent(ctx, {
    venueId: parsed.data.venueId,
    type: "task_status_updated",
    targetType: "task",
    targetId: parsed.data.taskId,
    summary: `Статус задачи обновлен: ${parsed.data.status}.`,
    metadata: { status: parsed.data.status },
  });

  revalidatePath("/team");
  return { ok: true, mode: "saved", message: "Статус задачи обновлен." };
}

export async function addTaskCommentAction(
  raw: unknown,
): Promise<TeamActionResult> {
  const parsed = AddTaskCommentInput.safeParse(raw);
  if (!parsed.success) {
    return { ok: false, error: "Напишите комментарий к задаче." };
  }

  const ctx = await getWritableTeamContext();
  if (!ctx.ok) return ctx;

  if (ctx.mode === "sandbox" || !ctx.supabase) {
    return {
      ok: true,
      mode: "sandbox",
      message: "Sandbox: комментарий добавлен в демо-режиме.",
    };
  }

  const { data: membership } = await ctx.supabase
    .from("venue_memberships")
    .select("id")
    .eq("venue_id", parsed.data.venueId)
    .eq("user_id", ctx.userId)
    .maybeSingle<{ id: string }>();

  const { data: comment, error } = await ctx.supabase
    .from("team_task_comments")
    .insert({
      venue_id: parsed.data.venueId,
      task_id: parsed.data.taskId,
      author_membership_id: membership?.id ?? null,
      author_user_id: ctx.userId,
      body: parsed.data.body,
    })
    .select("id")
    .maybeSingle<{ id: string }>();

  if (error) {
    if (missingTeamTables(error.message)) {
      return {
        ok: false,
        error:
          "В базе нет таблиц коммуникации команды. Примените миграцию 0005_team_communication.sql.",
      };
    }
    return { ok: false, error: error.message };
  }

  await writeTeamAuditEvent(ctx, {
    venueId: parsed.data.venueId,
    type: "comment_added",
    targetType: "comment",
    targetId: comment?.id ?? null,
    summary: "Добавлен комментарий к задаче.",
    metadata: { taskId: parsed.data.taskId },
  });

  revalidatePath("/team");
  return { ok: true, mode: "saved", message: "Комментарий добавлен." };
}

export async function createTeamAnnouncementAction(
  raw: unknown,
): Promise<TeamActionResult> {
  const parsed = CreateAnnouncementInput.safeParse(raw);
  if (!parsed.success) {
    return { ok: false, error: "Проверьте объявление и получателя." };
  }

  const ctx = await getWritableTeamContext();
  if (!ctx.ok) return ctx;

  if (ctx.mode === "sandbox" || !ctx.supabase) {
    return {
      ok: true,
      mode: "sandbox",
      message: "Sandbox: объявление опубликовано в демо-режиме.",
    };
  }

  const { data: announcement, error } = await ctx.supabase
    .from("team_announcements")
    .insert({
      venue_id: parsed.data.venueId,
      title: parsed.data.title,
      body: parsed.data.body,
      priority: parsed.data.priority,
      audience_type: parsed.data.audienceType,
      audience_role:
        parsed.data.audienceType === "role" ? parsed.data.audienceRole : null,
      created_by: ctx.userId,
    })
    .select("id")
    .maybeSingle<{ id: string }>();

  if (error) {
    if (missingTeamTables(error.message)) {
      return {
        ok: false,
        error:
          "В базе нет таблиц коммуникации команды. Примените миграцию 0005_team_communication.sql.",
      };
    }
    return { ok: false, error: error.message };
  }

  await writeTeamAuditEvent(ctx, {
    venueId: parsed.data.venueId,
    type: "announcement_created",
    targetType: "announcement",
    targetId: announcement?.id ?? null,
    summary: `Опубликовано объявление: ${parsed.data.title}.`,
    metadata: {
      priority: parsed.data.priority,
      audienceType: parsed.data.audienceType,
      audienceRole:
        parsed.data.audienceType === "role" ? parsed.data.audienceRole : null,
    },
  });

  revalidatePath("/team");
  return { ok: true, mode: "saved", message: "Объявление опубликовано." };
}
