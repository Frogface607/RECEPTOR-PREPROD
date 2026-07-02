"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { FileSpreadsheet, Search, ArrowUpRight, Route } from "lucide-react";
import { ToolIcon } from "./tool-icon";
import {
  CATEGORIES,
  TOOLS,
  type Tool,
  type ToolCategoryId,
} from "@/lib/tools/catalog";
import {
  TOOL_WORKFLOWS,
  getToolStrategy,
  getWorkflowTools,
} from "@/lib/tools/strategy";

type Filter = "all" | ToolCategoryId;

const CATEGORY_ACCENT: Record<ToolCategoryId, string> = {
  chef: "text-brand",
  waiter: "text-[color:var(--bi)]",
  marketing: "text-[color:var(--ai)]",
  management: "text-[color:var(--ai)]",
  hr: "text-[color:var(--pro)]",
  legal: "text-[color:var(--iiko)]",
};

export function ToolsBrowser() {
  const [filter, setFilter] = useState<Filter>("all");
  const [query, setQuery] = useState("");

  const visible = useMemo(() => {
    const q = query.trim().toLowerCase();
    return TOOLS.filter((t) => {
      if (filter !== "all" && t.category !== filter) return false;
      if (!q) return true;
      return (
        t.name.toLowerCase().includes(q) ||
        t.description.toLowerCase().includes(q)
      );
    });
  }, [filter, query]);

  const grouped = useMemo(() => {
    const map = new Map<ToolCategoryId, Tool[]>();
    for (const t of visible) {
      const arr = map.get(t.category) ?? [];
      arr.push(t);
      map.set(t.category, arr);
    }
    return map;
  }, [visible]);

  const showWorkflowView = filter === "all" && query.trim().length === 0;

  return (
    <div>
      {/* Controls */}
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="relative w-full lg:max-w-sm">
          <Search className="pointer-events-none absolute left-3.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Поиск сценария..."
            className="w-full rounded-lg border border-border/60 bg-card/60 py-2.5 pl-10 pr-3 text-sm text-foreground placeholder:text-muted-foreground/70 focus:border-brand/50 focus:outline-none"
          />
        </div>

        <div className="flex flex-wrap gap-2">
          <FilterChip active={filter === "all"} onClick={() => setFilter("all")}>
            Все сценарии
          </FilterChip>
          {CATEGORIES.map((c) => (
            <FilterChip
              key={c.id}
              active={filter === c.id}
              onClick={() => setFilter(c.id)}
            >
              {c.name}
            </FilterChip>
          ))}
        </div>
      </div>

      {/* Grid */}
      <div className="mt-10 space-y-12">
        {visible.length === 0 ? (
          <p className="py-16 text-center text-muted-foreground">
            Ничего не нашлось. Попробуйте другой запрос.
          </p>
        ) : showWorkflowView ? (
          <WorkflowView />
        ) : (
          CATEGORIES.filter((c) => grouped.has(c.id)).map((cat) => (
            <section key={cat.id}>
              <div className="mb-5 flex items-center gap-3">
                <span className={CATEGORY_ACCENT[cat.id]}>
                  <ToolIcon name={cat.icon} className="size-4" />
                </span>
                <h2 className="text-[12px] uppercase tracking-[0.2em] text-muted-foreground">
                  {cat.name}
                </h2>
                <span className="font-mono text-[10px] text-muted-foreground/70">
                  {grouped.get(cat.id)!.length}
                </span>
              </div>

              <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
                {grouped.get(cat.id)!.map((tool) => (
                  <ToolCard key={tool.id} tool={tool} accent={CATEGORY_ACCENT[cat.id]} />
                ))}
              </div>
            </section>
          ))
        )}
      </div>
    </div>
  );
}

