import { getCurrentUser } from "@/lib/auth/session";
import { getServerSupabase } from "@/lib/db/server";
import {
  DEMO_TEAM_AUDIT_EVENTS,
  DEMO_TASK_COMMENTS,
  DEMO_STAFF,
  DEMO_TEAM_ANNOUNCEMENTS,
  DEMO_TEAM_TASKS,
  TEAM_ROLES,
  getTeamRole,
  listAnnouncementsForRole,
  listTasksForMember,
  roleCan,
  type StaffMember,
  type TeamAnnouncement,
  type TeamAnnouncementRead,
  type TeamAuditEvent,
  type TeamAuditEventType,
  type TeamTaskComment,
  type TeamRoleId,
  type TeamTask,
} from "./team-os";
import type { TeamLearningProgress } from "./team-learning-progress";
import {
  normalizeLearningStandardStatus,
  type TeamLearningStandardOverride,
} from "./team-learning-standards";
import type { TeamShiftPlan } from "./team-shift-plan";

type DbMembership = {
  id: string;
  venue_id: string;
  user_id?: string | null;
  full_name: string;
  email?: string | null;
  role: string;
  status: string;
  shift_label: string | null;
  hourly_rate?: number | string | null;
  shift_pay?: number | string | null;
  revenue_bonus_pct?: number | string | null;
};

type DbTask = {
  id: string;
  venue_id: string;
  title: string;
  source: string;
  source_label?: string | null;
  priority: string;
  status: string;
  audience_type: string;
  audience_member_id: string | null;
  audience_role: string | null;
  due_label: string | null;
};

type DbTaskComment = {
  id: string;
  venue_id: string;
  task_id: string;
  author_membership_id: string | null;
  body: string;
  created_at: string | null;
};

type DbAnnouncement = {
  id: string;
  venue_id: string;
  title: string;
  body: string;
  priority: string;
  audience_type: string;
  audience_role: string | null;
  created_at: string | null;
};

type DbAnnouncementRead = {
  announcement_id: string;
  membership_id: string;
  read_at: string | null;
};

type DbAuditEvent = {
  id: string;
  venue_id: string;
  event_type: string;
  target_type: string;
  target_id: string | null;
  summary: string;
  metadata?: unknown;
  created_at: string | null;
};

type DbLearningProgress = {
  venue_id: string;
  membership_id: string;
  user_id: string | null;
  module_id: string;
  best_percentage: number | null;
  last_percentage: number | null;
  correct_count: number | null;
  total_questions: number | null;
  passed: boolean | null;
  answers: unknown;
  completed_at: string | null;
  updated_at: string | null;
};

type DbShiftPlan = {
  id: string;
  venue_id: string;
  membership_id: string;
  shift_date: string;
  shift_start: string | null;
  shift_end: string | null;
  is_day_off: boolean | null;
  note: string | null;
  updated_at: string | null;
};

type DbLearningStandard = {
  venue_id: string;
  role: string;
  module_id: string;
  status: string | null;
  updated_at: string | null;
};

type DbMembershipWithVenue = DbMembership & {
  venues?: { name: string | null; city: string | null } | null;
};

export type TeamWorkspace = {
  mode: "saved" | "sandbox";
  venueId: string;
  venueName: string;
  venueMeta: string;
  staff: StaffMember[];
  tasks: TeamTask[];
  comments: TeamTaskComment[];
  announcements: TeamAnnouncement[];
  announcementReads: TeamAnnouncementRead[];
  auditEvents: TeamAuditEvent[];
  learningProgress: TeamLearningProgress[];
  learningStandards: TeamLearningStandardOverride[];
  shiftPlans: TeamShiftPlan[];
};

export type PersonalTeamWorkspace =
  | {
      ok: true;
      mode: "saved" | "sandbox";
      venueId: string;
      venueName: string;
      member: StaffMember;
      tasks: TeamTask[];
      comments: TeamTaskComment[];
      announcements: TeamAnnouncement[];
      announcementReads: TeamAnnouncementRead[];
      learningProgress: TeamLearningProgress[];
      learningStandards: TeamLearningStandardOverride[];
      shiftPlans: TeamShiftPlan[];
    }
  | { ok: false; reason: "unauthenticated" | "no_membership" };

