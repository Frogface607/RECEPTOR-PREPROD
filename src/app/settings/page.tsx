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
  CreditCard,
  KeyRound,
  Plug,
  ScrollText,
  Store,
  User,
  type LucideIcon,
} from "lucide-react";
import { AppShell } from "@/components/dashboard/app-shell";
import { getCurrentUser } from "@/lib/auth/session";
import { isSupabaseConfigured } from "@/lib/db/env";
import { getServerSupabase } from "@/lib/db/server";
import { calculateContextCompletion } from "@/lib/venues/context-questionnaire";
import { listKnownVenues } from "@/lib/venues/get-venue";

export const metadata: Metadata = {
  title: "Настройки — RECEPTOR",
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
};

function normalizeIikoChannel(value: string | null | undefined): "cloud" | "rms" | null {
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

  let venues = venuesResult.data as
    | Array<{
        id: string;
        name: string;
        city: string | null;
        type: string | null;
        context_profile?: unknown | null;
      }>
    | null;

  if (venuesResult.error && /context_profile/i.test(venuesResult.error.message)) {
    const fallbackResult = await supabase
      .from("venues")
      .select("id,name,city,type")
      .eq("owner_user_id", user.id)
      .order("created_at", { ascending: true });

    venues = fallbackResult.data as
      | Array<{
          id: string;
          name: string;
          city: string | null;
          type: string | null;
          context_profile?: unknown | null;
        }>
      | null;
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

  return uniqueSettingsVenues(rows.map((venue) => {
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
    };
  }));
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
            "Restaurant OS"
          : "Restaurant OS"
      }
    >
      <main className="flex-1">
        <header className="border-b border-border/40 bg-background/85 backdrop-blur-xl lg:sticky lg:top-0 lg:z-30">
          <div className="mx-auto flex min-h-16 max-w-6xl flex-wrap items-center gap-3 px-6 py-4">
            <div>
              <p className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
                Workspace
              </p>
              <h1 className="mt-1 text-xl font-medium">Настройки</h1>
            </div>
            <div className="ml-auto flex flex-wrap items-center gap-2">
              <Link
                href={firstVenueHref}
                className="inline-flex h-9 items-center rounded-lg border border-border/60 bg-card/55 px-3 text-sm text-foreground transition-colors hover:bg-card"
              >
                Открыть cockpit
              </Link>
              <Link
                href="/onboarding?new=1"
                className="inline-flex h-9 items-center rounded-lg bg-brand px-3 text-sm font-medium text-primary-foreground transition-colors hover:bg-brand-hover"
              >
                Добавить заведение
              </Link>
            </div>
          </div>
        </header>

        <div className="mx-auto max-w-6xl px-6 py-8">
        {user?.isDemo ? (
          <div className="mb-8 flex items-start gap-3 rounded-xl border border-[color:var(--pro)]/30 bg-[color:var(--pro)]/8 p-4">
            <AlertCircle className="mt-0.5 size-4 shrink-0 text-[color:var(--pro)]" />
            <p className="text-[13px] leading-relaxed text-foreground/85">
              Тестовый доступ.{" "}
              {configured ? "Войдите" : "Подключите Supabase и войдите"},
              чтобы сохранять профиль, заведения и подключения.
            </p>
          </div>
        ) : null}

        <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
          <div className="space-y-6">
          <Section icon={User} title="Профиль">
            <Row label="Email" value={user?.email ?? "-"} />
            <Row
              label="Статус"
              value={
                user?.isDeveloper
                  ? "Разработчик"
                  : user?.isDemo
                    ? "Тестовый доступ"
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
              + Добавить заведение
            </Link>
          </Section>
          </div>

          <div className="space-y-6">
          <Section icon={Brain} title="Context Engine">
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
                  Добавьте заведение, чтобы собрать его операционный контекст.
                </p>
              )}
            </div>
          </Section>

          <IikoConnectionCenter venues={venues} />

          <Section icon={CreditCard} title="Подписка">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="rounded-full border border-border/60 bg-card/60 px-3 py-1 text-[11px] uppercase tracking-[0.16em] text-foreground">
                  Free
                </span>
                <span className="text-[13px] text-muted-foreground">
                  1 заведение · базовый дашборд
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

function IikoConnectionCenter({ venues }: { venues: SettingsVenue[] }) {
  const hasVenues = venues.length > 0;
  const connectedCount = venues.filter((venue) => venue.iikoConnected).length;

  return (
    <Section icon={Plug} title="iiko">
      <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h3 className="text-lg font-medium">Подключение данных</h3>
          <p className="mt-1 text-[13px] leading-relaxed text-muted-foreground">
            Ключ хранится в Supabase. BI включается после прав Cloud API.
          </p>
        </div>
        <StatusPill
          tone={connectedCount > 0 ? "ok" : "warn"}
          label={connectedCount > 0 ? `${connectedCount} активн.` : "нет ключа"}
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
                  {venue.iikoConnected ? "Проверить BI" : "Подключить"}
                </Link>
              </div>

              <div className="mt-4 grid gap-2 sm:grid-cols-3">
                <DiagnosticItem
                  icon={KeyRound}
                  title="API login"
                  text={venue.iikoConnected ? "сохранён" : "не подключён"}
                  tone={venue.iikoConnected ? "ok" : "warn"}
                />
                <DiagnosticItem
                  icon={CheckCircle2}
                  title="Организация"
                  text={
                    venue.iikoConnected
                      ? venue.iikoChannel === "rms"
                        ? "RMS server"
                        : "выбрана"
                      : "ожидает ключ"
                  }
                  tone={venue.iikoConnected ? "ok" : "muted"}
                />
                <DiagnosticItem
                  icon={Activity}
                  title="BI reports"
                  text={
                    venue.iikoConnected
                      ? venue.iikoChannel === "rms"
                        ? "OLAP доступен"
                        : "нужны OLAP-права"
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

function StatusPill({
  tone,
  label,
}: {
  tone: "ok" | "warn";
  label: string;
}) {
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
      Context {venue.contextRequiredPercentage}%
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
    <div className="flex items-center justify-between border-b border-border/30 py-2.5 last:border-b-0">
      <span className="text-[13px] text-muted-foreground">{label}</span>
      <span className="text-[14px] text-foreground">{value}</span>
    </div>
  );
}
