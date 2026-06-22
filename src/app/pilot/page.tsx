import type { Metadata } from "next";
import {
  ArrowRight,
  BadgeCheck,
  BookOpenCheck,
  Bot,
  BrainCircuit,
  CalendarDays,
  CheckCircle2,
  ClipboardList,
  KeyRound,
  MessageSquareText,
  Plug,
  RadioTower,
  Store,
  TriangleAlert,
  UtensilsCrossed,
  UsersRound,
} from "lucide-react";
import { SiteFooter } from "@/components/marketing/site-footer";
import { SiteHeader } from "@/components/marketing/site-header";
import { Badge } from "@/components/ui/badge";
import { LinkButton } from "@/components/ui/link-button";
import {
  listPilotBundleModules,
  getPilotCommandState,
  listPilotCommandStates,
  RESTAURANT_OS_MODULES,
  resolvePilotReadinessState,
  type PilotCommandCheck,
  type PilotReadinessTone,
  type ProductModuleId,
} from "@/lib/product/modules";
import {
  calculateContextCompletion,
  DEMO_CONTEXT_ANSWERS,
  VENUE_CONTEXT_QUESTIONNAIRE,
} from "@/lib/venues/context-questionnaire";

export const metadata: Metadata = {
  title: "Receptor Restaurant OS — RECEPTOR",
  description:
    "Операционная система управления рестораном: iiko, контекст, команда, меню, гости и Copilot.",
};

const pilotSteps = [
  {
    icon: KeyRound,
    title: "Подключить iiko",
    text: "Берем apiLogin, выбираем организацию, сохраняем доступы и отмечаем live/demo состояние.",
  },
  {
    icon: CalendarDays,
    title: "Запустить утренний бриф",
    text: "Каждый день владелец видит изменения, риски и действия для менеджера, кухни и маркетинга.",
  },
  {
    icon: Bot,
    title: "Дать команде Copilot",
    text: "Ответы строятся на фактах iiko и профиле заведения: факт, смысл, действие, недостающие данные.",
  },
  {
    icon: ClipboardList,
    title: "Собрать кейс",
    text: "Через две недели фиксируем найденные проблемы, решения и коммерческий эффект для продажи дальше.",
  },
];

const channels = [
  {
    icon: MessageSquareText,
    title: "Mikhno pilot",
    label: "Сначала",
    text: "Индивидуальная сборка для команды: роли, Telegram, ежедневный управленческий ритм.",
  },
  {
    icon: Store,
    title: "iiko Connector",
    label: "После первых продаж",
    text: "Официальная интеграция, но продажи и биллинг остаются на нашей стороне.",
  },
  {
    icon: RadioTower,
    title: "iiko Solution",
    label: "Масштабирование",
    text: "Путь к дилерской сети iiko после пилотов, материалов, поддержки и доказанной ценности.",
  },
];

