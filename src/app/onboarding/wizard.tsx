"use client";

import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import {
  Store,
  Plug,
  Rocket,
  ArrowRight,
  ArrowLeft,
  Check,
  Loader2,
  Search,
  Sparkles,
  Target,
  TriangleAlert,
  Users,
} from "lucide-react";
import {
  createVenueAction,
  probeIikoOrganizationsAction,
  probeRmsOrganizationsAction,
  type IikoOrganizationOption,
} from "./actions";
import type { VenueIntelligenceProfile } from "@/lib/venues/intelligence";
import type { VenueContextAnswers } from "@/lib/venues/context-questionnaire";

type VenueType = "restaurant" | "cafe" | "coffee" | "bar" | "chain" | "other";
type IikoChannel = "cloud" | "rms";

const VENUE_TYPES: { id: VenueType; label: string }[] = [
  { id: "restaurant", label: "Ресторан" },
  { id: "cafe", label: "Кафе" },
  { id: "coffee", label: "Кофейня" },
  { id: "bar", label: "Бар" },
  { id: "chain", label: "Сеть" },
  { id: "other", label: "Другое" },
];

const STEPS = [
  { icon: Store, label: "Заведение" },
  { icon: Plug, label: "Подключение iiko" },
  { icon: Rocket, label: "Готово" },
];

function researchProviderLabel(
  provider: string | null,
  profile: VenueIntelligenceProfile | null,
): string | null {
  if (!provider) return null;
  if (profile?.researchStatus === "researched") {
    if (provider === "openai") return "OpenAI Web Research";
    if (provider === "openrouter") return "Web Research";
    return "Deep Research";
  }
  if (provider === "fallback") return "Анкета";
  return "Черновик профиля";
}

function defaultRevenueModel(type: VenueType): string[] {
  if (type === "bar") return ["зал", "бар", "события"];
  if (type === "coffee") return ["зал", "самовывоз"];
  if (type === "chain") return ["зал", "доставка", "самовывоз"];
  return ["зал", "бар", "доставка"];
}

function buildOnboardingContextAnswers({
  type,
  city,
  ownerContext,
  profile,
}: {
  type: VenueType;
  city: string;
  ownerContext: string;
  profile: VenueIntelligenceProfile | null;
}): VenueContextAnswers {
  return {
    format: profile?.format ?? `${type} · ${city || "город не указан"}`,
    positioning: ownerContext || profile?.positioning || "",
    audience: profile?.audience ?? [],
    owner_goals: profile?.ownerGoals ?? [
      "видеть действия на сегодня",
      "сократить ручные отчеты",
      "контролировать меню и маржу",
    ],
    revenue_model: defaultRevenueModel(type),
    decision_metrics: [
      "выручка",
      "средний чек",
      "топ блюд",
      "категории",
      "смены",
    ],
    team_roles: ["владелец", "управляющий", "шеф", "администратор"],
    responsible_people:
      "Владелец получает управленческий бриф, управляющий отвечает за смену, кухня за меню и стоп-лист.",
    service_standards: profile?.decisionRules ?? [],
    pos_system: "iiko",
    channels: ["iiko", "Telegram", "ручные отчеты"],
    integration_pains: profile?.operatingRisks ?? [],
    ai_provider_policy: "пока не важно",
    copilot_tone:
      "Коротко, по делу, как операционный директор: факт, вывод, действие, недостающие данные.",
    red_lines: [
      "не делать кадровые выводы без проверки данных",
      "не менять цены автоматически",
      "не публиковать контент без подтверждения",
    ],
  };
}

