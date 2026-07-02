import type { Metadata } from "next";
import type { LucideIcon } from "lucide-react";
import {
  ArrowRight,
  BookOpenCheck,
  ClipboardList,
  MessageSquareText,
  NotebookPen,
  Sparkles,
  UserCheck,
} from "lucide-react";
import { SiteFooter } from "@/components/marketing/site-footer";
import { SiteHeader } from "@/components/marketing/site-header";
import { PilotNextStep } from "@/components/marketing/pilot-next-step";
import { LinkButton } from "@/components/ui/link-button";

export const metadata: Metadata = {
  title: "Пилот Receptor — экран сотрудника",
  description:
    "Публичное превью личного кабинета сотрудника Receptor: смена, стандарт, поручение и короткий итог.",
};

const employeeFacts = [
  ["Смена", "17:00–00:00", "зал · вечерняя посадка"],
  ["Стандарт", "1 пройти", "как предлагать десерт"],
  ["Поручение", "1 срочное", "проверить стоп-лист"],
  ["Итог", "3 строки", "после смены"],
];

const shiftRoute = [
  {
    icon: BookOpenCheck,
    label: "Перед сменой",
    title: "Пройти стандарт",
    text: "Короткое правило: как предложить десерт без навязчивости и что сказать при отказе.",
  },
  {
    icon: ClipboardList,
    label: "В смене",
    title: "Сделать поручение",
    text: "Проверить стоп-лист, знать замену лимонада и не обещать гостям то, чего нет.",
  },
  {
    icon: NotebookPen,
    label: "После смены",
    title: "Написать итог",
    text: "Что было, почему важно, сколько раз повторилось и что проверить утром.",
  },
];

const shiftSummary = [
  "Факт: после 20:00 гости трижды спрашивали десерт к стауту.",
  "Причина: один десерт был в стопе, замену не проговорили на брифе.",
  "Проверить утром: обновить стоп-лист и дать залу две замены.",
];

const whyItWorks = [
  {
    icon: UserCheck,
    title: "Сотрудник не тонет",
    text: "Он видит только свой минимум на смену, а не весь управленческий кабинет.",
  },
  {
    icon: Sparkles,
    title: "Обучение связано с работой",
    text: "Стандарт сразу возвращается в смену: прочитал, применил, оставил факт.",
  },
  {
    icon: MessageSquareText,
    title: "Контекст идет наверх",
    text: "Управляющий и владелец утром видят не только цифры, но и причину с поля.",
  },
];