const nextActions = [
  "Отправить iiko запрос на sandbox и партнерский маршрут.",
  "Получить от Михно apiLogin или контакт технического человека.",
  "Подготовить demo-state с языком владельца, а не разработчика.",
  "Выделить первый live-экран: утром, сегодня, риски, действия.",
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

const pilotModules = listPilotBundleModules();
const contextCompletion = calculateContextCompletion(DEMO_CONTEXT_ANSWERS);
const currentPilotState = getPilotCommandState(
  resolvePilotReadinessState({
    liveTargetSelected: true,
    targetHasIikoKey: false,
  }),
);
const pilotCommandStates = listPilotCommandStates();

function toneClass(tone: PilotReadinessTone): string {
  if (tone === "ready") return "border-brand/30 bg-brand/10 text-brand";
  if (tone === "active") return "border-pro/30 bg-pro/10 text-pro";
  if (tone === "error") return "border-destructive/30 bg-destructive/10 text-destructive";
  return "border-border bg-muted/40 text-muted-foreground";
}

function checkStatusClass(status: PilotCommandCheck["status"]): string {
  if (status === "done") return "border-brand/30 bg-brand/10 text-brand";
  if (status === "next") return "border-pro/30 bg-pro/10 text-pro";
  if (status === "blocked") {
    return "border-destructive/30 bg-destructive/10 text-destructive";
  }
  return "border-border bg-muted/40 text-muted-foreground";
}

export default function PilotPage() {
  return (
    <>
      <SiteHeader />
      <main className="flex-1">
        <section className="border-b border-border/40">
          <div className="mx-auto grid max-w-7xl gap-12 px-6 py-16 lg:grid-cols-[1.05fr_0.95fr] lg:py-20">
            <div>
              <Badge variant="outline" className="border-brand/30 text-brand">
                Restaurant OS
              </Badge>
              <h1 className="mt-6 max-w-3xl text-balance text-[clamp(2.35rem,5vw,4.25rem)] font-medium leading-[1.02]">
                Операционная система управления рестораном.
              </h1>
              <p className="mt-6 max-w-2xl text-[16px] leading-relaxed text-muted-foreground">
                Receptor собирает iiko-данные, контекст заведения, роли команды,
                меню, гостей и Copilot в один рабочий слой. Пилот начинаем узко:
                Morning Brief, Owner Cockpit, Context Engine и один модуль под
                боль клиента.
              </p>

              <div className="mt-8 flex flex-wrap gap-3">
                <LinkButton
                  href="/dashboard/dev-venue"
                  className="bg-brand text-primary-foreground hover:bg-brand-hover"
                >
                  Открыть demo cockpit
                  <ArrowRight className="size-4" />
                </LinkButton>
                <LinkButton href="/tools/tech-card-studio" variant="outline">
                  Tech Card Studio
                </LinkButton>
              </div>
            </div>

            <div className="self-start rounded-lg border border-border/60 bg-card/60 p-5">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-[11px] uppercase tracking-[0.22em] text-muted-foreground">
                    Pilot Command Center
                  </p>
                  <h2 className="mt-3 text-2xl font-medium leading-tight">
                    {currentPilotState.title}
                  </h2>
                </div>
                <Badge
                  variant="outline"
                  className={toneClass(currentPilotState.tone)}
                >
                  {currentPilotState.statusLabel}
                </Badge>
              </div>

              <div className="mt-6 flex items-end justify-between gap-5 border-y border-border/40 py-5">
                <div>
                  <p className="numeric text-5xl font-medium text-brand">
                    {currentPilotState.score}%
                  </p>
                  <p className="mt-1 text-xs uppercase tracking-[0.16em] text-muted-foreground">
                    launch readiness
                  </p>
                </div>
                <p className="max-w-xs text-right text-sm leading-relaxed text-muted-foreground">
                  {currentPilotState.ownerMessage}
                </p>
              </div>

              <p className="mt-5 text-sm leading-relaxed text-muted-foreground">
                {currentPilotState.summary}
              </p>

              <div className="mt-6 space-y-3">
                {currentPilotState.checks.map((check) => (
                  <div
                    key={check.label}
                    className="grid gap-2 border-t border-border/30 pt-3 sm:grid-cols-[0.7fr_1fr_auto] sm:items-start"
                  >
                    <p className="text-sm font-medium">{check.label}</p>
                    <p className="text-sm leading-relaxed text-muted-foreground">
                      {check.detail}
                    </p>
                    <Badge
                      variant="outline"
                      className={checkStatusClass(check.status)}
                    >
                      {check.status}
                    </Badge>
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
                Launch states
              </p>
              <h2 className="mt-4 text-3xl font-medium">
                Один пилот, четыре рабочих режима.
              </h2>
              <p className="mt-4 text-sm leading-relaxed text-muted-foreground">
                Демо не блокируется отсутствием ключа. Live-путь включается
                после apiLogin, а ошибка интеграции должна переводить нас в
                восстановление, не ломая продажу.
              </p>
            </div>

            <div className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              {pilotCommandStates.map((state) => (
                <article
                  key={state.id}
                  className={
                    "rounded-lg border p-5 " +
                    (state.id === currentPilotState.id
                      ? "border-brand/50 bg-card"
                      : "border-border/60 bg-card/45")
                  }
                >
                  <div className="flex items-center justify-between gap-3">
                    <Badge variant="outline" className={toneClass(state.tone)}>
                      {state.statusLabel}
                    </Badge>
                    <span className="numeric text-sm text-muted-foreground">
                      {state.score}%
                    </span>
                  </div>
                  <h3 className="mt-5 text-base font-medium">{state.label}</h3>
                  <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
                    {state.summary}
                  </p>
                  <div className="mt-5 border-t border-border/30 pt-4">
                    <p className="text-[11px] uppercase tracking-[0.16em] text-muted-foreground">
                      Next
                    </p>
                    <p className="mt-2 text-sm text-foreground">
                      {state.primaryAction}
                    </p>
                  </div>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className="border-b border-border/40">
          <div className="mx-auto max-w-7xl px-6 py-14">
            <div className="max-w-2xl">
              <p className="text-[11px] uppercase tracking-[0.22em] text-brand">
                Двухнедельный пилот
              </p>
              <h2 className="mt-4 text-3xl font-medium">
                Продаем утренние решения, не графики.
              </h2>
            </div>

            <div className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              {pilotSteps.map((step) => (
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
          <div className="mx-auto max-w-7xl px-6 py-14">
            <div className="max-w-3xl">
              <p className="text-[11px] uppercase tracking-[0.22em] text-brand">
                Pilot bundle
              </p>
              <h2 className="mt-4 text-3xl font-medium">
                Большая платформа, контролируемый первый запуск.
              </h2>
              <p className="mt-4 text-sm leading-relaxed text-muted-foreground">
                Каталог модулей уже живет в коде. Для Михно не продаем все сразу:
                ставим ядро, подключаем данные, собираем контекст и добавляем
                модуль, где боль сильнее всего.
              </p>
            </div>

            <div className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              {pilotModules.map((module) => {
                const Icon = moduleIconMap[module.id];
                return (
                  <div
                    key={module.id}
                    className="rounded-lg border border-border/60 bg-card/50 p-5"
                  >
                    <Icon className="size-5 text-ai" />
                    <div className="mt-5 flex items-start justify-between gap-3">
                      <h3 className="text-base font-medium">{module.title}</h3>
                      <Badge variant="outline" className="shrink-0 text-[10px]">
                        {module.source}
                      </Badge>
                    </div>
                    <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
                      {module.promise}
                    </p>
                  </div>
                );
              })}
            </div>
          </div>
        </section>

        <section className="border-b border-border/40">
          <div className="mx-auto grid max-w-7xl gap-8 px-6 py-14 lg:grid-cols-[0.9fr_1.1fr]">
            <div>
              <p className="text-[11px] uppercase tracking-[0.22em] text-brand">
                Context Engine
              </p>
              <h2 className="mt-4 text-3xl font-medium">
                Не ChatGPT-обертка. Сначала память ресторана.
              </h2>
              <p className="mt-4 text-sm leading-relaxed text-muted-foreground">
                Анкета фиксирует формат, цели владельца, команду, системы,
                ограничения по данным и тон Copilot. Это станет базовым контекстом
                для ответов, брифов и задач.
              </p>
              <div className="mt-6 grid grid-cols-2 gap-3">
                <div className="rounded-lg border border-border/60 bg-card/50 p-4">
                  <p className="numeric text-3xl font-medium text-brand">
                    {contextCompletion.percentage}%
                  </p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    demo-context заполнен
                  </p>
                </div>
                <div className="rounded-lg border border-border/60 bg-card/50 p-4">
                  <p className="numeric text-3xl font-medium text-brand">
                    {contextCompletion.requiredAnswered}/{contextCompletion.requiredTotal}
                  </p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    обязательных блоков
                  </p>
                </div>
              </div>
            </div>

            <div className="grid gap-3">
              {VENUE_CONTEXT_QUESTIONNAIRE.map((section) => (
                <div
                  key={section.id}
                  className="rounded-lg border border-border/60 bg-card/50 p-4"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <h3 className="text-sm font-medium">{section.title}</h3>
                      <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
                        {section.description}
                      </p>
                    </div>
                    <Badge variant="outline" className="shrink-0 text-[10px]">
                      {section.questions.length} поля
                    </Badge>
                  </div>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {section.questions.map((question) => (
                      <span
                        key={question.id}
                        className="rounded-md border border-border/50 bg-background/45 px-2 py-1 text-[11px] text-muted-foreground"
                      >
                        {question.label}
                        {question.required ? " *" : ""}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="border-b border-border/40">
          <div className="mx-auto max-w-7xl px-6 py-14">
            <div className="max-w-3xl">
              <p className="text-[11px] uppercase tracking-[0.22em] text-brand">
                Full module map
              </p>
              <h2 className="mt-4 text-3xl font-medium">
                Edison дает операционные модули, Receptor дает SaaS-ядро.
              </h2>
            </div>
            <div className="mt-8 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
              {RESTAURANT_OS_MODULES.map((module) => {
                const Icon = moduleIconMap[module.id];
                return (
                  <div
                    key={module.id}
                    className="rounded-lg border border-border/60 bg-card/45 p-4"
                  >
                    <div className="flex items-center justify-between gap-3">
                      <Icon className="size-4 text-brand" />
                      <Badge variant="outline" className="text-[10px]">
                        {module.phase}
                      </Badge>
                    </div>
                    <h3 className="mt-4 text-sm font-medium">{module.title}</h3>
                    <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
                      {module.promise}
                    </p>
                  </div>
                );
              })}
            </div>
          </div>
        </section>

        <section className="border-b border-border/40">
          <div className="mx-auto grid max-w-7xl gap-8 px-6 py-14 lg:grid-cols-[0.8fr_1.2fr]">
            <div>
              <p className="text-[11px] uppercase tracking-[0.22em] text-brand">
                Канал продаж
              </p>
              <h2 className="mt-4 text-3xl font-medium">Mikhno first, iiko next.</h2>
              <p className="mt-4 text-sm leading-relaxed text-muted-foreground">
                Путь через маркетплейс iiko имеет смысл после первых реальных
                пилотов: им нужны кейсы, материалы, поддержка и понятная
                партнерская экономика.
              </p>
            </div>

            <div className="grid gap-4 md:grid-cols-3">
              {channels.map((channel) => (
                <div
                  key={channel.title}
                  className="rounded-lg border border-border/60 bg-card/50 p-5"
                >
                  <channel.icon className="size-5 text-iiko" />
                  <Badge variant="outline" className="mt-5">
                    {channel.label}
                  </Badge>
                  <h3 className="mt-4 text-base font-medium">{channel.title}</h3>
                  <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
                    {channel.text}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section>
          <div className="mx-auto grid max-w-7xl gap-8 px-6 py-14 lg:grid-cols-[1fr_1fr]">
            <div className="rounded-lg border border-border/60 bg-card/50 p-6">
              <div className="flex items-center gap-3">
                <TriangleAlert className="size-5 text-pro" />
                <h2 className="text-xl font-medium">Ключа пока нет</h2>
              </div>
              <p className="mt-4 text-sm leading-relaxed text-muted-foreground">
                Поэтому сегодня строим то, что не зависит от ключа: продуктовую
                модель, Context Engine, demo-state, iiko outreach и pilot workflow.
                Когда ключ появится, меняем mock на live и проверяем цифры.
              </p>
            </div>

            <div className="rounded-lg border border-border/60 bg-card/50 p-6">
              <div className="flex items-center gap-3">
                <BadgeCheck className="size-5 text-brand" />
                <h2 className="text-xl font-medium">Следующие действия</h2>
              </div>
              <div className="mt-5 grid gap-3">
                {nextActions.map((action) => (
                  <div key={action} className="flex gap-3 text-sm">
                    <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-brand" />
                    <span className="leading-relaxed text-muted-foreground">
                      {action}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>
      </main>
      <SiteFooter />
    </>
  );
}
