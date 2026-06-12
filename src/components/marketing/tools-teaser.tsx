import Link from "next/link";
import { ArrowRight, FileSpreadsheet } from "lucide-react";
import { ToolIcon } from "@/components/tools/tool-icon";
import {
  CATEGORIES,
  getToolsByCategory,
  type ToolCategoryId,
} from "@/lib/tools/catalog";

const CATEGORY_ACCENT: Record<ToolCategoryId, string> = {
  chef: "text-brand",
  waiter: "text-[color:var(--bi)]",
  marketing: "text-[color:var(--ai)]",
  management: "text-[color:var(--ai)]",
  hr: "text-[color:var(--pro)]",
  legal: "text-[color:var(--iiko)]",
};

export function ToolsTeaser() {
  return (
    <section className="border-b border-border/40 bg-background">
      <div className="mx-auto max-w-7xl px-6 py-24">
        <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div className="max-w-xl">
            <p className="text-xs uppercase tracking-[0.22em] text-brand">
              Рабочие сценарии
            </p>
            <h2 className="mt-4 text-balance text-4xl font-medium leading-[1.05] tracking-[-0.02em] sm:text-[44px]">
              Операционный слой ресторана.
            </h2>
          </div>
          <p className="max-w-sm text-[14px] leading-relaxed text-muted-foreground">
            Техкарты, себестоимость, меню, скрипты зала, отзывы, HR и HACCP
            становятся частью одной системы, которая знает контекст заведения.
          </p>
        </div>

        <Link
          href="/tools/tech-card-studio"
          className="mt-10 flex flex-col gap-5 rounded-xl border border-brand/30 bg-brand/[0.06] p-7 transition-colors hover:border-brand/45 hover:bg-brand/[0.09] md:flex-row md:items-center md:justify-between"
        >
          <div className="flex items-start gap-4">
            <span className="flex size-11 shrink-0 items-center justify-center rounded-lg border border-brand/35 bg-brand/10 text-brand">
              <FileSpreadsheet className="size-5" />
            </span>
            <div>
              <p className="text-[11px] uppercase tracking-[0.18em] text-brand">
                Новый сценарий
              </p>
              <h3 className="mt-2 text-xl font-medium tracking-[-0.02em] text-foreground">
                Tech Card Studio
              </h3>
              <p className="mt-2 max-w-2xl text-[13px] leading-relaxed text-muted-foreground">
                Техкарта с ингредиентами, себестоимостью, КБЖУ, iiko-артикулами,
                историей и PDF-печатью. Это фундамент будущего меню-модуля.
              </p>
            </div>
          </div>
          <span className="inline-flex items-center gap-2 text-sm font-medium text-brand">
            Открыть студию
            <ArrowRight className="size-4" />
          </span>
        </Link>

        <div className="mt-8 grid gap-px overflow-hidden rounded-xl border border-border/60 bg-border/40 sm:grid-cols-2 lg:grid-cols-3">
          {CATEGORIES.map((cat) => {
            const sample = getToolsByCategory(cat.id)
              .slice(0, 3)
              .map((t) => t.name)
              .join(" · ");
            return (
              <Link
                key={cat.id}
                href="/tools"
                className="group flex flex-col gap-4 bg-card/50 p-7 transition-colors hover:bg-card/90"
              >
                <div className="flex items-center justify-between">
                  <span
                    className={
                      "flex size-10 items-center justify-center rounded-lg border border-border/50 bg-background/60 " +
                      CATEGORY_ACCENT[cat.id]
                    }
                  >
                    <ToolIcon name={cat.icon} className="size-5" />
                  </span>
                  <ArrowRight className="size-4 text-muted-foreground/45 transition-colors group-hover:text-brand" />
                </div>
                <div>
                  <h3 className="text-[18px] font-medium tracking-[-0.01em] text-foreground">
                    {cat.name}
                  </h3>
                  <p className="mt-2 text-[13px] leading-relaxed text-muted-foreground">
                    {sample}
                  </p>
                </div>
              </Link>
            );
          })}
        </div>

        <div className="mt-10">
          <Link
            href="/tools"
            className="inline-flex items-center gap-2 rounded-lg border border-border/60 bg-card/60 px-5 py-3 text-sm font-medium text-foreground transition-colors hover:border-brand/40 hover:bg-card"
          >
            Открыть рабочие сценарии
            <ArrowRight className="size-4 text-brand" />
          </Link>
        </div>
      </div>
    </section>
  );
}
