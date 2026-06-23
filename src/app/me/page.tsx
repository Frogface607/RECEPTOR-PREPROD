import type { Metadata } from "next";
import Link from "next/link";
import { redirect } from "next/navigation";
import {
  Bell,
  CheckCircle2,
  ClipboardList,
  GraduationCap,
  LayoutDashboard,
  LogOut,
  UserRound,
} from "lucide-react";
import { AppShell } from "@/components/dashboard/app-shell";
import { Badge } from "@/components/ui/badge";
import { isSupabaseConfigured } from "@/lib/db/env";
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

export default async function MyCabinetPage() {
  const workspace = await getPersonalTeamWorkspace();

  if (!workspace.ok) {
    if (workspace.reason === "unauthenticated" && isSupabaseConfigured()) {
      redirect("/auth?next=/me");
    }
    if (workspace.reason === "no_membership" && isSupabaseConfigured()) {
      redirect("/onboarding");
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
              Попросите владельца или управляющего добавить сотрудника в Team OS
              и выдать логин.
            </p>
            <Link
              href="/auth/signout"
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
  const openTasks = workspace.tasks.filter(
    (task) => task.status !== "done" && task.status !== "verified",
  );
  const completedTasks = workspace.tasks.filter(
    (task) => task.status === "done" || task.status === "verified",
  );

  return (
    <AppShell
      activeHref="/me"
      venueId={workspace.venueId}
      venueName={workspace.venueName}
      venueMeta="Team OS"
    >
      <main className="flex-1">
        <section className="border-b border-border/40">
          <div className="mx-auto grid max-w-7xl gap-8 px-6 py-14 lg:grid-cols-[0.95fr_1.05fr]">
            <div>
              <Badge variant="outline" className="border-brand/30 text-brand">
                Мой кабинет
              </Badge>
              <h1 className="mt-6 max-w-3xl text-balance text-[clamp(2.2rem,4.6vw,4rem)] font-medium leading-[1.03]">
                {workspace.member.name}
              </h1>
              <p className="mt-5 max-w-2xl text-sm leading-relaxed text-muted-foreground">
                {workspace.venueName} · {role.title.toLowerCase()}. Здесь только
                ваши задачи, объявления и рабочий контур на смену.
              </p>
              <div className="mt-7 flex flex-wrap gap-3">
                <Link
                  href={`/team?role=${role.id}&venueId=${encodeURIComponent(workspace.venueId)}`}
                  className="inline-flex h-10 items-center gap-2 rounded-lg bg-brand px-4 text-sm font-medium text-primary-foreground transition-colors hover:bg-brand-hover"
                >
                  <LayoutDashboard className="size-4" />
                  Открыть Team OS
                </Link>
                <Link
                  href="/auth/signout"
                  className="inline-flex h-10 items-center gap-2 rounded-lg border border-border/60 bg-card/50 px-4 text-sm text-foreground transition-colors hover:border-brand/40"
                >
                  <LogOut className="size-4" />
                  Выйти
                </Link>
              </div>
            </div>

            <div className="rounded-lg border border-border/60 bg-card/60 p-5">
              <div className="flex items-start gap-3">
                <UserRound className="mt-1 size-5 shrink-0 text-brand" />
                <div>
                  <p className="text-[11px] uppercase tracking-[0.22em] text-muted-foreground">
                    Роль и доступ
                  </p>
                  <h2 className="mt-3 text-2xl font-medium">{role.title}</h2>
                  <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                    {role.description}
                  </p>
                </div>
              </div>
              <div className="mt-6 grid gap-3 sm:grid-cols-3">
                <Metric label="активные задачи" value={openTasks.length} />
                <Metric label="объявления" value={workspace.announcements.length} />
                <Metric label="разделы" value={role.homeSections.length} />
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
        </section>

        <section className="border-b border-border/40">
          <div className="mx-auto grid max-w-7xl gap-6 px-6 py-14 lg:grid-cols-[1.1fr_0.9fr]">
            <div>
              <div className="flex items-center gap-3">
                <ClipboardList className="size-5 text-brand" />
                <h2 className="text-2xl font-medium">Мои задачи</h2>
              </div>
              <div className="mt-5 grid gap-3">
                {openTasks.length ? (
                  openTasks.map((task) => <TaskCard key={task.id} task={task} />)
                ) : (
                  <EmptyState text="Активных задач нет." />
                )}
              </div>
            </div>

            <div>
              <div className="flex items-center gap-3">
                <Bell className="size-5 text-brand" />
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
          </div>
        </section>

        <section>
          <div className="mx-auto grid max-w-7xl gap-6 px-6 py-14 lg:grid-cols-2">
            <div className="rounded-lg border border-border/60 bg-card/50 p-5">
              <div className="flex items-center gap-3">
                <GraduationCap className="size-5 text-brand" />
                <h2 className="text-xl font-medium">Обучение и стандарты</h2>
              </div>
              <p className="mt-4 text-sm leading-relaxed text-muted-foreground">
                Здесь будет база знаний, чек-листы смены и короткие тесты по
                роли. Сейчас этот блок фиксирует место для следующего слоя Team
                OS.
              </p>
            </div>

            <div className="rounded-lg border border-border/60 bg-card/50 p-5">
              <div className="flex items-center gap-3">
                <CheckCircle2 className="size-5 text-brand" />
                <h2 className="text-xl font-medium">Закрытые задачи</h2>
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

function TaskCard({ task }: { task: TeamTask }) {
  return (
    <article className="rounded-lg border border-border/60 bg-card/50 p-4">
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant="outline" className={priorityClass(task.priority)}>
          {task.priority}
        </Badge>
        <Badge variant="outline">{statusLabel(task.status)}</Badge>
        {task.dueLabel ? (
          <span className="text-[11px] uppercase tracking-[0.16em] text-muted-foreground">
            {task.dueLabel}
          </span>
        ) : null}
      </div>
      <p className="mt-3 text-sm leading-relaxed text-foreground/90">
        {task.title}
      </p>
      <TaskStatusButtons task={task} />
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

function EmptyState({ text }: { text: string }) {
  return (
    <div className="rounded-lg border border-border/60 bg-card/40 p-5 text-sm text-muted-foreground">
      {text}
    </div>
  );
}
