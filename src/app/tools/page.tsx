import type { Metadata } from "next";
import { SiteHeader } from "@/components/marketing/site-header";
import { SiteFooter } from "@/components/marketing/site-footer";
import { ToolsBrowser } from "@/components/tools/tools-browser";

export const metadata: Metadata = {
  title: "Инструменты — RECEPTOR",
  description:
    "Рабочие AI-сценарии для ресторана: техкарты, меню, зал, маркетинг, репутация и ежедневные разборы в одном кабинете.",
};

export default function ToolsPage() {
  return (
    <>
      <SiteHeader />
      <main className="flex-1">
        {/* Hero */}
        <section className="relative overflow-hidden border-b border-border/40">
          <div aria-hidden className="pointer-events-none absolute inset-0 -z-10">
          </div>

          <div className="mx-auto max-w-7xl px-6 py-20 lg:py-24">
            <p className="text-[11px] uppercase tracking-[0.22em] text-brand">
              Рабочие процессы
            </p>
            <h1 className="mt-6 max-w-3xl text-balance text-[clamp(2.5rem,6vw,4.5rem)] font-medium leading-[1.02] tracking-[-0.025em]">
              Ресторанная рабочая станция.
              <br />
              От идеи блюда до решения владельца.
            </h1>
            <p className="mt-7 max-w-xl text-[16px] leading-relaxed text-muted-foreground">
              Техкарты и себестоимость, меню, скрипты зала, отзывы, маркетинг,
              обучение команды и операционные брифинги. Инструменты сгруппированы
              в сценарии, которые потом питаются профилем заведения, iiko и живым
              контекстом смен.
            </p>

            <div className="mt-9 flex flex-wrap gap-x-7 gap-y-2 text-[12px] uppercase tracking-[0.16em] text-muted-foreground">
              <span>Профиль заведения</span>
              <span>Данные и разборы</span>
              <span>Техкарты</span>
              <span>Контекст AI-помощника</span>
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
