import type { Metadata } from "next";
import type { ReactNode } from "react";
import Link from "next/link";
import { redirect } from "next/navigation";
import {
  Activity,
  AlertCircle,
  ArrowUpRight,
  Brain,
  CheckCircle2,
  ClipboardList,
  CreditCard,
  KeyRound,
  ListChecks,
  Plug,
  ScrollText,
  Store,
  User,
  UsersRound,
  type LucideIcon,
} from "lucide-react";
import { AppShell } from "@/components/dashboard/app-shell";
import { IikoDiagnosticsPanel } from "@/components/settings/iiko-diagnostics-panel";
import { getCurrentUser } from "@/lib/auth/session";
import { isSupabaseConfigured } from "@/lib/db/env";
import { getServerSupabase } from "@/lib/db/server";
import {
  buildSecondBrainLaunchPath,
  type SecondBrainLaunchItemId,
} from "@/lib/settings/second-brain-launch";
import {
  DEMO_STAFF,
  DEMO_TASK_COMMENTS,
  DEMO_TEAM_TASKS,
} from "@/lib/team/team-os";
import { calculateContextCompletion } from "@/lib/venues/context-questionnaire";
import { listKnownVenues } from "@/lib/venues/get-venue";

export const metadata: Metadata = {
  title: "Запуск ресторана — RECEPTOR",
};

export const dynamic = "force-dynamic";

type SettingsVenue = {
  id: string;
  name: string;
  city: string;
  type: string;
  iikoConnected: boolean;
  iikoChannel: "cloud" | "rms" | null;
  contextRequiredPercentage: number;
  contextMissingRequired: number;
  teamMembersCount: number;
  openTasksCount: number;
  fieldNotesCount: number;
};

function normalizeIikoChannel(
  value: string | null | undefined,
): "cloud" | "rms" | null {
  return value === "cloud" || value === "rms" ? value : null;
}

