import type { Metadata } from "next";
import type { LucideIcon } from "lucide-react";
import {
  ArrowRight,
  BadgeCheck,
  ClipboardCheck,
  ClipboardList,
  MessageSquareText,
  NotebookPen,
  ShieldCheck,
  UsersRound,
} from "lucide-react";
import { SiteFooter } from "@/components/marketing/site-footer";
import { SiteHeader } from "@/components/marketing/site-header";
import { LinkButton } from "@/components/ui/link-button";

export const metadata: Metadata = {
  title: "Пилот Receptor — экран управляющего",
  description:
    "Публичное превью рабочего утра управляющего Receptor: смена, поручения, стандарты и итог смены.",
};

const managerFacts = [
  ["Смена", "17:00–00:00", "зал и кухня в фокусе"],
  ["Поручения", "3 срочных", "одно для кухни, два для зала"],
  ["Стандарты", "2 закрепить", "сервис и стоп-лист"],
  ["Итог смены", "нужно собрать", "3 строки после закрытия"],
];

const routeCards = [
  {
    icon: ClipboardList,
    label: "До смены",
    title: "Закрыть срочные поручения",
    text: "Проверить стоп-лист, назначить ответственного по десертам и сказать залу, что продавать после 20:00.",
  },
  {
    icon: ShieldCheck,
    label: "Во время смены",
    title: "Закрепить стандарт сервиса",
    text: "Официанты не просто проходят урок, а применяют правило в смене и возвращают короткий факт.",
  },
  {
    icon: NotebookPen,
    label: "После смены",
    title: "Оставить итог для владельца",
    text: "Что случилось, сколько гостей было, что помешало продажам и что проверить утром.",
  },
];

const assignmentRows = [
  {
    who: "Зал",
    task: "Вернуть десерты в рекомендацию после 20:00",
    result: "Итог: что отвечали гости и сколько раз предложили",
  },
  {
    who: "Кухня",
    task: "Проверить стоп по лимонаду и заготовкам",
    result: "Итог: что закончилось и кто отвечает за закупку",
  },
  {
    who: "Администратор",
    task: "Собрать причину двух отмен брони",
    result: "Итог: погода, событие, депозит или сервис",
  },
];

const briefingScript = [
  "Сегодня не распыляемся: сначала стоп-лист, потом десерты, потом итог смены.",
  "Каждый стандарт должен вернуться фактом с поля, иначе это просто прочитанный урок.",
  "После закрытия оставляем короткий итог: факт, причина, масштаб, что проверить утром.",
];

export default function PilotManagerPage() {
  return (
    <>
      <SiteHeader />
      <main className="flex-1">
        <section className="border-b border-border/40">
          <div className="mx-auto grid max-w-7xl gap-8 px-6 py-12 lg:grid-cols-[0.86fr_1.14fr] lg:py-16">
            <div className="self-center">
              <p className="text-[11px] uppercase tracking-[0.22em] text-brand">
                Manager preview
              </p>
              <h1 className="mt-5 max-w-3xl text-balance text-[clamp(2.35rem,5vw,4.7rem)] font-medium leading-[0.98]">
                Утро управляющего без хаоса.
              </h1>
              <p className="mt-6 max-w-xl text-[16px] leading-relaxed text-muted-foreground">
                Управляющему не нужна еще одна лента сообщений. Нужен короткий
                рабочий маршрут: что сказать перед сменой, кому поручить и
                какой итог вернуть владельцу.
              </p>
              <div className="mt-8 flex flex-wrap gap-3">
                <LinkButton
                  href="/team?role=venue_manager&venueId=dev-venue"
                  className="bg-brand text-primary-foreground hover:bg-brand-hover"
                >
                  Открыть рабочее управление
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
                    Сегодня · управляющий
                  </p>
                  <h2 className="mt-2 text-2xl font-medium">
                    Что нужно закрыть до вечерней смены?
                  </h2>
                </div>
                <span className="rounded-full border border-brand/30 bg-brand/10 px-3 py-1 text-[11px] uppercase tracking-[0.14em] text-brand">
                  demo data
                </span>
              </div>

              <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                {managerFacts.map(([label, value, note]) => (
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
                {routeCards.map((card) => (
                  <article
                    key={card.title}
                    className="rounded-lg border border-border/50 bg-background/40 p-4"
                  >
                    <card.icon className="size-4 text-brand" />
                    <p className="mt-4 text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
                      {card.label}
                    </p>
                    <h3 className="mt-2 text-base font-medium">
                      {card.title}
                    </h3>
                    <p className="mt-2 text-[13px] leading-relaxed text-muted-foreground">
                      {card.text}
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
                Поручения смене
              </p>
              <h2 className="mt-4 text-3xl font-medium">
                Не чат, а понятная ответственность.
              </h2>
              <div className="mt-8 space-y-3">
                {assignmentRows.map((row) => (
                  <div
                    key={row.task}
                    className="grid gap-4 rounded-lg border border-border/50 bg-card/45 p-4 md:grid-cols-[0.22fr_0.43fr_0.35fr]"
                  >
                    <p className="text-[11px] uppercase tracking-[0.16em] text-brand">
                      {row.who}
                    </p>
                    <p className="text-sm font-medium leading-relaxed text-foreground">
                      {row.task}
                    </p>
                    <p className="text-[13px] leading-relaxed text-muted-foreground">
                      {row.result}
                    </p>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-xl border border-brand/25 bg-brand/[0.055] p-6">
              <MessageSquareText className="size-6 text-brand" />
              <h2 className="mt-5 text-2xl font-medium">
                Бриф перед сменой
              </h2>
              <div className="mt-5 space-y-3">
                {briefingScript.map((line, index) => (
                  <div
                    key={line}
                    className="grid gap-3 rounded-lg border border-border/45 bg-background/35 p-4 sm:grid-cols-[2rem_1fr]"
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
          </div>
        </section>

        <section className="border-b border-border/40">
          <div className="mx-auto grid max-w-7xl gap-8 px-6 py-14 lg:grid-cols-[0.9fr_1.1fr]">
            <div>
              <p className="text-[11px] uppercase tracking-[0.22em] text-brand">
                Почему это ценно
              </p>
              <h2 className="mt-4 text-3xl font-medium">
                Управляющий возвращает владельцу живой контекст.
              </h2>
              <p className="mt-4 text-sm leading-relaxed text-muted-foreground">
                iiko покажет выручку и чеки, но не объяснит, что в зале был
                ливень, десерты не предлагали, а гости спрашивали замену
                лимонада. Этот слой собирает команда.
              </p>
            </div>
            <div className="grid gap-3 md:grid-cols-3">
              <PilotPoint icon={UsersRound} title="Люди" text="Кто отвечает за смену, стандарт и итог." />
              <PilotPoint icon={ClipboardCheck} title="Поручения" text="Что нужно сделать и какой результат вернуть." />
              <PilotPoint icon={BadgeCheck} title="Стандарты" text="Не просто уроки, а практика в реальной смене." />
            </div>
          </div>
        </section>
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
