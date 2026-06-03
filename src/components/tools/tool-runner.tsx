"use client";

import { useState, type FormEvent } from "react";
import { Play, Loader2, Copy, Check, RotateCcw } from "lucide-react";
import { Markdown } from "./markdown";
import type { ToolField } from "@/lib/tools/catalog";

/**
 * Serializable subset of a Tool that a Client Component can receive.
 * `buildPrompt` (a function) stays server-side — the API route looks the
 * tool up by id from the catalog when running it.
 */
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

export function ToolRunner({ tool }: { tool: RunnableTool }) {
  const initialValues = Object.fromEntries(
    tool.fields.map((f) => [f.id, ""]),
  ) as Record<string, string>;

  const [values, setValues] = useState<Record<string, string>>(initialValues);
  const [run, setRun] = useState<RunState>({ status: "idle" });
  const [copied, setCopied] = useState(false);

  const missingRequired = tool.fields
    .filter((f) => f.required && !values[f.id].trim())
    .map((f) => f.id);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (missingRequired.length > 0 || run.status === "running") return;

    setRun({ status: "running" });
    try {
      const res = await fetch("/api/tools/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ toolId: tool.id, values }),
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
        backend: data.backend ?? "mock",
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
    <div className="grid gap-8 lg:grid-cols-2">
      {/* Form */}
      <form onSubmit={onSubmit} className="flex flex-col gap-5">
        {tool.fields.map((field) => (
          <div key={field.id} className="flex flex-col gap-2">
            <label
              htmlFor={field.id}
              className="flex items-center gap-2 text-[13px] font-medium text-foreground"
            >
              {field.label}
              {field.required ? (
                <span className="text-brand">*</span>
              ) : (
                <span className="text-[10px] uppercase tracking-widest text-muted-foreground">
                  необязательно
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
                rows={5}
                className="resize-y rounded-lg border border-border/60 bg-card/60 px-3.5 py-2.5 text-sm text-foreground placeholder:text-muted-foreground/60 focus:border-brand/50 focus:outline-none"
              />
            ) : (
              <input
                id={field.id}
                value={values[field.id]}
                onChange={(e) =>
                  setValues((v) => ({ ...v, [field.id]: e.target.value }))
                }
                placeholder={field.placeholder}
                className="rounded-lg border border-border/60 bg-card/60 px-3.5 py-2.5 text-sm text-foreground placeholder:text-muted-foreground/60 focus:border-brand/50 focus:outline-none"
              />
            )}
          </div>
        ))}

        <button
          type="submit"
          disabled={missingRequired.length > 0 || run.status === "running"}
          className="mt-1 inline-flex h-11 items-center justify-center gap-2 rounded-lg bg-brand px-5 text-sm font-medium text-primary-foreground transition-colors hover:bg-brand-hover disabled:opacity-40"
        >
          {run.status === "running" ? (
            <>
              <Loader2 className="size-4 animate-spin" />
              Receptor думает…
            </>
          ) : (
            <>
              <Play className="size-4" />
              Запустить
            </>
          )}
        </button>

        {missingRequired.length > 0 ? (
          <p className="text-[12px] text-muted-foreground">
            Заполните обязательные поля, отмеченные{" "}
            <span className="text-brand">*</span>
          </p>
        ) : null}
      </form>

      {/* Result */}
      <div className="rounded-2xl border border-border/60 bg-card/40 p-6 min-h-[320px]">
        {run.status === "idle" ? (
          <ResultPlaceholder />
        ) : run.status === "running" ? (
          <ResultSkeleton />
        ) : run.status === "error" ? (
          <p className="text-sm text-destructive">Ошибка: {run.message}</p>
        ) : (
          <div>
            <div className="mb-5 flex items-center justify-between border-b border-border/40 pb-4">
              <span className="text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
                {run.backend === "claude" ? "Ответ Claude" : "Демо-превью"}
              </span>
              <button
                type="button"
                onClick={copyResult}
                className="inline-flex items-center gap-1.5 rounded-md border border-border/60 px-2.5 py-1 text-[12px] text-muted-foreground transition-colors hover:bg-card hover:text-foreground"
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

function ResultPlaceholder() {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-3 py-16 text-center">
      <span className="flex size-12 items-center justify-center rounded-xl border border-border/50 bg-background/60 text-brand">
        <Play className="size-5" />
      </span>
      <p className="font-display text-xl italic text-muted-foreground">
        Результат появится здесь
      </p>
      <p className="max-w-xs text-[13px] text-muted-foreground/80">
        Заполните поля слева и нажмите «Запустить».
      </p>
    </div>
  );
}

function ResultSkeleton() {
  return (
    <div className="space-y-3">
      {[88, 72, 94, 60, 80, 50].map((w, i) => (
        <div
          key={i}
          className="h-3.5 animate-pulse rounded bg-muted"
          style={{ width: `${w}%` }}
        />
      ))}
    </div>
  );
}
