import { ArrowRight } from "lucide-react";
import { LinkButton } from "@/components/ui/link-button";

export function Hero() {
  return (
    <section className="relative overflow-hidden border-b border-border/40">
      {/* Atmospheric backdrop: focused emerald glow + faint grid. */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 -z-10 opacity-90"
      >
        <div className="absolute left-1/2 top-[-30%] h-[700px] w-[700px] -translate-x-1/2 rounded-full bg-brand/15 blur-[140px]" />
        <div
          className="absolute inset-0"
          style={{
            backgroundImage:
              "linear-gradient(to right, rgba(255,255,255,0.04) 1px, transparent 1px), linear-gradient(to bottom, rgba(255,255,255,0.04) 1px, transparent 1px)",
            backgroundSize: "64px 64px",
            maskImage:
              "radial-gradient(ellipse at 50% 30%, black 40%, transparent 75%)",
            WebkitMaskImage:
              "radial-gradient(ellipse at 50% 30%, black 40%, transparent 75%)",
          }}
        />
      </div>

      <div className="mx-auto grid max-w-7xl gap-16 px-6 pb-28 pt-20 lg:grid-cols-12 lg:gap-12 lg:pb-36 lg:pt-28">
        <div className="lg:col-span-7">
          <div className="inline-flex items-center gap-2 rounded-full border border-border/60 bg-card/60 px-3 py-1 text-[11px] uppercase tracking-[0.18em] text-muted-foreground backdrop-blur">
            <span className="size-1.5 rounded-full bg-brand animate-pulse" />
            AI-копайлот владельца ресторана
          </div>

          <h1 className="mt-8 text-balance text-[clamp(3rem,7vw,6.25rem)] font-medium leading-[0.95] tracking-[-0.03em]">
            Чувствует
            <br />
            <span className="font-display italic text-brand glow-brand-soft">
              кухню.
            </span>
          </h1>

          <p className="mt-8 max-w-xl text-balance text-[17px] leading-[1.55] text-muted-foreground">
            Receptor подключается к iiko и превращает выручку, чеки и сменные
            продажи в один экран и живой чат с цифрами вечера.{" "}
            <span className="text-foreground/85">
              Без 18 окон бэк-офиса и Excel.
            </span>
          </p>

          <div className="mt-10 flex flex-wrap items-center gap-4">
            <LinkButton
              href="/auth"
              size="lg"
              className="press h-12 bg-brand px-6 text-base text-primary-foreground shadow-[0_8px_40px_-12px_var(--brand)] transition-shadow hover:bg-brand-hover hover:shadow-[0_10px_48px_-10px_var(--brand)]"
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
              Смотреть sandbox
              <ArrowRight className="ml-1 size-4 opacity-60" />
            </LinkButton>
          </div>

          <div className="mt-12 flex flex-wrap items-center gap-x-7 gap-y-2 text-[12px] uppercase tracking-[0.16em] text-muted-foreground">
            <span>iiko Cloud</span>
            <span className="text-border">/</span>
            <span>iiko RMS Server</span>
            <span className="text-border">/</span>
            <span>OLAP-аналитика</span>
            <span className="text-border">/</span>
            <span>Claude tool-calling</span>
          </div>
        </div>

        {/* Right column — editorial "chat snippet" mock. */}
        <div className="lg:col-span-5">
          <div className="relative">
            <div className="absolute inset-0 -z-10 translate-x-3 translate-y-3 rounded-2xl bg-brand/10 blur-2xl" />
            <div className="rounded-2xl border border-border/60 bg-card/80 p-6 backdrop-blur-xl shadow-2xl shadow-black/40">
              <div className="flex items-center justify-between border-b border-border/50 pb-4">
                <div className="flex items-center gap-2">
                  <div className="size-2 rounded-full bg-brand" />
                  <span className="text-xs uppercase tracking-[0.18em] text-muted-foreground">
                    Demo Restaurant · сегодня
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
