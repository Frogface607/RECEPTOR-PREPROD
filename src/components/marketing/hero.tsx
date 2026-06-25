import { ArrowRight } from "lucide-react";
import { LinkButton } from "@/components/ui/link-button";

export function Hero() {
  return (
    <section className="relative overflow-hidden border-b border-border/40">
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

          <h1 className="mt-8 text-balance text-[clamp(3rem,7vw,6rem)] font-medium leading-[0.96]">
            Управляет
            <br />
            <span className="text-foreground/70">рестораном.</span>
          </h1>

          <p className="mt-8 max-w-xl text-balance text-[17px] leading-[1.55] text-muted-foreground">
            Receptor подключается к iiko и собирает BI, AI-помощника,
            техкарты, меню, команду и ежедневные решения в одну рабочую
            систему.{" "}
            <span className="text-foreground/85">
              Не еще один отчет, а операционный контур владельца.
            </span>
          </p>

          <div className="mt-10 flex flex-wrap items-center gap-4">
            <LinkButton
              href="/auth?next=/onboarding"
              size="lg"
              className="press h-12 bg-brand px-6 text-base text-primary-foreground shadow-none transition-colors hover:bg-brand-hover"
            >
              Начать бесплатно
              <ArrowRight className="ml-1 size-4" />
            </LinkButton>
            <LinkButton
              href="/platform"
              size="lg"
              variant="ghost"
              className="press h-12 px-6 text-base text-foreground/80 hover:bg-transparent hover:text-foreground"
            >
              Смотреть платформу
              <ArrowRight className="ml-1 size-4 opacity-60" />
            </LinkButton>
          </div>

          <div className="mt-12 flex flex-wrap items-center gap-x-5 gap-y-2 text-[12px] uppercase tracking-[0.14em] text-muted-foreground">
            <span>iiko Cloud</span>
            <span>BI</span>
            <span>AI-помощник</span>
            <span>Tech Cards</span>
            <span>Команда</span>
          </div>
        </div>

        <div className="lg:col-span-5">
          <div className="rounded-xl border border-border/60 bg-card/80 p-6 shadow-2xl shadow-black/30 backdrop-blur-xl">
            <div className="flex items-center justify-between border-b border-border/50 pb-4">
              <div className="flex items-center gap-2">
                <div className="size-2 rounded-full bg-brand" />
                <span className="text-xs uppercase tracking-[0.18em] text-muted-foreground">
                  Операционный контур
                </span>
              </div>
              <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                пример интерфейса
              </span>
            </div>

            <div className="mt-5 space-y-5">
              <div>
                <p className="text-xs uppercase tracking-widest text-muted-foreground">
                  Владелец
                </p>
                <p className="mt-1 text-[15px] leading-snug">
                  Что мне проверить сегодня?
                </p>
              </div>

              <div>
                <p className="text-xs uppercase tracking-widest text-brand">
                  Receptor
                </p>
                <p className="mt-1 text-[15px] leading-snug text-foreground/90">
                  Начать стоит с четырех зон:
                </p>
                <ol className="mt-2 space-y-1.5 text-[14px] text-foreground/85">
                  {[
                    "Продажи против такого же дня недели",
                    "Блюда с оборотом, но слабой маржой",
                    "Смены, где просел средний чек",
                    "Позиции без техкарт и iiko-связки",
                  ].map((item, index) => (
                    <li key={item} className="flex items-baseline gap-2">
                      <span className="font-mono text-[11px] text-muted-foreground">
                        {String(index + 1).padStart(2, "0")}
                      </span>
                      <span className="flex-1">{item}</span>
                    </li>
                  ))}
                </ol>
                <p className="mt-3 text-[13px] leading-snug text-muted-foreground">
                  После подключения данных ответы используют реальные цифры.
                  До этого кабинет можно изучить на примерах.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
