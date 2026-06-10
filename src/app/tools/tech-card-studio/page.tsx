import type { Metadata } from "next";
import Link from "next/link";
import { ArrowLeft, FileSpreadsheet } from "lucide-react";
import { SiteHeader } from "@/components/marketing/site-header";
import { SiteFooter } from "@/components/marketing/site-footer";
import { TechCardStudio } from "@/components/tools/tech-card-studio";

export const metadata: Metadata = {
  title: "Tech Card Studio — RECEPTOR",
  description:
    "Рабочая студия техкарт: ингредиенты, себестоимость, КБЖУ, фудкост, артикулы iiko и PDF-печать.",
};

export default function TechCardStudioPage() {
  return (
    <>
      <SiteHeader />
      <main className="flex-1">
        <section className="print:hidden border-b border-border/40 bg-background">
          <div className="mx-auto max-w-7xl px-6 py-12 lg:py-16">
            <Link
              href="/tools"
              className="inline-flex items-center gap-2 text-[13px] text-muted-foreground transition-colors hover:text-foreground"
            >
              <ArrowLeft className="size-4" />
              Все инструменты
            </Link>

            <div className="mt-8 flex items-start gap-5">
              <span className="flex size-14 shrink-0 items-center justify-center rounded-xl border border-brand/30 bg-brand/10 text-brand">
                <FileSpreadsheet className="size-7" />
              </span>
              <div>
                <div className="flex flex-wrap items-center gap-3">
                  <span className="text-[11px] uppercase tracking-[0.18em] text-brand">
                    Ядро продукта
                  </span>
                  <span className="rounded-full border border-brand/35 bg-brand/10 px-2 py-0.5 text-[9px] uppercase tracking-[0.14em] text-brand">
                    MVP
                  </span>
                </div>
                <h1 className="mt-2 text-balance text-3xl font-medium tracking-[-0.02em] sm:text-4xl">
                  Tech Card Studio
                </h1>
                <p className="mt-3 max-w-3xl text-[15px] leading-relaxed text-muted-foreground">
                  Первый взрослый сценарий инструментов: не генератор текста, а
                  рабочая техкарта с расчётами, историей версии и печатью в PDF.
                  Следующий слой — автозаполнение через Copilot и iiko-артикулы.
                </p>
              </div>
            </div>
          </div>
        </section>

        <section className="bg-background print:bg-white">
          <div className="mx-auto max-w-7xl px-6 py-12 print:max-w-none print:p-0">
            <TechCardStudio />
          </div>
        </section>
      </main>
      <div className="print:hidden">
        <SiteFooter />
      </div>
    </>
  );
}
