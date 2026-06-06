import { Check, ArrowRight, Sparkles } from "lucide-react";
import { SiteHeader } from "@/components/marketing/site-header";
import { SiteFooter } from "@/components/marketing/site-footer";
import { LinkButton } from "@/components/ui/link-button";

const TIERS = [
  {
    name: "Free",
    price: "0",
    blurb: "Чтобы пощупать продукт и убедиться, что цифры реальные.",
    cta: { label: "Подключить", href: "/auth" },
    features: [
      "1 заведение",
      "7 дней истории",
      "Базовый dashboard (KPI + графики)",
      "10 chat-сообщений в день",
      "CSV-экспорт топ-10 блюд",
    ],
    accent: "muted" as const,
  },
  {
    name: "Pro",
    price: "9 900",
    blurb: "Один заведение или маленькая группа. Полный аналитический контур.",
    cta: { label: "Выбрать Pro", href: "/auth?plan=pro" },
    features: [
      "До 5 заведений",
      "Полная история (без ограничений)",
      "CSV + PDF экспорт",
      "AI Chat — 200 сообщений / день",
      "Алерты по выручке и фудкосту",
      "Сравнение периодов",
      "Приоритетная поддержка в Telegram",
    ],
    accent: "brand" as const,
    badge: "Самый частый выбор",
  },
  {
    name: "Team",
    price: "24 900",
    blurb: "Сети и управляющие компании с несколькими точками.",
    cta: {
      label: "Связаться",
      href: "mailto:bro@frogface.space?subject=Receptor%20Team",
    },
    features: [
      "Безлимит заведений",
      "Multi-user — до 10 аккаунтов",
      "Сравнение точек между собой",
      "White-label (брендирование под вас)",
      "Безлимит AI Chat",
      "API access",
      "Dedicated support — отдельный менеджер",
    ],
    accent: "pro" as const,
  },
] as const;

const COMPARISON_ROWS = [
  { label: "Заведений", values: ["1", "до 5", "∞"] },
  { label: "История данных", values: ["7 дней", "Полная", "Полная"] },
  { label: "AI Chat — сообщений / день", values: ["10", "200", "∞"] },
  { label: "CSV / PDF экспорт", values: ["CSV", "CSV + PDF", "CSV + PDF"] },
  { label: "Алерты по выручке", values: ["—", "✓", "✓"] },
  { label: "Сравнение периодов", values: ["—", "✓", "✓"] },
  { label: "Multi-user", values: ["—", "—", "до 10"] },
  { label: "White-label", values: ["—", "—", "✓"] },
  { label: "API access", values: ["—", "—", "✓"] },
  { label: "Dedicated support", values: ["—", "—", "✓"] },
] as const;

const FAQ = [
  {
    q: "Какие данные iiko вы читаете?",
    a:
      "Read-only OLAP: выручка по дням, чеки, продажи блюд, сменные итоги, " +
      "номенклатура. Никаких изменений в вашем iiko — мы только читаем.",
  },
  {
    q: "Сколько времени занимает подключение?",
    a:
      "Cloud-канал — около 10 минут: вы вставляете apiLogin из личного " +
      "кабинета iiko. RMS-канал чуть дольше (около 30 минут). Опциональная " +
      "одноразовая настройка — мы делаем всё за вас.",
  },
  {
    q: "Что входит в одноразовую настройку за ₽39 000?",
    a:
      "Подключаем к iiko, проверяем выгрузку OLAP, кастомизируем dashboard " +
      "и AI-промпт под вашу специфику, обучаем команду за два онлайн-сеанса.",
  },
  {
    q: "Можно ли вернуть деньги?",
    a:
      "Pro и Team — 14 дней безоговорочного возврата с момента оплаты. " +
      "Одноразовая настройка возвращается, если мы не справились с подключением.",
  },
] as const;

