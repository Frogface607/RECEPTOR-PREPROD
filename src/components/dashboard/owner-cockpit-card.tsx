import {
  AlertTriangle,
  BadgeCheck,
  CheckCircle2,
  DatabaseZap,
  RadioTower,
  TrendingDown,
  TrendingUp,
  type LucideIcon,
} from "lucide-react";
import type { ReactNode } from "react";
import { formatRubles } from "@/lib/format";
import type { DailyBrief, OwnerSignal } from "@/lib/brief/daily-brief";
import type { ResolvedVenue } from "@/lib/venues/get-venue";
import { calculateContextCompletion } from "@/lib/venues/context-questionnaire";

type OwnerCockpitDataMode = "live" | "mock";

export function OwnerCockpitCard({
  venue,
  brief,
  periodLabel,
  dataMode,
}: {
  venue: ResolvedVenue;
  brief: DailyBrief;
  periodLabel: string;
  dataMode: OwnerCockpitDataMode;
}) {
  const isDown = brief.revenue.deltaPct < 0;
  const DeltaIcon = isDown ? TrendingDown : TrendingUp;
  const contextCompletion = calculateContextCompletion(venue.context);
  const prioritySignal = pickPrioritySignal(brief.signals);
  const actions = brief.actions.slice(0, 3);
  const dataModeLabel = dataMode === "live" ? "Live iiko" : "Mock iiko";
  const dataModeDetail =
    dataMode === "live"
      ? "Работает на подключенной организации."
      : "Демо-цифры, готово к замене на live key.";

  return (
    <section className="rounded-xl border border-brand/30 bg-card/70 p-5 sm:p-6">
      <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded-full border border-brand/35 bg-brand/10 px-3 py-1 text-[11px] uppercase tracking-[0.18em] text-brand">
              Owner Cockpit
            </span>
            <span
              className={
                "rounded-full border px-3 py-1 text-[11px] uppercase tracking-[0.18em] " +
                (dataMode === "live"
                  ? "border-brand/35 bg-brand/10 text-brand"
                  : "border-[color:var(--pro)]/35 bg-[color:var(--pro)]/10 text-[color:var(--pro)]")
              }
            >
              {dataModeLabel}
            </span>
          </div>

          <h1 className="mt-5 max-w-3xl text-balance text-3xl font-medium leading-tight tracking-[-0.02em] text-foreground sm:text-4xl">
            {brief.headline}
          </h1>

          <p className="mt-4 max-w-3xl text-[15px] leading-relaxed text-muted-foreground">
            {prioritySignal
              ? prioritySignal.detail
              : "Грубых перекосов не видно. Держим фокус на марже, наличии и дисциплине смен."}
          </p>

          <div className="mt-6 grid gap-3 sm:grid-cols-3">
            <MetricPill
              label={periodLabel}
              value={formatRubles(brief.revenue.current)}
              detail="выручка периода"
            />
            <MetricPill
              label="Сравнение"
              value={`${brief.revenue.deltaPct > 0 ? "+" : ""}${brief.revenue.deltaPct}%`}
              detail={isDown ? "просадка к базе" : "динамика к базе"}
              icon={<DeltaIcon className={isDown ? "size-4 text-destructive" : "size-4 text-brand"} />}
            />
            <MetricPill
              label="Контекст"
              value={`${contextCompletion.requiredPercentage}%`}
              detail="анкета для Copilot"
            />
          </div>
        </div>

        <div className="rounded-lg border border-border/55 bg-background/35 p-4">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
                Что сделать сегодня
              </p>
              <h2 className="mt-2 text-lg font-medium">Три управленческих шага</h2>
            </div>
            <BadgeCheck className="size-5 text-brand" />
          </div>

          <ol className="mt-5 space-y-3">
            {actions.map((action, index) => (
              <li
                key={action}
                className="grid gap-3 rounded-lg border border-border/40 bg-card/45 p-3 sm:grid-cols-[auto_1fr]"
              >
                <span className="flex size-7 items-center justify-center rounded-md border border-brand/35 bg-brand/10 font-mono text-[11px] text-brand">
                  {index + 1}
                </span>
                <div>
                  <p className="text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
                    {roleForAction(index)}
                  </p>
                  <p className="mt-1 text-[13px] leading-relaxed text-foreground/85">
                    {action}
                  </p>
                </div>
              </li>
            ))}
          </ol>

          <div className="mt-5 grid gap-2 sm:grid-cols-2">
            <StatusNote
              icon={dataMode === "live" ? RadioTower : DatabaseZap}
              title={dataModeLabel}
              detail={dataModeDetail}
            />
            <StatusNote
              icon={
                prioritySignal?.level === "risk" ? AlertTriangle : CheckCircle2
              }
              title={prioritySignal?.title ?? "Контур спокойный"}
              detail={prioritySignal?.metric ?? "без красного риска"}
            />
          </div>
        </div>
      </div>
    </section>
  );
}

function pickPrioritySignal(signals: OwnerSignal[]): OwnerSignal | undefined {
  return (
    signals.find((signal) => signal.level === "risk") ??
    signals.find((signal) => signal.level === "watch") ??
    signals[0]
  );
}

function roleForAction(index: number): string {
  if (index === 0) return "владелец / управляющий";
  if (index === 1) return "зал / кухня";
  return "шеф / управляющий";
}

function MetricPill({
  label,
  value,
  detail,
  icon,
}: {
  label: string;
  value: string;
  detail: string;
  icon?: ReactNode;
}) {
  return (
    <div className="rounded-lg border border-border/50 bg-background/35 p-3">
      <p className="text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
        {label}
      </p>
      <div className="mt-2 flex items-center gap-2">
        {icon}
        <p className="numeric text-xl font-medium text-foreground">{value}</p>
      </div>
      <p className="mt-1 text-[12px] text-muted-foreground">{detail}</p>
    </div>
  );
}

function StatusNote({
  icon: Icon,
  title,
  detail,
}: {
  icon: LucideIcon;
  title: string;
  detail: string;
}) {
  return (
    <div className="rounded-lg border border-border/40 bg-background/35 p-3">
      <div className="flex items-start gap-2">
        <Icon className="mt-0.5 size-4 shrink-0 text-brand" />
        <div className="min-w-0">
          <p className="text-[13px] font-medium text-foreground">{title}</p>
          <p className="mt-1 text-[12px] leading-relaxed text-muted-foreground">
            {detail}
          </p>
        </div>
      </div>
    </div>
  );
}
