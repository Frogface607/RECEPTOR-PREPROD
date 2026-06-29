"use server";

import { revalidatePath } from "next/cache";
import { z } from "zod";
import { getCurrentUser } from "@/lib/auth/session";
import { normalizeStaffLoginToEmail } from "@/lib/auth/staff-login";
import { getSupabaseAdmin } from "@/lib/db/admin";
import { getServerSupabase } from "@/lib/db/server";
import { normalizeIikoStaffName } from "@/lib/team/team-iiko-staff-import";
import { listLearningItemsForRole } from "@/lib/team/team-learning";
import type { TeamLearningStandardStatus } from "@/lib/team/team-learning-standards";
import { TEAM_ROLES, type TeamRoleId, type TeamTask } from "@/lib/team/team-os";
import { selectLaborRateTasksToClose } from "@/lib/team/team-task-autoresolve";

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
const OPEN_TASK_STATUSES = [
  "new",
  "accepted",
  "in_progress",
] satisfies TeamTask["status"][];
const TaskSourceSchema = z.enum(["owner", "copilot", "manager", "chef"]);
const TaskAudienceTypeSchema = z.enum(["member", "role", "venue"]);
const LearningStandardStatusSchema = z.enum(["required", "ready", "hidden"]);
const AnnouncementAudienceTypeSchema = z.enum(["role", "venue"]);
const AnnouncementPrioritySchema = z.enum(["normal", "important"]);
const MemberStatusSchema = z.enum(["active", "paused"]);
const NonNegativeMoneySchema = z.coerce
  .number()
  .min(0)
  .max(1_000_000)
  .default(0);
const ShiftDateSchema = z.string().regex(/^\d{4}-\d{2}-\d{2}$/);
const ShiftTimeSchema = z.string().regex(/^([01]\d|2[0-3]):[0-5]\d$/);

const InviteMemberInput = z.object({
  venueId: z.string().min(1),
  fullName: z.string().trim().min(2).max(120),
  email: z.string().trim().email().optional().or(z.literal("")),
  phone: z.string().trim().max(40).optional().or(z.literal("")),
  login: z.string().trim().max(80).optional().or(z.literal("")),
  password: z.string().min(6).max(72).optional().or(z.literal("")),
  role: TeamRoleIdSchema,
  shiftLabel: z.string().trim().max(120).optional().or(z.literal("")),
  hourlyRate: NonNegativeMoneySchema,
  shiftPay: NonNegativeMoneySchema,
  revenueBonusPct: z.coerce.number().min(0).max(100).default(0),
});

const ImportIikoMembersInput = z.object({
  venueId: z.string().min(1),
  members: z
    .array(
      z.object({
        fullName: z.string().trim().min(2).max(120),
        role: TeamRoleIdSchema.default("service"),
        shiftLabel: z.string().trim().max(120).optional().or(z.literal("")),
      }),
    )
    .min(1)
    .max(20),
});