const ROLE_IDS = new Set<TeamRoleId>(TEAM_ROLES.map((role) => role.id));
const TASK_SOURCES = new Set<TeamTask["source"]>([
  "owner",
  "copilot",
  "manager",
  "chef",
]);
const TASK_PRIORITIES = new Set<TeamTask["priority"]>([
  "high",
  "medium",
  "low",
]);
const TASK_STATUSES = new Set<TeamTask["status"]>([
  "new",
  "accepted",
  "in_progress",
  "done",
  "verified",
]);
const TASK_SELECT_COLUMNS =
  "id,venue_id,title,source,source_label,priority,status,audience_type,audience_member_id,audience_role,due_label";
const TASK_SELECT_COLUMNS_LEGACY =
  "id,venue_id,title,source,priority,status,audience_type,audience_member_id,audience_role,due_label";

function isMissingTeamTable(message: string): boolean {
  return /venue_memberships|team_tasks|team_task_comments|team_announcements|team_announcement_reads|team_audit_events|team_learning_progress|team_learning_standards|team_shift_plans|hourly_rate|shift_pay|revenue_bonus_pct|shift_date|shift_start|shift_end|is_day_off|relation .* does not exist|column .* does not exist/i.test(
    message,
  );
}

function missingSourceLabelColumn(message: string): boolean {
  return /source_label/i.test(message);
}