function WorkflowView() {
  return (
    <div className="space-y-8">
      <div className="rounded-xl border border-brand/25 bg-brand/[0.06] p-5 sm:p-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <div className="flex items-center gap-2 text-brand">
              <Route className="size-4" />
              <p className="text-[11px] uppercase tracking-[0.2em]">
                Операционный маршрут
              </p>
            </div>
            <h2 className="mt-3 max-w-3xl text-2xl font-medium tracking-[-0.02em] text-foreground">
              Профиль заведения, разбор данных, затем техкарта или меню.
            </h2>
            <p className="mt-3 max-w-2xl text-[14px] leading-relaxed text-muted-foreground">
              Сценарии подключаются к профилю заведения и операционным данным.
              Так советник работает не как общий чат, а как управленческий
              помощник конкретного ресторана.
            </p>
            <Link
              href="/tools/tech-card-studio"
              className="mt-5 inline-flex h-10 items-center gap-2 rounded-lg bg-brand px-4 text-[13px] font-medium text-primary-foreground transition hover:bg-brand-hover"
            >
              <FileSpreadsheet className="size-4" />
              Открыть Tech Card Studio
            </Link>
          </div>
          <div className="grid min-w-[260px] grid-cols-3 gap-2 text-center">
            <Metric label="контекст" value="Профиль" />
            <Metric label="данные" value="Разбор" />
            <Metric label="действия" value="Задачи" />
          </div>
        </div>
      </div>

      {TOOL_WORKFLOWS.map((workflow) => {
        const tools = getWorkflowTools(workflow);
        return (
          <section
            key={workflow.id}
            className="rounded-xl border border-border/60 bg-card/30 p-5 sm:p-6"
          >
            <div className="mb-5 flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
              <div>
                <div className="flex items-center gap-3">
                  <h2 className="text-xl font-medium tracking-[-0.02em] text-foreground">
                    {workflow.title}
                  </h2>
                  <span className="font-mono text-[10px] text-muted-foreground/70">
                    {tools.length}
                  </span>
                </div>
                <p className="mt-2 max-w-2xl text-[13px] leading-relaxed text-muted-foreground">
                  {workflow.description}
                </p>
              </div>
              <p className="max-w-sm text-[12px] leading-relaxed text-muted-foreground lg:text-right">
                {workflow.promise}
              </p>
            </div>

            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
              {tools.map((tool) => (
                <ToolCard key={`${workflow.id}-${tool.id}`} tool={tool} />
              ))}
            </div>
          </section>
        );
      })}
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-border/50 bg-background/40 px-3 py-2">
      <p className="text-sm font-medium text-foreground">{value}</p>
      <p className="text-[9px] uppercase tracking-[0.14em] text-muted-foreground">
        {label}
      </p>
    </div>
  );
}

function FilterChip({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={
        "inline-flex min-h-[40px] items-center rounded-full border px-4 py-2 text-[13px] transition-colors " +
        (active
          ? "border-brand/50 bg-brand/10 text-brand"
          : "border-border/60 bg-card/40 text-muted-foreground hover:bg-card hover:text-foreground")
      }
    >
      {children}
    </button>
  );
}

function roleClass(role: ReturnType<typeof getToolStrategy>["role"]) {
  if (role === "core") return "border-brand/40 bg-brand/10 text-brand";
  if (role === "lead") return "border-[color:var(--bi)]/35 bg-[color:var(--bi)]/10 text-[color:var(--bi)]";
  if (role === "caution") return "border-[color:var(--pro)]/35 bg-[color:var(--pro)]/10 text-[color:var(--pro)]";
  if (role === "later") return "border-border/60 bg-background/40 text-muted-foreground";
  return "border-[color:var(--ai)]/35 bg-[color:var(--ai)]/10 text-[color:var(--ai)]";
}

function ToolCard({ tool, accent }: { tool: Tool; accent?: string }) {
  const strategy = getToolStrategy(tool.id);
  return (
    <Link
      href={`/tools/${tool.id}`}
      className="press group flex h-full flex-col rounded-xl border border-border/60 bg-card/50 p-5 transition-all hover:border-brand/40 hover:bg-card/90"
    >
      <div className="flex items-start justify-between">
        <span
          className={
            "flex size-10 items-center justify-center rounded-lg border border-border/50 bg-background/60 " +
            (accent ?? "text-brand")
          }
        >
          <ToolIcon name={tool.icon} className="size-5" />
        </span>
        <div className="flex items-center gap-2">
          <span
            className={
              "rounded-full border px-2 py-0.5 text-[9px] uppercase tracking-[0.14em] " +
              roleClass(strategy.role)
            }
          >
            {strategy.label}
          </span>
          {tool.free ? (
            <span className="rounded-full border border-brand/40 bg-brand/10 px-2 py-0.5 text-[9px] uppercase tracking-[0.14em] text-brand">
              Free
            </span>
          ) : (
            <span className="rounded-full border border-[color:var(--pro)]/35 bg-[color:var(--pro)]/10 px-2 py-0.5 text-[9px] uppercase tracking-[0.14em] text-[color:var(--pro)]">
              Pro
            </span>
          )}
          <ArrowUpRight className="size-4 text-muted-foreground/50 transition-colors group-hover:text-brand" />
        </div>
      </div>

      <h3 className="mt-4 text-[16px] font-medium tracking-[-0.01em] text-foreground">
        {tool.name}
      </h3>
      <p className="mt-2 text-[13px] leading-relaxed text-muted-foreground">
        {tool.description}
      </p>
      <p className="mt-4 border-t border-border/35 pt-3 text-[12px] leading-relaxed text-muted-foreground">
        <span className="text-foreground/80">Результат:</span>{" "}
        {strategy.result}
      </p>
    </Link>
  );
}
