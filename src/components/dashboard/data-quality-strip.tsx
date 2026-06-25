import {
  AlertTriangle,
  CalendarDays,
  CheckCircle2,
  DatabaseZap,
  Info,
} from "lucide-react";
import type { RevenueDataQuality } from "@/lib/iiko/data-quality";

const STATUS_LABEL: Record<RevenueDataQuality["status"], string> = {
  ok: "данные в порядке",
  watch: "проверь покрытие",
  risk: "данные неполные",
};

const STATUS_TONE: Record<RevenueDataQuality["status"], string> = {
  ok: "border-brand/35 bg-brand/10 text-brand",
  watch: "border-amber-400/35 bg-amber-400/10 text-amber-200",
  risk: "border-destructive/35 bg-destructive/10 text-destructive",
};

export function DataQualityStrip({
  quality,
}: {
  quality: RevenueDataQuality;
}) {
  const StatusIcon =
    quality.status === "ok"
      ? CheckCircle2
      : quality.status === "watch"
        ? Info
        : AlertTriangle;

  return (
    <section className="rounded-xl border border-border/60 bg-card/55 p-4">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span
              className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-[11px] uppercase tracking-[0.16em] ${STATUS_TONE[quality.status]}`}
            >
              <StatusIcon className="size-3.5" />
              {STATUS_LABEL[quality.status]}
            </span>
            <span className="text-[12px] text-muted-foreground">
              {quality.summary}
            </span>
          </div>

          <p className="mt-3 max-w-3xl text-[13px] leading-relaxed text-muted-foreground">
            {quality.basis}. Receptor показывает покрытие периода, чтобы длинные
            отчеты не выглядели точнее, чем позволяет источник.
          </p>

          {quality.warnings.length > 0 ? (
            <ul className="mt-3 space-y-1.5">
              {quality.warnings.slice(0, 2).map((warning) => (
                <li
                  key={warning}
                  className="flex gap-2 text-[13px] leading-relaxed text-foreground/80"
                >
                  <AlertTriangle className="mt-0.5 size-3.5 shrink-0 text-amber-300" />
                  <span>{warning}</span>
                </li>
              ))}
            </ul>
          ) : null}
        </div>

        <div className="grid shrink-0 grid-cols-2 gap-2 sm:grid-cols-4 lg:min-w-[420px]">
          <QualityMetric
            icon={CalendarDays}
            label="Дней"
            value={`${quality.activeDays}/${quality.requestedDays}`}
          />
          <QualityMetric
            icon={DatabaseZap}
            label="Покрытие"
            value={`${quality.coveragePct}%`}
          />
          <QualityMetric
            label="Первый день"
            value={quality.firstDataDate ?? "—"}
          />
          <QualityMetric
            label="Последний день"
            value={quality.lastDataDate ?? "—"}
          />
        </div>
      </div>
    </section>
  );
}

function QualityMetric({
  icon: Icon,
  label,
  value,
}: {
  icon?: typeof CalendarDays;
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-lg border border-border/45 bg-background/35 p-3">
      <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
        {Icon ? <Icon className="size-3.5" /> : null}
        {label}
      </div>
      <p className="numeric mt-2 text-sm font-medium text-foreground">
        {value}
      </p>
    </div>
  );
}
