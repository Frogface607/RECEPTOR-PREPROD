"use client";

import { useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  Loader2,
  RefreshCw,
  XCircle,
} from "lucide-react";
import type {
  IikoDiagnosticCheck,
  IikoDiagnosticReport,
  IikoDiagnosticStatus,
} from "@/lib/iiko/diagnostics";

type DiagnosticsResponse = {
  report?: IikoDiagnosticReport;
  error?: string;
};

type Props = {
  venueId: string;
  connected: boolean;
};

const STATUS_STYLES: Record<IikoDiagnosticStatus, string> = {
  ok: "border-brand/30 bg-brand/10 text-brand",
  warn: "border-[color:var(--pro)]/35 bg-[color:var(--pro)]/10 text-[color:var(--pro)]",
  fail: "border-destructive/35 bg-destructive/10 text-destructive",
};

function StatusIcon({ status }: { status: IikoDiagnosticStatus }) {
  if (status === "ok") return <CheckCircle2 className="size-4" />;
  if (status === "warn") return <AlertTriangle className="size-4" />;
  return <XCircle className="size-4" />;
}

function statusLabel(status: IikoDiagnosticStatus): string {
  if (status === "ok") return "готово";
  if (status === "warn") return "внимание";
  return "ошибка";
}

function formatCheckedAt(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";

  return new Intl.DateTimeFormat("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function DiagnosticRow({ check }: { check: IikoDiagnosticCheck }) {
  return (
    <div className="rounded-lg border border-border/45 bg-card/35 p-3">
      <div className="flex items-start gap-3">
        <span
          className={
            "mt-0.5 inline-flex size-7 shrink-0 items-center justify-center rounded-md border " +
            STATUS_STYLES[check.status]
          }
        >
          <StatusIcon status={check.status} />
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-sm font-medium text-foreground">
              {check.title}
            </p>
            <span
              className={
                "rounded-full border px-2 py-0.5 text-[10px] uppercase tracking-[0.12em] " +
                STATUS_STYLES[check.status]
              }
            >
              {statusLabel(check.status)}
            </span>
          </div>
          <p className="mt-1 text-[13px] leading-relaxed text-muted-foreground">
            {check.detail}
          </p>
          {check.action ? (
            <p className="mt-2 text-[13px] leading-relaxed text-foreground/85">
              {check.action}
            </p>
          ) : null}
        </div>
      </div>
    </div>
  );
}

export function IikoDiagnosticsPanel({ venueId, connected }: Props) {
  const [report, setReport] = useState<IikoDiagnosticReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  async function runDiagnostics() {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `/api/iiko/diagnostics?venueId=${encodeURIComponent(venueId)}`,
        {
          method: "GET",
          headers: { Accept: "application/json" },
        },
      );
      const payload = (await response.json()) as DiagnosticsResponse;

      if (!response.ok || !payload.report) {
        throw new Error(payload.error ?? "Не удалось проверить iiko.");
      }

      setReport(payload.report);
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Не удалось проверить iiko.",
      );
    } finally {
      setIsLoading(false);
    }
  }

  const failures =
    report?.checks.filter((check) => check.status === "fail").length ?? 0;
  const warnings =
    report?.checks.filter((check) => check.status === "warn").length ?? 0;
  const tone: IikoDiagnosticStatus = failures > 0
    ? "fail"
    : warnings > 0
      ? "warn"
      : report
        ? "ok"
        : connected
          ? "warn"
          : "warn";

  return (
    <div className="mt-4 rounded-lg border border-border/50 bg-background/45 p-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <h4 className="text-sm font-medium text-foreground">
              Проверка iiko
            </h4>
            <span
              className={
                "rounded-full border px-2 py-1 text-[10px] uppercase tracking-[0.12em] " +
                STATUS_STYLES[tone]
              }
            >
              {report
                ? report.mode === "live"
                  ? report.channel ?? "live"
                  : "демо"
                : connected
                  ? "можно проверить"
                  : "нет ключа"}
            </span>
          </div>
          <p className="mt-1 max-w-2xl text-[13px] leading-relaxed text-muted-foreground">
            {report
              ? report.summary
              : connected
                ? "Проверим ключ, организацию, BI-отчет и продажи блюд."
                : "Сначала подключите ключ. Проверка покажет, почему кабинет работает на демо-данных."}
          </p>
          {report ? (
            <p className="mt-2 text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
              Проверено {formatCheckedAt(report.checkedAt)}
            </p>
          ) : null}
        </div>

        <button
          type="button"
          onClick={runDiagnostics}
          disabled={isLoading}
          className="inline-flex h-9 shrink-0 items-center justify-center gap-2 rounded-lg border border-border/60 bg-card/55 px-3 text-sm text-foreground transition-colors hover:bg-card disabled:cursor-wait disabled:opacity-60"
        >
          {isLoading ? (
            <Loader2 className="size-4 animate-spin" />
          ) : (
            <RefreshCw className="size-4" />
          )}
          {isLoading ? "Проверяем" : "Проверить"}
        </button>
      </div>

      {error ? (
        <div className="mt-4 rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-[13px] text-destructive">
          {error}
        </div>
      ) : null}

      {report ? (
        <div className="mt-4 space-y-2">
          {report.checks.map((check) => (
            <DiagnosticRow key={check.id} check={check} />
          ))}
        </div>
      ) : null}
    </div>
  );
}
