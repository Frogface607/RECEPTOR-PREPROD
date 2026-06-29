import Link from "next/link";
import {
  AlertTriangle,
  CalendarDays,
  CheckCircle2,
  DatabaseZap,
  RadioTower,
  Settings,
  type LucideIcon,
} from "lucide-react";
import type { RevenueDataQuality } from "@/lib/iiko/data-quality";

type DataMode = "live" | "mock";

export function DataSourcePanel({
  chatHref,
  periodLabel,
  dataMode,
  intendedDataMode,
  channel,
  dataError,
  quality,
}: {
  chatHref: string;
  periodLabel: string;
  dataMode: DataMode;
  intendedDataMode: DataMode;
  channel: "cloud" | "rms" | null;
  dataError: string | null;
  quality: RevenueDataQuality;
}) {
  const fallbackToDemo = intendedDataMode === "live" && dataMode === "mock";
  const isLive = dataMode === "live";
  const statusTitle = fallbackToDemo
    ? "iiko подключен, BI временно в тестовом контуре"
    : isLive
      ? "Работаем на реальных данных iiko"
      : "Пока показываем тестовые данные";
  const statusText =
    dataError ??
    (isLive
      ? "Цифры получены из подключенного источника. Проверьте покрытие периода перед управленческим решением."
      : "Кабинет можно изучать и настраивать. После подключения iiko эти же блоки перейдут на реальные цифры.");
  const statusTone = fallbackToDemo
    ? "border-amber-400/35 bg-amber-400/10 text-amber-200"
    : isLive
      ? "border-brand/35 bg-brand/10 text-brand"
      : "border-[color:var(--pro)]/35 bg-[color:var(--pro)]/10 text-[color:var(--pro)]";
  const StatusIcon = fallbackToDemo
    ? AlertTriangle
    : isLive
      ? RadioTower
      : DatabaseZap;
  const sourceLabel = isLive
    ? channel === "rms"
      ? "iiko RMS"
      : "iiko Cloud"
    : "Тестовый контур";
  const settingsActionLabel =
    isLive && !fallbackToDemo ? "Настройки данных" : "Проверить iiko";

  return (
    <section className="rounded-xl border border-border/60 bg-card/55 p-4">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span
              className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-[11px] uppercase tracking-[0.16em] ${statusTone}`}
            >
              <StatusIcon className="size-3.5" />
              {isLive ? "реальные данные" : fallbackToDemo ? "резерв" : "тест"}
            </span>
            <span className="text-[12px] text-muted-foreground">
              {sourceLabel} · {periodLabel}
            </span>
          </div>

          <h2 className="mt-3 text-lg font-medium text-foreground">
            {statusTitle}
          </h2>
          <p className="mt-2 max-w-3xl text-[13px] leading-relaxed text-muted-foreground">
            {statusText}
          </p>
        </div>

        <div className="grid gap-2 sm:grid-cols-2 xl:min-w-[520px] xl:grid-cols-4">
          <SourceMetric
            icon={DatabaseZap}
            label="Источник"
            value={sourceLabel}
          />
          <SourceMetric
            icon={CalendarDays}
            label="Период"
            value={periodLabel}
          />
          <SourceMetric
            icon={CheckCircle2}
            label="Покрытие"
            value={`${quality.coveragePct}%`}
          />
          <SourceMetric
            label="Дней с продажами"
            value={`${quality.activeDays}/${quality.requestedDays}`}
          />
        </div>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        <Link
          href="/settings#iiko"
          className="inline-flex h-9 items-center gap-2 rounded-lg border border-border/60 bg-background/45 px-3 text-sm text-foreground transition-colors hover:bg-card"
        >
          <Settings className="size-4 text-muted-foreground" />
          {settingsActionLabel}
        </Link>
        <Link
          href={chatHref}
          scroll={false}
          className="inline-flex h-9 items-center rounded-lg bg-brand px-3 text-sm font-medium text-primary-foreground transition-colors hover:bg-brand-hover"
        >
          Спросить советника
        </Link>
      </div>
    </section>
  );
}

function SourceMetric({
  icon: Icon,
  label,
  value,
}: {
  icon?: LucideIcon;
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-lg border border-border/45 bg-background/35 p-3">
      <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
        {Icon ? <Icon className="size-3.5" /> : null}
        {label}
      </div>
      <p className="mt-2 truncate text-sm font-medium text-foreground">
        {value}
      </p>
    </div>
  );
}
