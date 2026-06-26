import type { Metadata } from "next";
import Link from "next/link";
import { redirect } from "next/navigation";
import {
  ArrowRight,
  BookOpenCheck,
  CalendarClock,
  CheckCircle2,
  ClipboardCheck,
  Clock3,
  Flame,
  GraduationCap,
  Inbox,
  LayoutDashboard,
  LogOut,
  Megaphone,
  UserRound,
} from "lucide-react";
import { AppShell } from "@/components/dashboard/app-shell";
import { Badge } from "@/components/ui/badge";
import { getCurrentUser } from "@/lib/auth/session";
import { isSupabaseConfigured } from "@/lib/db/env";
import { getServerSupabase } from "@/lib/db/server";
import {
  getRoleDayFocus,
  listLearningItemsForRole,
  listShiftChecklistForRole,
  type TeamLearningItem,
} from "@/lib/team/team-learning";
import { getTeamRole, type TeamAnnouncement, type TeamTask } from "@/lib/team/team-os";
import { getPersonalTeamWorkspace } from "@/lib/team/team-store";
import { TaskStatusButtons } from "./task-status-buttons";

export const metadata: Metadata = {
  title: "Мой кабинет — RECEPTOR",
  description: "Персональный кабинет сотрудника ресторана в Receptor.",
};

