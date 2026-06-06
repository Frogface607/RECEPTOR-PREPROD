import type { Metadata } from "next";
import { SiteHeader } from "@/components/marketing/site-header";
import { SiteFooter } from "@/components/marketing/site-footer";
import { ToolsBrowser } from "@/components/tools/tools-browser";
import { TOOLS, CATEGORIES, getFreeTools } from "@/lib/tools/catalog";

export const metadata: Metadata = {
  title: "Инструменты — RECEPTOR",
  description:
    "27 AI-инструментов для ресторана: рецепты, себестоимость, скрипты официантов, маркетинг, HR, HACCP. Один клик — готовый результат.",
};

export default function ToolsPage() {
  const freeCount = getFreeTools().length;

  return (
    <>
      <SiteHeader />
      <main className="flex-1">
        {/* Hero */}
        <section className="relative overflow-hidden border-b border-border/40">
          <div aria-hidden className="pointer-events-none absolute inset-0 -z-10">
            <div className="absolute left-1/2 top-[-40%] h-[560px] w-[820px] -translate-x-1/2 rounded-full bg-brand/12 blur-[150px]" />
          </div>

          <div className="mx-auto max-w-7xl px-6 py-20 lg:py-24">
            <p className="text-[11px] uppercase tracking-[0.22em] text-brand">
              Инструменты
            </p>
            <h1 className="mt-6 max-w-3xl text-balance text-[clamp(2.5rem,6vw,4.5rem)] font-medium leading-[1.02] tracking-[-0.025em]">
              {TOOLS.length} инструментов.
              <br />
              Один клик —{" "}
              <span className="font-display italic text-brand glow-brand-soft">
                готовый результат.
              </span>
            </h1>
            <p className="mt-7 max-w-xl text-[16px] leading-relaxed text-muted-foreground">
              Рецепты и себестоимость, скрипты официантов, посты и ответы на
              отзывы, вакансии, HACCP и СанПиН. Всё, что обычно делают вручную
              или отдают разным подрядчикам — здесь в одном окне.
            </p>

            <div className="mt-9 flex flex-wrap gap-x-7 gap-y-2 text-[12px] uppercase tracking-[0.16em] text-muted-foreground">
              <span>{CATEGORIES.length} направлений</span>
              <span className="text-border">/</span>
              <span>{freeCount} бесплатных</span>
              <span className="text-border">/</span>
              <span>Русский язык</span>
              <span className="text-border">/</span>
              <span>Без эмодзи-воды</span>
            </div>
          </div>
        </section>

        {/* Browser */}
        <section className="bg-background">
          <div className="mx-auto max-w-7xl px-6 py-14">
            <ToolsBrowser />
          </div>
        </section>
      </main>
      <SiteFooter />
    </>
  );
}
