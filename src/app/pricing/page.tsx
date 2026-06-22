import type { Metadata } from "next";
import {
  ArrowRight,
  BadgeCheck,
  BadgePercent,
  BookOpenCheck,
  BrainCircuit,
  Check,
  CheckCircle2,
  MessageSquareText,
  Plug,
  RadioTower,
  Store,
  UtensilsCrossed,
  UsersRound,
} from "lucide-react";
import { SiteHeader } from "@/components/marketing/site-header";
import { SiteFooter } from "@/components/marketing/site-footer";
import { Badge } from "@/components/ui/badge";
import { LinkButton } from "@/components/ui/link-button";
import {
  listPilotBundleModules,
  RESTAURANT_OS_MODULES,
  type ProductModuleId,
} from "@/lib/product/modules";

export const metadata: Metadata = {
  title: "Тарифы Receptor Restaurant OS — RECEPTOR",
  description:
    "Модульная подписка на операционную систему управления рестораном: Owner Cockpit, Context Engine, Menu OS, Team OS, Guest OS и интеграции.",
};

const TIERS = [
  {
    name: "Starter",
    price: "9 900",
    period: "₽ / месяц",
    blurb: "Один ресторан, утренний контур владельца и базовая память заведения.",
    cta: { label: "Начать со Starter", href: "/auth?plan=starter" },
    modules: ["Owner Cockpit", "Context Engine", "Menu OS starter"],
    features: [
      "1 заведение",
      "Daily Brief и KPI по iiko",
      "Context Engine для Copilot",
      "Базовые инструменты меню",
      "До 50 AI-сообщений в день",
      "CSV-экспорт ключевых отчетов",
    ],
    accent: "muted" as const,
  },
  {
    name: "Pro OS",
    price: "24 900",
    period: "₽ / месяц",
    blurb: "Рабочий слой для владельца, управляющего, кухни и маркетинга.",
    cta: { label: "Выбрать Pro OS", href: "/auth?plan=pro-os" },
    modules: ["Owner Cockpit", "Menu OS", "Team OS", "Integrations"],
    features: [
      "До 5 заведений",
      "Owner Cockpit и недельный отчет",
      "Menu OS: QR, food cost, техкарты",
      "Team OS: роли, доступы, задачи",
      "До 200 AI-сообщений в день",
      "Telegram/web уведомления",
    ],
    accent: "brand" as const,
    badge: "Основной SaaS",
  },
  {
    name: "Group",
    price: "от 59 000",
    period: "₽ / месяц",
    blurb: "Холдинги, несколько брендов, кастомные роли и отдельный контур данных.",
    cta: {
      label: "Обсудить Group",
      href: "mailto:bro@frogface.space?subject=Receptor%20Group",
    },
    modules: ["Multi-venue Cockpit", "Team OS", "Guest OS", "AI policy"],
    features: [
      "Любое число заведений",
      "Сравнение точек и брендов",
      "White-label и внутренний домен",
      "Расширенные роли и права",
      "YandexGPT/GigaChat/Qwen режим по требованию",
      "Выделенная настройка и поддержка",
    ],
    accent: "pro" as const,
  },
] as const;

const COMPARISON_ROWS = [
  { label: "Заведений", values: ["1", "до 5", "индивидуально"] },
  { label: "Context Engine", values: ["базовый", "полный", "по холдингу"] },
  { label: "Owner Cockpit", values: ["1 точка", "точки + недели", "холдинг"] },
  { label: "Menu OS", values: ["starter", "полный", "кастом"] },
  { label: "Team OS", values: ["—", "роли + задачи", "расширенный"] },
  { label: "Guest/Delivery/Marketing OS", values: ["аддоны", "аддоны", "в сборке"] },
  { label: "AI-сообщений / день", values: ["50", "200", "индивидуально"] },
  { label: "AI provider mode", values: ["OpenAI/OpenRouter", "на выбор", "частный контур"] },
  { label: "Поддержка", values: ["чат", "приоритет", "выделенная"] },
] as const;