function formatCreatedAtLabel(value: string | null): string {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";

  return new Intl.DateTimeFormat("ru-RU", {
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

export function normalizeTeamRoleId(
  value: string | null | undefined,
): TeamRoleId {
  return value && ROLE_IDS.has(value as TeamRoleId)
    ? (value as TeamRoleId)
    : "service";
}

export function mapMembershipRow(row: DbMembership): StaffMember {
  return {
    id: row.id,
    userId: row.user_id ?? null,
    name: row.full_name,
    email: row.email ?? null,
    roleId: normalizeTeamRoleId(row.role),
    venueId: row.venue_id,
    status:
      row.status === "active" ||
      row.status === "invited" ||
      row.status === "paused"
        ? row.status
        : "invited",
    shiftLabel: row.shift_label ?? "",
    hourlyRate: normalizeMoney(row.hourly_rate),
    shiftPay: normalizeMoney(row.shift_pay),
    revenueBonusPct: normalizeMoney(row.revenue_bonus_pct),
  };
}

function normalizeMoney(value: number | string | null | undefined): number {
  if (typeof value === "number" && Number.isFinite(value) && value >= 0) {
    return value;
  }
  if (typeof value === "string" && value.trim()) {
    const parsed = Number(value.replace(",", "."));
    if (Number.isFinite(parsed) && parsed >= 0) return parsed;
  }
  return 0;
}

function normalizeTaskSourceLabel(
  value: string | null | undefined,
): string | undefined {
  if (!value?.trim()) return undefined;
  const normalized = value.replace(/\s+/g, " ").trim();
  return normalized.length > 80
    ? `${normalized.slice(0, 77).trim()}...`
    : normalized;
}

export function mapTaskRow(row: DbTask, sourceLabel?: string): TeamTask {
  const roleId = normalizeTeamRoleId(row.audience_role);
  const audience =
    row.audience_type === "member" && row.audience_member_id
      ? ({ type: "member", memberId: row.audience_member_id } as const)
      : row.audience_type === "role"
        ? ({ type: "role", roleId } as const)
        : ({ type: "venue", venueId: row.venue_id } as const);

  return {
    id: row.id,
    title: row.title,
    source: TASK_SOURCES.has(row.source as TeamTask["source"])
      ? (row.source as TeamTask["source"])
      : "manager",
    sourceLabel: normalizeTaskSourceLabel(row.source_label) ?? sourceLabel,
    priority: TASK_PRIORITIES.has(row.priority as TeamTask["priority"])
      ? (row.priority as TeamTask["priority"])
      : "medium",
    status: TASK_STATUSES.has(row.status as TeamTask["status"])
      ? (row.status as TeamTask["status"])
      : "new",
    venueId: row.venue_id,
    audience,
    dueLabel: row.due_label ?? "",
  };
}

export function mapCommentRow(
  row: DbTaskComment,
  staff: StaffMember[] = [],
): TeamTaskComment {
  const author = row.author_membership_id
    ? staff.find((member) => member.id === row.author_membership_id)
    : null;

  return {
    id: row.id,
    venueId: row.venue_id,
    taskId: row.task_id,
    authorName: author?.name ?? "Команда",
    body: row.body,
    createdAtLabel: formatCreatedAtLabel(row.created_at),
  };
}

export function mapAnnouncementRow(row: DbAnnouncement): TeamAnnouncement {
  const roleId = normalizeTeamRoleId(row.audience_role);
  const audience =
    row.audience_type === "role"
      ? ({ type: "role", roleId } as const)
      : ({ type: "venue", venueId: row.venue_id } as const);

  return {
    id: row.id,
    venueId: row.venue_id,
    title: row.title,
    body: row.body,
    priority: row.priority === "important" ? "important" : "normal",
    audience,
    createdByName: "Команда",
    createdAtLabel: formatCreatedAtLabel(row.created_at),
  };
}

export function mapAnnouncementReadRow(
  row: DbAnnouncementRead,
): TeamAnnouncementRead {
  return {
    announcementId: row.announcement_id,
    memberId: row.membership_id,
    readAtLabel: formatCreatedAtLabel(row.read_at),
  };
}

function normalizeAuditEventType(value: string): TeamAuditEventType {
  const known = new Set<TeamAuditEventType>([
    "member_invited",
    "member_status_updated",
    "member_password_reset",
    "member_labor_rate_updated",
    "task_created",
    "task_status_updated",
    "comment_added",
    "announcement_created",
    "shift_plan_updated",
    "learning_standard_updated",
  ]);
  return known.has(value as TeamAuditEventType)
    ? (value as TeamAuditEventType)
    : "task_created";
}

export function mapAuditEventRow(row: DbAuditEvent): TeamAuditEvent {
  return {
    id: row.id,
    venueId: row.venue_id,
    type: normalizeAuditEventType(row.event_type),
    sourceLabel: metadataSourceLabel(row.metadata),
    targetType:
      row.target_type === "member" ||
      row.target_type === "task" ||
      row.target_type === "comment" ||
      row.target_type === "announcement" ||
      row.target_type === "shift_plan" ||
      row.target_type === "learning_standard"
        ? row.target_type
        : "task",
    targetId: row.target_id,
    summary: row.summary,
    createdAtLabel: formatCreatedAtLabel(row.created_at),
  };
}

function metadataSourceLabel(value: unknown): string | undefined {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return undefined;
  }

  const label = (value as { sourceLabel?: unknown }).sourceLabel;
  if (typeof label !== "string") return undefined;

  const normalized = label.replace(/\s+/g, " ").trim();
  if (!normalized) return undefined;
  return normalized.length > 80 ? `${normalized.slice(0, 77).trim()}...` : normalized;
}

export function buildTaskSourceLabelMap(
  rows: Array<{
    event_type: string;
    target_type: string;
    target_id: string | null;
    metadata?: unknown;
  }>,
): Map<string, string> {
  const labels = new Map<string, string>();

  for (const row of rows) {
    if (
      row.event_type !== "task_created" ||
      row.target_type !== "task" ||
      !row.target_id ||
      labels.has(row.target_id)
    ) {
      continue;
    }

    const label = metadataSourceLabel(row.metadata);
    if (label) labels.set(row.target_id, label);
  }

  return labels;
}

function normalizeAnswers(value: unknown): number[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => (typeof item === "number" ? item : Number(item)))
    .filter((item) => Number.isInteger(item));
}

function normalizePercent(value: number | null | undefined): number {
  if (typeof value !== "number" || Number.isNaN(value)) return 0;
  return Math.max(0, Math.min(100, Math.round(value)));
}

export function mapLearningProgressRow(
  row: DbLearningProgress,
): TeamLearningProgress {
  const completedAt = row.completed_at ?? "";
  const updatedAt = row.updated_at ?? completedAt;

  return {
    venueId: row.venue_id,
    membershipId: row.membership_id,
    userId: row.user_id,
    moduleId: row.module_id,
    bestPercentage: normalizePercent(row.best_percentage),
    lastPercentage: normalizePercent(row.last_percentage),
    correct: Math.max(0, Math.round(row.correct_count ?? 0)),
    total: Math.max(0, Math.round(row.total_questions ?? 0)),
    passed: Boolean(row.passed),
    answers: normalizeAnswers(row.answers),
    completedAt,
    updatedAt,
  };
}

export function mapShiftPlanRow(row: DbShiftPlan): TeamShiftPlan {
  return {
    id: row.id,
    venueId: row.venue_id,
    memberId: row.membership_id,
    shiftDate: row.shift_date,
    shiftStart: normalizeShiftTime(row.shift_start),
    shiftEnd: normalizeShiftTime(row.shift_end),
    isDayOff: Boolean(row.is_day_off),
    note: row.note ?? "",
    updatedAt: row.updated_at ?? "",
  };
}

export function mapLearningStandardRow(
  row: DbLearningStandard,
): TeamLearningStandardOverride {
  return {
    venueId: row.venue_id,
    roleId: normalizeTeamRoleId(row.role),
    moduleId: row.module_id,
    status: normalizeLearningStandardStatus(row.status),
    updatedAt: row.updated_at ?? "",
  };
}

function normalizeShiftTime(value: string | null): string | null {
  if (!value) return null;
  const match = value.match(/^(\d{2}):(\d{2})/);
  return match ? `${match[1]}:${match[2]}` : null;
}

const DEMO_LEARNING_PROGRESS: TeamLearningProgress[] = [
  {
    venueId: "dev-venue",
    membershipId: "staff-manager",
    userId: "demo-manager",
    moduleId: "shift-brief",
    bestPercentage: 100,
    lastPercentage: 100,
    correct: 3,
    total: 3,
    passed: true,
    answers: [0, 1, 1],
    completedAt: "2026-06-26T08:30:00.000Z",
    updatedAt: "2026-06-26T08:30:00.000Z",
  },
  {
    venueId: "dev-venue",
    membershipId: "staff-chef",
    userId: "demo-chef",
    moduleId: "kitchen-stop-list",
    bestPercentage: 100,
    lastPercentage: 100,
    correct: 3,
    total: 3,
    passed: true,
    answers: [0, 1, 1],
    completedAt: "2026-06-26T09:05:00.000Z",
    updatedAt: "2026-06-26T09:05:00.000Z",
  },
  {
    venueId: "dev-venue",
    membershipId: "staff-cook",
    userId: "demo-cook",
    moduleId: "tech-card-discipline",
    bestPercentage: 67,
    lastPercentage: 67,
    correct: 2,
    total: 3,
    passed: false,
    answers: [0, 1, 1],
    completedAt: "2026-06-26T09:30:00.000Z",
    updatedAt: "2026-06-26T09:30:00.000Z",
  },
  {
    venueId: "dev-venue",
    membershipId: "staff-service",
    userId: "demo-service",
    moduleId: "service-recommendation",
    bestPercentage: 100,
    lastPercentage: 100,
    correct: 3,
    total: 3,
    passed: true,
    answers: [1, 0, 2],
    completedAt: "2026-06-26T10:15:00.000Z",
    updatedAt: "2026-06-26T10:15:00.000Z",
  },
];

const DEMO_LEARNING_STANDARDS: TeamLearningStandardOverride[] = [
  {
    venueId: "dev-venue",
    roleId: "service",
    moduleId: "guest-feedback",
    status: "required",
    updatedAt: "2026-06-28T08:00:00.000Z",
  },
];

const DEMO_SHIFT_PLANS: TeamShiftPlan[] = [
  {
    id: "demo-plan-manager-1",
    venueId: "dev-venue",
    memberId: "staff-manager",
    shiftDate: "2026-06-29",
    shiftStart: "12:00",
    shiftEnd: "23:00",
    isDayOff: false,
    note: "зал + касса",
    updatedAt: "2026-06-27T10:00:00.000Z",
  },
  {
    id: "demo-plan-service-1",
    venueId: "dev-venue",
    memberId: "staff-service",
    shiftDate: "2026-06-29",
    shiftStart: "16:00",
    shiftEnd: "00:00",
    isDayOff: false,
    note: "вечерняя посадка",
    updatedAt: "2026-06-27T10:00:00.000Z",
  },
  {
    id: "demo-plan-chef-1",
    venueId: "dev-venue",
    memberId: "staff-chef",
    shiftDate: "2026-06-29",
    shiftStart: "11:00",
    shiftEnd: "22:00",
    isDayOff: false,
    note: "закрыть стоп-лист",
    updatedAt: "2026-06-27T10:00:00.000Z",
  },
  {
    id: "demo-plan-manager-off",
    venueId: "dev-venue",
    memberId: "staff-manager",
    shiftDate: "2026-06-30",
    shiftStart: null,
    shiftEnd: null,
    isDayOff: true,
    note: "после банкета",
    updatedAt: "2026-06-27T10:00:00.000Z",
  },
];

const DEMO_ANNOUNCEMENT_READS: TeamAnnouncementRead[] = [
  {
    announcementId: "announcement-venue-1",
    memberId: "staff-service",
    readAtLabel: "10:05",
  },
  {
    announcementId: "announcement-venue-1",
    memberId: "staff-chef",
    readAtLabel: "10:08",
  },
];

export function getDemoTeamWorkspace(venueId = "dev-venue"): TeamWorkspace {
  return {
    mode: "sandbox",
    venueId,
    venueName: "Demo Restaurant",
    venueMeta: "Иркутск · restaurant",
    staff: DEMO_STAFF.filter((member) => member.venueId === "dev-venue"),
    tasks: DEMO_TEAM_TASKS.filter((task) => task.venueId === "dev-venue"),
    comments: DEMO_TASK_COMMENTS.filter(
      (comment) => comment.venueId === "dev-venue",
    ),
    announcements: DEMO_TEAM_ANNOUNCEMENTS.filter(
      (announcement) => announcement.venueId === "dev-venue",
    ),
    announcementReads: DEMO_ANNOUNCEMENT_READS,
    auditEvents: DEMO_TEAM_AUDIT_EVENTS.filter(
      (event) => event.venueId === "dev-venue",
    ),
    learningProgress: DEMO_LEARNING_PROGRESS.filter(
      (progress) => progress.venueId === "dev-venue",
    ),
    learningStandards: DEMO_LEARNING_STANDARDS.filter(
      (standard) => standard.venueId === "dev-venue",
    ),
    shiftPlans: DEMO_SHIFT_PLANS.filter((plan) => plan.venueId === "dev-venue"),
  };
}

export async function getTeamWorkspace(
  venueId = "dev-venue",
): Promise<TeamWorkspace> {
  const user = await getCurrentUser();
  const supabase = await getServerSupabase();

  if (!supabase || !user || user.isDemo || venueId === "dev-venue") {
    return getDemoTeamWorkspace(venueId);
  }

  const membershipsResult = await supabase
    .from("venue_memberships")
    .select(
      "id,venue_id,user_id,full_name,email,role,status,shift_label,hourly_rate,shift_pay,revenue_bonus_pct",
    )
    .eq("venue_id", venueId)
    .order("created_at", { ascending: true });

  if (membershipsResult.error) {
    if (isMissingTeamTable(membershipsResult.error.message)) {
      return getDemoTeamWorkspace(venueId);
    }
    return {
      mode: "saved",
      venueId,
      venueName: "Рабочий кабинет",
      venueMeta: "Receptor",
      staff: [],
      tasks: [],
      comments: [],
      announcements: [],
      announcementReads: [],
      auditEvents: [],
      learningProgress: [],
      learningStandards: [],
      shiftPlans: [],
    };
  }

  const tasksResult = await supabase
    .from("team_tasks")
    .select(TASK_SELECT_COLUMNS)
    .eq("venue_id", venueId)
    .order("created_at", { ascending: false });
  let tasksData = tasksResult.data as DbTask[] | null;
  let tasksError = tasksResult.error;

  if (tasksError && missingSourceLabelColumn(tasksError.message)) {
    const fallbackResult = await supabase
      .from("team_tasks")
      .select(TASK_SELECT_COLUMNS_LEGACY)
      .eq("venue_id", venueId)
      .order("created_at", { ascending: false });
    tasksData = fallbackResult.data as DbTask[] | null;
    tasksError = fallbackResult.error;
  }

  if (tasksError) {
    if (isMissingTeamTable(tasksError.message)) {
      return getDemoTeamWorkspace(venueId);
    }
    return {
      mode: "saved",
      venueId,
      venueName: "Рабочий кабинет",
      venueMeta: "Receptor",
      staff: ((membershipsResult.data ?? []) as DbMembership[]).map(
        mapMembershipRow,
      ),
      tasks: [],
      comments: [],
      announcements: [],
      announcementReads: [],
      auditEvents: [],
      learningProgress: [],
      learningStandards: [],
      shiftPlans: [],
    };
  }

  const staff = ((membershipsResult.data ?? []) as DbMembership[]).map(
    mapMembershipRow,
  );
  const taskRows = tasksData ?? [];
  const venueResult = await supabase
    .from("venues")
    .select("name,city,type")
    .eq("id", venueId)
    .maybeSingle<{ name: string; city: string | null; type: string | null }>();
  const venueName = venueResult.data?.name?.trim() || "Рабочий кабинет";
  const venueMeta =
    [venueResult.data?.city?.trim(), venueResult.data?.type?.trim()]
      .filter(Boolean)
      .join(" · ") || "Receptor";

  const commentsResult = await supabase
    .from("team_task_comments")
    .select("id,venue_id,task_id,author_membership_id,body,created_at")
    .eq("venue_id", venueId)
    .order("created_at", { ascending: true });

  const comments =
    commentsResult.error && isMissingTeamTable(commentsResult.error.message)
      ? []
      : ((commentsResult.data ?? []) as DbTaskComment[]).map((row) =>
          mapCommentRow(row, staff),
        );

  const announcementsResult = await supabase
    .from("team_announcements")
    .select(
      "id,venue_id,title,body,priority,audience_type,audience_role,created_at",
    )
    .eq("venue_id", venueId)
    .order("created_at", { ascending: false });

  const announcements =
    announcementsResult.error &&
    isMissingTeamTable(announcementsResult.error.message)
      ? []
      : ((announcementsResult.data ?? []) as DbAnnouncement[]).map(
          mapAnnouncementRow,
        );

  const announcementReadsResult = await supabase
    .from("team_announcement_reads")
    .select("announcement_id,membership_id,read_at")
    .eq("venue_id", venueId)
    .order("read_at", { ascending: false });

  const announcementReads =
    announcementReadsResult.error &&
    isMissingTeamTable(announcementReadsResult.error.message)
      ? []
      : ((announcementReadsResult.data ?? []) as DbAnnouncementRead[]).map(
          mapAnnouncementReadRow,
        );

  const auditEventsResult = await supabase
    .from("team_audit_events")
    .select(
      "id,venue_id,event_type,target_type,target_id,summary,metadata,created_at",
    )
    .eq("venue_id", venueId)
    .order("created_at", { ascending: false })
    .limit(12);

  const auditEvents =
    auditEventsResult.error &&
    isMissingTeamTable(auditEventsResult.error.message)
      ? []
      : ((auditEventsResult.data ?? []) as DbAuditEvent[]).map(
          mapAuditEventRow,
        );

  const taskLabelEventsResult = await supabase
    .from("team_audit_events")
    .select("event_type,target_type,target_id,metadata")
    .eq("venue_id", venueId)
    .eq("event_type", "task_created")
    .order("created_at", { ascending: false })
    .limit(200);

  const taskSourceLabels =
    taskLabelEventsResult.error &&
    isMissingTeamTable(taskLabelEventsResult.error.message)
      ? new Map<string, string>()
      : buildTaskSourceLabelMap(
          (taskLabelEventsResult.data ?? []) as DbAuditEvent[],
        );
  const tasks = taskRows.map((row) =>
    mapTaskRow(row, taskSourceLabels.get(row.id)),
  );

  const learningProgressResult = await supabase
    .from("team_learning_progress")
    .select(
      "venue_id,membership_id,user_id,module_id,best_percentage,last_percentage,correct_count,total_questions,passed,answers,completed_at,updated_at",
    )
    .eq("venue_id", venueId)
    .order("completed_at", { ascending: false });

  const learningProgress =
    learningProgressResult.error &&
    isMissingTeamTable(learningProgressResult.error.message)
      ? []
      : ((learningProgressResult.data ?? []) as DbLearningProgress[]).map(
          mapLearningProgressRow,
        );

  const learningStandardsResult = await supabase
    .from("team_learning_standards")
    .select("venue_id,role,module_id,status,updated_at")
    .eq("venue_id", venueId)
    .order("role", { ascending: true })
    .order("module_id", { ascending: true });

  const learningStandards =
    learningStandardsResult.error &&
    isMissingTeamTable(learningStandardsResult.error.message)
      ? []
      : ((learningStandardsResult.data ?? []) as DbLearningStandard[]).map(
          mapLearningStandardRow,
        );

  const shiftPlansResult = await supabase
    .from("team_shift_plans")
    .select(
      "id,venue_id,membership_id,shift_date,shift_start,shift_end,is_day_off,note,updated_at",
    )
    .eq("venue_id", venueId)
    .order("shift_date", { ascending: true })
    .order("shift_start", { ascending: true });

  const shiftPlans =
    shiftPlansResult.error && isMissingTeamTable(shiftPlansResult.error.message)
      ? []
      : ((shiftPlansResult.data ?? []) as DbShiftPlan[]).map(mapShiftPlanRow);

  return {
    mode: "saved",
    venueId,
    venueName,
    venueMeta,
    staff,
    tasks,
    comments,
    announcements,
    announcementReads,
    auditEvents,
    learningProgress,
    learningStandards,
    shiftPlans,
  };
}

function getDemoPersonalWorkspace(): PersonalTeamWorkspace {
  const member =
    DEMO_STAFF.find((item) => item.id === "staff-service") ?? DEMO_STAFF[0];

  return {
    ok: true,
    mode: "sandbox",
    venueId: "dev-venue",
    venueName: "Demo Restaurant",
    member,
    tasks: listTasksForMember(member.id),
    comments: DEMO_TASK_COMMENTS,
    announcements: listAnnouncementsForRole(member.roleId),
    announcementReads: DEMO_ANNOUNCEMENT_READS.filter(
      (read) => read.memberId === member.id,
    ),
    learningProgress: DEMO_LEARNING_PROGRESS.filter(
      (progress) => progress.membershipId === member.id,
    ),
    learningStandards: DEMO_LEARNING_STANDARDS.filter(
      (standard) => standard.venueId === "dev-venue",
    ),
    shiftPlans: DEMO_SHIFT_PLANS.filter((plan) => plan.memberId === member.id),
  };
}

export async function getPersonalTeamWorkspace(): Promise<PersonalTeamWorkspace> {
  const user = await getCurrentUser();
  const supabase = await getServerSupabase();

  if (!supabase || user?.isDemo) {
    return getDemoPersonalWorkspace();
  }

  if (!user) {
    return { ok: false, reason: "unauthenticated" };
  }

  const membershipResult = await supabase
    .from("venue_memberships")
    .select(
      "id,venue_id,user_id,full_name,email,role,status,shift_label,hourly_rate,shift_pay,revenue_bonus_pct,venues(name,city)",
    )
    .eq("user_id", user.id)
    .neq("status", "paused")
    .order("created_at", { ascending: true })
    .limit(1)
    .maybeSingle<DbMembershipWithVenue>();

  if (membershipResult.error) {
    if (isMissingTeamTable(membershipResult.error.message)) {
      return getDemoPersonalWorkspace();
    }
    return { ok: false, reason: "no_membership" };
  }

  if (!membershipResult.data) {
    return { ok: false, reason: "no_membership" };
  }

  const member = mapMembershipRow(membershipResult.data);
  const venueId = member.venueId;
  const venueName =
    membershipResult.data.venues?.name?.trim() || "Рабочий кабинет";

  const staffResult = await supabase
    .from("venue_memberships")
    .select(
      "id,venue_id,user_id,full_name,email,role,status,shift_label,hourly_rate,shift_pay,revenue_bonus_pct",
    )
    .eq("venue_id", venueId)
    .order("created_at", { ascending: true });

  const staff =
    staffResult.error && !isMissingTeamTable(staffResult.error.message)
      ? [member]
      : ((staffResult.data ?? [membershipResult.data]) as DbMembership[]).map(
          mapMembershipRow,
        );

  const tasksResult = await supabase
    .from("team_tasks")
    .select(TASK_SELECT_COLUMNS)
    .eq("venue_id", venueId)
    .order("created_at", { ascending: false });
  let tasksData = tasksResult.data as DbTask[] | null;
  let tasksError = tasksResult.error;

  if (tasksError && missingSourceLabelColumn(tasksError.message)) {
    const fallbackResult = await supabase
      .from("team_tasks")
      .select(TASK_SELECT_COLUMNS_LEGACY)
      .eq("venue_id", venueId)
      .order("created_at", { ascending: false });
    tasksData = fallbackResult.data as DbTask[] | null;
    tasksError = fallbackResult.error;
  }

  const taskRows =
    tasksError && !isMissingTeamTable(tasksError.message)
      ? []
      : (tasksData ?? []);

  const auditEventsResult = await supabase
    .from("team_audit_events")
    .select("event_type,target_type,target_id,metadata")
    .eq("venue_id", venueId)
    .eq("event_type", "task_created")
    .order("created_at", { ascending: false })
    .limit(100);

  const taskSourceLabels =
    auditEventsResult.error && !isMissingTeamTable(auditEventsResult.error.message)
      ? new Map<string, string>()
      : buildTaskSourceLabelMap(
          (auditEventsResult.data ?? []) as DbAuditEvent[],
        );

  const tasks = taskRows.map((row) =>
    mapTaskRow(row, taskSourceLabels.get(row.id)),
  );

  const visibleTasks = roleCan(member.roleId, "view_all_tasks")
    ? tasks
    : listTasksForMember(member.id, staff, tasks);

  const commentsResult = await supabase
    .from("team_task_comments")
    .select("id,venue_id,task_id,author_membership_id,body,created_at")
    .eq("venue_id", venueId)
    .order("created_at", { ascending: true });

  const comments =
    commentsResult.error && !isMissingTeamTable(commentsResult.error.message)
      ? []
      : ((commentsResult.data ?? []) as DbTaskComment[])
          .map((row) => mapCommentRow(row, staff))
          .filter((comment) =>
            visibleTasks.some((task) => task.id === comment.taskId),
          );

  const announcementsResult = await supabase
    .from("team_announcements")
    .select(
      "id,venue_id,title,body,priority,audience_type,audience_role,created_at",
    )
    .eq("venue_id", venueId)
    .order("created_at", { ascending: false });

  const announcements =
    announcementsResult.error &&
    !isMissingTeamTable(announcementsResult.error.message)
      ? []
      : listAnnouncementsForRole(
          member.roleId,
          venueId,
          ((announcementsResult.data ?? []) as DbAnnouncement[]).map(
            mapAnnouncementRow,
          ),
        );

  const announcementReadsResult = await supabase
    .from("team_announcement_reads")
    .select("announcement_id,membership_id,read_at")
    .eq("venue_id", venueId)
    .eq("membership_id", member.id)
    .order("read_at", { ascending: false });

  const announcementReads =
    announcementReadsResult.error &&
    !isMissingTeamTable(announcementReadsResult.error.message)
      ? []
      : ((announcementReadsResult.data ?? []) as DbAnnouncementRead[]).map(
          mapAnnouncementReadRow,
        );

  const learningProgressResult = await supabase
    .from("team_learning_progress")
    .select(
      "venue_id,membership_id,user_id,module_id,best_percentage,last_percentage,correct_count,total_questions,passed,answers,completed_at,updated_at",
    )
    .eq("venue_id", venueId)
    .eq("membership_id", member.id)
    .order("completed_at", { ascending: false });

  const learningProgress =
    learningProgressResult.error &&
    !isMissingTeamTable(learningProgressResult.error.message)
      ? []
      : ((learningProgressResult.data ?? []) as DbLearningProgress[]).map(
          mapLearningProgressRow,
        );

  const learningStandardsResult = await supabase
    .from("team_learning_standards")
    .select("venue_id,role,module_id,status,updated_at")
    .eq("venue_id", venueId)
    .order("role", { ascending: true })
    .order("module_id", { ascending: true });

  const learningStandards =
    learningStandardsResult.error &&
    !isMissingTeamTable(learningStandardsResult.error.message)
      ? []
      : ((learningStandardsResult.data ?? []) as DbLearningStandard[]).map(
          mapLearningStandardRow,
        );

  const shiftPlansResult = await supabase
    .from("team_shift_plans")
    .select(
      "id,venue_id,membership_id,shift_date,shift_start,shift_end,is_day_off,note,updated_at",
    )
    .eq("venue_id", venueId)
    .eq("membership_id", member.id)
    .order("shift_date", { ascending: true })
    .order("shift_start", { ascending: true });

  const shiftPlans =
    shiftPlansResult.error &&
    !isMissingTeamTable(shiftPlansResult.error.message)
      ? []
      : ((shiftPlansResult.data ?? []) as DbShiftPlan[]).map(mapShiftPlanRow);

  getTeamRole(member.roleId);

  return {
    ok: true,
    mode: "saved",
    venueId,
    venueName,
    member,
    tasks: visibleTasks,
    comments,
    announcements,
    announcementReads,
    learningProgress,
    learningStandards,
    shiftPlans,
  };
}