const CreateTeamTaskInput = z
  .object({
    venueId: z.string().min(1),
    title: z.string().trim().min(3).max(240),
    source: TaskSourceSchema.default("manager"),
    priority: TaskPrioritySchema.default("medium"),
    audienceType: TaskAudienceTypeSchema,
    audienceMemberId: z.string().trim().optional().or(z.literal("")),
    audienceRole: TeamRoleIdSchema.optional(),
    dueLabel: z.string().trim().max(120).optional().or(z.literal("")),
    sourceLabel: z.string().trim().max(80).optional().or(z.literal("")),
    dedupeOpenTask: z.boolean().optional().default(false),
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

const SaveTeamLearningStandardInput = z.object({
  venueId: z.string().min(1),
  roleId: TeamRoleIdSchema,
  moduleId: z.string().trim().min(1),
  status: LearningStandardStatusSchema,
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

const UpdateTeamMemberLaborRateInput = z.object({
  venueId: z.string().min(1),
  memberId: z.string().min(1),
  hourlyRate: NonNegativeMoneySchema,
  shiftPay: NonNegativeMoneySchema,
  revenueBonusPct: z.coerce.number().min(0).max(100).default(0),
});

const BulkUpdateTeamMemberLaborRatesInput = z
  .object({
    venueId: z.string().min(1),
    memberIds: z.array(z.string().min(1)).min(1).max(100),
    hourlyRate: NonNegativeMoneySchema,
    shiftPay: NonNegativeMoneySchema,
    revenueBonusPct: z.coerce.number().min(0).max(100).default(0),
  })
  .refine(
    (value) =>
      value.hourlyRate > 0 || value.shiftPay > 0 || value.revenueBonusPct > 0,
    {
      message: "Укажите хотя бы один тип ставки.",
    },
  );

const SaveTeamShiftPlanInput = z
  .object({
    venueId: z.string().min(1),
    memberId: z.string().min(1),
    shiftDate: ShiftDateSchema,
    shiftStart: ShiftTimeSchema.optional().or(z.literal("")),
    shiftEnd: ShiftTimeSchema.optional().or(z.literal("")),
    isDayOff: z.boolean().default(false),
    note: z.string().trim().max(240).optional().or(z.literal("")),
  })
  .superRefine((value, ctx) => {
    if (!value.isDayOff && (!value.shiftStart || !value.shiftEnd)) {
      ctx.addIssue({
        code: "custom",
        path: ["shiftStart"],
        message: "Укажите начало и конец смены.",
      });
    }
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

type CreateTeamTaskData = z.output<typeof CreateTeamTaskInput>;
type ImportIikoMembersData = z.output<typeof ImportIikoMembersInput>;
type SaveTeamLearningStandardData = z.output<
  typeof SaveTeamLearningStandardInput
>;

type LaborRateRow = {
  id: string;
  full_name: string;
  hourly_rate: number | string | null;
  shift_pay: number | string | null;
  revenue_bonus_pct: number | string | null;
};

type AutoCloseTaskRow = {
  id: string;
  title: string;
  status: TeamTask["status"];
  audience_member_id: string | null;
};

type TeamAuditEventInput = {
  venueId: string;
  type:
    | "member_invited"
    | "member_status_updated"
    | "member_password_reset"
    | "member_labor_rate_updated"
    | "task_created"
    | "task_status_updated"
    | "comment_added"
    | "announcement_created"
    | "shift_plan_updated"
    | "learning_standard_updated";
  targetType:
    | "member"
    | "task"
    | "comment"
    | "announcement"
    | "shift_plan"
    | "learning_standard";
  targetId?: string | null;
  summary: string;
  metadata?: Record<string, unknown>;
};

function missingTeamTables(message: string): boolean {
  return /venue_memberships|team_tasks|team_task_comments|team_announcements|team_audit_events|team_learning_standards|team_shift_plans|hourly_rate|shift_pay|revenue_bonus_pct|shift_date|shift_start|shift_end|is_day_off|relation .* does not exist|column .* does not exist/i.test(
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
  if (!user)
    return { ok: false, error: "Нужно войти, чтобы работать с командой." };

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

async function findExistingOpenTask(
  ctx: WritableTeamContext,
  task: CreateTeamTaskData,
): Promise<{ id: string } | null> {
  if (ctx.mode === "sandbox" || !ctx.supabase) return null;

  let query = ctx.supabase
    .from("team_tasks")
    .select("id")
    .eq("venue_id", task.venueId)
    .eq("title", task.title)
    .eq("audience_type", task.audienceType)
    .in("status", OPEN_TASK_STATUSES)
    .limit(1);

  if (task.audienceType === "member") {
    query = query.eq("audience_member_id", task.audienceMemberId);
  } else if (task.audienceType === "role") {
    query = query.eq("audience_role", task.audienceRole);
  } else {
    query = query.is("audience_member_id", null).is("audience_role", null);
  }

  const { data, error } = await query.maybeSingle<{ id: string }>();
  if (error) {
    if (missingTeamTables(error.message)) return null;
    throw new Error(error.message);
  }

  return data ?? null;
}

function normalizeTaskSourceLabel(value: unknown): string | null {
  if (typeof value !== "string") return null;
  const normalized = value.replace(/\s+/g, " ").trim();
  if (!normalized) return null;
  return normalized.length > 80 ? `${normalized.slice(0, 77).trim()}...` : normalized;
}

async function findTaskSourceLabel(
  ctx: WritableTeamContext,
  venueId: string,
  taskId: string,
): Promise<string | null> {
  if (ctx.mode === "sandbox" || !ctx.supabase) return null;

  const { data, error } = await ctx.supabase
    .from("team_audit_events")
    .select("metadata")
    .eq("venue_id", venueId)
    .eq("event_type", "task_created")
    .eq("target_type", "task")
    .eq("target_id", taskId)
    .order("created_at", { ascending: false })
    .limit(1)
    .maybeSingle<{ metadata: Record<string, unknown> | null }>();

  if (error) return null;
  return normalizeTaskSourceLabel(data?.metadata?.sourceLabel);
}

async function closeLaborRateTasksForMembers(
  ctx: WritableTeamContext,
  venueId: string,
  memberIds: string[],
): Promise<string[]> {
  if (ctx.mode === "sandbox" || !ctx.supabase || memberIds.length === 0) {
    return [];
  }

  const uniqueMemberIds = [...new Set(memberIds.filter(Boolean))];
  if (uniqueMemberIds.length === 0) return [];

  const { data, error } = await ctx.supabase
    .from("team_tasks")
    .select("id,title,status,audience_member_id")
    .eq("venue_id", venueId)
    .eq("audience_type", "member")
    .in("audience_member_id", uniqueMemberIds)
    .in("status", OPEN_TASK_STATUSES);

  if (error) {
    if (missingTeamTables(error.message)) return [];
    throw new Error(error.message);
  }

  const taskIds = selectLaborRateTasksToClose(
    ((data ?? []) as AutoCloseTaskRow[]).map((task) => ({
      id: task.id,
      title: task.title,
      status: task.status,
      audience: {
        type: "member",
        memberId: task.audience_member_id ?? "",
      },
    })),
    uniqueMemberIds,
  ).map((task) => task.id);

  if (taskIds.length === 0) return [];

  const { error: updateError } = await ctx.supabase
    .from("team_tasks")
    .update({
      status: "done" satisfies TeamTask["status"],
      updated_at: new Date().toISOString(),
    })
    .eq("venue_id", venueId)
    .in("id", taskIds);

  if (updateError) {
    if (missingTeamTables(updateError.message)) return [];
    throw new Error(updateError.message);
  }

  await writeTeamAuditEvent(ctx, {
    venueId,
    type: "task_status_updated",
    targetType: "task",
    targetId: taskIds[0] ?? null,
    summary: `Автоматически закрыты задачи ФОТ после обновления ставок: ${taskIds.length}.`,
    metadata: {
      memberIds: uniqueMemberIds,
      taskIds,
      status: "done",
      sourceLabel: "ФОТ setup",
    },
  });

  return taskIds;
}

function parseActionInput(raw: unknown): Record<string, unknown> {
  if (raw instanceof FormData) {
    return Object.fromEntries(raw.entries());
  }
  return typeof raw === "object" && raw !== null
    ? (raw as Record<string, unknown>)
    : {};
}

function uniqueIikoImportMembers(
  members: ImportIikoMembersData["members"],
): ImportIikoMembersData["members"] {
  const seen = new Set<string>();

  return members.flatMap((member) => {
    const key = normalizeIikoStaffName(member.fullName);
    if (!key || seen.has(key)) return [];
    seen.add(key);
    return [{ ...member, fullName: member.fullName.trim() }];
  });
}

function hasSavedLaborRate(row: LaborRateRow): boolean {
  return Boolean(
    Number(row.hourly_rate ?? 0) ||
    Number(row.shift_pay ?? 0) ||
    Number(row.revenue_bonus_pct ?? 0),
  );
}

function learningStandardStatusLabel(
  status: TeamLearningStandardStatus,
): string {
  if (status === "required") return "обязательный допуск";
  if (status === "hidden") return "скрыт";
  return "развитие";
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
      hourly_rate: parsed.data.hourlyRate,
      shift_pay: parsed.data.shiftPay,
      revenue_bonus_pct: parsed.data.revenueBonusPct,
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
        error:
          "В базе нет таблиц команды. Примените миграцию 0004_team_os.sql.",
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
      hourlyRate: parsed.data.hourlyRate,
      shiftPay: parsed.data.shiftPay,
      revenueBonusPct: parsed.data.revenueBonusPct,
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

export async function importIikoTeamMembersAction(
  raw: unknown,
): Promise<TeamActionResult> {
  const parsed = ImportIikoMembersInput.safeParse(raw);
  if (!parsed.success) {
    return { ok: false, error: "Проверьте сотрудников из iiko для импорта." };
  }

  const members = uniqueIikoImportMembers(parsed.data.members);
  if (members.length === 0) {
    return { ok: false, error: "Нет сотрудников iiko для импорта." };
  }

  const ctx = await getWritableTeamContext();
  if (!ctx.ok) return ctx;

  if (ctx.mode === "sandbox" || !ctx.supabase) {
    return {
      ok: true,
      mode: "sandbox",
      message: `Sandbox: подготовлен импорт из iiko (${members.length}).`,
    };
  }

  const { data: existingMembers, error: existingError } = await ctx.supabase
    .from("venue_memberships")
    .select("full_name")
    .eq("venue_id", parsed.data.venueId);

  if (existingError) {
    if (missingTeamTables(existingError.message)) {
      return {
        ok: false,
        error:
          "В базе нет таблиц команды. Примените миграцию 0004_team_os.sql.",
      };
    }
    return { ok: false, error: existingError.message };
  }

  const existingNames = new Set(
    (existingMembers ?? []).map((member) =>
      normalizeIikoStaffName(String(member.full_name ?? "")),
    ),
  );
  const rows = members
    .filter(
      (member) => !existingNames.has(normalizeIikoStaffName(member.fullName)),
    )
    .map((member) => ({
      venue_id: parsed.data.venueId,
      user_id: null,
      full_name: member.fullName,
      email: null,
      phone: null,
      role: member.role,
      status: "active",
      shift_label: member.shiftLabel || "из смен iiko",
      hourly_rate: 0,
      shift_pay: 0,
      revenue_bonus_pct: 0,
      created_by: ctx.userId,
    }));

  if (rows.length === 0) {
    return {
      ok: true,
      mode: "saved",
      message: "Сотрудники из iiko уже есть в Team OS.",
    };
  }

  const { data: createdMembers, error } = await ctx.supabase
    .from("venue_memberships")
    .insert(rows)
    .select("id,full_name");

  if (error) {
    if (missingTeamTables(error.message)) {
      return {
        ok: false,
        error:
          "В базе нет таблиц команды. Примените миграцию 0004_team_os.sql.",
      };
    }
    return { ok: false, error: error.message };
  }

  const names = (createdMembers ?? rows)
    .map((member) => String(member.full_name ?? ""))
    .filter(Boolean);

  await writeTeamAuditEvent(ctx, {
    venueId: parsed.data.venueId,
    type: "member_invited",
    targetType: "member",
    targetId: createdMembers?.[0]?.id ?? null,
    summary: `Импортированы сотрудники из iiko: ${names.join(", ")}.`,
    metadata: {
      source: "iiko",
      count: rows.length,
      names,
    },
  });

  revalidatePath("/team");
  revalidatePath(`/dashboard/${parsed.data.venueId}`);
  return {
    ok: true,
    mode: "saved",
    message: `Добавлены сотрудники из iiko: ${names.join(", ")}. Теперь заполните ставки ФОТ.`,
  };
}

export async function updateTeamMemberLaborRateAction(
  raw: unknown,
): Promise<TeamActionResult> {
  const parsed = UpdateTeamMemberLaborRateInput.safeParse(raw);
  if (!parsed.success) {
    return { ok: false, error: "Проверьте ставки сотрудника." };
  }

  const ctx = await getWritableTeamContext();
  if (!ctx.ok) return ctx;

  if (
    parsed.data.venueId === "dev-venue" ||
    ctx.mode === "sandbox" ||
    !ctx.supabase
  ) {
    return {
      ok: true,
      mode: "sandbox",
      message: "Sandbox: ставки сотрудника обновлены.",
    };
  }

  const { data, error } = await ctx.supabase
    .from("venue_memberships")
    .update({
      hourly_rate: parsed.data.hourlyRate,
      shift_pay: parsed.data.shiftPay,
      revenue_bonus_pct: parsed.data.revenueBonusPct,
      updated_at: new Date().toISOString(),
    })
    .eq("id", parsed.data.memberId)
    .eq("venue_id", parsed.data.venueId)
    .select("id,full_name")
    .maybeSingle<{ id: string; full_name: string }>();

  if (error) {
    if (missingTeamTables(error.message)) {
      return {
        ok: false,
        error:
          "В базе нет полей ставок команды. Примените миграцию 0009_team_labor_rates.sql.",
      };
    }
    return { ok: false, error: error.message };
  }

  if (!data) {
    return { ok: false, error: "Сотрудник не найден или нет доступа." };
  }

  await writeTeamAuditEvent(ctx, {
    venueId: parsed.data.venueId,
    type: "member_labor_rate_updated",
    targetType: "member",
    targetId: parsed.data.memberId,
    summary: `Ставки ФОТ обновлены: ${data.full_name}.`,
    metadata: {
      hourlyRate: parsed.data.hourlyRate,
      shiftPay: parsed.data.shiftPay,
      revenueBonusPct: parsed.data.revenueBonusPct,
    },
  });

  let closedTaskIds: string[] = [];
  let taskCloseWarning = false;
  try {
    closedTaskIds = await closeLaborRateTasksForMembers(
      ctx,
      parsed.data.venueId,
      [parsed.data.memberId],
    );
  } catch (error) {
    taskCloseWarning = true;
    console.warn("Failed to auto-close labor rate task:", error);
  }

  revalidatePath("/team");
  revalidatePath("/me");
  revalidatePath(`/dashboard/${parsed.data.venueId}`);
  return {
    ok: true,
    mode: "saved",
    message:
      closedTaskIds.length > 0
        ? "Ставки сотрудника обновлены, задача ФОТ закрыта."
        : taskCloseWarning
          ? "Ставки сотрудника обновлены. Задача ФОТ не закрылась автоматически."
          : "Ставки сотрудника обновлены.",
  };
}

export async function bulkUpdateTeamMemberLaborRatesAction(
  raw: unknown,
): Promise<TeamActionResult> {
  const parsed = BulkUpdateTeamMemberLaborRatesInput.safeParse(raw);
  if (!parsed.success) {
    return { ok: false, error: "Проверьте массовую ставку ФОТ." };
  }

  const ctx = await getWritableTeamContext();
  if (!ctx.ok) return ctx;

  const memberIds = [...new Set(parsed.data.memberIds)];

  if (
    parsed.data.venueId === "dev-venue" ||
    ctx.mode === "sandbox" ||
    !ctx.supabase
  ) {
    return {
      ok: true,
      mode: "sandbox",
      message: `Sandbox: массовая ставка ФОТ применена к ${memberIds.length}.`,
    };
  }

  const { data: members, error: membersError } = await ctx.supabase
    .from("venue_memberships")
    .select("id,full_name,hourly_rate,shift_pay,revenue_bonus_pct")
    .eq("venue_id", parsed.data.venueId)
    .in("id", memberIds);

  if (membersError) {
    if (missingTeamTables(membersError.message)) {
      return {
        ok: false,
        error:
          "В базе нет полей ставок команды. Примените миграцию 0009_team_labor_rates.sql.",
      };
    }
    return { ok: false, error: membersError.message };
  }

  const targetMembers = ((members ?? []) as LaborRateRow[]).filter(
    (member) => !hasSavedLaborRate(member),
  );
  if (targetMembers.length === 0) {
    return {
      ok: true,
      mode: "saved",
      message: "Ставки уже заполнены, массовое обновление не потребовалось.",
    };
  }

  const targetIds = targetMembers.map((member) => member.id);
  const { error } = await ctx.supabase
    .from("venue_memberships")
    .update({
      hourly_rate: parsed.data.hourlyRate,
      shift_pay: parsed.data.shiftPay,
      revenue_bonus_pct: parsed.data.revenueBonusPct,
      updated_at: new Date().toISOString(),
    })
    .eq("venue_id", parsed.data.venueId)
    .in("id", targetIds);

  if (error) {
    if (missingTeamTables(error.message)) {
      return {
        ok: false,
        error:
          "В базе нет полей ставок команды. Примените миграцию 0009_team_labor_rates.sql.",
      };
    }
    return { ok: false, error: error.message };
  }

  await writeTeamAuditEvent(ctx, {
    venueId: parsed.data.venueId,
    type: "member_labor_rate_updated",
    targetType: "member",
    targetId: targetIds[0] ?? null,
    summary: `Массово обновлены ставки ФОТ: ${targetMembers.length}.`,
    metadata: {
      memberIds: targetIds,
      names: targetMembers.map((member) => member.full_name),
      hourlyRate: parsed.data.hourlyRate,
      shiftPay: parsed.data.shiftPay,
      revenueBonusPct: parsed.data.revenueBonusPct,
    },
  });

  let closedTaskIds: string[] = [];
  let taskCloseWarning = false;
  try {
    closedTaskIds = await closeLaborRateTasksForMembers(
      ctx,
      parsed.data.venueId,
      targetIds,
    );
  } catch (error) {
    taskCloseWarning = true;
    console.warn("Failed to auto-close labor rate tasks:", error);
  }

  revalidatePath("/team");
  revalidatePath("/me");
  revalidatePath(`/dashboard/${parsed.data.venueId}`);
  return {
    ok: true,
    mode: "saved",
    message:
      `Ставки ФОТ применены к ${targetMembers.length} сотрудникам без ставки.` +
      (closedTaskIds.length > 0
        ? ` Закрыто задач ФОТ: ${closedTaskIds.length}.`
        : taskCloseWarning
          ? " Задачи ФОТ не закрылись автоматически."
          : ""),
  };
}

export async function saveTeamShiftPlanAction(
  raw: unknown,
): Promise<TeamActionResult> {
  const parsed = SaveTeamShiftPlanInput.safeParse(raw);
  if (!parsed.success) {
    return { ok: false, error: "Проверьте дату и время смены." };
  }

  const ctx = await getWritableTeamContext();
  if (!ctx.ok) return ctx;

  if (ctx.mode === "sandbox" || !ctx.supabase) {
    return {
      ok: true,
      mode: "sandbox",
      message: "Sandbox: план смены сохранен.",
    };
  }

  const { data: member, error: memberError } = await ctx.supabase
    .from("venue_memberships")
    .select("id,full_name")
    .eq("id", parsed.data.memberId)
    .eq("venue_id", parsed.data.venueId)
    .maybeSingle<{ id: string; full_name: string }>();

  if (memberError) {
    if (missingTeamTables(memberError.message)) {
      return {
        ok: false,
        error: "В базе нет таблиц Team OS. Примените миграции команды.",
      };
    }
    return { ok: false, error: memberError.message };
  }

  if (!member) {
    return { ok: false, error: "Сотрудник не найден или нет доступа." };
  }

  const { data, error } = await ctx.supabase
    .from("team_shift_plans")
    .upsert(
      {
        venue_id: parsed.data.venueId,
        membership_id: parsed.data.memberId,
        shift_date: parsed.data.shiftDate,
        shift_start: parsed.data.isDayOff ? null : parsed.data.shiftStart,
        shift_end: parsed.data.isDayOff ? null : parsed.data.shiftEnd,
        is_day_off: parsed.data.isDayOff,
        note: parsed.data.note ?? "",
        created_by: ctx.userId,
        updated_at: new Date().toISOString(),
      },
      { onConflict: "venue_id,membership_id,shift_date" },
    )
    .select("id")
    .maybeSingle<{ id: string }>();

  if (error) {
    if (missingTeamTables(error.message)) {
      return {
        ok: false,
        error:
          "В базе нет таблицы планов смен. Примените миграцию 0010_team_shift_plans.sql.",
      };
    }
    return { ok: false, error: error.message };
  }

  await writeTeamAuditEvent(ctx, {
    venueId: parsed.data.venueId,
    type: "shift_plan_updated",
    targetType: "shift_plan",
    targetId: data?.id ?? null,
    summary: parsed.data.isDayOff
      ? `Поставлен выходной: ${member.full_name}, ${parsed.data.shiftDate}.`
      : `План смены обновлен: ${member.full_name}, ${parsed.data.shiftDate} ${parsed.data.shiftStart}-${parsed.data.shiftEnd}.`,
    metadata: {
      memberId: parsed.data.memberId,
      shiftDate: parsed.data.shiftDate,
      shiftStart: parsed.data.shiftStart,
      shiftEnd: parsed.data.shiftEnd,
      isDayOff: parsed.data.isDayOff,
    },
  });

  revalidatePath("/team");
  revalidatePath("/me");
  revalidatePath(`/dashboard/${parsed.data.venueId}`);
  return { ok: true, mode: "saved", message: "План смены сохранен." };
}

export async function saveTeamLearningStandardAction(
  raw: unknown,
): Promise<TeamActionResult> {
  const parsed = SaveTeamLearningStandardInput.safeParse(parseActionInput(raw));
  if (!parsed.success) {
    return { ok: false, error: "Проверьте стандарт обучения." };
  }

  const item = listLearningItemsForRole(parsed.data.roleId).find(
    (learningItem) => learningItem.id === parsed.data.moduleId,
  );
  if (!item) {
    return {
      ok: false,
      error: "Материал не входит в эту роль.",
    };
  }

  const ctx = await getWritableTeamContext();
  if (!ctx.ok) return ctx;

  if (
    parsed.data.venueId === "dev-venue" ||
    ctx.mode === "sandbox" ||
    !ctx.supabase
  ) {
    revalidatePath("/team");
    return {
      ok: true,
      mode: "sandbox",
      message: "Sandbox: стандарт роли обновлен.",
    };
  }

  const payload = learningStandardPayload(parsed.data, ctx.userId);
  const { error } = await ctx.supabase
    .from("team_learning_standards")
    .upsert(payload, {
      onConflict: "venue_id,role,module_id",
    });

  if (error) {
    if (missingTeamTables(error.message)) {
      return {
        ok: false,
        error:
          "В базе нет таблицы стандартов обучения. Примените миграцию 0011_team_learning_standards.sql.",
      };
    }
    return { ok: false, error: error.message };
  }

  await writeTeamAuditEvent(ctx, {
    venueId: parsed.data.venueId,
    type: "learning_standard_updated",
    targetType: "learning_standard",
    targetId: null,
    summary: `Стандарт обучения обновлен: ${parsed.data.roleId} / ${item.title} -> ${learningStandardStatusLabel(parsed.data.status)}.`,
    metadata: {
      roleId: parsed.data.roleId,
      moduleId: parsed.data.moduleId,
      status: parsed.data.status,
    },
  });

  revalidatePath("/team");
  revalidatePath("/me");
  revalidatePath("/me/learning");
  return { ok: true, mode: "saved", message: "Стандарт роли обновлен." };
}

function learningStandardPayload(
  data: SaveTeamLearningStandardData,
  userId: string,
) {
  return {
    venue_id: data.venueId,
    role: data.roleId,
    module_id: data.moduleId,
    status: data.status,
    updated_by: userId,
    updated_at: new Date().toISOString(),
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
        error:
          "В базе нет таблиц команды. Примените миграцию 0004_team_os.sql.",
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
    .maybeSingle<{
      id: string;
      user_id: string | null;
      email: string | null;
    }>();

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

  if (parsed.data.dedupeOpenTask) {
    try {
      const existingTask = await findExistingOpenTask(ctx, parsed.data);
      if (existingTask) {
        revalidatePath("/team");
        return {
          ok: true,
          mode: "saved",
          message: "Задача уже есть.",
        };
      }
    } catch (error) {
      return {
        ok: false,
        error:
          error instanceof Error
            ? error.message
            : "Не удалось проверить дубли задач.",
      };
    }
  }

  const insert = {
    venue_id: parsed.data.venueId,
    title: parsed.data.title,
    source: parsed.data.source satisfies TeamTask["source"],
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
        error:
          "В базе нет таблиц команды. Примените миграцию 0004_team_os.sql.",
      };
    }
    return { ok: false, error: error.message };
  }

  const sourceLabel = parsed.data.sourceLabel?.trim() || null;

  await writeTeamAuditEvent(ctx, {
    venueId: parsed.data.venueId,
    type: "task_created",
    targetType: "task",
    targetId: task?.id ?? null,
    summary: `Создана задача: ${parsed.data.title}.`,
    metadata: {
      source: parsed.data.source,
      sourceLabel,
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
    .update({
      status: parsed.data.status,
      updated_at: new Date().toISOString(),
    })
    .eq("id", parsed.data.taskId)
    .eq("venue_id", parsed.data.venueId)
    .select("id")
    .maybeSingle();

  if (error) {
    if (missingTeamTables(error.message)) {
      return {
        ok: false,
        error:
          "В базе нет таблиц команды. Примените миграцию 0004_team_os.sql.",
      };
    }
    return { ok: false, error: error.message };
  }

  if (!data) {
    return { ok: false, error: "Задача не найдена или нет доступа." };
  }

  const sourceLabel = await findTaskSourceLabel(
    ctx,
    parsed.data.venueId,
    parsed.data.taskId,
  );

  await writeTeamAuditEvent(ctx, {
    venueId: parsed.data.venueId,
    type: "task_status_updated",
    targetType: "task",
    targetId: parsed.data.taskId,
    summary: `Статус задачи обновлен: ${parsed.data.status}.`,
    metadata: { status: parsed.data.status, sourceLabel },
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