export default function PilotEmployeePage() {
  return (
    <>
      <SiteHeader />
      <main className="flex-1">
        <section className="border-b border-border/40">
          <div className="mx-auto grid max-w-7xl gap-8 px-6 py-12 lg:grid-cols-[0.86fr_1.14fr] lg:py-16">
            <div className="self-center">
              <p className="text-[11px] uppercase tracking-[0.22em] text-brand">
                Экран сотрудника
              </p>
              <h1 className="mt-5 max-w-3xl text-balance text-[clamp(2.35rem,5vw,4.7rem)] font-medium leading-[0.98]">
                Сотруднику понятно, что делать.
              </h1>
              <p className="mt-6 max-w-xl text-[16px] leading-relaxed text-muted-foreground">
                Линейному сотруднику не нужен большой дашборд. Ему нужен один
                экран на смену: стандарт, поручение и короткий итог после
                работы.
              </p>
              <div className="mt-8 flex flex-wrap gap-3">
                <LinkButton
                  href="/team?role=service&venueId=dev-venue"
                  className="bg-brand text-primary-foreground hover:bg-brand-hover"
                >
                  Открыть рабочий кабинет
                  <ArrowRight className="size-4" />
                </LinkButton>
                <LinkButton href="/pilot" variant="outline">
                  Назад к маршруту
                </LinkButton>
              </div>
            </div>

            <div className="rounded-xl border border-border/60 bg-card/55 p-5">
              <div className="flex flex-wrap items-start justify-between gap-4 border-b border-border/45 pb-4">
                <div>
                  <p className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
                    Сегодня · официант
                  </p>
                  <h2 className="mt-2 text-2xl font-medium">
                    Минимум на смену: стандарт, поручение, итог.
                  </h2>
                </div>
                <span className="rounded-full border border-brand/30 bg-brand/10 px-3 py-1 text-[11px] uppercase tracking-[0.14em] text-brand">
                  пример смены
                </span>
              </div>

              <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                {employeeFacts.map(([label, value, note]) => (
                  <div
                    key={label}
                    className="rounded-lg border border-border/50 bg-background/40 p-4"
                  >
                    <p className="text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
                      {label}
                    </p>
                    <p className="mt-3 text-2xl font-medium">{value}</p>
                    <p className="mt-1 text-[12px] leading-relaxed text-muted-foreground">
                      {note}
                    </p>
                  </div>
                ))}
              </div>

              <div className="mt-5 grid gap-3 md:grid-cols-3">
                {shiftRoute.map((step) => (
                  <article
                    key={step.title}
                    className="rounded-lg border border-border/50 bg-background/40 p-4"
                  >
                    <step.icon className="size-4 text-brand" />
                    <p className="mt-4 text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
                      {step.label}
                    </p>
                    <h3 className="mt-2 text-base font-medium">
                      {step.title}
                    </h3>
                    <p className="mt-2 text-[13px] leading-relaxed text-muted-foreground">
                      {step.text}
                    </p>
                  </article>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section className="border-b border-border/40">
          <div className="mx-auto grid max-w-7xl gap-8 px-6 py-14 lg:grid-cols-[1fr_0.95fr]">
            <div>
              <p className="text-[11px] uppercase tracking-[0.22em] text-brand">
                Итог смены
              </p>
              <h2 className="mt-4 text-3xl font-medium">
                Три строки, которые объяснят цифры.
              </h2>
              <div className="mt-8 space-y-3">
                {shiftSummary.map((line, index) => (
                  <div
                    key={line}
                    className="grid gap-3 rounded-lg border border-border/50 bg-card/45 p-4 sm:grid-cols-[2rem_1fr]"
                  >
                    <span className="font-mono text-sm text-brand">
                      {String(index + 1).padStart(2, "0")}
                    </span>
                    <p className="text-sm leading-relaxed text-foreground/85">
                      {line}
                    </p>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-xl border border-brand/25 bg-brand/[0.055] p-6">
              <NotebookPen className="size-6 text-brand" />
              <h2 className="mt-5 text-2xl font-medium">
                Как это сказать сотруднику
              </h2>
              <p className="mt-4 text-sm leading-relaxed text-muted-foreground">
                “Тебе не нужно заполнять большой отчет. После смены напиши три
                строки: что произошло, почему это важно и что проверить утром.
                Это увидит управляющий и владелец.”
              </p>
              <p className="mt-4 rounded-lg border border-border/45 bg-background/35 p-4 text-sm leading-relaxed text-foreground/85">
                Так Receptor собирает живой контекст без лишней бюрократии.
              </p>
            </div>
          </div>
        </section>

        <section className="border-b border-border/40">
          <div className="mx-auto grid max-w-7xl gap-8 px-6 py-14 lg:grid-cols-[0.9fr_1.1fr]">
            <div>
              <p className="text-[11px] uppercase tracking-[0.22em] text-brand">
                Почему это работает
              </p>
              <h2 className="mt-4 text-3xl font-medium">
                Система начинается с простого действия на смене.
              </h2>
              <p className="mt-4 text-sm leading-relaxed text-muted-foreground">
                Чем проще сотруднику оставить факт, тем точнее утренний разбор
                владельца. Цифры из iiko получают объяснение, а обучение
                перестает быть отдельным курсом.
              </p>
            </div>
            <div className="grid gap-3 md:grid-cols-3">
              {whyItWorks.map((item) => (
                <PilotPoint
                  key={item.title}
                  icon={item.icon}
                  title={item.title}
                  text={item.text}
                />
              ))}
            </div>
          </div>
        </section>
        <PilotNextStep
          title="Теперь можно открыть рабочий кабинет."
          text="Публичный маршрут объяснил роли. Следующий шаг: зайти в рабочий экран сотрудника и показать, как это выглядит в продукте."
          primaryHref="/team?role=service&venueId=dev-venue"
          primaryLabel="Открыть кабинет"
        />
      </main>
      <SiteFooter />
    </>
  );
}

function PilotPoint({
  icon: Icon,
  title,
  text,
}: {
  icon: LucideIcon;
  title: string;
  text: string;
}) {
  return (
    <article className="rounded-lg border border-border/60 bg-card/50 p-5">
      <Icon className="size-5 text-brand" />
      <h3 className="mt-5 text-base font-medium">{title}</h3>
      <p className="mt-3 text-[13px] leading-relaxed text-muted-foreground">
        {text}
      </p>
    </article>
  );
}
