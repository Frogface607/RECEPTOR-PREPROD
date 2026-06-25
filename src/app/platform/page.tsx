import type { Metadata } from "next";
import {
  ArrowRight,
  BadgeCheck,
  BookOpenCheck,
  BrainCircuit,
  ClipboardList,
  MessageSquareText,
  Plug,
  RadioTower,
  Store,
  UtensilsCrossed,
  UsersRound,
} from "lucide-react";
import { SiteFooter } from "@/components/marketing/site-footer";
import { SiteHeader } from "@/components/marketing/site-header";
import { Badge } from "@/components/ui/badge";
import { LinkButton } from "@/components/ui/link-button";
import {
  listFoundationModules,
  RESTAURANT_OS_MODULES,
  type ProductModule,
  type ProductModuleId,
} from "@/lib/product/modules";
import { VENUE_CONTEXT_QUESTIONNAIRE } from "@/lib/venues/context-questionnaire";

export const metadata: Metadata = {
  title: "Receptor — операционная система ресторана",
  description:
    "SaaS-платформа для управления рестораном: данные, контекст, меню, команда, задачи, гости и интеграции.",
};

const operatingFlow = [
  {
    icon: Plug,
    title: "Подключить данные",
    text: "iiko Cloud/RMS, ручной импорт или тестовые данные для быстрого старта кабинета.",
  },
  {
    icon: BookOpenCheck,
    title: "Собрать контекст",
    text: "Формат, цели владельца, команда, ограничения, правила принятия решений и тон AI.",
  },
  {
    icon: ClipboardList,
    title: "Раздать действия",
    text: "Управляющий, кухня, зал и маркетинг получают задачи в одном рабочем пространстве.",
  },
  {
    icon: BadgeCheck,
    title: "Управлять ритмом",
    text: "Ежедневный бриф, отчеты, контроль меню, смены и понятные действия на сегодня.",
  },
];

const cockpitRows = [
  {
    label: "Утро владельца",
    value: "Факты, выводы, действия",
  },
  {
    label: "Команда",
    value: "Роли, смены, задачи",
  },
  {
    label: "Меню",
    value: "QR, стоп-лист, техкарты",
  },
  {
    label: "AI-помощник",
    value: "Ответы с памятью ресторана",
  },
];

const connectionSteps = [
  {
    title: "Создать заведение",
    text: "Название, город, формат и базовая структура ресторана или сети.",
  },
  {
    title: "Заполнить память",
    text: "Анкета и ресерч собирают контекст для AI-помощника, брифов и задач.",
  },
  {
    title: "Подключить источники",
    text: "iiko, меню, команда, гости, доставка и каналы коммуникации.",
  },
  {
    title: "Включить модули",
    text: "Ресторан использует только те инструменты, которые нужны сейчас.",
  },
];

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

const foundationModules = listFoundationModules();

