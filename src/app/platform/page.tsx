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
  getIntegrationReadinessState,
  listFoundationModules,
  listIntegrationReadinessStates,
  RESTAURANT_OS_MODULES,
  resolveIntegrationReadinessState,
  type IntegrationReadinessCheck,
  type IntegrationReadinessTone,
  type ProductModuleId,
} from "@/lib/product/modules";
import {
  calculateContextCompletion,
  DEMO_CONTEXT_ANSWERS,
  VENUE_CONTEXT_QUESTIONNAIRE,
} from "@/lib/venues/context-questionnaire";

export const metadata: Metadata = {
  title: "Платформа Receptor Restaurant OS — RECEPTOR",
  description:
    "SaaS-платформа для управления рестораном: данные, контекст, меню, команда, задачи, гости и интеграции.",
};

const operatingFlow = [
  {
    icon: Plug,
    title: "Подключить данные",
    text: "iiko Cloud/RMS, ручной импорт или demo-данные для старта без ожидания интеграции.",
  },
  {
    icon: BookOpenCheck,
    title: "Собрать контекст",
    text: "Формат, цели владельца, команда, ограничения, правила принятия решений и тон AI.",
  },
  {
    icon: ClipboardList,
    title: "Раздать действия",
    text: "Управляющий, кухня, зал и маркетинг получают задачи из одного рабочего слоя.",
  },
  {
    icon: BadgeCheck,
    title: "Управлять повторяемо",
    text: "Ежедневный бриф, еженедельный отчет и модули, которые можно включать по мере роста.",
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
const contextCompletion = calculateContextCompletion(DEMO_CONTEXT_ANSWERS);
const readiness = getIntegrationReadinessState(
  resolveIntegrationReadinessState({
    liveVenueSelected: true,
    hasIikoCredentials: false,
  }),
);
const readinessStates = listIntegrationReadinessStates();

function toneClass(tone: IntegrationReadinessTone): string {
  if (tone === "ready") return "border-brand/30 bg-brand/10 text-brand";
  if (tone === "active") return "border-pro/30 bg-pro/10 text-pro";
  if (tone === "error") return "border-destructive/30 bg-destructive/10 text-destructive";
  return "border-border bg-muted/40 text-muted-foreground";
}

function checkStatusClass(status: IntegrationReadinessCheck["status"]): string {
  if (status === "done") return "border-brand/30 bg-brand/10 text-brand";
  if (status === "next") return "border-pro/30 bg-pro/10 text-pro";
  if (status === "blocked") {
    return "border-destructive/30 bg-destructive/10 text-destructive";
  }
  return "border-border bg-muted/40 text-muted-foreground";
}

export default function PlatformPage() {
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
                Receptor объединяет данные из iiko, память заведения, меню,
                команду, задачи, гостей и AI-помощника в один SaaS-кабинет.
                Это не кастомный проект под один ресторан, а модульная
                платформа для разных форматов и сетей.
              </p>

              <div className="mt-8 flex flex-wrap gap-3">
                <LinkButton
                  href="/dashboard/dev-venue"
                  className="bg-brand text-primary-foreground hover:bg-brand-hover"
                >
                  Открыть demo cockpit
                  <ArrowRight className="size-4" />
                </LinkButton>
                <LinkButton href="/pricing" variant="outline">
                  Смотреть тарифы
                </LinkButton>
              </div>
            </div>

            <div className="self-start rounded-lg border border-border/60 bg-card/60 p-5">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-[11px] uppercase tracking-[0.22em] text-muted-foreground">
                    Integration Readiness
                  </p>
                  <h2 className="mt-3 text-2xl font-medium leading-tight">
                    {readiness.title}
                  </h2>
                </div>
                <Badge variant="outline" className={toneClass(readiness.tone)}>
                  {readiness.statusLabel}
                </Badge>
              </div>

              <div className="mt-6 flex items-end justify-between gap-5 border-y border-border/40 py-5">
                <div>
                  <p className="numeric text-5xl font-medium text-brand">
                    {readiness.score}%
                  </p>
                  <p className="mt-1 text-xs uppercase tracking-[0.16em] text-muted-foreground">
                    workspace readiness
                  </p>
                </div>
                <p className="max-w-xs text-right text-sm leading-relaxed text-muted-foreground">
                  {readiness.ownerMessage}
                </p>
              </div>

              <p className="mt-5 text-sm leading-relaxed text-muted-foreground">
                {readiness.summary}
              </p>

              <div className="mt-6 space-y-3">
                {readiness.checks.map((check) => (
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
                Platform Core
              </p>
              <h2 className="mt-4 text-3xl font-medium">
                Сначала ядро, затем модули под конкретный ресторан.
              </h2>
              <p className="mt-4 text-sm leading-relaxed text-muted-foreground">
                Базовая платформа одна: данные, контекст, операционные роли и
                ежедневные решения. Дальше ресторан включает Menu OS, Team OS,
                Guest OS, Delivery OS и маркетинговые сценарии по подписке.
              </p>
            </div>

            <div className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              {foundationModules.map((module) => {
                const Icon = moduleIconMap[module.id];
                return (
                  <article
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
                  </article>
                );
              })}
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
                Context Engine
              </p>
              <h2 className="mt-4 text-3xl font-medium">
                Не ChatGPT-обертка. Сначала память ресторана.
              </h2>
              <p className="mt-4 text-sm leading-relaxed text-muted-foreground">
                Анкета фиксирует формат, цели владельца, команду, системы,
                ограничения по данным и тон AI. Этот контекст используется в
                ответах, брифах, задачах и настройках модулей.
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
                Модульная подписка вместо бесконечной индивидуальной разработки.
              </h2>
            </div>
            <div className="mt-8 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
              {RESTAURANT_OS_MODULES.map((module) => {
                const Icon = moduleIconMap[module.id];
                return (
                  <article
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
                  </article>
                );
              })}
            </div>
          </div>
        </section>

        <section>
          <div className="mx-auto max-w-7xl px-6 py-14">
            <div className="max-w-3xl">
              <p className="text-[11px] uppercase tracking-[0.22em] text-brand">
                Readiness States
              </p>
              <h2 className="mt-4 text-3xl font-medium">
                Платформа работает в demo, setup и live-режимах.
              </h2>
              <p className="mt-4 text-sm leading-relaxed text-muted-foreground">
                Клиентский кабинет не должен зависеть от одного внешнего ключа.
                Если интеграция еще не подключена, Receptor показывает структуру
                работы и собирает контекст. После подключения live-данные
                включаются в тот же интерфейс.
              </p>
            </div>

            <div className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              {readinessStates.map((state) => (
                <article
                  key={state.id}
                  className={
                    "rounded-lg border p-5 " +
                    (state.id === readiness.id
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
      </main>
      <SiteFooter />
    </>
  );
}
