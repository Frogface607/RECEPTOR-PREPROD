import type { Metadata } from "next";
import Link from "next/link";
import {
  ArrowRight,
  CheckCircle2,
  ClipboardList,
  GraduationCap,
  KeyRound,
  ShieldCheck,
  UserRoundCog,
  UsersRound,
} from "lucide-react";
import { AppShell } from "@/components/dashboard/app-shell";
import { Badge } from "@/components/ui/badge";
import { LinkButton } from "@/components/ui/link-button";
import { TeamActionsPanel } from "./team-actions-panel";
import { TeamCommunicationPanel } from "./team-communication-panel";
import {
  buildRoleHome,
  getTeamRole,
  listTasksForMember,
  TEAM_ROLES,
  type StaffMember,
  type TeamRoleId,
  type TeamTask,
} from "@/lib/team/team-os";
import { getTeamWorkspace } from "@/lib/team/team-store";

export const metadata: Metadata = {
  title: "Team OS — RECEPTOR",
  description:
    "Роли, права, сотрудники, задачи, обучение и смены внутри Receptor Restaurant OS.",
};

const ROLE_PARAM_VALUES = new Set<TeamRoleId>(TEAM_ROLES.map((role) => role.id));

function parseRole(value: string | string[] | undefined): TeamRoleId {
  const raw = Array.isArray(value) ? value[0] : value;
  return raw && ROLE_PARAM_VALUES.has(raw as TeamRoleId)
    ? (raw as TeamRoleId)
    : "owner";
}

function parseVenueId(value: string | string[] | undefined): string {
  const raw = Array.isArray(value) ? value[0] : value;
  return raw?.trim() || "dev-venue";
}

function priorityClass(priority: TeamTask["priority"]): string {
  if (priority === "high") {
    return "border-destructive/30 bg-destructive/10 text-destructive";
  }
  if (priority === "medium") {
    return "border-[color:var(--pro)]/30 bg-[color:var(--pro)]/10 text-[color:var(--pro)]";
  }
  return "border-border bg-muted/40 text-muted-foreground";
}

function statusLabel(status: TeamTask["status"]): string {
  if (status === "new") return "новая";
  if (status === "accepted") return "принята";
  if (status === "in_progress") return "в работе";
  if (status === "done") return "сделано";
  return "проверено";
}

