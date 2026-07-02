import Link from "next/link";

const AREAS = [
  {
    title: "Панель владельца",
    label: "Ядро",
    tagline: "Ежедневный бриф, KPI, риски и действия владельца в одном кабинете.",
    metric: "Ежедневный бриф",
    href: "/pilot#show-route",
  },
  {
    title: "Память заведения",
    label: "Память",
    tagline: "Анкета превращает ресторан в понятный контекст для советника, отчетов и поручений.",
    metric: "Память заведения",
    href: "/pilot#show-route",
  },
  {
    title: "Команда",
    label: "Смена",
    tagline: "Роли, доступы, поручения и коммуникация для управляющих, кухни и зала.",
    metric: "Командный слой",
    href: "/pilot#show-route",
  },
] as const;

export function Cases() {
  return (
    <section className="border-b border-border/40 bg-background">
      <div className="mx-auto max-w-7xl px-6 py-24">
        <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div className="max-w-xl">
            <p className="text-xs uppercase tracking-[0.22em] text-brand">
              03 · Что внутри
            </p>
            <h2 className="mt-4 text-balance text-4xl font-medium leading-[1.05] sm:text-[44px]">
              Платформа собирается из рабочих зон.
            </h2>
          </div>
          <p className="max-w-sm text-[14px] leading-relaxed text-muted-foreground">
            Каждый модуль закрывает конкретный контур управления рестораном.
            Можно начать с ядра и подключать дополнительные зоны по мере роста.
          </p>
        </div>

        <div className="mt-14 grid gap-6 md:grid-cols-3">
          {AREAS.map((area) => (
            <Link key={area.title} href={area.href} className="contents">
              <article className="group flex h-full flex-col rounded-xl border border-border/60 bg-card/55 p-8 transition-all hover:border-border hover:bg-card/90">
                <div className="flex items-center justify-between">
                  <span className="inline-flex items-center gap-1.5 rounded-full border border-brand/35 bg-brand/10 px-2.5 py-0.5 text-[10px] uppercase tracking-[0.18em] text-brand">
                    <span className="size-1 rounded-full bg-current" />
                    {area.label}
                  </span>
                  <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                    Receptor
                  </span>
                </div>
                <h3 className="mt-8 text-balance text-[24px] font-medium leading-[1.1]">
                  {area.title}
                </h3>
                <p className="mt-3 text-[14px] leading-relaxed text-muted-foreground">
                  {area.tagline}
                </p>
                <p className="numeric mt-auto pt-10 text-[22px] font-medium text-foreground">
                  {area.metric}
                </p>
              </article>
            </Link>
          ))}
        </div>
      </div>
    </section>
  );
}
