import type { Metadata } from "next";
import {
  ArrowRight,
  BadgeCheck,
  ClipboardList,
  KeyRound,
  MessageSquareText,
  Mic2,
  MonitorCheck,
  NotebookPen,
  UserRoundCog,
  UsersRound,
} from "lucide-react";
import { SiteFooter } from "@/components/marketing/site-footer";
import { SiteHeader } from "@/components/marketing/site-header";
import { LinkButton } from "@/components/ui/link-button";

export const metadata: Metadata = {
  title: "Пилот Receptor — показать ресторану",
  description:
    "Короткий маршрут показа Receptor: подключение ресторана, экран владельца, управляющий, сотрудник, итог смены и советник.",
};

const showRoute = [
  {
    id: "setup",
    icon: KeyRound,
    step: "01",
    title: "Подключить ресторан",
    text: "Владелец входит, создает заведение, добавляет контекст и подключает iiko, когда доступы готовы.",
    href: "/auth?next=/onboarding%3Fnew%3D1",
    action: "Начать подключение",
  },
  {
    id: "owner",
    icon: MonitorCheck,
    step: "02",
    title: "Показать владельца",
    text: "Один утренний экран: что проверить, кому поручить, какие факты уже учтены и где открыть советника.",
    href: "/pilot/owner",
    action: "Открыть превью",
  },
  {
    id: "team",
    icon: UserRoundCog,
    step: "03",
    title: "Показать управляющего",
    text: "Управляющий видит смену, срочные поручения, стандарты, людей и что собрать после рабочего дня.",
    href: "/pilot/manager",
    action: "Открыть превью",
  },
  {
    id: "employee",
    icon: UsersRound,
    step: "04",
    title: "Показать сотрудника",
    text: "У сотрудника только свое: смена, стандарт, поручение и короткий итог, который попадет в память заведения.",
    href: "/pilot/employee",
    action: "Открыть превью",
  },
];

const pitchBeats = [
  {
    icon: Mic2,
    title: "Проблема",
    text: "В ресторане много данных, но люди часто не понимают, что с ними делать и кто за что отвечает.",
  },
  {
    icon: NotebookPen,
    title: "Решение",
    text: "Receptor собирает контекст заведения, роли, стандарты, итоги смен и факты iiko в один рабочий ритм.",
  },
  {
    icon: MessageSquareText,
    title: "Магия",
    text: "Советник отвечает не абстрактно, а из памяти конкретного ресторана: цифры, люди, смены, боли и правила.",
  },
];

const pilotChecklist = [
  "Владелец получил логин и вошел в кабинет.",
  "Заведение создано чисто: название, формат, роли, первый контекст.",
  "iiko подключается через Cloud API ключ или iiko Server.",
  "Управляющий видит поручения, стандарты и итог смены.",
  "Сотрудник понимает свой минимум: смена, стандарт, поручение, итог.",
  "Советник открывается как ежедневный помощник, а не как чат ради чата.",
];

