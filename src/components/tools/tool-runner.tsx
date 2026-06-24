"use client";

import { useState, type FormEvent } from "react";
import {
  Check,
  Clipboard,
  Copy,
  Building2,
  Loader2,
  Play,
  RotateCcw,
  Sparkles,
} from "lucide-react";
import { Markdown } from "./markdown";
import type { ToolField } from "@/lib/tools/catalog";
import {
  DEFAULT_VENUE_INTELLIGENCE,
  type VenueIntelligenceProfile,
} from "@/lib/venues/intelligence";

export type RunnableTool = {
  id: string;
  name: string;
  fields: ToolField[];
};

type RunState =
  | { status: "idle" }
  | { status: "running" }
  | { status: "done"; markdown: string; backend: string }
  | { status: "error"; message: string };

function backendLabel(backend: string): string {
  if (backend === "openai") return "OpenAI";
  if (backend === "claude") return "Claude";
  return "Receptor";
}

function exampleValue(field: ToolField, toolName: string): string {
  const label = field.label.toLowerCase();
  if (field.placeholder) return field.placeholder;
  if (label.includes("заведение")) return "Тестовый ресторан";
  if (label.includes("город")) return "Город";
  if (label.includes("цель")) return "увеличить продажи ужинов в будни";
  if (label.includes("блюдо")) return "стейк из говядины";
  if (label.includes("аудитория")) return "гости 25-40, офисы рядом";
  if (field.multiline) {
    return `${toolName}: нужен аккуратный рабочий результат для ресторана, без воды.`;
  }
  return "рабочий пример";
}