const FAQ = [
  {
    q: "Это BI, CRM или ChatGPT-обертка?",
    a:
      "Нет. BI и Copilot входят в ядро, но продукт шире: Receptor хранит контекст ресторана, читает операционные данные, раскладывает роли и превращает цифры в действия для команды.",
  },
  {
    q: "Что если iiko-ключа пока нет?",
    a:
      "Можно начать с демо и Context Engine. Когда apiLogin появится, подключаем live-данные, сверяем цифры с iiko и включаем Morning Brief на реальной точке.",
  },
  {
    q: "Можно ли работать без OpenAI?",
    a:
      "Да. Архитектура идет через AI provider adapter: OpenAI/OpenRouter для качества и разработки, YandexGPT/GigaChat/Qwen или частный режим для клиентов с ограничениями по данным.",
  },
  {
    q: "Зачем отдельный paid pilot?",
    a:
      "Пилот нужен, чтобы не продавать абстрактную платформу. За две недели мы подключаем одну точку, собираем контекст, показываем первые управленческие решения и фиксируем конфигурацию подписки.",
  },
  {
    q: "Как здесь появляется iiko Marketplace?",
    a:
      "После первых пилотов: нужны кейсы, понятная поддержка, sandbox, требования к интеграции и партнерская экономика. Marketplace должен усиливать продажи, а не заменять прямой запуск.",
  },
] as const;

const moduleIconMap: Record<ProductModuleId, typeof BrainCircuit> = {
  owner_cockpit: BrainCircuit,
  context_engine: BookOpenCheck,
  menu_os: UtensilsCrossed,
  team_os: UsersRound,
  guest_os: MessageSquareText,
  delivery_os: Store,
  marketing_os: RadioTower,
  integration_pack: Plug,
};

const pilotModules = listPilotBundleModules();

function cardClass(accent: (typeof TIERS)[number]["accent"]): string {
  if (accent === "brand") return "border-brand/55 bg-card";
  if (accent === "pro") return "border-[color:var(--pro)]/45 bg-card/80";
  return "border-border/60 bg-card/60";
}

