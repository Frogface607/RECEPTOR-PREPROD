import {
  AlertTriangle,
  ArrowRight,
  Banknote,
  CheckCircle2,
  Clock3,
  Percent,
  SearchCheck,
  Settings2,
  UsersRound,
} from "lucide-react";
import type { ReactNode } from "react";
import { LinkButton } from "@/components/ui/link-button";
import { formatInteger, formatRubles } from "@/lib/format";
import {
  buildLaborInsights,
  type LaborBiSummary,
  type LaborInsightTone,
} from "@/lib/team/labor-bi";

function formatPct(value: number | null): string {
  if (value === null) return "—";
  return `${value.toLocaleString("ru-RU", { maximumFractionDigits: 1 })}%`;
}

function formatHours(value: number): string {
  return `${value.toLocaleString("ru-RU", { maximumFractionDigits: 1 })} ч`;
}

function formatRatio(value: number | null): string {
  return value === null ? "—" : formatRubles(value);
}

export function LaborBiCard({
  labor,
  ratesHref,
}: {
  labor: LaborBiSummary;
  ratesHref?: string;
}) {
  const hasRates = labor.missingRates === 0 && labor.staffShifts > 0;
  const insights = buildLaborInsights(labor);
  const statusCopy = hasRates
    ? {
        label: "ФОТ считается",
        title: "Стоимость смен под контролем",
        detail:
          "Ставки заведены. Можно сравнивать выручку, человеко-часы и нагрузку команды.",
        className: "border-brand/35 bg-brand/10 text-brand",
      }
    : {
        label: "Нужны ставки",
        title: "Смены видны, ФОТ требует ставок",
        detail:
          "Receptor уже видит смены и часы. Добавьте ставки сотрудников или ролей в Team OS, чтобы считать ФОТ к выручке.",
        className: "border-amber-400/35 bg-amber-400/10 text-amber-200",
      };

  const topEmployees = labor.employees.slice(0, 4);

  return (
    <section className="rounded-xl border border-border/60 bg-card/50 p-5 sm:p-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex min-w-0 items-start gap-4">
          <div className="flex size-10 shrink-0 items-center justify-center rounded-lg border border-border/60 bg-background/45 text-brand">
            <UsersRound className="size-5" />
          </div>
          <div className="min-w-0">
            <p className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
              Смены и ФОТ
            </p>
            <h2 className="mt-2 text-xl font-medium leading-tight text-foreground">
              {statusCopy.title}
            </h2>
            <p className="mt-2 max-w-2xl text-[13px] leading-relaxed text-muted-foreground">
              {statusCopy.detail}
            </p>
          </div>
        </div>

        <span
          className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-[11px] uppercase tracking-[0.14em] ${statusCopy.className}`}
        >
          <Percent className="size-3.5" />
          {statusCopy.label}
        </span>
      </div>

      {!hasRates && ratesHref ? (
        <div className="mt-4 flex flex-col gap-3 rounded-lg border border-amber-400/25 bg-amber-400/5 p-3 sm:flex-row sm:items-center sm:justify-between">
          <p className="max-w-2xl text-[13px] leading-relaxed text-amber-100/85">
            Чтобы ФОТ стал точным, откройте Team OS и заполните ставки для
            сотрудников, которых iiko видит в сменах.
          </p>
          <LinkButton
            href={ratesHref}
            variant="outline"
            className="w-full border-amber-400/35 bg-background/45 text-amber-100 hover:border-amber-300 sm:w-auto"
          >
            Заполнить ставки
            <ArrowRight className="size-4" />
          </LinkButton>
        </div>
      ) : null}

      <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <Metric
          icon={<Banknote className="size-4" />}
          label="ФОТ периода"
          value={formatRubles(labor.laborCost)}
          detail={`${formatPct(labor.laborCostPct)} от выручки`}
        />
        <Metric
          icon={<Clock3 className="size-4" />}
          label="Человеко-часы"
          value={formatHours(labor.staffHours)}
          detail={`${formatRatio(labor.revenuePerLaborHour)} / час`}
        />
        <Metric
          icon={<UsersRound className="size-4" />}
          label="Смены команды"
          value={formatInteger(labor.staffShifts)}
          detail={`${labor.averageStaffPerShift.toLocaleString("ru-RU")} человека на смену`}
        />
        <Metric
          icon={<Percent className="size-4" />}
          label="Ставки не заведены"
          value={formatInteger(labor.missingRates)}
          detail={labor.missingRates > 0 ? "мешают посчитать ФОТ" : "данные готовы"}
        />
      </div>

      <div className="mt-5 grid gap-3 lg:grid-cols-3">
        {insights.map((insight) => (
          <InsightCard
            key={`${insight.tone}-${insight.title}`}
            tone={insight.tone}
            title={insight.title}
            detail={insight.detail}
            action={insight.action}
          />
        ))}
      </div>

      {topEmployees.length > 0 ? (
        <div className="mt-5 overflow-x-auto rounded-lg border border-border/45 bg-background/25">
          <table className="w-full text-left text-[13px]">
            <thead>
              <tr className="border-b border-border/40 text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
                <th className="py-3 pl-3 pr-4 font-normal">Сотрудник</th>
                <th className="py-3 pr-4 text-right font-normal">Часы</th>
                <th className="py-3 pr-4 text-right font-normal">Продажи</th>
                <th className="py-3 pr-3 text-right font-normal">ФОТ</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/25">
              {topEmployees.map((employee) => (
                <tr key={employee.memberId ?? employee.name}>
                  <td className="py-3 pl-3 pr-4 text-foreground">
                    {employee.name}
                  </td>
                  <td className="numeric py-3 pr-4 text-right font-mono text-muted-foreground">
                    {formatHours(employee.hours)}
                  </td>
                  <td className="numeric py-3 pr-4 text-right font-mono text-foreground">
                    {formatRubles(employee.sales)}
                  </td>
                  <td className="numeric py-3 pr-3 text-right font-mono text-foreground">
                    {employee.missingRate ? "—" : formatRubles(employee.laborCost)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </section>
  );
}

function InsightIcon({ tone }: { tone: LaborInsightTone }) {
  if (tone === "risk") return <AlertTriangle className="size-4" />;
  if (tone === "watch") return <SearchCheck className="size-4" />;
  if (tone === "setup") return <Settings2 className="size-4" />;
  return <CheckCircle2 className="size-4" />;
}

function insightClass(tone: LaborInsightTone): string {
  if (tone === "risk") return "border-destructive/35 bg-destructive/10 text-destructive";
  if (tone === "watch") return "border-amber-400/35 bg-amber-400/10 text-amber-200";
  if (tone === "setup") return "border-border/60 bg-background/45 text-muted-foreground";
  return "border-brand/35 bg-brand/10 text-brand";
}

function InsightCard({
  tone,
  title,
  detail,
  action,
}: {
  tone: LaborInsightTone;
  title: string;
  detail: string;
  action: string;
}) {
  return (
    <div className="rounded-lg border border-border/45 bg-background/30 p-3">
      <div className="flex items-start gap-3">
        <span
          className={`inline-flex size-8 shrink-0 items-center justify-center rounded-lg border ${insightClass(tone)}`}
        >
          <InsightIcon tone={tone} />
        </span>
        <div className="min-w-0">
          <p className="text-[13px] font-medium leading-snug text-foreground">
            {title}
          </p>
          <p className="mt-1 text-[12px] leading-relaxed text-muted-foreground">
            {detail}
          </p>
          <p className="mt-2 text-[12px] leading-relaxed text-foreground/85">
            {action}
          </p>
        </div>
      </div>
    </div>
  );
}

function Metric({
  icon,
  label,
  value,
  detail,
}: {
  icon: ReactNode;
  label: string;
  value: string;
  detail: string;
}) {
  return (
    <div className="rounded-lg border border-border/45 bg-background/35 p-3">
      <div className="flex items-center justify-between gap-3">
        <p className="text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
          {label}
        </p>
        <span className="text-brand">{icon}</span>
      </div>
      <p className="numeric mt-3 text-xl font-medium text-foreground">{value}</p>
      <p className="mt-1 text-[12px] leading-relaxed text-muted-foreground">
        {detail}
      </p>
    </div>
  );
}