export function ToolRunner({ tool }: { tool: RunnableTool }) {
  const initialValues = Object.fromEntries(
    tool.fields.map((f) => [f.id, ""]),
  ) as Record<string, string>;

  const [values, setValues] = useState<Record<string, string>>(initialValues);
  const [run, setRun] = useState<RunState>({ status: "idle" });
  const [copied, setCopied] = useState(false);
  const [useVenueContext, setUseVenueContext] = useState(true);
  const [venueProfile, setVenueProfile] = useState<VenueIntelligenceProfile>(
    DEFAULT_VENUE_INTELLIGENCE,
  );

  const missingRequired = tool.fields
    .filter((f) => f.required && !values[f.id].trim())
    .map((f) => f.id);
  const filledCount = Object.values(values).filter((v) => v.trim()).length;

  const fillExample = () => {
    setValues(
      Object.fromEntries(
        tool.fields.map((field) => [
          field.id,
          values[field.id]?.trim() || exampleValue(field, tool.name),
        ]),
      ) as Record<string, string>,
    );
  };

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (missingRequired.length > 0 || run.status === "running") return;

    setRun({ status: "running" });
    try {
      const res = await fetch("/api/tools/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          toolId: tool.id,
          values,
          venueProfile: useVenueContext ? venueProfile : undefined,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        setRun({
          status: "error",
          message: data.error ?? `HTTP ${res.status}`,
        });
        return;
      }
      setRun({
        status: "done",
        markdown: data.markdown,
        backend: data.backend ?? "preview",
      });
    } catch (err) {
      setRun({
        status: "error",
        message: err instanceof Error ? err.message : "network error",
      });
    }
  };

  const copyResult = async () => {
    if (run.status !== "done") return;
    await navigator.clipboard.writeText(run.markdown);
    setCopied(true);
    setTimeout(() => setCopied(false), 1600);
  };

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
      <form
        onSubmit={onSubmit}
        className="rounded-xl border border-border/60 bg-card/45 p-5 sm:p-6"
      >
        <div className="flex items-start justify-between gap-4 border-b border-border/40 pb-5">
          <div>
            <p className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
              Input
            </p>
            <h2 className="mt-1 text-lg font-medium tracking-[-0.01em]">
              Рабочие вводные
            </h2>
          </div>
          <button
            type="button"
            onClick={fillExample}
            className="inline-flex h-8 items-center gap-2 rounded-lg border border-border/60 bg-background/50 px-3 text-[12px] text-foreground/80 transition hover:border-brand/50 hover:text-foreground"
          >
            <Clipboard className="size-3.5" />
            Пример
          </button>
        </div>

        <div className="mt-5 flex flex-col gap-4">
          <VenueContextPanel
            enabled={useVenueContext}
            profile={venueProfile}
            onToggle={setUseVenueContext}
            onChange={setVenueProfile}
          />

          {tool.fields.map((field) => (
            <div key={field.id} className="flex flex-col gap-2">
              <label
                htmlFor={field.id}
                className="flex items-center justify-between gap-3 text-[13px] font-medium text-foreground"
              >
                <span>{field.label}</span>
                {field.required ? (
                  <span className="text-[10px] uppercase tracking-widest text-brand">
                    Required
                  </span>
                ) : (
                  <span className="text-[10px] uppercase tracking-widest text-muted-foreground">
                    Optional
                  </span>
                )}
              </label>
              {field.multiline ? (
                <textarea
                  id={field.id}
                  value={values[field.id]}
                  onChange={(e) =>
                    setValues((v) => ({ ...v, [field.id]: e.target.value }))
                  }
                  placeholder={field.placeholder}
                  rows={6}
                  className="min-h-[132px] resize-y rounded-lg border border-border/60 bg-background/55 px-3.5 py-3 text-sm leading-relaxed text-foreground placeholder:text-muted-foreground/55 focus:border-brand/50 focus:outline-none"
                />
              ) : (
                <input
                  id={field.id}
                  value={values[field.id]}
                  onChange={(e) =>
                    setValues((v) => ({ ...v, [field.id]: e.target.value }))
                  }
                  placeholder={field.placeholder}
                  className="h-10 rounded-lg border border-border/60 bg-background/55 px-3.5 text-sm text-foreground placeholder:text-muted-foreground/55 focus:border-brand/50 focus:outline-none"
                />
              )}
            </div>
          ))}
        </div>

        <div className="mt-6 flex flex-col gap-3 border-t border-border/40 pt-5 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-[12px] text-muted-foreground">
            Заполнено: <span className="text-foreground">{filledCount}</span> /{" "}
            {tool.fields.length}
          </p>
          <button
            type="submit"
            disabled={missingRequired.length > 0 || run.status === "running"}
            className="inline-flex h-10 items-center justify-center gap-2 rounded-lg bg-brand px-5 text-sm font-medium text-primary-foreground transition-colors hover:bg-brand-hover disabled:opacity-40"
          >
            {run.status === "running" ? (
              <>
                <Loader2 className="size-4 animate-spin" />
                Генерирую
              </>
            ) : (
              <>
                <Play className="size-4" />
                Запустить
              </>
            )}
          </button>
        </div>

        {missingRequired.length > 0 ? (
          <p className="mt-3 text-[12px] text-muted-foreground">
            Заполните обязательные поля, отмеченные `Required`.
          </p>
        ) : null}
      </form>

      <div className="min-h-[520px] rounded-xl border border-border/60 bg-card/35 p-5 sm:p-6">
        {run.status === "idle" ? (
          <ResultPlaceholder toolName={tool.name} />
        ) : run.status === "running" ? (
          <ResultSkeleton />
        ) : run.status === "error" ? (
          <div className="rounded-lg border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive">
            Ошибка: {run.message}
          </div>
        ) : (
          <div>
            <div className="mb-5 flex flex-wrap items-center justify-between gap-3 border-b border-border/40 pb-4">
              <div className="flex items-center gap-2">
                <span className="flex size-8 items-center justify-center rounded-lg border border-brand/30 bg-brand/10 text-brand">
                  <Sparkles className="size-4" />
                </span>
                <div>
                  <p className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
                    AI Output
                  </p>
                  <p className="text-[13px] text-foreground">
                    {backendLabel(run.backend)}
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={copyResult}
                className="inline-flex h-8 items-center gap-2 rounded-lg border border-border/60 bg-background/40 px-3 text-[12px] text-muted-foreground transition-colors hover:bg-card hover:text-foreground"
              >
                {copied ? (
                  <>
                    <Check className="size-3.5 text-brand" /> Скопировано
                  </>
                ) : (
                  <>
                    <Copy className="size-3.5" /> Копировать
                  </>
                )}
              </button>
            </div>
            <Markdown>{run.markdown}</Markdown>

            <button
              type="button"
              onClick={() => setRun({ status: "idle" })}
              className="mt-6 inline-flex items-center gap-1.5 text-[12px] text-muted-foreground transition-colors hover:text-foreground"
            >
              <RotateCcw className="size-3.5" /> Запустить заново
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

function VenueContextPanel({
  enabled,
  profile,
  onToggle,
  onChange,
}: {
  enabled: boolean;
  profile: VenueIntelligenceProfile;
  onToggle: (enabled: boolean) => void;
  onChange: (profile: VenueIntelligenceProfile) => void;
}) {
  const update = (patch: Partial<VenueIntelligenceProfile>) => {
    onChange({ ...profile, ...patch });
  };

  const updateList = (
    field: "ownerGoals" | "guestPains" | "recommendedFocus",
    value: string,
  ) => {
    update({
      [field]: value
        .split("\n")
        .map((item) => item.trim())
        .filter(Boolean),
    });
  };

  return (
    <section className="rounded-lg border border-brand/25 bg-brand/[0.045] p-4">
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <span className="mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-lg border border-brand/30 bg-brand/10 text-brand">
            <Building2 className="size-4" />
          </span>
          <div>
            <p className="text-[11px] uppercase tracking-[0.18em] text-brand">
              Контекст заведения
            </p>
            <p className="mt-1 text-[13px] leading-relaxed text-muted-foreground">
              Инструмент будет учитывать формат, позиционирование, боли и цели
              ресторана. Это черновой профиль; после onboarding сюда попадёт
              исследованный профиль заведения.
            </p>
          </div>
        </div>

        <label className="inline-flex cursor-pointer items-center gap-2 text-[12px] text-foreground">
          <input
            type="checkbox"
            checked={enabled}
            onChange={(event) => onToggle(event.target.checked)}
            className="size-4 accent-brand"
          />
          Включить
        </label>
      </div>

      {enabled ? (
        <div className="mt-4 grid gap-3">
          <label className="grid gap-1.5">
            <span className="text-[12px] font-medium text-foreground">
              Формат
            </span>
            <input
              value={profile.format}
              onChange={(event) => update({ format: event.target.value })}
              className="h-9 rounded-lg border border-border/60 bg-background/55 px-3 text-[13px] outline-none focus:border-brand/50"
            />
          </label>
          <label className="grid gap-1.5">
            <span className="text-[12px] font-medium text-foreground">
              Позиционирование
            </span>
            <textarea
              value={profile.positioning}
              onChange={(event) => update({ positioning: event.target.value })}
              rows={2}
              className="min-h-[70px] rounded-lg border border-border/60 bg-background/55 px-3 py-2 text-[13px] leading-relaxed outline-none focus:border-brand/50"
            />
          </label>
          <div className="grid gap-3 md:grid-cols-3">
            <ContextList
              label="Цели владельца"
              value={profile.ownerGoals.join("\n")}
              onChange={(value) => updateList("ownerGoals", value)}
            />
            <ContextList
              label="Боли гостей"
              value={profile.guestPains.join("\n")}
              onChange={(value) => updateList("guestPains", value)}
            />
            <ContextList
              label="Фокус Receptor"
              value={profile.recommendedFocus.join("\n")}
              onChange={(value) => updateList("recommendedFocus", value)}
            />
          </div>
        </div>
      ) : null}
    </section>
  );
}

function ContextList({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <label className="grid gap-1.5">
      <span className="text-[12px] font-medium text-foreground">{label}</span>
      <textarea
        value={value}
        onChange={(event) => onChange(event.target.value)}
        rows={4}
        className="min-h-[104px] rounded-lg border border-border/60 bg-background/55 px-3 py-2 text-[12px] leading-relaxed outline-none focus:border-brand/50"
      />
    </label>
  );
}

function ResultPlaceholder({ toolName }: { toolName: string }) {
  return (
    <div className="flex h-full min-h-[460px] flex-col items-center justify-center gap-4 py-16 text-center">
      <span className="flex size-14 items-center justify-center rounded-xl border border-border/50 bg-background/60 text-brand">
        <Sparkles className="size-6" />
      </span>
      <div>
        <p className="text-2xl font-medium tracking-[-0.01em] text-foreground/85">
          {toolName}
        </p>
        <p className="mt-2 max-w-sm text-[13px] leading-relaxed text-muted-foreground">
          Заполните вводные слева или нажмите `Пример`, чтобы быстро показать
          результат на встрече.
        </p>
      </div>
    </div>
  );
}

function ResultSkeleton() {
  return (
    <div>
      <div className="mb-5 flex items-center gap-3 border-b border-border/40 pb-4">
        <div className="size-8 animate-pulse rounded-lg bg-muted" />
        <div className="space-y-2">
          <div className="h-2.5 w-24 animate-pulse rounded bg-muted" />
          <div className="h-3 w-36 animate-pulse rounded bg-muted" />
        </div>
      </div>
      <div className="space-y-3">
        {[88, 72, 94, 60, 80, 50, 68, 42].map((w, i) => (
          <div
            key={i}
            className="h-3.5 animate-pulse rounded bg-muted"
            style={{ width: `${w}%` }}
          />
        ))}
      </div>
    </div>
  );
}
