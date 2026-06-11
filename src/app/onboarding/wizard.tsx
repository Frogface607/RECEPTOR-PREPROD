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
} from "lucide-react";
import {
  createVenueAction,
  probeIikoOrganizationsAction,
  type IikoOrganizationOption,
} from "./actions";
import type { VenueIntelligenceProfile } from "@/lib/venues/intelligence";

type VenueType = "restaurant" | "cafe" | "coffee" | "bar" | "chain" | "other";

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

export function OnboardingWizard({ demoMode }: { demoMode: boolean }) {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [pending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);

  const [name, setName] = useState("");
  const [type, setType] = useState<VenueType>("bar");
  const [city, setCity] = useState("");
  const [apiLogin, setApiLogin] = useState("");
  const [organizations, setOrganizations] = useState<IikoOrganizationOption[]>([]);
  const [organizationId, setOrganizationId] = useState("");
  const [checkingIiko, setCheckingIiko] = useState(false);
  const [ownerContext, setOwnerContext] = useState("");
  const [intelligenceProfile, setIntelligenceProfile] =
    useState<VenueIntelligenceProfile | null>(null);
  const [researchingVenue, setResearchingVenue] = useState(false);
  const [researchProvider, setResearchProvider] = useState<string | null>(null);

  const canNext0 = name.trim().length > 0;
  const canNext1 = organizationId.length > 0;

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
        profile?: VenueIntelligenceProfile;
      };
      if (!response.ok || !data.profile) {
        throw new Error(data.error || "Не удалось собрать профиль заведения.");
      }

      setIntelligenceProfile(data.profile);
      setResearchProvider(data.provider ?? "profile");
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
      const res = await probeIikoOrganizationsAction({ apiLogin });
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
        apiLogin,
        organizationId,
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
                placeholder="Иркутск"
                className="input-base"
              />
            </Field>

            <div className="rounded-lg border border-border/50 bg-background/35 p-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="text-[13px] font-medium text-foreground">
                    Профиль заведения для Copilot
                  </p>
                  <p className="mt-1 text-[13px] leading-relaxed text-muted-foreground">
                    Receptor исследует публичный контекст, отзывы и
                    позиционирование, а затем соберёт профиль: концепцию,
                    сильные стороны, риски и правила для Copilot.
                  </p>
                </div>
                {researchProviderLabel(researchProvider, intelligenceProfile) ? (
                  <span className="rounded-md border border-border/60 bg-card/60 px-2 py-1 text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
                    {researchProviderLabel(researchProvider, intelligenceProfile)}
                  </span>
                ) : null}
              </div>

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
                <div className="mt-4 grid gap-3 md:grid-cols-2">
                  <ProfileList
                    icon={<Sparkles className="size-4 text-brand" />}
                    title="Сильные стороны"
                    items={intelligenceProfile.strengths}
                  />
                  <ProfileList
                    icon={<Search className="size-4 text-amber-400" />}
                    title="Что учитывать"
                    items={[
                      ...intelligenceProfile.guestPains.slice(0, 2),
                      ...intelligenceProfile.operatingRisks.slice(0, 1),
                    ]}
                  />
                </div>
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
                Откройте карточку интеграции в iiko Web и вставьте полный API
                ключ из строки «API ключ». Поле «Имя API логина» вроде
                EdisonCraft — это только название интеграции.
              </p>
            </div>

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

            <button
              type="button"
              onClick={checkIiko}
              disabled={!apiLogin.trim() || checkingIiko || pending}
              className="inline-flex h-10 items-center justify-center gap-2 rounded-lg border border-border/60 bg-background/60 px-4 text-sm text-foreground transition-colors hover:border-brand/40 disabled:opacity-50"
            >
              {checkingIiko ? (
                <>
                  <Loader2 className="size-4 animate-spin" /> Проверяю iiko…
                </>
              ) : (
                "Проверить iiko и загрузить точки"
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
                <p>
                  Нужен полный API ключ, который скрыт маской вроде
                  261******69b. Нажмите иконку копирования рядом с ключом в
                  iiko Web и вставьте получившееся значение сюда.
                </p>
                {demoMode ? (
                  <button
                    type="button"
                    onClick={openSandbox}
                    className="inline-flex h-9 items-center justify-center rounded-md border border-border/60 bg-card/70 px-3 text-xs font-medium text-foreground transition-colors hover:border-brand/40"
                  >
                    Открыть тестовый кабинет без iiko
                  </button>
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
                ? "Откроем тестовый кабинет. Реальные цифры появятся после успешной проверки активного iiko Cloud API."
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
    <div className="rounded-lg border border-border/50 bg-card/35 p-3">
      <div className="mb-2 flex items-center gap-2 text-[12px] font-medium text-foreground">
        {icon}
        {title}
      </div>
      <ul className="space-y-1.5 text-[12px] leading-relaxed text-muted-foreground">
        {items.slice(0, 4).map((item) => (
          <li key={item}>• {item}</li>
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
