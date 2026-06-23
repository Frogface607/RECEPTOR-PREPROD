import { getCurrentUser } from "@/lib/auth/session";
import { getServerSupabase } from "@/lib/db/server";
import {
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
  type TeamTaskComment,
  type TeamRoleId,
  type TeamTask,
} from "./team-os";

type DbMembership = {
  id: string;
  venue_id: string;
  user_id?: string | null;
  full_name: string;
  email?: string | null;
  role: string;
  status: string;
  shift_label: string | null;
};

type DbTask = {
  id: string;
  venue_id: string;
  title: string;
  source: string;
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

type DbMembershipWithVenue = DbMembership & {
  venues?: { name: string | null; city: string | null } | null;
};

export type TeamWorkspace = {
  mode: "saved" | "sandbox";
  venueId: string;
  staff: StaffMember[];
  tasks: TeamTask[];
  comments: TeamTaskComment[];
  announcements: TeamAnnouncement[];
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

function isMissingTeamTable(message: string): boolean {
  return /venue_memberships|team_tasks|team_task_comments|team_announcements|relation .* does not exist/i.test(
    message,
  );
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

export function normalizeTeamRoleId(value: string | null | undefined): TeamRoleId {
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
      row.status === "active" || row.status === "invited" || row.status === "paused"
        ? row.status
        : "invited",
    shiftLabel: row.shift_label ?? "",
  };
}

export function mapTaskRow(row: DbTask): TeamTask {
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

export function getDemoTeamWorkspace(venueId = "dev-venue"): TeamWorkspace {
  return {
    mode: "sandbox",
    venueId,
    staff: DEMO_STAFF.filter((member) => member.venueId === "dev-venue"),
    tasks: DEMO_TEAM_TASKS.filter((task) => task.venueId === "dev-venue"),
    comments: DEMO_TASK_COMMENTS.filter(
      (comment) => comment.venueId === "dev-venue",
    ),
    announcements: DEMO_TEAM_ANNOUNCEMENTS.filter(
      (announcement) => announcement.venueId === "dev-venue",
    ),
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
    .select("id,venue_id,user_id,full_name,email,role,status,shift_label")
    .eq("venue_id", venueId)
    .order("created_at", { ascending: true });

  if (membershipsResult.error) {
    if (isMissingTeamTable(membershipsResult.error.message)) {
      return getDemoTeamWorkspace(venueId);
    }
    return {
      mode: "saved",
      venueId,
      staff: [],
      tasks: [],
      comments: [],
      announcements: [],
    };
  }

  const tasksResult = await supabase
    .from("team_tasks")
    .select(
      "id,venue_id,title,source,priority,status,audience_type,audience_member_id,audience_role,due_label",
    )
    .eq("venue_id", venueId)
    .order("created_at", { ascending: false });

  if (tasksResult.error) {
    if (isMissingTeamTable(tasksResult.error.message)) {
      return getDemoTeamWorkspace(venueId);
    }
    return {
      mode: "saved",
      venueId,
      staff: ((membershipsResult.data ?? []) as DbMembership[]).map(
        mapMembershipRow,
      ),
      tasks: [],
      comments: [],
      announcements: [],
    };
  }

  const staff = ((membershipsResult.data ?? []) as DbMembership[]).map(
    mapMembershipRow,
  );
  const tasks = ((tasksResult.data ?? []) as DbTask[]).map(mapTaskRow);

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
    .select("id,venue_id,title,body,priority,audience_type,audience_role,created_at")
    .eq("venue_id", venueId)
    .order("created_at", { ascending: false });

  const announcements =
    announcementsResult.error &&
    isMissingTeamTable(announcementsResult.error.message)
      ? []
      : ((announcementsResult.data ?? []) as DbAnnouncement[]).map(
          mapAnnouncementRow,
        );

  return {
    mode: "saved",
    venueId,
    staff,
    tasks,
    comments,
    announcements,
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
    .select("id,venue_id,user_id,full_name,email,role,status,shift_label,venues(name,city)")
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
    .select("id,venue_id,user_id,full_name,email,role,status,shift_label")
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
    .select(
      "id,venue_id,title,source,priority,status,audience_type,audience_member_id,audience_role,due_label",
    )
    .eq("venue_id", venueId)
    .order("created_at", { ascending: false });

  const tasks =
    tasksResult.error && !isMissingTeamTable(tasksResult.error.message)
      ? []
      : ((tasksResult.data ?? []) as DbTask[]).map(mapTaskRow);

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
    .select("id,venue_id,title,body,priority,audience_type,audience_role,created_at")
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
  };
}
