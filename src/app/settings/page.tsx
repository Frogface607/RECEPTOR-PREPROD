import type { Metadata } from "next";
import Link from "next/link";
import { redirect } from "next/navigation";
import {
  ArrowLeft,
  User,
  Store,
  Brain,
  Plug,
  CreditCard,
  ScrollText,
  CheckCircle2,
  AlertCircle,
  ArrowUpRight,
  type LucideIcon,
} from "lucide-react";
import { getCurrentUser } from "@/lib/auth/session";
import { isSupabaseConfigured } from "@/lib/db/env";
import { getServerSupabase } from "@/lib/db/server";
import { listKnownVenues } from "@/lib/venues/get-venue";
import { calculateContextCompletion } from "@/lib/venues/context-questionnaire";

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
  contextRequiredPercentage: number;
  contextMissingRequired: number;
};

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
    .order("created_at", { ascending: false });

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
      .order("created_at", { ascending: false });

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
        .select("venue_id")
        .in("venue_id", ids)
        .eq("status", "active")
    : { data: [] };
  const connected = new Set(
    ((creds ?? []) as Array<{ venue_id: string }>).map((cred) => cred.venue_id),
  );

  return rows.map((venue) => {
    const completion = calculateContextCompletion(venue.context_profile);

    return {
      id: venue.id,
      name: venue.name,
      city: venue.city ?? "",
      type: venue.type ?? "other",
      iikoConnected: connected.has(venue.id),
      contextRequiredPercentage: completion.requiredPercentage,
      contextMissingRequired: completion.missingRequired.length,
    };
  });
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
    : "/onboarding";

  return (
    <main className="min-h-screen bg-background">
      <header className="border-b border-border/40">
        <div className="mx-auto flex h-16 max-w-4xl items-center gap-4 px-6">
          <Link
            href={firstVenueHref}
            className="inline-flex items-center gap-2 text-[13px] text-muted-foreground transition-colors hover:text-foreground"
          >
            <ArrowLeft className="size-4" />
            Дашборд
          </Link>
          <span className="ml-auto text-[14px] font-medium">Настройки</span>
        </div>
      </header>

      <div className="mx-auto max-w-4xl px-6 py-10">
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

        <div className="space-y-6">
          <Section icon={User} title="Профиль">
            <Row label="Email" value={user?.email ?? "—"} />
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
                          iiko
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
                  Заведения ещё не подключены.
                </p>
              )}
            </div>
            <Link
              href="/onboarding"
              className="mt-3 inline-block text-[13px] text-muted-foreground transition-colors hover:text-foreground"
            >
              + Добавить заведение
            </Link>
          </Section>

          <Section icon={Brain} title="Context Engine">
            <div className="space-y-3">
              <p className="text-[13px] leading-relaxed text-muted-foreground">
                Анкета заведения даёт Copilot постоянный контекст: формат,
                экономику, команду, интеграции и правила работы с AI.
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
                            : " Готово для пилота."}
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

          <Section icon={Plug} title="Подключение iiko">
            <div className="flex items-center gap-3">
              {venues.some((venue) => venue.iikoConnected) ? (
                <>
                  <CheckCircle2 className="size-4 text-brand" />
                  <span className="text-[14px] text-foreground">
                    iiko Cloud подключён — BI и copilot работают на живых данных
                  </span>
                </>
              ) : (
                <>
                  <span className="size-2 rounded-full bg-[color:var(--pro)]" />
                  <span className="text-[14px] text-muted-foreground">
                    iiko apiLogin ещё не подключён.
                  </span>
                </>
              )}
            </div>
            <p className="mt-3 text-[13px] leading-relaxed text-muted-foreground">
              Новый apiLogin добавляется через onboarding. Ключ проверяется в
              iiko Cloud, шифруется и хранится в Supabase credentials.
            </p>
          </Section>

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
    </main>
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
  children: React.ReactNode;
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