export default function PlatformPage() {
  return (
    <>
      <SiteHeader />
      <main className="flex-1">
        <section className="border-b border-border/40">
          <div className="mx-auto grid max-w-7xl gap-12 px-6 py-16 lg:grid-cols-[1.05fr_0.95fr] lg:py-20">
            <div>
              <Badge variant="outline" className="border-brand/30 text-brand">
                Операционная система ресторана
              </Badge>
              <h1 className="mt-6 max-w-3xl text-balance text-[clamp(2.35rem,5vw,4.25rem)] font-medium leading-[1.02]">
                Операционная система управления рестораном.
              </h1>
              <p className="mt-6 max-w-2xl text-[16px] leading-relaxed text-muted-foreground">
                Receptor объединяет данные, меню, команду, задачи, гостей и
                AI-помощника в один кабинет. Ресторан подключает ядро платформы
                и включает нужные модули по подписке.
              </p>

              <div className="mt-8 flex flex-wrap gap-3">
                <LinkButton
                  href="/dashboard/dev-venue"
                  className="bg-brand text-primary-foreground hover:bg-brand-hover"
                >
                  Открыть демо-кабинет
                  <ArrowRight className="size-4" />
                </LinkButton>
                <LinkButton href="/pricing" variant="outline">
                  Смотреть тарифы
                </LinkButton>
              </div>
            </div>

            <div className="self-start rounded-lg border border-border/60 bg-card/60 p-5">
              <p className="text-[11px] uppercase tracking-[0.22em] text-muted-foreground">
                Product Workspace
              </p>
              <h2 className="mt-3 text-2xl font-medium leading-tight">
                Единый рабочий слой для владельца, управляющего и команды.
              </h2>
              <p className="mt-4 text-sm leading-relaxed text-muted-foreground">
                Кабинет показывает ресторан как систему: цифры, контекст,
                ответственных людей и следующие действия.
              </p>

              <div className="mt-6 divide-y divide-border/35 rounded-lg border border-border/50 bg-background/35">
                {cockpitRows.map((row) => (
                  <div
                    key={row.label}
                    className="grid gap-2 p-4 sm:grid-cols-[0.45fr_1fr] sm:items-center"
                  >
                    <p className="text-sm font-medium">{row.label}</p>
                    <p className="text-sm leading-relaxed text-muted-foreground">
                      {row.value}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section className="border-b border-border/40">
          <div className="mx-auto max-w-7xl px-6 py-14">
            <div className="max-w-3xl">
              <p className="text-[11px] uppercase tracking-[0.22em] text-brand">
                Platform Core
              </p>
              <h2 className="mt-4 text-3xl font-medium">
                Сначала ядро управления, затем модули под задачи ресторана.
              </h2>
              <p className="mt-4 text-sm leading-relaxed text-muted-foreground">
                База одна: данные, контекст, роли и ежедневные решения. Дальше
                ресторан добавляет меню, команду, гостей, доставку, маркетинг и
                интеграции без отдельной разработки с нуля.
              </p>
            </div>

            <div className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              {foundationModules.map((module) => (
                <ModuleCard key={module.id} module={module} featured />
              ))}
            </div>
          </div>
        </section>

        <section className="border-b border-border/40">
          <div className="mx-auto max-w-7xl px-6 py-14">
            <div className="max-w-3xl">
              <p className="text-[11px] uppercase tracking-[0.22em] text-brand">
                Operating Flow
              </p>
              <h2 className="mt-4 text-3xl font-medium">
                Receptor превращает данные в управленческий ритм.
              </h2>
            </div>

            <div className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              {operatingFlow.map((step) => (
                <div
                  key={step.title}
                  className="rounded-lg border border-border/60 bg-card/50 p-5"
                >
                  <step.icon className="size-5 text-brand" />
                  <h3 className="mt-5 text-base font-medium">{step.title}</h3>
                  <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
                    {step.text}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="border-b border-border/40">
          <div className="mx-auto grid max-w-7xl gap-8 px-6 py-14 lg:grid-cols-[0.9fr_1.1fr]">
            <div>
              <p className="text-[11px] uppercase tracking-[0.22em] text-brand">
                Память заведения
              </p>
              <h2 className="mt-4 text-3xl font-medium">
                AI отвечает не из пустоты, а из памяти ресторана.
              </h2>
              <p className="mt-4 text-sm leading-relaxed text-muted-foreground">
                Анкета и ресерч собирают формат, аудиторию, экономику, команду,
                системы, ограничения и правила решений. Этот контекст питает
                AI-помощник, брифы, задачи и настройки модулей.
              </p>
            </div>

            <div className="grid gap-3">
              {VENUE_CONTEXT_QUESTIONNAIRE.map((section) => (
                <div
                  key={section.id}
                  className="rounded-lg border border-border/60 bg-card/50 p-4"
                >
                  <h3 className="text-sm font-medium">{section.title}</h3>
                  <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
                    {section.description}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="border-b border-border/40">
          <div className="mx-auto max-w-7xl px-6 py-14">
            <div className="max-w-3xl">
              <p className="text-[11px] uppercase tracking-[0.22em] text-brand">
                Module Map
              </p>
              <h2 className="mt-4 text-3xl font-medium">
                Модульная подписка для ежедневной работы ресторана.
              </h2>
            </div>
            <div className="mt-8 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
              {RESTAURANT_OS_MODULES.map((module) => (
                <ModuleCard key={module.id} module={module} />
              ))}
            </div>
          </div>
        </section>

        <section>
          <div className="mx-auto max-w-7xl px-6 py-14">
            <div className="max-w-3xl">
              <p className="text-[11px] uppercase tracking-[0.22em] text-brand">
                Launch Flow
              </p>
              <h2 className="mt-4 text-3xl font-medium">
                Подключение начинается с кабинета, а не с долгого техпроекта.
              </h2>
              <p className="mt-4 text-sm leading-relaxed text-muted-foreground">
                Receptor можно показать на демо-данных, затем добавить контекст
                конкретного ресторана и подключить реальные источники. Для
                команды интерфейс остается тем же.
              </p>
            </div>

            <div className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              {connectionSteps.map((step, index) => (
                <article
                  key={step.title}
                  className="rounded-lg border border-border/60 bg-card/45 p-5"
                >
                  <span className="numeric text-sm text-brand">
                    {String(index + 1).padStart(2, "0")}
                  </span>
                  <h3 className="mt-4 text-base font-medium">{step.title}</h3>
                  <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
                    {step.text}
                  </p>
                </article>
              ))}
            </div>
          </div>
        </section>
      </main>
      <SiteFooter />
    </>
  );
}

function ModuleCard({
  module,
  featured = false,
}: {
  module: ProductModule;
  featured?: boolean;
}) {
  const Icon = moduleIconMap[module.id];

  return (
    <article
      className={
        "rounded-lg border p-5 " +
        (featured
          ? "border-brand/30 bg-card/60"
          : "border-border/60 bg-card/45")
      }
    >
      <Icon className={featured ? "size-5 text-ai" : "size-4 text-brand"} />
      <h3 className="mt-5 text-base font-medium">{module.title}</h3>
      <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
        {module.promise}
      </p>
    </article>
  );
}
