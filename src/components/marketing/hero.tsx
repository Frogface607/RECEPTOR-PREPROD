import { ArrowRight } from "lucide-react";
import { LinkButton } from "@/components/ui/link-button";

export function Hero() {
  return (
    <section className="relative overflow-hidden border-b border-border/40">
      {/* Quiet graphite backdrop with a restrained grid. */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 -z-10 opacity-90"
      >
        <div
          className="absolute inset-0"
          style={{
            backgroundImage:
              "linear-gradient(to right, rgba(255,255,255,0.032) 1px, transparent 1px), linear-gradient(to bottom, rgba(255,255,255,0.032) 1px, transparent 1px)",
            backgroundSize: "72px 72px",
            maskImage:
              "linear-gradient(to bottom, black 0%, black 45%, transparent 88%)",
            WebkitMaskImage:
              "linear-gradient(to bottom, black 0%, black 45%, transparent 88%)",
          }}
        />
      </div>

      <div className="mx-auto grid max-w-7xl gap-16 px-6 pb-28 pt-20 lg:grid-cols-12 lg:gap-12 lg:pb-36 lg:pt-28">
        <div className="lg:col-span-7">
          <div className="inline-flex items-center border-l border-brand/50 pl-3 text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
            AI operating system для ресторана
          </div>

          <h1 className="mt-8 text-balance text-[clamp(3rem,7vw,6rem)] font-medium leading-[0.96] tracking-[-0.035em]">
            Управляет
            <br />
            <span className="text-foreground/70">рестораном.</span>
          </h1>

          <p className="mt-8 max-w-xl text-balance text-[17px] leading-[1.55] text-muted-foreground">
            Receptor подключается к iiko и собирает BI, Copilot, техкарты,
            меню, команду и ежедневные решения в одну рабочую систему.{" "}
            <span className="text-foreground/85">
              Не ещё один отчёт, а операционный контур владельца.
            </span>
          </p>

          <div className="mt-10 flex flex-wrap items-center gap-4">
            <LinkButton
              href="/auth"
              size="lg"
              className="press h-12 bg-brand px-6 text-base text-primary-foreground shadow-none transition-colors hover:bg-brand-hover"
            >
              Начать бесплатно
              <ArrowRight className="ml-1 size-4" />
            </LinkButton>
            <LinkButton
              href="/dashboard/dev-venue"
              size="lg"
              variant="ghost"
              className="press h-12 px-6 text-base text-foreground/80 hover:bg-transparent hover:text-foreground"
            >
              Открыть кабинет
              <ArrowRight className="ml-1 size-4 opacity-60" />
            </LinkButton>
          </div>

          <div className="mt-12 flex flex-wrap items-center gap-x-5 gap-y-2 text-[12px] uppercase tracking-[0.14em] text-muted-foreground">
            <span>iiko Cloud</span>
            <span>RMS Server</span>
            <span>BI</span>
            <span>Copilot</span>
            <span>Tech Cards</span>
          </div>
        </div>

        {/* Right column — compact working-room snapshot. */}
        <div className="lg:col-span-5">
          <div className="relative">
            <div className="rounded-xl border border-border/60 bg-card/80 p-6 backdrop-blur-xl shadow-2xl shadow-black/30">
              <div className="flex items-center justify-between border-b border-border/50 pb-4">
                <div className="flex items-center gap-2">
                  <div className="size-2 rounded-full bg-brand" />
                  <span className="text-xs uppercase tracking-[0.18em] text-muted-foreground">
                    Рабочий кабинет · сегодня
                  </span>
                </div>
                <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                  receptor.ai
                </span>
              </div>

              <div className="mt-5 space-y-5">
                <div>
                  <p className="text-xs uppercase tracking-widest text-muted-foreground">
                    Серёжа
                  </p>
                  <p className="mt-1 text-[15px] leading-snug">
                    Какие топ-5 блюд за неделю?
                  </p>
                </div>

                <div>
                  <p className="text-xs uppercase tracking-widest text-brand">
                    Receptor
                  </p>
                  <p className="mt-1 text-[15px] leading-snug text-foreground/90">
                    За последние 7 дней:
                  </p>
                  <ol className="mt-2 space-y-1.5 text-[14px] text-foreground/85">
                    <li className="flex items-baseline gap-2">
                      <span className="font-mono text-[11px] text-muted-foreground">
                        01
                      </span>
                      <span className="flex-1">Бургер Нечто</span>
                      <span className="numeric font-mono text-foreground">
                        ₽328&nbsp;500
                      </span>
                    </li>
                    <li className="flex items-baseline gap-2">
                      <span className="font-mono text-[11px] text-muted-foreground">
                        02
                      </span>
                      <span className="flex-1">Крафт IPA 0.5л</span>
                      <span className="numeric font-mono text-foreground">
                        ₽142&nbsp;100
                      </span>
                    </li>
                    <li className="flex items-baseline gap-2">
                      <span className="font-mono text-[11px] text-muted-foreground">
                        03
                      </span>
                      <span className="flex-1">Signature Sour</span>
                      <span className="numeric font-mono text-foreground">
                        ₽98&nbsp;400
                      </span>
                    </li>
                    <li className="flex items-baseline gap-2">
                      <span className="font-mono text-[11px] text-muted-foreground">
                        04
                      </span>
                      <span className="flex-1">Бургер Двойной Нечто</span>
                      <span className="numeric font-mono text-foreground">
                        ₽89&nbsp;300
                      </span>
                    </li>
                    <li className="flex items-baseline gap-2">
                      <span className="font-mono text-[11px] text-muted-foreground">
                        05
                      </span>
                      <span className="flex-1">Old Fashioned</span>
                      <span className="numeric font-mono text-foreground">
                        ₽76&nbsp;700
                      </span>
                    </li>
                  </ol>
                  <p className="mt-3 text-[13px] leading-snug text-muted-foreground">
                    Бургеры дают&nbsp;35% выручки. Хочешь увидеть,&nbsp;что
                    тянет вниз?
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