function uniqueSettingsVenues(venues: SettingsVenue[]): SettingsVenue[] {
  const seen = new Set<string>();

  return venues.filter((venue) => {
    const key = [
      venue.name.trim().toLowerCase(),
      venue.city.trim().toLowerCase(),
      venue.type,
    ].join("|");
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

async function listSettingsVenues(): Promise<SettingsVenue[]> {
  const user = await getCurrentUser();
  if (!user || user.isDemo) {
    return listKnownVenues().map((venue) => {
      const completion = calculateContextCompletion(venue.context);

      return {
        id: venue.id,
        name: venue.name,
        city: venue.city,
        type: venue.type,
        iikoConnected: Boolean(venue.iiko.apiLogin),
        iikoChannel: normalizeIikoChannel(venue.iiko.channel),
        contextRequiredPercentage: completion.requiredPercentage,
        contextMissingRequired: completion.missingRequired.length,
        teamMembersCount: DEMO_STAFF.filter(
          (member) => member.venueId === venue.id,
        ).length,
        openTasksCount: DEMO_TEAM_TASKS.filter(
          (task) =>
            task.venueId === venue.id &&
            task.status !== "done" &&
            task.status !== "verified",
        ).length,
        fieldNotesCount: DEMO_TASK_COMMENTS.filter(
          (comment) => comment.venueId === venue.id,
        ).length,
      };
    });
  }

  const supabase = await getServerSupabase();
  if (!supabase) return [];

  const venuesResult = await supabase
    .from("venues")
    .select("id,name,city,type,context_profile")
    .eq("owner_user_id", user.id)
    .order("created_at", { ascending: true });

  let venues = venuesResult.data as Array<{
    id: string;
    name: string;
    city: string | null;
    type: string | null;
    context_profile?: unknown | null;
  }> | null;

  if (
    venuesResult.error &&
    /context_profile/i.test(venuesResult.error.message)
  ) {
    const fallbackResult = await supabase
      .from("venues")
      .select("id,name,city,type")
      .eq("owner_user_id", user.id)
      .order("created_at", { ascending: true });

    venues = fallbackResult.data as Array<{
      id: string;
      name: string;
      city: string | null;
      type: string | null;
      context_profile?: unknown | null;
    }> | null;
  }

  const rows = (venues ?? []) as Array<{
    id: string;
    name: string;
    city: string | null;
    type: string | null;
    context_profile?: unknown | null;
  }>;

  const ids = rows.map((venue) => venue.id);
  const { data: creds } = ids.length
    ? await supabase
        .from("iiko_credentials")
        .select("venue_id,channel")
        .in("venue_id", ids)
        .eq("status", "active")
    : { data: [] };
  const connected = new Map(
    ((creds ?? []) as Array<{ venue_id: string; channel: string | null }>).map(
      (cred) => [
        cred.venue_id,
        cred.channel === "rms" || cred.channel === "cloud"
          ? cred.channel
          : null,
      ],
    ),
  );
  const [membershipsResult, tasksResult, commentsResult] = ids.length
    ? await Promise.all([
        supabase
          .from("venue_memberships")
          .select("venue_id")
          .in("venue_id", ids)
          .eq("status", "active"),
        supabase
          .from("team_tasks")
          .select("venue_id,status")
          .in("venue_id", ids),
        supabase
          .from("team_task_comments")
          .select("venue_id")
          .in("venue_id", ids),
      ])
    : [{ data: [] }, { data: [] }, { data: [] }];
  const teamMembersByVenue = new Map<string, number>();
  for (const membership of (membershipsResult.data ?? []) as Array<{
    venue_id: string;
  }>) {
    teamMembersByVenue.set(
      membership.venue_id,
      (teamMembersByVenue.get(membership.venue_id) ?? 0) + 1,
    );
  }

  const openTasksByVenue = new Map<string, number>();
  for (const task of (tasksResult.data ?? []) as Array<{
    venue_id: string;
    status: string | null;
  }>) {
    if (task.status === "done" || task.status === "verified") continue;
    openTasksByVenue.set(
      task.venue_id,
      (openTasksByVenue.get(task.venue_id) ?? 0) + 1,
    );
  }
  const fieldNotesByVenue = new Map<string, number>();
  for (const comment of (commentsResult.data ?? []) as Array<{
    venue_id: string;
  }>) {
    fieldNotesByVenue.set(
      comment.venue_id,
      (fieldNotesByVenue.get(comment.venue_id) ?? 0) + 1,
    );
  }

  return uniqueSettingsVenues(
    rows.map((venue) => {
      const completion = calculateContextCompletion(venue.context_profile);

      return {
        id: venue.id,
        name: venue.name,
        city: venue.city ?? "",
        type: venue.type ?? "other",
        iikoConnected: connected.has(venue.id),
        iikoChannel: normalizeIikoChannel(connected.get(venue.id)),
        contextRequiredPercentage: completion.requiredPercentage,
        contextMissingRequired: completion.missingRequired.length,
        teamMembersCount: teamMembersByVenue.get(venue.id) ?? 0,
        openTasksCount: openTasksByVenue.get(venue.id) ?? 0,
        fieldNotesCount: fieldNotesByVenue.get(venue.id) ?? 0,
      };
    }),
  );
}

export default async function SettingsPage() {
  const user = await getCurrentUser();
  const configured = isSupabaseConfigured();
  if (configured && !user) {
    redirect("/auth?next=/settings");
  }
  const venues = await listSettingsVenues();
  const firstVenueHref = venues[0]
    ? `/dashboard/${venues[0].id}`
    : "/onboarding?new=1";
  const activeVenue = venues[0];

  return (
    <AppShell
      activeHref="/settings"
      venueId={activeVenue?.id ?? "dev-venue"}
      venueName={activeVenue?.name ?? "Рабочий кабинет"}
      venueMeta={
        activeVenue
          ? [activeVenue.city, activeVenue.type].filter(Boolean).join(" · ") ||
            "Receptor"
          : "Receptor"
      }
    >
      <main className="flex-1">
        <header className="border-b border-border/40 bg-background/85 backdrop-blur-xl lg:sticky lg:top-0 lg:z-30">
          <div className="mx-auto flex min-h-16 max-w-6xl flex-wrap items-center gap-3 px-6 py-4">
            <div>
              <p className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
                Первый запуск
              </p>
              <h1 className="mt-1 text-xl font-medium">Запуск ресторана</h1>
              <p className="mt-1 max-w-xl text-[13px] leading-relaxed text-muted-foreground">
                Доведите кабинет до первого рабочего разбора: профиль, iiko,
                команда, итог смены и понятное действие для владельца.
              </p>
            </div>
            <div className="ml-auto flex flex-wrap items-center gap-2">
              <Link
                href={firstVenueHref}
                className="inline-flex h-9 items-center rounded-lg border border-border/60 bg-card/55 px-3 text-sm text-foreground transition-colors hover:bg-card"
              >
                Открыть разбор
              </Link>
              <Link
                href="/onboarding?new=1"
                className="inline-flex h-9 items-center rounded-lg bg-brand px-3 text-sm font-medium text-primary-foreground transition-colors hover:bg-brand-hover"
              >
                Подключить ресторан
              </Link>
            </div>
          </div>
        </header>

        <div className="mx-auto max-w-6xl px-6 py-8">
          {user?.isDemo ? (
            <div className="mb-8 flex items-start gap-3 rounded-xl border border-[color:var(--pro)]/30 bg-[color:var(--pro)]/8 p-4">
              <AlertCircle className="mt-0.5 size-4 shrink-0 text-[color:var(--pro)]" />
              <p className="text-[13px] leading-relaxed text-foreground/85">
                Режим просмотра.{" "}
                {configured ? "Войдите" : "Настройте рабочий вход"},
                чтобы сохранять профиль, заведения, iiko и команду.
              </p>
            </div>
          ) : null}

          <LaunchChecklist venues={venues} firstVenueHref={firstVenueHref} />

          <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
            <div className="space-y-6">
              <Section icon={User} title="Профиль">
                <Row label="Email" value={user?.email ?? "-"} />
                <Row
                  label="Статус"
                  value={
                    user?.isDeveloper
                      ? "Режим просмотра"
                      : user?.isDemo
                        ? "Режим просмотра"
                        : "Авторизован"
                  }
                />
              </Section>

              <Section icon={Store} title="Заведения">
                <div className="space-y-2">
                  {venues.length > 0 ? (
                    venues.map((venue) => (
                      <div
                        key={venue.id}
                        className="flex items-center justify-between rounded-lg border border-border/50 bg-background/40 px-4 py-3"
                      >
                        <div>
                          <p className="text-[14px] font-medium text-foreground">
                            {venue.name}
                          </p>
                          <p className="text-[11px] uppercase tracking-widest text-muted-foreground">
                            {venue.city || "город не указан"} · {venue.type}
                          </p>
                        </div>
                        <div className="flex items-center gap-3">
                          <ContextStatus venue={venue} />
                          {venue.iikoConnected ? (
                            <span className="hidden items-center gap-1.5 text-[11px] uppercase tracking-[0.14em] text-brand sm:inline-flex">
                              <CheckCircle2 className="size-3.5" />
                              {venue.iikoChannel ?? "iiko"}
                            </span>
                          ) : (
                            <span className="hidden text-[11px] uppercase tracking-[0.14em] text-muted-foreground sm:inline">
                              нет iiko
                            </span>
                          )}
                          <Link
                            href={`/dashboard/${venue.id}`}
                            className="text-[13px] text-brand underline-offset-4 hover:underline"
                          >
                            Открыть
                          </Link>
                        </div>
                      </div>
                    ))
                  ) : (
                    <p className="text-[13px] text-muted-foreground">
                      Заведения еще не подключены.
                    </p>
                  )}
                </div>
                <Link
                  href="/onboarding?new=1"
                  className="mt-3 inline-block text-[13px] text-muted-foreground transition-colors hover:text-foreground"
                >
                  + Подключить ресторан
                </Link>
              </Section>
            </div>

            <div className="space-y-6">
              <Section icon={Brain} title="Память заведения">
                <div className="space-y-3">
                  <p className="text-[13px] leading-relaxed text-muted-foreground">
                    Анкета заведения дает AI постоянный контекст: формат,
                    экономику, команду, интеграции и правила работы с данными.
                  </p>
                  {venues.length > 0 ? (
                    <div className="space-y-2">
                      {venues.map((venue) => (
                        <div
                          key={venue.id}
                          className="flex items-center justify-between rounded-lg border border-border/50 bg-background/40 px-4 py-3"
                        >
                          <div>
                            <p className="text-[14px] font-medium text-foreground">
                              {venue.name}
                            </p>
                            <p className="text-[12px] text-muted-foreground">
                              Обязательный контекст заполнен на{" "}
                              {venue.contextRequiredPercentage}%.
                              {venue.contextMissingRequired > 0
                                ? ` Осталось полей: ${venue.contextMissingRequired}.`
                                : " Готово к работе."}
                            </p>
                          </div>
                          <Link
                            href={`/context?venueId=${encodeURIComponent(venue.id)}`}
                            className="inline-flex items-center gap-1.5 text-[13px] text-brand underline-offset-4 hover:underline"
                          >
                            Анкета
                            <ArrowUpRight className="size-3.5" />
                          </Link>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-[13px] text-muted-foreground">
                      Добавьте заведение, чтобы собрать его операционный
                      контекст.
                    </p>
                  )}
                </div>
              </Section>

              <div id="iiko">
                <IikoConnectionCenter venues={venues} />
              </div>

              <Section icon={CreditCard} title="Подписка">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="rounded-full border border-border/60 bg-card/60 px-3 py-1 text-[11px] uppercase tracking-[0.16em] text-foreground">
                      Free
                    </span>
                    <span className="text-[13px] text-muted-foreground">
                      1 заведение · базовый разбор
                    </span>
                  </div>
                  <Link
                    href="/pricing"
                    className="text-[13px] text-brand underline-offset-4 hover:underline"
                  >
                    Сравнить тарифы
                  </Link>
                </div>
              </Section>

              <Section icon={ScrollText} title="Журнал действий">
                <p className="text-[13px] text-muted-foreground">
                  Появится после первого входа и подключения iiko.
                </p>
              </Section>
            </div>
          </div>
        </div>
      </main>
    </AppShell>
  );
}

function LaunchChecklist({
  venues,
  firstVenueHref,
}: {
  venues: SettingsVenue[];
  firstVenueHref: string;
}) {
  const venue = venues[0];
  const launchPath = buildSecondBrainLaunchPath({
    venue: venue ?? null,
    firstVenueHref,
  });
  const focus = launchPath.focus;

  return (
    <section className="mb-6 rounded-xl border border-border/60 bg-card/45 p-5">
      <div className="mb-5 grid gap-4 lg:grid-cols-[1fr_0.62fr]">
        <div>
          <div className="flex items-center gap-2.5">
            <span className="flex size-8 items-center justify-center rounded-lg border border-border/50 bg-background/60 text-brand">
              <ListChecks className="size-4" />
            </span>
            <h2 className="text-[12px] uppercase tracking-[0.18em] text-muted-foreground">
              План запуска
            </h2>
          </div>
          <p className="mt-3 text-lg font-medium leading-snug text-foreground">
            {launchPath.headline}
          </p>
          <p className="mt-2 max-w-2xl text-[13px] leading-relaxed text-muted-foreground">
            Сначала сохраняем ресторан и iiko, затем добавляем роли, итог смены
            и первый разбор для владельца. Так кабинет сразу становится рабочим,
            а не превращается в набор отдельных отчетов.
          </p>
        </div>

        <div className="rounded-lg border border-brand/25 bg-brand/[0.05] p-4">
          <p className="text-[11px] uppercase tracking-[0.16em] text-brand">
            Следующий шаг
          </p>
          <div className="mt-3 flex items-start justify-between gap-3">
            <div>
              <p className="text-sm font-medium text-foreground">
                {focus.title}
              </p>
              <p className="mt-1 text-[12px] leading-relaxed text-muted-foreground">
                {focus.detail}
              </p>
            </div>
            <span className="rounded-md border border-border/50 bg-background/60 px-2 py-1 text-[10px] uppercase tracking-[0.12em] text-muted-foreground">
              {launchPath.readyCount}/{launchPath.totalCount}
            </span>
          </div>
          <Link
            href={focus.href}
            className="mt-4 inline-flex h-9 items-center justify-center rounded-lg bg-brand px-3 text-sm font-medium text-primary-foreground transition-colors hover:bg-brand-hover"
          >
            {focus.action}
          </Link>
        </div>
      </div>

      <div className="grid gap-2 md:grid-cols-2 xl:grid-cols-5">
        {launchPath.items.map((item) => {
          const Icon = launchIcon(item.id);

          return (
            <Link
              key={item.id}
              href={item.href}
              className={
                "group flex min-h-32 flex-col justify-between rounded-lg border p-4 transition-colors hover:border-brand/35 hover:bg-background/55 " +
                (item.id === focus.id
                  ? "border-brand/35 bg-brand/[0.04]"
                  : "border-border/45 bg-background/35")
              }
            >
              <div className="flex items-start justify-between gap-3">
                <span className="flex size-9 items-center justify-center rounded-lg border border-border/45 bg-card/45 text-foreground">
                  <Icon className="size-4" />
                </span>
                <span
                  className={
                    "rounded-full border px-2 py-1 text-[10px] uppercase tracking-[0.12em] " +
                    (item.ready
                      ? "border-brand/25 bg-brand/10 text-brand"
                      : "border-[color:var(--pro)]/25 bg-[color:var(--pro)]/10 text-[color:var(--pro)]")
                  }
                >
                  {item.status}
                </span>
              </div>
              <div>
                <p className="text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
                  {item.step}
                </p>
                <p className="text-[14px] font-medium text-foreground">
                  {item.title}
                </p>
                <p className="mt-1 line-clamp-2 text-[12px] leading-relaxed text-muted-foreground">
                  {item.detail}
                </p>
                <p className="mt-2 inline-flex items-center gap-1.5 text-[13px] text-muted-foreground transition-colors group-hover:text-foreground">
                  {item.action}
                  <ArrowUpRight className="size-3.5" />
                </p>
              </div>
            </Link>
          );
        })}
      </div>
    </section>
  );
}

function launchIcon(id: SecondBrainLaunchItemId): LucideIcon {
  if (id === "context") return Brain;
  if (id === "people") return UsersRound;
  if (id === "field_note") return ClipboardList;
  if (id === "advisor") return Activity;
  return Plug;
}

function IikoConnectionCenter({ venues }: { venues: SettingsVenue[] }) {
  const hasVenues = venues.length > 0;
  const connectedCount = venues.filter((venue) => venue.iikoConnected).length;

  return (
    <Section icon={Plug} title="iiko">
      <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h3 className="text-lg font-medium">iiko и данные продаж</h3>
          <p className="mt-1 text-[13px] leading-relaxed text-muted-foreground">
            Доступ сохраняется в кабинете и используется для продаж, меню,
            смен и управленческих отчетов.
          </p>
        </div>
        <StatusPill
          tone={connectedCount > 0 ? "ok" : "warn"}
          label={connectedCount > 0 ? `${connectedCount} активн.` : "не подключено"}
        />
      </div>

      {hasVenues ? (
        <div className="space-y-2">
          {venues.map((venue) => (
            <div
              key={venue.id}
              className="rounded-lg border border-border/50 bg-background/40 p-4"
            >
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="text-sm font-medium text-foreground">
                    {venue.name}
                  </p>
                  <p className="mt-1 text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
                    {venue.city || "город не указан"} · {venue.type}
                    {venue.iikoChannel ? ` · ${venue.iikoChannel}` : ""}
                  </p>
                </div>
                <Link
                  href={
                    venue.iikoConnected
                      ? `/dashboard/${venue.id}`
                      : "/onboarding?new=1"
                  }
                  className="inline-flex h-8 items-center justify-center rounded-md border border-border/60 bg-card/55 px-3 text-[13px] text-foreground transition-colors hover:bg-card"
                >
                  {venue.iikoConnected ? "Открыть разбор" : "Подключить"}
                </Link>
              </div>

              <div className="mt-4 grid gap-2 sm:grid-cols-3">
                <DiagnosticItem
                  icon={KeyRound}
                  title="Ключ iiko"
                  text={venue.iikoConnected ? "сохранён" : "не подключён"}
                  tone={venue.iikoConnected ? "ok" : "warn"}
                />
                <DiagnosticItem
                  icon={CheckCircle2}
                  title="Точка продаж"
                  text={
                    venue.iikoConnected
                      ? venue.iikoChannel === "rms"
                        ? "сервер подключен"
                        : "выбрана"
                      : "ожидает ключ"
                  }
                  tone={venue.iikoConnected ? "ok" : "muted"}
                />
                <DiagnosticItem
                  icon={Activity}
                  title="Отчеты"
                  text={
                    venue.iikoConnected
                      ? venue.iikoChannel === "rms"
                        ? "продажи доступны"
                        : "нужны права отчетов"
                      : "после ключа"
                  }
                  tone={
                    venue.iikoConnected && venue.iikoChannel === "rms"
                      ? "ok"
                      : venue.iikoConnected
                        ? "warn"
                        : "muted"
                  }
                />
              </div>
              <div id={`iiko-diagnostics-${venue.id}`} className="scroll-mt-24">
                <IikoDiagnosticsPanel
                  venueId={venue.id}
                  connected={venue.iikoConnected}
                />
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-[13px] text-muted-foreground">
          Добавьте заведение, чтобы подключить iiko.
        </p>
      )}
    </Section>
  );
}

function DiagnosticItem({
  icon: Icon,
  title,
  text,
  tone,
}: {
  icon: LucideIcon;
  title: string;
  text: string;
  tone: "ok" | "warn" | "muted";
}) {
  return (
    <div className="rounded-md border border-border/45 bg-card/35 p-3">
      <div className="flex items-center gap-2">
        <Icon
          className={
            "size-3.5 " +
            (tone === "ok"
              ? "text-brand"
              : tone === "warn"
                ? "text-[color:var(--pro)]"
                : "text-muted-foreground")
          }
        />
        <p className="text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
          {title}
        </p>
      </div>
      <p className="mt-2 text-[13px] text-foreground">{text}</p>
    </div>
  );
}

function StatusPill({ tone, label }: { tone: "ok" | "warn"; label: string }) {
  return (
    <span
      className={
        "inline-flex h-7 shrink-0 items-center rounded-full border px-2.5 text-[11px] uppercase tracking-[0.14em] " +
        (tone === "ok"
          ? "border-brand/30 bg-brand/10 text-brand"
          : "border-[color:var(--pro)]/30 bg-[color:var(--pro)]/10 text-[color:var(--pro)]")
      }
    >
      {label}
    </span>
  );
}

function ContextStatus({ venue }: { venue: SettingsVenue }) {
  const ready = venue.contextRequiredPercentage >= 100;

  return (
    <Link
      href={`/context?venueId=${encodeURIComponent(venue.id)}`}
      className={
        ready
          ? "hidden items-center gap-1.5 text-[11px] uppercase tracking-[0.14em] text-brand sm:inline-flex"
          : "hidden items-center gap-1.5 text-[11px] uppercase tracking-[0.14em] text-[color:var(--pro)] sm:inline-flex"
      }
    >
      {ready ? (
        <CheckCircle2 className="size-3.5" />
      ) : (
        <AlertCircle className="size-3.5" />
      )}
      Память {venue.contextRequiredPercentage}%
    </Link>
  );
}

function Section({
  icon: Icon,
  title,
  children,
}: {
  icon: LucideIcon;
  title: string;
  children: ReactNode;
}) {
  return (
    <section className="rounded-xl border border-border/60 bg-card/50 p-6">
      <div className="mb-5 flex items-center gap-2.5">
        <span className="flex size-8 items-center justify-center rounded-lg border border-border/50 bg-background/60 text-brand">
          <Icon className="size-4" />
        </span>
        <h2 className="text-[12px] uppercase tracking-[0.18em] text-muted-foreground">
          {title}
        </h2>
      </div>
      {children}
    </section>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-1 border-b border-border/30 py-2.5 last:border-b-0 sm:flex-row sm:items-center sm:justify-between">
      <span className="text-[13px] text-muted-foreground">{label}</span>
      <span className="max-w-full break-all text-[14px] text-foreground sm:max-w-[70%] sm:text-right sm:break-words">
        {value}
      </span>
    </div>
  );
}