export default function PilotPage() {
  return (
    <>
      <SiteHeader />
      <main className="flex-1">
        <section className="border-b border-border/40">
          <div className="mx-auto grid max-w-7xl gap-10 px-6 py-14 lg:grid-cols-[0.92fr_1.08fr] lg:py-18">
            <div className="self-center">
              <p className="text-[11px] uppercase tracking-[0.22em] text-brand">
                Маршрут показа
              </p>
              <h1 className="mt-5 max-w-3xl text-balance text-[clamp(2.4rem,5vw,4.6rem)] font-medium leading-[0.98]">
                Показать ресторану, как работает Receptor.
              </h1>
              <p className="mt-6 max-w-xl text-[16px] leading-relaxed text-muted-foreground">
                Это короткий маршрут для первого разговора: подключили
                заведение, показали владельца, управляющего, сотрудника и
                ежедневный советник.
              </p>
              <div className="mt-8 flex flex-wrap gap-3">
                <LinkButton
                  href="/auth?next=/onboarding%3Fnew%3D1"
                  className="bg-brand text-primary-foreground hover:bg-brand-hover"
                >
                  Подключить ресторан
                  <ArrowRight className="size-4" />
                </LinkButton>
                <LinkButton href="#show-route" variant="outline">
                  Смотреть маршрут
                </LinkButton>
              </div>
            </div>

            <div className="rounded-xl border border-border/60 bg-card/55 p-5">
              <div className="flex items-center justify-between border-b border-border/45 pb-4">
                <div>
                  <p className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
                    Показ за 7 минут
                  </p>
                  <h2 className="mt-2 text-2xl font-medium">
                    Четыре двери в продукт
                  </h2>
                </div>
                <span className="rounded-full border border-brand/30 bg-brand/10 px-3 py-1 text-[11px] uppercase tracking-[0.14em] text-brand">
                  маршрут собран
                </span>
              </div>
              <div className="mt-5 grid gap-3 sm:grid-cols-2">
                {showRoute.map((item) => (
                  <a
                    key={item.id}
                    href={item.href}
                    className="group rounded-lg border border-border/50 bg-background/40 p-4 transition-colors hover:border-brand/35 hover:bg-background/70"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <span className="flex size-9 items-center justify-center rounded-lg border border-border/45 bg-card/55 text-brand">
                        <item.icon className="size-4" />
                      </span>
                      <span className="font-mono text-[11px] text-muted-foreground">
                        {item.step}
                      </span>
                    </div>
                    <h3 className="mt-5 text-base font-medium">
                      {item.title}
                    </h3>
                    <p className="mt-2 min-h-16 text-[13px] leading-relaxed text-muted-foreground">
                      {item.text}
                    </p>
                    <p className="mt-4 inline-flex items-center gap-1.5 text-[13px] text-brand">
                      {item.action}
                      <ArrowRight className="size-3.5 transition-transform group-hover:translate-x-0.5" />
                    </p>
                  </a>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section id="show-route" className="border-b border-border/40">
          <div className="mx-auto max-w-7xl px-6 py-14">
            <div className="grid gap-8 lg:grid-cols-[0.7fr_1.3fr]">
              <div>
                <p className="text-[11px] uppercase tracking-[0.22em] text-brand">
                  Что показать
                </p>
                <h2 className="mt-4 text-3xl font-medium">
                  Не экраны ради экранов, а ежедневная система.
                </h2>
                <p className="mt-4 text-sm leading-relaxed text-muted-foreground">
                  Маршрут должен объяснить человеку одну мысль: Receptor знает
                  ресторан, собирает факты с поля и превращает их в понятные
                  действия для разных ролей.
                </p>
              </div>

              <div className="grid gap-3 md:grid-cols-3">
                {pitchBeats.map((beat) => (
                  <article
                    key={beat.title}
                    className="rounded-lg border border-border/60 bg-card/50 p-5"
                  >
                    <beat.icon className="size-5 text-brand" />
                    <h3 className="mt-5 text-base font-medium">
                      {beat.title}
                    </h3>
                    <p className="mt-3 text-[13px] leading-relaxed text-muted-foreground">
                      {beat.text}
                    </p>
                  </article>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section className="border-b border-border/40">
          <div className="mx-auto grid max-w-7xl gap-8 px-6 py-14 lg:grid-cols-[1fr_0.9fr]">
            <div>
              <p className="text-[11px] uppercase tracking-[0.22em] text-brand">
                Перед пилотом
              </p>
              <h2 className="mt-4 text-3xl font-medium">
                Что должно быть готово перед первым рестораном.
              </h2>
              <div className="mt-8 grid gap-2">
                {pilotChecklist.map((item) => (
                  <div
                    key={item}
                    className="flex items-start gap-3 rounded-lg border border-border/50 bg-card/45 p-4"
                  >
                    <BadgeCheck className="mt-0.5 size-4 shrink-0 text-brand" />
                    <p className="text-sm leading-relaxed text-foreground/85">
                      {item}
                    </p>
                  </div>
                ))}
              </div>
            </div>

            <div className="self-start rounded-xl border border-brand/25 bg-brand/[0.055] p-6">
              <ClipboardList className="size-6 text-brand" />
              <h3 className="mt-5 text-2xl font-medium">
                Сценарий для первого видео
              </h3>
              <p className="mt-4 text-sm leading-relaxed text-muted-foreground">
                “Я десять лет работал в общепите и понял: ресторану нужен не
                очередной отчет, а система, которая знает заведение, людей,
                смены и помогает понять, что делать сегодня. Поэтому мы
                запускаем Receptor и строим его публично.”
              </p>
              <div className="mt-6 flex flex-wrap gap-3">
                <LinkButton
                  href="/pilot/owner"
                  className="bg-brand text-primary-foreground hover:bg-brand-hover"
                >
                  Начать с владельца
                  <ArrowRight className="size-4" />
                </LinkButton>
                <LinkButton href="/platform" variant="outline">
                  Открыть платформу
                </LinkButton>
              </div>
            </div>
          </div>
        </section>
      </main>
      <SiteFooter />
    </>
  );
}