export default async function TeamPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const sp = await searchParams;
  const roleId = parseRole(sp.role);
  const workspace = await getTeamWorkspace(parseVenueId(sp.venueId));
  const home = buildRoleHome(roleId, workspace.tasks);
  const visibleStaff = workspace.staff.filter((member) =>
    roleId === "owner" ||
    roleId === "operations_manager" ||
    roleId === "venue_manager"
      ? true
      : member.roleId === roleId,
  );
  const representativeMember =
    workspace.staff.find((member) => member.roleId === roleId) ??
    workspace.staff[0];
  const memberTasks = representativeMember
    ? listTasksForMember(
        representativeMember.id,
        workspace.staff,
        workspace.tasks,
      )
    : [];

  return (
    <AppShell
      activeHref="/team"
      venueId={workspace.venueId}
      venueName={workspace.venueName}
      venueMeta={workspace.venueMeta}
    >
      <main className="flex-1">
        <section className="border-b border-border/40">
          <div className="mx-auto grid max-w-7xl gap-5 px-6 py-8 lg:grid-cols-[0.72fr_1.28fr]">
            <div className="flex flex-col justify-between gap-5">
              <Badge variant="outline" className="border-brand/30 text-brand">
                Team OS
              </Badge>
              <h1 className="max-w-2xl text-balance text-[clamp(2rem,4vw,3.25rem)] font-medium leading-[1.04]">
                Команда, роли и задачи.
              </h1>
              <p className="max-w-xl text-sm leading-relaxed text-muted-foreground">
                Один рабочий экран для доступа, задач и сменной коммуникации.
              </p>
              <div className="flex flex-wrap gap-3">
                <LinkButton
                  href={`/dashboard/${encodeURIComponent(workspace.venueId)}`}
                  className="bg-brand text-primary-foreground hover:bg-brand-hover"
                >
                  Owner Cockpit
                  <ArrowRight className="size-4" />
                </LinkButton>
                <LinkButton
                  href={`/team?role=service&venueId=${encodeURIComponent(workspace.venueId)}`}
                  variant="outline"
                >
                  Вид официанта
                </LinkButton>
              </div>
            </div>

            <div className="rounded-lg border border-border/60 bg-card/60 p-5">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-[11px] uppercase tracking-[0.22em] text-muted-foreground">
                    Текущий кабинет
                  </p>
                  <h2 className="mt-3 text-2xl font-medium">
                    {home.role.title}
                  </h2>
                  <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                    {home.role.description}
                  </p>
                </div>
                <UserRoundCog className="size-6 shrink-0 text-brand" />
              </div>

              <div className="mt-4 inline-flex rounded-md border border-border/50 bg-background/35 px-2.5 py-1 text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
                {workspace.venueName}
              </div>

              <div className="mt-5 grid gap-3 sm:grid-cols-3">
                <Metric label="Разделов" value={home.sections.length} />
                <Metric label="Прав" value={home.permissions.length} />
                <Metric label="Задач видно" value={home.visibleTasks.length} />
              </div>

              <div className="mt-5 flex flex-wrap gap-2">
                {home.sections.map((section) => (
                  <span
                    key={section}
                    className="rounded-md border border-border/50 bg-background/45 px-2.5 py-1 text-[12px] text-muted-foreground"
                  >
                    {section}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section className="border-b border-border/40">
          <div className="mx-auto max-w-7xl px-6 py-6">
            <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
              <p className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground lg:w-36">
                Кабинет
              </p>
              <div className="grid flex-1 gap-2 sm:grid-cols-2 lg:grid-cols-7">
              {TEAM_ROLES.map((role) => {
                const active = role.id === roleId;
                return (
                  <Link
                    key={role.id}
                    href={`/team?role=${role.id}&venueId=${encodeURIComponent(workspace.venueId)}`}
                    className={
                      "rounded-lg border px-3 py-2 transition-colors " +
                      (active
                        ? "border-brand/50 bg-card"
                        : "border-border/60 bg-card/45 hover:bg-card/75")
                    }
                  >
                    <div className="flex items-center justify-between gap-2">
                      <p className="truncate text-sm font-medium">{role.title}</p>
                      <span className="text-[10px] uppercase tracking-[0.12em] text-muted-foreground">
                        {role.shortTitle}
                      </span>
                    </div>
                  </Link>
                );
              })}
              </div>
            </div>
          </div>
        </section>

        <TeamActionsPanel
          venueId={workspace.venueId}
          staff={workspace.staff}
          tasks={workspace.tasks}
          auditEvents={workspace.auditEvents}
        />

        <TeamCommunicationPanel
          venueId={workspace.venueId}
          roleId={roleId}
          tasks={workspace.tasks}
          comments={workspace.comments}
          announcements={workspace.announcements}
        />

        <section className="border-b border-border/40">
          <div className="mx-auto grid max-w-7xl gap-6 px-6 py-14 lg:grid-cols-[0.9fr_1.1fr]">
            <div className="rounded-lg border border-border/60 bg-card/50 p-5">
              <div className="flex items-center gap-3">
                <ShieldCheck className="size-5 text-brand" />
                <h2 className="text-xl font-medium">Права кабинета</h2>
              </div>
              <div className="mt-5 grid gap-3">
                {home.permissions.map((permission) => (
                  <div
                    key={permission.id}
                    className="rounded-lg border border-border/45 bg-background/35 p-3"
                  >
                    <p className="text-sm font-medium">{permission.title}</p>
                    <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
                      {permission.description}
                    </p>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-lg border border-border/60 bg-card/50 p-5">
              <div className="flex items-center gap-3">
                <ClipboardList className="size-5 text-brand" />
                <h2 className="text-xl font-medium">Задачи в этом кабинете</h2>
              </div>
              <div className="mt-5 grid gap-3">
                {home.visibleTasks.map((task) => (
                  <TaskRow key={task.id} task={task} />
                ))}
              </div>
            </div>
          </div>
        </section>

        <section className="border-b border-border/40">
          <div className="mx-auto grid max-w-7xl gap-6 px-6 py-14 lg:grid-cols-[1.1fr_0.9fr]">
            <div className="rounded-lg border border-border/60 bg-card/50 p-5">
              <div className="flex items-center gap-3">
                <UsersRound className="size-5 text-brand" />
                <h2 className="text-xl font-medium">Сотрудники</h2>
              </div>
              <div className="mt-5 grid gap-3">
                {visibleStaff.map((member) => (
                  <StaffRow key={member.id} member={member} />
                ))}
              </div>
            </div>

            <div className="rounded-lg border border-border/60 bg-card/50 p-5">
              <div className="flex items-center gap-3">
                <GraduationCap className="size-5 text-brand" />
                <h2 className="text-xl font-medium">Что видит сотрудник</h2>
              </div>
              {representativeMember ? (
                <>
                  <p className="mt-4 text-sm leading-relaxed text-muted-foreground">
                    Пример кабинета: {representativeMember.name},{" "}
                    {getTeamRole(representativeMember.roleId).title.toLowerCase()}.
                  </p>
                  <div className="mt-5 grid gap-3">
                    {memberTasks.map((task) => (
                      <TaskRow key={task.id} task={task} compact />
                    ))}
                  </div>
                </>
              ) : (
                <p className="mt-4 text-sm text-muted-foreground">
                  Для этой роли пока нет демо-сотрудника.
                </p>
              )}
            </div>
          </div>
        </section>

        <section>
          <div className="mx-auto max-w-7xl px-6 py-14">
            <div className="rounded-lg border border-border/60 bg-card/50 p-6">
              <div className="flex items-start gap-3">
                <KeyRound className="mt-1 size-5 shrink-0 text-brand" />
                <div>
                  <h2 className="text-xl font-medium">
                    Далее: сменный чат.
                  </h2>
                  <p className="mt-3 max-w-3xl text-sm leading-relaxed text-muted-foreground">
                    Сейчас фиксируем задачи, объявления и комментарии. Чат
                    добавим поверх этой структуры.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>
    </AppShell>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-border/50 bg-background/35 p-3">
      <p className="numeric text-2xl font-medium text-foreground">{value}</p>
      <p className="mt-1 text-[11px] uppercase tracking-[0.16em] text-muted-foreground">
        {label}
      </p>
    </div>
  );
}

function TaskRow({
  task,
  compact = false,
}: {
  task: TeamTask;
  compact?: boolean;
}) {
  return (
    <div className="rounded-lg border border-border/45 bg-background/35 p-3">
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant="outline" className={priorityClass(task.priority)}>
          {task.priority}
        </Badge>
        <Badge variant="outline">{statusLabel(task.status)}</Badge>
        <span className="text-[11px] uppercase tracking-[0.16em] text-muted-foreground">
          {task.dueLabel}
        </span>
      </div>
      <p
        className={
          "mt-3 leading-relaxed text-foreground/90 " +
          (compact ? "text-[13px]" : "text-sm")
        }
      >
        {task.title}
      </p>
    </div>
  );
}

function StaffRow({ member }: { member: StaffMember }) {
  const role = getTeamRole(member.roleId);

  return (
    <div className="grid gap-3 rounded-lg border border-border/45 bg-background/35 p-3 sm:grid-cols-[1fr_auto] sm:items-center">
      <div>
        <div className="flex flex-wrap items-center gap-2">
          <p className="text-sm font-medium">{member.name}</p>
          <Badge variant="outline">{role.title}</Badge>
        </div>
        <p className="mt-1 text-xs text-muted-foreground">{member.shiftLabel}</p>
      </div>
      <div className="flex items-center gap-2 text-[12px] text-muted-foreground">
        <CheckCircle2 className="size-4 text-brand" />
        {member.status === "active" ? "активен" : member.status}
      </div>
    </div>
  );
}
