import Link from "next/link";
import { ArrowRight, Check } from "lucide-react";
import { LinkButton } from "@/components/ui/link-button";

const TIERS = [
  {
    name: "Starter",
    price: "9 900",
    cadence: "руб. / месяц",
    blurb: "Для одного заведения: панель владельца, контекст и базовое меню.",
    features: [
      "1 заведение",
      "Ежедневный бриф",
      "Память заведения",
      "Базовый dashboard",
      "50 AI-сообщений в день",
    ],
    cta: "Подключить",
    href: "/auth",
    accent: "muted" as const,
  },
  {
    name: "Pro OS",
    price: "24 900",
    cadence: "руб. / месяц",
    blurb: "Для владельца и команды: меню, задачи, роли и расширенная панель.",
    features: [
      "До 5 заведений",
      "Панель владельца",
      "Меню",
      "Команда",
      "200 AI-сообщений в день",
      "Приоритетная поддержка",
    ],
    cta: "Выбрать Pro",
    href: "/pricing",
    accent: "brand" as const,
    badge: "Основной тариф",
  },
  {
    name: "Group",
    price: "от 59 000",
    cadence: "руб. / месяц",
    blurb: "Для сетей и управляющих компаний с отдельным контуром данных.",
    features: [
      "Любое число точек",
      "Сравнение заведений",
      "White-label",
      "Расширенные права",
      "AI provider на выбор",
      "Выделенная поддержка",
    ],
    cta: "Связаться",
    href: "mailto:bro@frogface.space?subject=Receptor%20Group",
    accent: "pro" as const,
  },
] as const;

export function PricingTeaser() {
  return (
    <section id="pricing" className="border-b border-border/40 bg-background">
      <div className="mx-auto max-w-7xl px-6 py-24">
        <div className="max-w-2xl">
          <p className="text-xs uppercase tracking-[0.22em] text-brand">
            04 · Цены
          </p>
          <h2 className="mt-4 text-balance text-4xl font-medium leading-[1.05] sm:text-[44px]">
            Тариф окупается первой найденной просадкой.
          </h2>
          <p className="mt-5 max-w-xl text-[16px] leading-relaxed text-muted-foreground">
            Receptor находит дыру в себестоимости, проваленную смену или
            забытую позицию меню. Один такой инсайт может окупить год подписки.
          </p>
        </div>

        <div className="mt-16 grid gap-6 md:grid-cols-3">
          {TIERS.map((t) => {
            const isFeatured = t.accent === "brand";
            return (
              <article
                key={t.name}
                className={
                  "relative flex flex-col rounded-xl border p-8 transition-all " +
                  (isFeatured
                    ? "border-brand/55 bg-card"
                    : "border-border/60 bg-card/60 hover:bg-card/95")
                }
              >
                {"badge" in t && t.badge ? (
                  <span className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full border border-brand/60 bg-background px-3 py-1 text-[10px] uppercase tracking-[0.18em] text-brand">
                    {t.badge}
                  </span>
                ) : null}

                <div className="flex items-baseline justify-between">
                  <h3 className="text-[20px] font-medium">{t.name}</h3>
                  <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                    Тариф
                  </span>
                </div>
                <p className="mt-3 text-[14px] leading-relaxed text-muted-foreground">
                  {t.blurb}
                </p>

                <div className="mt-8 flex items-baseline gap-2">
                  <span
                    className={
                      "numeric text-[54px] font-medium leading-none " +
                      (isFeatured ? "text-brand" : "text-foreground")
                    }
                  >
                    {t.price}
                  </span>
                  <span className="text-[12px] uppercase tracking-[0.16em] text-muted-foreground">
                    {t.cadence}
                  </span>
                </div>

                <ul className="mt-8 space-y-3 text-[14px]">
                  {t.features.map((f) => (
                    <li key={f} className="flex items-start gap-3">
                      <Check
                        className={
                          "mt-0.5 size-4 flex-none " +
                          (isFeatured ? "text-brand" : "text-foreground/60")
                        }
                      />
                      <span className="text-foreground/90">{f}</span>
                    </li>
                  ))}
                </ul>

                <LinkButton
                  href={t.href}
                  size="lg"
                  variant={isFeatured ? "default" : "outline"}
                  external={t.href.startsWith("mailto:")}
                  className={
                    "mt-10 h-12 " +
                    (isFeatured
                      ? "bg-brand text-primary-foreground hover:bg-brand-hover"
                      : "")
                  }
                >
                  {t.cta}
                  <ArrowRight className="ml-1 size-4" />
                </LinkButton>
              </article>
            );
          })}
        </div>

        <p className="mt-10 max-w-3xl text-[14px] leading-relaxed text-muted-foreground">
          <span className="text-foreground/80">Внедрение 39 000 руб.</span>{" "}
          подключает данные, память заведения, первый утренний бриф и набор
          модулей под ресторан.{" "}
          <Link
            href="/pricing"
            className="text-foreground/80 underline-offset-4 hover:underline"
          >
            Подробнее о тарифах →
          </Link>
        </p>
      </div>
    </section>
  );
}