function statusLabel(status: TeamTask["status"]): string {
  if (status === "new") return "новая";
  if (status === "accepted") return "принята";
  if (status === "in_progress") return "в работе";
  if (status === "done") return "сделано";
  return "проверено";
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

function priorityLabel(priority: TeamTask["priority"]): string {
  if (priority === "high") return "важно";
  if (priority === "medium") return "средне";
  return "низко";
}

function learningStatusLabel(status: TeamLearningItem["status"]): string {
  if (status === "required") return "обязательно";
  if (status === "ready") return "готово";
  return "скоро";
}

function learningStatusClass(status: TeamLearningItem["status"]): string {
  if (status === "required") {
    return "border-brand/30 bg-brand/10 text-brand";
  }
  if (status === "ready") {
    return "border-[color:var(--pro)]/30 bg-[color:var(--pro)]/10 text-[color:var(--pro)]";
  }
  return "border-border bg-muted/40 text-muted-foreground";
}

function statusClass(status: TeamTask["status"]): string {
  if (status === "in_progress") return "border-brand/35 bg-brand/10 text-brand";
  if (status === "new") return "border-amber-400/30 bg-amber-400/10 text-amber-200";
  if (status === "accepted") return "border-[color:var(--pro)]/30 bg-[color:var(--pro)]/10 text-[color:var(--pro)]";
  return "border-border bg-muted/40 text-muted-foreground";
}

const TASK_STATUS_ORDER: Record<TeamTask["status"], number> = {
  in_progress: 0,
  new: 1,
  accepted: 2,
  done: 3,
  verified: 4,
};

const TASK_PRIORITY_ORDER: Record<TeamTask["priority"], number> = {
  high: 0,
  medium: 1,
  low: 2,
};

function sortTasks(tasks: TeamTask[]): TeamTask[] {
  return [...tasks].sort((a, b) => {
    const byStatus = TASK_STATUS_ORDER[a.status] - TASK_STATUS_ORDER[b.status];
    if (byStatus !== 0) return byStatus;
    const byPriority =
      TASK_PRIORITY_ORDER[a.priority] - TASK_PRIORITY_ORDER[b.priority];
    if (byPriority !== 0) return byPriority;
    return a.title.localeCompare(b.title, "ru");
  });
}

async function getFirstOwnedVenueId(): Promise<string | null> {
  const [user, supabase] = await Promise.all([
    getCurrentUser(),
    getServerSupabase(),
  ]);
  if (!user || user.isDemo || !supabase) return null;

  const { data } = await supabase
    .from("venues")
    .select("id")
    .eq("owner_user_id", user.id)
    .order("created_at", { ascending: true })
    .limit(1)
    .maybeSingle<{ id: string }>();

  return data?.id ?? null;
}

export default async function MyCabinetPage() {
  const workspace = await getPersonalTeamWorkspace();

  if (!workspace.ok) {
    if (workspace.reason === "unauthenticated" && isSupabaseConfigured()) {
      redirect("/auth?next=/me");
    }
    if (workspace.reason === "no_membership" && isSupabaseConfigured()) {
      const venueId = await getFirstOwnedVenueId();
      if (venueId) {
        redirect(`/dashboard/${venueId}`);
      }
      redirect("/onboarding?new=1");
    }

    return (
      <AppShell activeHref="/me" chat={false}>
        <main className="flex-1">
          <section className="mx-auto max-w-3xl px-6 py-20">
            <Badge variant="outline" className="border-brand/30 text-brand">
              Мой кабинет
            </Badge>
            <h1 className="mt-6 text-4xl font-medium">
              Для этого пользователя пока нет роли в заведении.
            </h1>
            <p className="mt-4 text-sm leading-relaxed text-muted-foreground">
              Попросите владельца или управляющего добавить сотрудника в команду
              и выдать логин.
            </p>
            <Link
              href="/auth/signout"
              prefetch={false}
              className="mt-8 inline-flex h-10 items-center gap-2 rounded-lg border border-border/60 bg-card/50 px-4 text-sm text-foreground transition-colors hover:border-brand/40"
            >
              <LogOut className="size-4" />
              Выйти
            </Link>
          </section>
        </main>
      </AppShell>
    );
  }

  const role = getTeamRole(workspace.member.roleId);
  const roleFocus = getRoleDayFocus(workspace.member.roleId);
  const shiftChecklist = listShiftChecklistForRole(workspace.member.roleId);
  const learningItems = listLearningItemsForRole(workspace.member.roleId);
  const shiftLabel = workspace.member.shiftLabel?.trim() || "Смена не указана";
  const openTasks = workspace.tasks.filter(
    (task) => task.status !== "done" && task.status !== "verified",
  );
  const completedTasks = workspace.tasks.filter(
    (task) => task.status === "done" || task.status === "verified",
  );
  const sortedOpenTasks = sortTasks(openTasks);
  const nextTask = sortedOpenTasks[0];
  const urgentTasks = openTasks.filter((task) => task.priority === "high");
  const taskGroups = [
    {
      id: "in_progress" as const,
      title: "В работе",
      hint: "То, что уже принято в смену.",
      tasks: sortedOpenTasks.filter((task) => task.status === "in_progress"),
    },
    {
      id: "new" as const,
      title: "Новые",
      hint: "Нужно принять или быстро отклонить через управляющего.",
      tasks: sortedOpenTasks.filter((task) => task.status === "new"),
    },
    {
      id: "accepted" as const,
      title: "Принятые",
      hint: "Следующий шаг — взять в работу.",
      tasks: sortedOpenTasks.filter((task) => task.status === "accepted"),
    },
  ].filter((group) => group.tasks.length > 0);

  return (
    <AppShell
      activeHref="/me"
      venueId={workspace.venueId}
      venueName={workspace.venueName}
      venueMeta="Команда"
    >
      <main className="flex-1">
        <section className="border-b border-border/40">
          <div className="mx-auto grid max-w-7xl gap-6 px-6 py-8 lg:grid-cols-[0.86fr_1.14fr]">
            <div>
              <Badge variant="outline" className="border-brand/30 text-brand">
                Мой кабинет
              </Badge>
              <h1 className="mt-5 max-w-3xl text-balance text-[clamp(2rem,4.2vw,3.4rem)] font-medium leading-[1.03]">
                Сегодня: {role.title.toLowerCase()}
              </h1>
              <p className="mt-5 max-w-2xl text-sm leading-relaxed text-muted-foreground">
                {workspace.member.name} · {workspace.venueName}. {shiftLabel}.{" "}
                {roleFocus.summary}
              </p>
              <div className="mt-6 flex flex-wrap gap-3">
                <Link
                  href={`/team?role=${role.id}&venueId=${encodeURIComponent(workspace.venueId)}`}
                  className="inline-flex h-10 items-center gap-2 rounded-lg bg-brand px-4 text-sm font-medium text-primary-foreground transition-colors hover:bg-brand-hover"
                >
                  <LayoutDashboard className="size-4" />
                  Открыть команду
                </Link>
                <Link
                  href="/auth/signout"
                  prefetch={false}
                  className="inline-flex h-10 items-center gap-2 rounded-lg border border-border/60 bg-card/50 px-4 text-sm text-foreground transition-colors hover:border-brand/40"
                >
                  <LogOut className="size-4" />
                  Выйти
                </Link>
              </div>
            </div>

            <div className="rounded-lg border border-brand/35 bg-card/65 p-5">
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0">
                  <p className="text-[11px] uppercase tracking-[0.22em] text-muted-foreground">
                    Следующее действие
                  </p>
                  {nextTask ? (
                    <>
                      <div className="mt-3 flex flex-wrap items-center gap-2">
                        <Badge
                          variant="outline"
                          className={priorityClass(nextTask.priority)}
                        >
                          {priorityLabel(nextTask.priority)}
                        </Badge>
                        <Badge
                          variant="outline"
                          className={statusClass(nextTask.status)}
                        >
                          {statusLabel(nextTask.status)}
                        </Badge>
                        {nextTask.dueLabel ? (
                          <span className="inline-flex items-center gap-1 text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
                            <Clock3 className="size-3.5" />
                            {nextTask.dueLabel}
                          </span>
                        ) : null}
                      </div>
                      <h2 className="mt-4 text-xl font-medium leading-tight">
                        {nextTask.title}
                      </h2>
                      <TaskStatusButtons
                        key={`${nextTask.id}-${nextTask.status}`}
                        task={nextTask}
                      />
                    </>
                  ) : (
                    <>
                      <h2 className="mt-3 text-xl font-medium">
                        Активных задач нет
                      </h2>
                      <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                        Проверь объявления и подготовь смену по стандартам роли.
                      </p>
                    </>
                  )}
                </div>
                <Inbox className="size-5 shrink-0 text-brand" />
              </div>
            </div>
          </div>

          <div className="mx-auto grid max-w-7xl gap-3 px-6 pb-8 sm:grid-cols-2 lg:grid-cols-4">
            <Metric label="активные" value={openTasks.length} />
            <Metric label="важные" value={urgentTasks.length} />
            <Metric label="объявления" value={workspace.announcements.length} />
            <Metric label="закрыто" value={completedTasks.length} />
          </div>
        </section>

        <section className="border-b border-border/40">
          <div className="mx-auto grid max-w-7xl gap-6 px-6 py-10 lg:grid-cols-[1.12fr_0.88fr]">
            <div>
              <div className="flex items-center gap-3">
                <Flame className="size-5 text-brand" />
                <h2 className="text-2xl font-medium">Рабочая лента</h2>
              </div>
              <div className="mt-5 grid gap-5">
                {taskGroups.length ? (
                  taskGroups.map((group) => (
                    <TaskGroup
                      key={group.id}
                      title={group.title}
                      hint={group.hint}
                      tasks={group.tasks}
                    />
                  ))
                ) : (
                  <EmptyState text="Активных задач нет." />
                )}
              </div>
            </div>

            <div className="space-y-6">
              <div>
                <div className="flex items-center gap-3">
                  <Megaphone className="size-5 text-brand" />
                  <h2 className="text-2xl font-medium">Объявления</h2>
                </div>
                <div className="mt-5 grid gap-3">
                  {workspace.announcements.length ? (
                    workspace.announcements.map((announcement) => (
                      <AnnouncementCard
                        key={announcement.id}
                        announcement={announcement}
                      />
                    ))
                  ) : (
                    <EmptyState text="Новых объявлений нет." />
                  )}
                </div>
              </div>

              <div className="rounded-lg border border-border/60 bg-card/50 p-5">
                <div className="flex items-start gap-3">
                  <UserRound className="mt-1 size-5 shrink-0 text-brand" />
                  <div>
                    <p className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
                      Роль и доступ
                    </p>
                    <h2 className="mt-3 text-xl font-medium">{role.title}</h2>
                    <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                      {role.description}
                    </p>
                  </div>
                </div>
                <div className="mt-5 flex flex-wrap gap-2">
                  {role.homeSections.map((section) => (
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
          </div>
        </section>

        <section>
          <div className="mx-auto grid max-w-7xl gap-6 px-6 py-14 lg:grid-cols-[0.9fr_1.1fr]">
            <div className="space-y-6">
              <div className="rounded-lg border border-border/60 bg-card/50 p-5">
                <div className="flex items-center gap-3">
                  <CalendarClock className="size-5 text-brand" />
                  <h2 className="text-xl font-medium">Смена сегодня</h2>
                </div>
                <div className="mt-4 rounded-lg border border-brand/25 bg-brand/10 p-4">
                  <p className="text-[11px] uppercase tracking-[0.18em] text-brand">
                    {shiftLabel}
                  </p>
                  <h3 className="mt-3 text-lg font-medium">{roleFocus.title}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                    {roleFocus.summary}
                  </p>
                </div>
                <div className="mt-5 grid gap-2">
                  {shiftChecklist.map((item) => (
                    <div
                      key={item}
                      className="flex gap-3 rounded-lg border border-border/45 bg-background/35 p-3 text-sm leading-relaxed text-foreground/85"
                    >
                      <ClipboardCheck className="mt-0.5 size-4 shrink-0 text-brand" />
                      <span>{item}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="rounded-lg border border-border/60 bg-card/50 p-5">
                <div className="flex items-center gap-3">
                  <CheckCircle2 className="size-5 text-brand" />
                  <h2 className="text-xl font-medium">Завершено</h2>
                </div>
                <div className="mt-4 grid gap-3">
                  {completedTasks.length ? (
                    completedTasks.slice(0, 4).map((task) => (
                      <div
                        key={task.id}
                        className="rounded-lg border border-border/45 bg-background/35 p-3 text-sm text-muted-foreground"
                      >
                        {task.title}
                      </div>
                    ))
                  ) : (
                    <EmptyState text="Пока нет закрытых задач." />
                  )}
                </div>
              </div>
            </div>

            <div className="rounded-lg border border-border/60 bg-card/50 p-5">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <div className="flex items-center gap-3">
                    <GraduationCap className="size-5 text-brand" />
                    <h2 className="text-xl font-medium">Обучение по роли</h2>
                  </div>
                  <p className="mt-3 max-w-2xl text-sm leading-relaxed text-muted-foreground">
                    Короткие материалы, которые привязаны к должности и задачам
                    на смену. Внутри — стандарт, проверка и личный прогресс.
                  </p>
                </div>
                <BookOpenCheck className="size-5 shrink-0 text-brand" />
              </div>
              <div className="mt-5 grid gap-3">
                {learningItems.map((item) => (
                  <LearningCard key={item.id} item={item} />
                ))}
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
      <p className="mt-1 text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
        {label}
      </p>
    </div>
  );
}

function TaskGroup({
  title,
  hint,
  tasks,
}: {
  title: string;
  hint: string;
  tasks: TeamTask[];
}) {
  return (
    <div className="rounded-lg border border-border/60 bg-card/45 p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-sm font-medium text-foreground">{title}</h3>
          <p className="mt-1 text-[12px] leading-relaxed text-muted-foreground">
            {hint}
          </p>
        </div>
        <span className="rounded-md border border-border/50 bg-background/45 px-2 py-0.5 font-mono text-[11px] text-muted-foreground">
          {tasks.length}
        </span>
      </div>
      <div className="mt-4 grid gap-3">
        {tasks.map((task) => (
          <TaskCard key={task.id} task={task} />
        ))}
      </div>
    </div>
  );
}

function TaskCard({ task }: { task: TeamTask }) {
  return (
    <article className="rounded-lg border border-border/60 bg-card/50 p-4">
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant="outline" className={priorityClass(task.priority)}>
          {priorityLabel(task.priority)}
        </Badge>
        <Badge variant="outline" className={statusClass(task.status)}>
          {statusLabel(task.status)}
        </Badge>
        {task.dueLabel ? (
          <span className="inline-flex items-center gap-1 text-[11px] uppercase tracking-[0.16em] text-muted-foreground">
            <Clock3 className="size-3.5" />
            {task.dueLabel}
          </span>
        ) : null}
      </div>
      <p className="mt-3 text-sm leading-relaxed text-foreground/90">
        {task.title}
      </p>
      <TaskStatusButtons key={`${task.id}-${task.status}`} task={task} />
    </article>
  );
}

function AnnouncementCard({
  announcement,
}: {
  announcement: TeamAnnouncement;
}) {
  return (
    <article className="rounded-lg border border-border/60 bg-card/50 p-4">
      <div className="flex flex-wrap items-center gap-2">
        <Badge
          variant="outline"
          className={
            announcement.priority === "important"
              ? "border-brand/30 bg-brand/10 text-brand"
              : ""
          }
        >
          {announcement.priority === "important" ? "важно" : "инфо"}
        </Badge>
        {announcement.createdAtLabel ? (
          <span className="text-[11px] uppercase tracking-[0.16em] text-muted-foreground">
            {announcement.createdAtLabel}
          </span>
        ) : null}
      </div>
      <h3 className="mt-3 text-sm font-medium">{announcement.title}</h3>
      <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
        {announcement.body}
      </p>
    </article>
  );
}

function LearningCard({ item }: { item: TeamLearningItem }) {
  return (
    <Link
      href={`/me/learning?module=${encodeURIComponent(item.id)}`}
      className="block rounded-lg border border-border/60 bg-background/35 p-4 transition-colors hover:border-brand/40 hover:bg-card/70"
    >
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant="outline" className={learningStatusClass(item.status)}>
          {learningStatusLabel(item.status)}
        </Badge>
        <span className="text-[11px] uppercase tracking-[0.16em] text-muted-foreground">
          {item.timeLabel}
        </span>
      </div>
      <h3 className="mt-3 text-sm font-medium">{item.title}</h3>
      <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
        {item.description}
      </p>
      <span className="mt-4 inline-flex items-center gap-2 text-sm font-medium text-brand">
        Открыть урок
        <ArrowRight className="size-4" />
      </span>
    </Link>
  );
}

function EmptyState({ text }: { text: string }) {
  return (
    <div className="rounded-lg border border-border/60 bg-card/40 p-5 text-sm text-muted-foreground">
      {text}
    </div>
  );
}
