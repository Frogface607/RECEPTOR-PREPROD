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
} from "lucide-react";
import {
  createVenueAction,
  probeIikoOrganizationsAction,
  type IikoOrganizationOption,
} from "./actions";

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

  const canNext0 = name.trim().length > 0;
  const canNext1 = demoMode || organizationId.length > 0;

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

  const finish = () => {
    setError(null);
    startTransition(async () => {
      const res = await createVenueAction({
        name,
        type,
        city,
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
          </div>
        ) : step === 1 ? (
          <div className="flex flex-col gap-5">
            <div>
              <h2 className="text-xl font-medium tracking-[-0.01em]">
                Подключение iiko
              </h2>
              <p className="mt-2 text-[14px] leading-relaxed text-muted-foreground">
                Откройте карточку интеграции в iiko Web и вставьте именно
                значение apiLogin. Название строки вроде EdisonCraft и
                secret/key сюда не подходят.
              </p>
            </div>

            <Field label="iiko apiLogin">
              <input
                value={apiLogin}
                onChange={(e) => {
                  setApiLogin(e.target.value);
                  setOrganizations([]);
                  setOrganizationId("");
                }}
                placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
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
              <div className="rounded-lg border border-border/50 bg-background/40 p-4 text-[13px] leading-relaxed text-muted-foreground">
                Нужен apiLogin из карточки Cloud API. Если видите в списке
                только название интеграции, откройте строку и скопируйте
                отдельное значение apiLogin. Для холдингов затем выберите
                конкретную точку, к которой привяжем BI и copilot.
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
                ? "Откроем рабочий кабинет. Реальные цифры подключатся, когда добавите iiko-ключ."
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
