import type { Metadata } from "next";
import { notFound } from "next/navigation";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { SiteHeader } from "@/components/marketing/site-header";
import { SiteFooter } from "@/components/marketing/site-footer";
import { ToolIcon } from "@/components/tools/tool-icon";
import { ToolRunner } from "@/components/tools/tool-runner";
import { getToolById, getToolsByCategory, CATEGORIES, TOOLS } from "@/lib/tools/catalog";
import { getToolStrategy } from "@/lib/tools/strategy";

export function generateStaticParams() {
  return TOOLS.map((t) => ({ toolId: t.id }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ toolId: string }>;
}): Promise<Metadata> {
  const { toolId } = await params;
  const tool = getToolById(toolId);
  if (!tool) return { title: "Инструмент не найден — RECEPTOR" };
  return {
    title: `${tool.name} — RECEPTOR`,
    description: tool.description,
  };
}

export default async function ToolPage({
  params,
}: {
  params: Promise<{ toolId: string }>;
}) {
  const { toolId } = await params;
  const tool = getToolById(toolId);
  if (!tool) notFound();

  const category = CATEGORIES.find((c) => c.id === tool.category)!;
  const strategy = getToolStrategy(tool.id);
  const related = getToolsByCategory(tool.category)
    .filter((t) => t.id !== tool.id)
    .slice(0, 4);

  return (
    <>
      <SiteHeader />
      <main className="flex-1">
        <section className="border-b border-border/40 bg-background">
          <div className="mx-auto max-w-6xl px-6 py-12 lg:py-16">
            <Link
              href="/tools"
              className="inline-flex items-center gap-2 text-[13px] text-muted-foreground transition-colors hover:text-foreground"
            >
              <ArrowLeft className="size-4" />
              Все инструменты
            </Link>

            <div className="mt-8 flex items-start gap-5">
              <span className="flex size-14 shrink-0 items-center justify-center rounded-xl border border-border/50 bg-card/60 text-brand">
                <ToolIcon name={tool.icon} className="size-7" />
              </span>
              <div>
                <div className="flex flex-wrap items-center gap-3">
                  <span className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
                    {category.name}
                  </span>
                  <span className="rounded-full border border-brand/35 bg-brand/10 px-2 py-0.5 text-[9px] uppercase tracking-[0.14em] text-brand">
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
                </div>
                <h1 className="mt-2 text-balance text-3xl font-medium tracking-[-0.02em] sm:text-4xl">
                  {tool.name}
                </h1>
                <p className="mt-3 max-w-2xl text-[15px] leading-relaxed text-muted-foreground">
                  {tool.description}
                </p>
                <div className="mt-5 grid max-w-3xl gap-3 sm:grid-cols-2">
                  <div className="rounded-lg border border-border/55 bg-card/45 p-4">
                    <p className="text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
                      Результат
                    </p>
                    <p className="mt-2 text-[13px] leading-relaxed text-foreground/85">
                      {strategy.result}
                    </p>
                  </div>
                  <div className="rounded-lg border border-border/55 bg-card/45 p-4">
                    <p className="text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
                      Роль в продукте
                    </p>
                    <p className="mt-2 text-[13px] leading-relaxed text-foreground/85">
                      {strategy.note}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="bg-background">
          <div className="mx-auto max-w-6xl px-6 py-12">
            <ToolRunner
              tool={{ id: tool.id, name: tool.name, fields: tool.fields }}
            />
          </div>
        </section>

        {related.length > 0 ? (
          <section className="border-t border-border/40 bg-background">
            <div className="mx-auto max-w-6xl px-6 py-12">
              <h2 className="text-[12px] uppercase tracking-[0.2em] text-muted-foreground">
                Ещё в категории «{category.name}»
              </h2>
              <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                {related.map((t) => (
                  <Link
                    key={t.id}
                    href={`/tools/${t.id}`}
                    className="group rounded-xl border border-border/60 bg-card/50 p-4 transition-all hover:border-brand/40 hover:bg-card/90"
                  >
                    <span className="flex size-9 items-center justify-center rounded-lg border border-border/50 bg-background/60 text-brand">
                      <ToolIcon name={t.icon} className="size-4" />
                    </span>
                    <h3 className="mt-3 text-[14px] font-medium text-foreground">
                      {t.name}
                    </h3>
                  </Link>
                ))}
              </div>
            </div>
          </section>
        ) : null}
      </main>
      <SiteFooter />
    </>
  );
}