export function OnboardingWizard({ demoMode }: { demoMode: boolean }) {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [pending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);

  const [name, setName] = useState("");
  const [type, setType] = useState<VenueType>("restaurant");
  const [city, setCity] = useState("");
  const [channel, setChannel] = useState<IikoChannel>("cloud");
  const [apiLogin, setApiLogin] = useState("");
  const [rmsHost, setRmsHost] = useState("");
  const [rmsLogin, setRmsLogin] = useState("");
  const [rmsPassword, setRmsPassword] = useState("");
  const [organizations, setOrganizations] = useState<IikoOrganizationOption[]>([]);
  const [organizationId, setOrganizationId] = useState("");
  const [checkingIiko, setCheckingIiko] = useState(false);
  const [ownerContext, setOwnerContext] = useState("");
  const [intelligenceProfile, setIntelligenceProfile] =
    useState<VenueIntelligenceProfile | null>(null);
  const [researchingVenue, setResearchingVenue] = useState(false);
  const [researchProvider, setResearchProvider] = useState<string | null>(null);
  const [researchSummary, setResearchSummary] = useState<string | null>(null);
  const [researchDiagnostics, setResearchDiagnostics] = useState<string[]>([]);

  const canNext0 = name.trim().length > 0;
  const canNext1 =
    organizationId.length > 0 &&
    (channel === "cloud" ? apiLogin.trim().length > 0 : true);

  const researchVenue = async () => {
    if (!name.trim()) {
      setError("Введите название заведения.");
      return;
    }

    setError(null);
    setResearchingVenue(true);
    try {
      const response = await fetch("/api/venue/research", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: name.trim(),
          city: city.trim(),
          type,
          ownerContext: ownerContext.trim(),
        }),
      });

      const data = (await response.json()) as {
        error?: string;
        provider?: string;
        summary?: string;
        diagnostics?: string[];
        profile?: VenueIntelligenceProfile;
      };
      if (!response.ok || !data.profile) {
        throw new Error(data.error || "Не удалось собрать профиль заведения.");
      }

      setIntelligenceProfile(data.profile);
      setResearchProvider(data.provider ?? "profile");
      setResearchSummary(data.summary ?? null);
      setResearchDiagnostics(data.diagnostics ?? []);
      setOwnerContext(data.profile.positioning);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Не удалось собрать профиль заведения.",
      );
    } finally {
      setResearchingVenue(false);
    }
  };

  const checkIiko = () => {
    setError(null);
    setCheckingIiko(true);
    startTransition(async () => {
      const res =
        channel === "cloud"
          ? await probeIikoOrganizationsAction({ apiLogin })
          : await probeRmsOrganizationsAction({
              host: rmsHost,
              login: rmsLogin,
              password: rmsPassword,
            });
      setCheckingIiko(false);
      if (!res.ok) {
        setOrganizations([]);
        setOrganizationId("");
        setError(res.error);
        return;
      }
      setOrganizations(res.organizations);
      setOrganizationId(res.organizations[0]?.id ?? "");
    });
  };

  const openSandbox = () => {
    router.push("/dashboard/dev-venue");
  };

  const finish = () => {
    setError(null);
    startTransition(async () => {
      const res = await createVenueAction({
        name,
        type,
        city,
        intelligenceProfile: intelligenceProfile
          ? { ...intelligenceProfile, positioning: ownerContext || intelligenceProfile.positioning }
          : ownerContext
            ? {
                format: `${type} · ${city || "город не указан"}`,
                positioning: ownerContext,
                researchStatus: "manual",
              }
            : undefined,
        contextAnswers: buildOnboardingContextAnswers({
          type,
          city,
          ownerContext,
          profile: intelligenceProfile,
        }),
        channel,
        apiLogin,
        organizationId,
        rmsHost,
        rmsLogin,
        rmsPassword,
      });
      if (!res.ok) {
        setError(res.error);
        return;
      }
      router.push(`/dashboard/${res.venueId}`);
    });
  };

  return (
    <div>
      {/* Stepper */}
      <ol className="mb-10 flex items-center gap-2">
        {STEPS.map((s, i) => {
          const Icon = s.icon;
          const active = i === step;
          const done = i < step;
          return (
            <li key={s.label} className="flex flex-1 items-center gap-2">
              <div
                className={
                  "flex size-9 shrink-0 items-center justify-center rounded-lg border transition-colors " +
                  (done
                    ? "border-brand/50 bg-brand/15 text-brand"
                    : active
                      ? "border-brand/60 bg-brand text-primary-foreground"
                      : "border-border/60 bg-card/60 text-muted-foreground")
                }
              >
                {done ? <Check className="size-4" /> : <Icon className="size-4" />}
              </div>
              <span
                className={
                  "hidden text-[12px] uppercase tracking-[0.14em] sm:inline " +
                  (active ? "text-foreground" : "text-muted-foreground")
                }
              >
                {s.label}
              </span>
              {i < STEPS.length - 1 ? (
                <span className="mx-1 h-px flex-1 bg-border/50" />
              ) : null}
            </li>
          );
        })}
      </ol>

      <div className="rounded-xl border border-border/60 bg-card/50 p-7">
        {step === 0 ? (
          <div className="flex flex-col gap-5">
            <div>
              <h2 className="text-xl font-medium tracking-[-0.01em]">
                Расскажите о заведении
              </h2>
              <p className="mt-2 text-[14px] text-muted-foreground">
                С этого начнём — потом подключим данные.
              </p>
            </div>

            <Field label="Название" required>
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Название ресторана"
                className="input-base"
              />
            </Field>

            <Field label="Тип заведения">
              <div className="flex flex-wrap gap-2">
                {VENUE_TYPES.map((t) => (
                  <button
                    key={t.id}
                    type="button"
                    onClick={() => setType(t.id)}
                    className={
                      "rounded-full border px-3.5 py-1.5 text-[13px] transition-colors " +
                      (type === t.id
                        ? "border-brand/50 bg-brand/10 text-brand"
                        : "border-border/60 bg-background/50 text-muted-foreground hover:text-foreground")
                    }
                  >
                    {t.label}
                  </button>
                ))}
              </div>
            </Field>

            <Field label="Город">
              <input
                value={city}
                onChange={(e) => setCity(e.target.value)}
                placeholder="Город"
                className="input-base"
              />
            </Field>

            <div className="rounded-lg border border-border/50 bg-background/35 p-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="text-[13px] font-medium text-foreground">
                    Профиль заведения для советника
                  </p>
                  <p className="mt-1 text-[13px] leading-relaxed text-muted-foreground">
                    Receptor исследует публичный контекст, отзывы и
                    позиционирование, а затем соберёт профиль: концепцию,
                    сильные стороны, риски и правила для советника.
                  </p>
                </div>
                {researchProviderLabel(researchProvider, intelligenceProfile) ? (
                  <span className="rounded-md border border-border/60 bg-card/60 px-2 py-1 text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
                    {researchProviderLabel(researchProvider, intelligenceProfile)}
                  </span>
                ) : null}
              </div>

              {researchSummary ? (
                <div className="mt-3 rounded-lg border border-border/50 bg-background/35 px-3 py-2 text-[12px] leading-relaxed text-muted-foreground">
                  <p>{researchSummary}</p>
                  {researchDiagnostics.length > 0 ? (
                    <p className="mt-1 text-[11px] text-muted-foreground/75">
                      {researchDiagnostics.join(" · ")}
                    </p>
                  ) : null}
                </div>
              ) : null}

              <textarea
                value={ownerContext}
                onChange={(event) => setOwnerContext(event.target.value)}
                placeholder="Концепция, специфика, боли владельца, что важно учитывать..."
                rows={4}
                className="mt-4 input-base min-h-28 resize-y leading-relaxed"
              />

              <div className="mt-3 flex flex-wrap items-center gap-2">
                <button
                  type="button"
                  onClick={researchVenue}
                  disabled={researchingVenue || !name.trim()}
                  className="inline-flex h-10 items-center justify-center gap-2 rounded-lg border border-border/60 bg-background/60 px-4 text-sm text-foreground transition-colors hover:border-brand/40 disabled:opacity-50"
                >
                  {researchingVenue ? (
                    <>
                      <Loader2 className="size-4 animate-spin" /> Изучаю
                      заведение...
                    </>
                  ) : (
                    <>
                      <Search className="size-4" /> Собрать профиль
                    </>
                  )}
                </button>
                <span className="text-[12px] text-muted-foreground">
                  Можно оставить вручную и продолжить.
                </span>
              </div>

              {intelligenceProfile ? (
                <ResearchProfilePreview profile={intelligenceProfile} />
              ) : null}
            </div>
          </div>
        ) : step === 1 ? (
          <div className="flex flex-col gap-5">
            <div>
              <h2 className="text-xl font-medium tracking-[-0.01em]">
                Подключение iiko
              </h2>
              <p className="mt-2 text-[14px] leading-relaxed text-muted-foreground">
                Выберите Cloud API или прямой iiko RMS. Доступы хранятся
                зашифрованно и используются только для BI и операционного контура.
              </p>
            </div>

            <div className="grid grid-cols-2 rounded-lg border border-border/60 bg-background/50 p-1">
              {([
                ["cloud", "Cloud API"],
                ["rms", "RMS server"],
              ] as const).map(([id, label]) => (
                <button
                  key={id}
                  type="button"
                  onClick={() => {
                    setChannel(id);
                    setOrganizations([]);
                    setOrganizationId("");
                    setError(null);
                  }}
                  className={
                    "rounded-md px-3 py-2 text-sm transition-colors " +
                    (channel === id
                      ? "bg-card text-foreground"
                      : "text-muted-foreground hover:text-foreground")
                  }
                >
                  {label}
                </button>
              ))}
            </div>

            {channel === "cloud" ? (
              <Field label="iiko API ключ">
                <input
                  value={apiLogin}
                  onChange={(e) => {
                    setApiLogin(e.target.value);
                    setOrganizations([]);
                    setOrganizationId("");
                  }}
                  placeholder="Скопируйте кнопкой рядом с «API ключ»"
                  className="input-base font-mono text-[13px]"
                />
              </Field>
            ) : (
              <div className="grid gap-4">
                <Field label="RMS host">
                  <input
                    value={rmsHost}
                    onChange={(e) => {
                      setRmsHost(e.target.value);
                      setOrganizations([]);
                      setOrganizationId("");
                    }}
                    placeholder="your-company.iiko.it"
                    className="input-base font-mono text-[13px]"
                  />
                </Field>
                <div className="grid gap-4 sm:grid-cols-2">
                  <Field label="Логин RMS">
                    <input
                      value={rmsLogin}
                      onChange={(e) => {
                        setRmsLogin(e.target.value);
                        setOrganizations([]);
                        setOrganizationId("");
                      }}
                      placeholder="Логин"
                      className="input-base"
                    />
                  </Field>
                  <Field label="Пароль RMS">
                    <input
                      value={rmsPassword}
                      onChange={(e) => {
                        setRmsPassword(e.target.value);
                        setOrganizations([]);
                        setOrganizationId("");
                      }}
                      type="password"
                      placeholder="Пароль"
                      className="input-base"
                    />
                  </Field>
                </div>
              </div>
            )}

            <button
              type="button"
              onClick={checkIiko}
              disabled={
                checkingIiko ||
                pending ||
                (channel === "cloud"
                  ? !apiLogin.trim()
                  : !rmsHost.trim() || !rmsLogin.trim() || !rmsPassword)
              }
              className="inline-flex h-10 items-center justify-center gap-2 rounded-lg border border-border/60 bg-background/60 px-4 text-sm text-foreground transition-colors hover:border-brand/40 disabled:opacity-50"
            >
              {checkingIiko ? (
                <>
                  <Loader2 className="size-4 animate-spin" /> Проверяю iiko…
                </>
              ) : (
                "Проверить iiko"
              )}
            </button>

            {organizations.length > 0 ? (
              <Field label="Организация iiko" required>
                <div className="space-y-2">
                  {organizations.map((org) => (
                    <button
                      key={org.id}
                      type="button"
                      onClick={() => setOrganizationId(org.id)}
                      className={
                        "flex w-full items-center justify-between rounded-lg border px-3.5 py-3 text-left transition-colors " +
                        (organizationId === org.id
                          ? "border-brand/50 bg-brand/10 text-foreground"
                          : "border-border/60 bg-background/50 text-muted-foreground hover:text-foreground")
                      }
                    >
                      <span>
                        <span className="block text-sm font-medium">
                          {org.name || "Без названия"}
                        </span>
                        <span className="mt-1 block font-mono text-[11px] text-muted-foreground">
                          {org.id}
                        </span>
                      </span>
                      {organizationId === org.id ? (
                        <Check className="size-4 text-brand" />
                      ) : null}
                    </button>
                  ))}
                </div>
              </Field>
            ) : (
              <div className="space-y-3 rounded-lg border border-border/50 bg-background/40 p-4 text-[13px] leading-relaxed text-muted-foreground">
                {channel === "cloud" ? (
                  <p>
                    Нужен полный API ключ, который скрыт маской вроде
                    261******69b. Нажмите иконку копирования рядом с ключом в
                    iiko Web и вставьте получившееся значение сюда.
                  </p>
                ) : (
                  <p>
                    RMS проверяется через сервер `/resto/api/auth`, а dashboard
                    читает продажи через `/resto/api/v2/reports/olap`.
                  </p>
                )}
              {demoMode ? (
                <button
                  type="button"
                  onClick={openSandbox}
                    className="inline-flex h-9 items-center justify-center rounded-md border border-border/60 bg-card/70 px-3 text-xs font-medium text-foreground transition-colors hover:border-brand/40"
                  >
                    Открыть тестовый кабинет без iiko
                  </button>
                ) : null}
                {demoMode ? (
                  <p className="text-[12px] text-[color:var(--pro)]">
                    В developer/demo режиме Receptor может проверить ключ iiko,
                    но live-заведение и credentials не сохраняются. Для боевого
                    подключения войдите обычным email/паролем.
                  </p>
                ) : null}
              </div>
            )}
          </div>
        ) : (
          <div className="flex flex-col items-center gap-4 py-6 text-center">
            <div className="flex size-14 items-center justify-center rounded-lg border border-border/60 bg-background/45 text-brand">
              <Rocket className="size-7" />
            </div>
            <h2 className="text-2xl font-medium tracking-[-0.02em]">
              Всё готово
            </h2>
            <p className="max-w-sm text-[14px] leading-relaxed text-muted-foreground">
              {demoMode
                ? "Developer/demo режим не сохраняет live iiko. Войдите обычной учеткой, чтобы создать заведение и открыть BI на реальных данных."
                : "Создадим заведение, сохраним выбранную организацию iiko и откроем BI на живых данных."}
            </p>
            {error ? (
              <p className="text-[13px] text-destructive">{error}</p>
            ) : null}
          </div>
        )}

        {/* Nav */}
        <div className="mt-8 flex items-center justify-between">
          <button
            type="button"
            onClick={() => setStep((s) => Math.max(0, s - 1))}
            disabled={step === 0 || pending}
            className="inline-flex items-center gap-2 rounded-lg px-3 py-2 text-[13px] text-muted-foreground transition-colors hover:text-foreground disabled:opacity-0"
          >
            <ArrowLeft className="size-4" /> Назад
          </button>

          {step < 2 ? (
            <button
              type="button"
              onClick={() => setStep((s) => s + 1)}
              disabled={(step === 0 && !canNext0) || (step === 1 && !canNext1)}
              className="inline-flex items-center gap-2 rounded-lg bg-brand px-5 py-2.5 text-sm font-medium text-primary-foreground transition-colors hover:bg-brand-hover disabled:opacity-40"
            >
              Далее <ArrowRight className="size-4" />
            </button>
          ) : (
            <button
              type="button"
              onClick={finish}
              disabled={pending}
              className="inline-flex items-center gap-2 rounded-lg bg-brand px-5 py-2.5 text-sm font-medium text-primary-foreground transition-colors hover:bg-brand-hover disabled:opacity-60"
            >
              {pending ? (
                <>
                  <Loader2 className="size-4 animate-spin" /> Открываю…
                </>
              ) : (
                <>
                  Открыть дашборд <ArrowRight className="size-4" />
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

function ResearchProfilePreview({
  profile,
}: {
  profile: VenueIntelligenceProfile;
}) {
  return (
    <div className="mt-5 overflow-hidden rounded-xl border border-brand/25 bg-brand/[0.04]">
      <div className="border-b border-border/45 bg-background/35 p-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <div className="flex items-center gap-2 text-brand">
              <Sparkles className="size-4" />
              <p className="text-[11px] uppercase tracking-[0.18em]">
                Receptor понял заведение
              </p>
            </div>
            <h3 className="mt-2 text-lg font-medium tracking-[-0.01em] text-foreground">
              {profile.format}
            </h3>
          </div>
          <span className="rounded-md border border-brand/30 bg-brand/10 px-2.5 py-1 text-[10px] uppercase tracking-[0.14em] text-brand">
            Готово для советника
          </span>
        </div>
        <p className="mt-3 text-[14px] leading-relaxed text-foreground/85">
          {profile.positioning}
        </p>
      </div>

      <div className="grid gap-px bg-border/35 md:grid-cols-2">
        <ProfileList
          icon={<Sparkles className="size-4 text-brand" />}
          title="Сильные стороны"
          items={profile.strengths}
        />
        <ProfileList
          icon={<Users className="size-4 text-[color:var(--bi)]" />}
          title="Кто приходит"
          items={profile.audience}
        />
        <ProfileList
          icon={<TriangleAlert className="size-4 text-amber-400" />}
          title="Риски и боли"
          items={[
            ...profile.guestPains.slice(0, 2),
            ...profile.operatingRisks.slice(0, 2),
          ]}
        />
        <ProfileList
          icon={<Target className="size-4 text-[color:var(--ai)]" />}
          title="Фокус советника"
          items={[
            ...profile.ownerGoals.slice(0, 2),
            ...profile.recommendedFocus.slice(0, 2),
          ]}
        />
      </div>
    </div>
  );
}

function ProfileList({
  icon,
  title,
  items,
}: {
  icon: React.ReactNode;
  title: string;
  items: string[];
}) {
  return (
    <div className="bg-card/65 p-4">
      <div className="mb-2 flex items-center gap-2 text-[12px] font-medium text-foreground">
        {icon}
        {title}
      </div>
      <ul className="space-y-2 text-[12px] leading-relaxed text-muted-foreground">
        {items.slice(0, 4).map((item) => (
          <li key={item} className="flex gap-2">
            <span className="mt-2 size-1 shrink-0 rounded-full bg-brand/70" />
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function Field({
  label,
  required,
  children,
}: {
  label: string;
  required?: boolean;
  children: React.ReactNode;
}) {
  return (
    <label className="flex flex-col gap-2">
      <span className="flex items-center gap-2 text-[13px] font-medium text-foreground">
        {label}
        {required ? <span className="text-brand">*</span> : null}
      </span>
      {children}
    </label>
  );
}