export default function PricingPage() {
  return (
    <>
      <SiteHeader />
      <main className="flex-1">
        {/* Hero */}
        <section className="relative overflow-hidden border-b border-border/40">
          <div
            aria-hidden
            className="pointer-events-none absolute inset-0 -z-10"
          >
            <div className="absolute left-1/2 top-[-30%] h-[600px] w-[800px] -translate-x-1/2 rounded-full bg-brand/12 blur-[140px]" />
          </div>

          <div className="mx-auto max-w-5xl px-6 py-24 text-center">
            <p className="text-[11px] uppercase tracking-[0.22em] text-brand">
              Тарифы
            </p>
            <h1 className="mt-6 text-balance text-[clamp(2.5rem,6vw,5rem)] font-medium leading-[1] tracking-[-0.025em]">
              Платите за{" "}
              <span className="font-display italic text-brand glow-brand-soft">
                ответы.
              </span>
              <br />
              Не за{" "}
              <span className="font-display italic text-muted-foreground">
                интеграции.
              </span>
            </h1>
            <p className="mx-auto mt-8 max-w-xl text-[16px] leading-relaxed text-muted-foreground">
              Один найденный инсайт — забытая позиция, проваленная смена,
              нерентабельная категория — окупает год Pro. Receptor находит
              такие за первую неделю.
            </p>
          </div>
        </section>

        {/* Tier cards */}
        <section className="border-b border-border/40 bg-background">
          <div className="mx-auto max-w-7xl px-6 py-16">
            <div className="grid gap-6 md:grid-cols-3">
              {TIERS.map((t) => {
                const isFeatured = t.accent === "brand";
                return (
                  <article
                    key={t.name}
                    className={
                      "relative flex flex-col rounded-2xl border p-8 transition-all " +
                      (isFeatured
                        ? "border-brand/60 bg-card shadow-[0_0_80px_-30px_var(--brand)]"
                        : "border-border/60 bg-card/60 hover:bg-card/95")
                    }
                  >
                    {"badge" in t && t.badge ? (
                      <span className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full border border-brand/60 bg-background px-3 py-1 text-[10px] uppercase tracking-[0.18em] text-brand">
                        {t.badge}
                      </span>
                    ) : null}

                    <div className="flex items-baseline justify-between">
                      <h3 className="text-[22px] font-medium tracking-tight">
                        {t.name}
                      </h3>
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
                          "numeric font-display text-[56px] leading-none tracking-[-0.02em] " +
                          (isFeatured ? "text-brand" : "text-foreground")
                        }
                      >
                        {t.price}
                      </span>
                      <span className="text-[12px] uppercase tracking-[0.16em] text-muted-foreground">
                        ₽ / месяц
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
                      href={t.cta.href}
                      size="lg"
                      variant={isFeatured ? "default" : "outline"}
                      external={t.cta.href.startsWith("mailto:")}
                      className={
                        "mt-10 h-12 " +
                        (isFeatured
                          ? "bg-brand text-primary-foreground hover:bg-brand-hover"
                          : "")
                      }
                    >
                      {t.cta.label}
                      <ArrowRight className="ml-1 size-4" />
                    </LinkButton>
                  </article>
                );
              })}
            </div>
          </div>
        </section>

        {/* Setup + pilot */}
        <section className="border-b border-border/40 bg-background">
          <div className="mx-auto max-w-7xl px-6 py-16">
            <div className="grid gap-6 lg:grid-cols-2">
              <article className="rounded-2xl border border-border/60 bg-card/60 p-8">
                <p className="text-[11px] uppercase tracking-[0.2em] text-muted-foreground">
                  Опционально
                </p>
                <h3 className="mt-3 text-[24px] font-medium tracking-[-0.01em]">
                  Одноразовая настройка
                </h3>
                <p className="numeric mt-6 font-display text-[42px] tracking-[-0.02em] text-foreground">
                  39 000 ₽
                </p>
                <p className="mt-4 text-[14px] leading-relaxed text-muted-foreground">
                  Мы подключаем к iiko, проверяем OLAP, обучаем команду и
                  кастомизируем UI под бренд. Идёт в комплекте с любым тарифом
                  или как отдельная услуга для разового сетапа.
                </p>
              </article>

              <article className="relative overflow-hidden rounded-2xl border border-brand/40 bg-card/80 p-8">
                <Sparkles className="absolute right-6 top-6 size-5 text-brand" />
                <p className="text-[11px] uppercase tracking-[0.2em] text-brand">
                  Пилоты-первооткрыватели
                </p>
                <h3 className="mt-3 text-[24px] font-medium tracking-[-0.01em]">
                  3 первых клиента
                </h3>
                <p className="numeric mt-6 font-display text-[42px] italic tracking-[-0.02em] text-brand">
                  19 900 ₽
                </p>
                <p className="text-[12px] uppercase tracking-[0.16em] text-muted-foreground">
                  setup + 3 месяца Pro бесплатно
                </p>
                <p className="mt-4 text-[14px] leading-relaxed text-muted-foreground">
                  Дальше — стандартный Pro ₽9 900 / мес. После пилота попадаете
                  на главную страницу как кейс.
                </p>
                <LinkButton
                  href="mailto:bro@frogface.space?subject=Receptor%20pilot"
                  size="default"
                  external
                  className="mt-6 bg-brand text-primary-foreground hover:bg-brand-hover"
                >
                  Стать пилотом
                  <ArrowRight className="ml-1 size-4" />
                </LinkButton>
              </article>
            </div>
          </div>
        </section>

        {/* Comparison */}
        <section className="border-b border-border/40 bg-background">
          <div className="mx-auto max-w-7xl px-6 py-20">
            <div className="max-w-2xl">
              <p className="text-[11px] uppercase tracking-[0.22em] text-brand">
                Что входит
              </p>
              <h2 className="mt-4 text-balance text-[40px] font-medium leading-[1.05] tracking-[-0.02em]">
                Сравнение тарифов
              </h2>
            </div>
            <p className="mt-4 text-[11px] uppercase tracking-[0.16em] text-muted-foreground sm:hidden">
              ← листайте таблицу →
            </p>
            <div className="mt-4 overflow-x-auto rounded-2xl border border-border/60 sm:mt-10">
              <table className="w-full min-w-[560px] text-left text-[14px]">
                <thead>
                  <tr className="border-b border-border/50 bg-card/60 text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
                    <th className="px-6 py-4 font-normal">Возможность</th>
                    <th className="px-4 py-4 font-normal text-center">Free</th>
                    <th className="px-4 py-4 font-normal text-center text-brand">
                      Pro
                    </th>
                    <th className="px-4 py-4 font-normal text-center">Team</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/30">
                  {COMPARISON_ROWS.map((row) => (
                    <tr key={row.label} className="transition-colors hover:bg-card/40">
                      <td className="px-6 py-4 text-foreground">{row.label}</td>
                      {row.values.map((v, i) => (
                        <td
                          key={i}
                          className={
                            "px-4 py-4 text-center font-mono text-[13px] " +
                            (i === 1
                              ? "text-foreground"
                              : "text-muted-foreground")
                          }
                        >
                          {v}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>

        {/* FAQ */}
        <section className="border-b border-border/40 bg-background">
          <div className="mx-auto max-w-3xl px-6 py-20">
            <p className="text-[11px] uppercase tracking-[0.22em] text-brand">
              Вопросы
            </p>
            <h2 className="mt-4 text-balance text-[40px] font-medium leading-[1.05] tracking-[-0.02em]">
              Что обычно{" "}
              <span className="font-display italic text-brand">спрашивают</span>
            </h2>

            <div className="mt-10 space-y-4">
              {FAQ.map((f) => (
                <details
                  key={f.q}
                  className="group rounded-xl border border-border/60 bg-card/60 px-6 py-5 transition-colors hover:bg-card/95"
                >
                  <summary className="flex cursor-pointer items-center justify-between text-[15px] font-medium text-foreground marker:hidden [&::-webkit-details-marker]:hidden">
                    <span>{f.q}</span>
                    <span className="font-mono text-xs text-muted-foreground transition-transform group-open:rotate-45">
                      +
                    </span>
                  </summary>
                  <p className="mt-3 text-[14px] leading-relaxed text-muted-foreground">
                    {f.a}
                  </p>
                </details>
              ))}
            </div>
          </div>
        </section>

        {/* Closing CTA */}
        <section className="bg-background">
          <div className="mx-auto max-w-4xl px-6 py-24 text-center">
            <h2 className="text-balance text-[44px] font-medium leading-[1.05] tracking-[-0.02em]">
              Подключиться можно{" "}
              <span className="font-display italic text-brand">за десять минут.</span>
            </h2>
            <p className="mt-6 text-[16px] text-muted-foreground">
              Начните с Free, потрогайте свои реальные цифры. Перейти на Pro
              можно в один клик.
            </p>
            <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
              <LinkButton
                href="/auth"
                size="lg"
                className="h-12 bg-brand px-6 text-base text-primary-foreground hover:bg-brand-hover"
              >
                Начать бесплатно
                <ArrowRight className="ml-1 size-4" />
              </LinkButton>
              <LinkButton
                href="/dashboard/edison-demo"
                size="lg"
                variant="ghost"
                className="h-12 px-6 text-base"
              >
                Смотреть демо на Edison
              </LinkButton>
            </div>
          </div>
        </section>
      </main>
      <SiteFooter />
    </>
  );
}