export default function PricingPage() {
  return (
    <>
      <SiteHeader />
      <main className="flex-1">
        <section className="border-b border-border/40 bg-background">
          <div className="mx-auto max-w-7xl px-6 py-20">
            <div className="max-w-4xl">
              <p className="text-[11px] uppercase tracking-[0.22em] text-brand">
                Тарифы
              </p>
              <h1 className="mt-6 text-balance text-5xl font-medium leading-none sm:text-6xl lg:text-7xl">
                Receptor Restaurant OS.
              </h1>
              <p className="mt-8 max-w-2xl text-[17px] leading-relaxed text-muted-foreground">
                Операционная система управления рестораном: данные из iiko,
                память заведения, Copilot, меню, команда, гости и модули под
                конкретную боль.
              </p>
            </div>

            <div className="mt-10 grid gap-3 md:grid-cols-4">
              {pilotModules.map((module) => {
                const Icon = moduleIconMap[module.id];
                return (
                  <div
                    key={module.id}
                    className="rounded-lg border border-border/60 bg-card/45 p-4"
                  >
                    <Icon className="size-5 text-brand" />
                    <p className="mt-4 text-sm font-medium">{module.title}</p>
                    <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
                      {module.promise}
                    </p>
                  </div>
                );
              })}
            </div>
          </div>
        </section>

        <section className="border-b border-border/40 bg-background">
          <div className="mx-auto max-w-7xl px-6 py-16">
            <div className="grid gap-5 lg:grid-cols-3">
              {TIERS.map((tier) => {
                const isFeatured = tier.accent === "brand";
                const isExternal = tier.cta.href.startsWith("mailto:");

                return (
                  <article
                    key={tier.name}
                    className={`relative flex flex-col rounded-lg border p-7 ${cardClass(tier.accent)}`}
                  >
                    {"badge" in tier && tier.badge ? (
                      <span className="absolute -top-3 left-6 rounded-full border border-brand/60 bg-background px-3 py-1 text-[10px] uppercase tracking-[0.18em] text-brand">
                        {tier.badge}
                      </span>
                    ) : null}

                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <h2 className="text-2xl font-medium">{tier.name}</h2>
                        <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
                          {tier.blurb}
                        </p>
                      </div>
                      {isFeatured ? (
                        <BadgeCheck className="size-5 shrink-0 text-brand" />
                      ) : null}
                    </div>

                    <div className="mt-8">
                      <span
                        className={
                          "numeric text-5xl font-medium leading-none " +
                          (isFeatured ? "text-brand" : "text-foreground")
                        }
                      >
                        {tier.price}
                      </span>
                      <span className="ml-2 text-[12px] uppercase tracking-[0.16em] text-muted-foreground">
                        {tier.period}
                      </span>
                    </div>

                    <div className="mt-6 flex flex-wrap gap-2">
                      {tier.modules.map((module) => (
                        <span
                          key={module}
                          className="rounded-md border border-border/50 bg-background/45 px-2 py-1 text-[11px] text-muted-foreground"
                        >
                          {module}
                        </span>
                      ))}
                    </div>

                    <ul className="mt-7 space-y-3 text-[14px]">
                      {tier.features.map((feature) => (
                        <li key={feature} className="flex items-start gap-3">
                          <Check
                            className={
                              "mt-0.5 size-4 flex-none " +
                              (isFeatured ? "text-brand" : "text-foreground/60")
                            }
                          />
                          <span className="text-foreground/90">{feature}</span>
                        </li>
                      ))}
                    </ul>

                    <LinkButton
                      href={tier.cta.href}
                      size="lg"
                      variant={isFeatured ? "default" : "outline"}
                      external={isExternal}
                      className={
                        "mt-auto h-12 " +
                        (isFeatured
                          ? "bg-brand text-primary-foreground hover:bg-brand-hover"
                          : "")
                      }
                    >
                      {tier.cta.label}
                      <ArrowRight className="ml-1 size-4" />
                    </LinkButton>
                  </article>
                );
              })}
            </div>
          </div>
        </section>

        <section className="border-b border-border/40 bg-background">
          <div className="mx-auto grid max-w-7xl gap-6 px-6 py-16 lg:grid-cols-[0.9fr_1.1fr]">
            <div>
              <p className="text-[11px] uppercase tracking-[0.22em] text-brand">
                Paid pilot
              </p>
              <h2 className="mt-4 text-4xl font-medium leading-tight">
                Вход через две недели реальной операционной пользы.
              </h2>
              <p className="mt-5 text-sm leading-relaxed text-muted-foreground">
                Для первых клиентов не продаем “всю платформу”. Подключаем одну
                точку, собираем контекст, включаем Morning Brief и фиксируем,
                какой модуль нужен следующим.
              </p>
            </div>

            <article className="rounded-lg border border-brand/40 bg-card/75 p-7">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <Badge variant="outline" className="border-brand/35 text-brand">
                    Первые 3 клиента
                  </Badge>
                  <h3 className="mt-4 text-2xl font-medium">
                    Pilot setup + 2 недели запуска
                  </h3>
                </div>
                <BadgePercent className="size-6 text-brand" />
              </div>
              <p className="numeric mt-7 text-5xl font-medium text-brand">
                19 900 ₽
              </p>
              <p className="mt-2 text-[12px] uppercase tracking-[0.16em] text-muted-foreground">
                засчитывается в первый месяц Pro OS
              </p>
              <div className="mt-6 grid gap-3 sm:grid-cols-2">
                {[
                  "iiko live/mock контур",
                  "контекстная анкета заведения",
                  "первый Morning Brief",
                  "план модулей под команду",
                ].map((item) => (
                  <div key={item} className="flex gap-3 text-sm">
                    <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-brand" />
                    <span className="text-muted-foreground">{item}</span>
                  </div>
                ))}
              </div>
              <LinkButton
                href="mailto:bro@frogface.space?subject=Receptor%20pilot"
                size="default"
                external
                className="mt-7 bg-brand text-primary-foreground hover:bg-brand-hover"
              >
                Запустить пилот
                <ArrowRight className="ml-1 size-4" />
              </LinkButton>
            </article>
          </div>
        </section>

        <section className="border-b border-border/40 bg-background">
          <div className="mx-auto max-w-7xl px-6 py-16">
            <div className="max-w-3xl">
              <p className="text-[11px] uppercase tracking-[0.22em] text-brand">
                Модули
              </p>
              <h2 className="mt-4 text-4xl font-medium leading-tight">
                Подписка собирается как операционный конструктор.
              </h2>
              <p className="mt-4 text-sm leading-relaxed text-muted-foreground">
                Ядро одно: данные, контекст, роли и Copilot. Дальше подключаются
                модули, которые реально нужны конкретному ресторану или холдингу.
              </p>
            </div>

            <div className="mt-8 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
              {RESTAURANT_OS_MODULES.map((module) => {
                const Icon = moduleIconMap[module.id];
                return (
                  <article
                    key={module.id}
                    className="rounded-lg border border-border/60 bg-card/45 p-5"
                  >
                    <div className="flex items-center justify-between gap-3">
                      <Icon className="size-5 text-brand" />
                      <Badge variant="outline" className="text-[10px]">
                        {module.phase}
                      </Badge>
                    </div>
                    <h3 className="mt-5 text-base font-medium">{module.title}</h3>
                    <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
                      {module.promise}
                    </p>
                  </article>
                );
              })}
            </div>
          </div>
        </section>

        <section className="border-b border-border/40 bg-background">
          <div className="mx-auto max-w-7xl px-6 py-16">
            <div className="max-w-2xl">
              <p className="text-[11px] uppercase tracking-[0.22em] text-brand">
                Сравнение
              </p>
              <h2 className="mt-4 text-4xl font-medium leading-tight">
                Где заканчивается тариф и начинается индивидуальная сборка.
              </h2>
            </div>
            <p className="mt-4 text-[11px] uppercase tracking-[0.16em] text-muted-foreground sm:hidden">
              листайте таблицу
            </p>
            <div className="mt-5 overflow-x-auto rounded-lg border border-border/60 sm:mt-8">
              <table className="w-full min-w-[680px] text-left text-[14px]">
                <thead>
                  <tr className="border-b border-border/50 bg-card/60 text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
                    <th className="px-6 py-4 font-normal">Возможность</th>
                    <th className="px-4 py-4 font-normal text-center">
                      Starter
                    </th>
                    <th className="px-4 py-4 font-normal text-center text-brand">
                      Pro OS
                    </th>
                    <th className="px-4 py-4 font-normal text-center">Group</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/30">
                  {COMPARISON_ROWS.map((row) => (
                    <tr key={row.label} className="transition-colors hover:bg-card/40">
                      <td className="px-6 py-4 text-foreground">{row.label}</td>
                      {row.values.map((value, index) => (
                        <td
                          key={`${row.label}-${index}`}
                          className={
                            "px-4 py-4 text-center font-mono text-[13px] " +
                            (index === 1
                              ? "text-foreground"
                              : "text-muted-foreground")
                          }
                        >
                          {value}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>

        <section className="border-b border-border/40 bg-background">
          <div className="mx-auto max-w-3xl px-6 py-16">
            <p className="text-[11px] uppercase tracking-[0.22em] text-brand">
              Вопросы
            </p>
            <h2 className="mt-4 text-4xl font-medium leading-tight">
              Что важно решить до оплаты.
            </h2>

            <div className="mt-8 space-y-3">
              {FAQ.map((item) => (
                <details
                  key={item.q}
                  className="group rounded-lg border border-border/60 bg-card/60 px-6 py-5 transition-colors hover:bg-card/95"
                >
                  <summary className="flex cursor-pointer items-center justify-between gap-4 text-[15px] font-medium text-foreground marker:hidden [&::-webkit-details-marker]:hidden">
                    <span>{item.q}</span>
                    <span className="font-mono text-xs text-muted-foreground transition-transform group-open:rotate-45">
                      +
                    </span>
                  </summary>
                  <p className="mt-3 text-[14px] leading-relaxed text-muted-foreground">
                    {item.a}
                  </p>
                </details>
              ))}
            </div>
          </div>
        </section>

        <section className="bg-background">
          <div className="mx-auto max-w-4xl px-6 py-20 text-center">
            <h2 className="text-balance text-4xl font-medium leading-tight sm:text-5xl">
              Начинать надо с одного заведения и одного утреннего решения.
            </h2>
            <p className="mx-auto mt-6 max-w-2xl text-[16px] leading-relaxed text-muted-foreground">
              Подключаем данные, собираем контекст, показываем действие на
              сегодня. После этого выбираем подписку и модули без лишней
              архитектурной фантазии.
            </p>
            <div className="mt-9 flex flex-wrap items-center justify-center gap-4">
              <LinkButton
                href="mailto:bro@frogface.space?subject=Receptor%20pilot"
                size="lg"
                external
                className="h-12 bg-brand px-6 text-base text-primary-foreground hover:bg-brand-hover"
              >
                Обсудить пилот
                <ArrowRight className="ml-1 size-4" />
              </LinkButton>
              <LinkButton
                href="/pilot"
                size="lg"
                variant="outline"
                className="h-12 px-6 text-base"
              >
                Открыть план запуска
              </LinkButton>
            </div>
          </div>
        </section>
      </main>
      <SiteFooter />
    </>
  );
}
