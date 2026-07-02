import type { Metadata } from "next";
import {
  ArrowRight,
  BadgeCheck,
  ClipboardList,
  MessageSquareText,
  NotebookPen,
  RadioTower,
  SearchCheck,
  UsersRound,
} from "lucide-react";
import { SiteFooter } from "@/components/marketing/site-footer";
import { SiteHeader } from "@/components/marketing/site-header";
import { PilotNextStep } from "@/components/marketing/pilot-next-step";
import { LinkButton } from "@/components/ui/link-button";

export const metadata: Metadata = {
  title: "Пилот Receptor — экран владельца",
  description:
    "Публичное превью утреннего экрана владельца Receptor: решение дня, поручения, итог смены и советник.",
};

const morningChecks = [
  {
    label: "Проверить",
    title: "Почему вчера просел средний чек",
    text: "iiko показывает продажи, а итог смены добавляет контекст: был дождь, две брони отменились, команда продавала без десертов.",
  },
  {
    label: "Поручить",
    title: "Управляющему разобрать стоп-лист",
    text: "Receptor не пишет абстрактный совет, а сразу ведет к поручению для смены и ответственному человеку.",
  },
  {
    label: "Спросить",
    title: "Что сказать команде на брифинге",
    text: "Советник собирает цифры, роли, стандарты и полевые заметки в короткий управленческий ответ.",
  },
];

const ownerFacts = [
  ["Продажи", "156 400 ₽", "факт из iiko"],
  ["Итог смены", "получен", "администратор оставил заметку"],
  ["Поручения", "3 открыто", "одно срочное"],
  ["Стандарты", "2 на проверке", "официанты возвращают практику"],
];

const briefing = [
  "Сначала спросить у управляющего, почему десерты не предлагали после 20:00.",
  "Попросить официантов вернуть короткий итог по возражениям гостей.",
  "После смены сравнить средний чек с похожей пятницей, а не с календарным вчера.",
];

export default function PilotOwnerPage() {
  return (
    <>
      <SiteHeader />
      <main className="flex-1">
        <section className="border-b border-border/40">
          <div className="mx-auto grid max-w-7xl gap-8 px-6 py-12 lg:grid-cols-[0.86fr_1.14fr] lg:py-16">
            <div className="self-center">
              <p className="text-[11px] uppercase tracking-[0.22em] text-brand">
                Owner preview
              </p>
              <h1 className="mt-5 max-w-3xl text-balance text-[clamp(2.35rem,5vw,4.7rem)] font-medium leading-[0.98]">
                Утро владельца без шума.
              </h1>
              <p className="mt-6 max-w-xl text-[16px] leading-relaxed text-muted-foreground">
                Владелец не должен копаться в отчетах с утра. Первый экран
                отвечает на три вопроса: что произошло, кому поручить и что
                сделать сегодня.
              </p>
              <div className="mt-8 flex flex-wrap gap-3">
                <LinkButton
                  href="/auth?next=/dashboard/dev-venue"
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
                    Сегодня · владелец
                  </p>
                  <h2 className="mt-2 text-2xl font-medium">
                    Что мне проверить до вечерней посадки?
                  </h2>
                </div>
                <span className="rounded-full border border-brand/30 bg-brand/10 px-3 py-1 text-[11px] uppercase tracking-[0.14em] text-brand">
                  demo data
                </span>
              </div>

              <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                {ownerFacts.map(([label, value, note]) => (
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

              <div className="mt-5 rounded-lg border border-brand/25 bg-brand/[0.055] p-5">
                <div className="flex items-center gap-2 text-brand">
                  <SearchCheck className="size-4" />
                  <p className="text-[11px] uppercase tracking-[0.18em]">
                    Решение дня
                  </p>
                </div>
                <h3 className="mt-3 text-xl font-medium">
                  Разобрать вечерние продажи с управляющим, а не менять меню.
                </h3>
                <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
                  День похож не на провал меню, а на сбой в смене: отмены из-за
                  погоды, стоп по десертам и слабая продажа после 20:00. Сначала
                  восстановить стандарт сервиса, потом смотреть маржу.
                </p>
              </div>
            </div>
          </div>
        </section>

        <section className="border-b border-border/40">
          <div className="mx-auto max-w-7xl px-6 py-14">
            <div className="grid gap-8 lg:grid-cols-[0.72fr_1.28fr]">
              <div>
                <p className="text-[11px] uppercase tracking-[0.22em] text-brand">
                  Как читать экран
                </p>
                <h2 className="mt-4 text-3xl font-medium">
                  Не графики отдельно, а управленческое действие.
                </h2>
                <p className="mt-4 text-sm leading-relaxed text-muted-foreground">
                  Receptor показывает владельцу не все подряд, а один короткий
                  маршрут: факт, контекст смены, ответственная роль и следующий
                  вопрос для команды.
                </p>
              </div>

              <div className="grid gap-3 md:grid-cols-3">
                {morningChecks.map((item) => (
                  <article
                    key={item.title}
                    className="rounded-lg border border-border/60 bg-card/50 p-5"
                  >
                    <p className="text-[11px] uppercase tracking-[0.18em] text-brand">
                      {item.label}
                    </p>
                    <h3 className="mt-5 text-base font-medium">
                      {item.title}
                    </h3>
                    <p className="mt-3 text-[13px] leading-relaxed text-muted-foreground">
                      {item.text}
                    </p>
                  </article>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section className="border-b border-border/40">
          <div className="mx-auto grid max-w-7xl gap-8 px-6 py-14 lg:grid-cols-[1fr_0.95fr]">
            <div className="rounded-xl border border-border/60 bg-card/50 p-6">
              <div className="flex items-center gap-2 text-brand">
                <ClipboardList className="size-5" />
                <p className="text-[11px] uppercase tracking-[0.18em]">
                  Брифинг управляющему
                </p>
              </div>
              <h2 className="mt-4 text-2xl font-medium">
                Что спросить сегодня
              </h2>
              <div className="mt-5 space-y-3">
                {briefing.map((item, index) => (
                  <div
                    key={item}
                    className="grid gap-3 rounded-lg border border-border/50 bg-background/35 p-4 sm:grid-cols-[2rem_1fr]"
                  >
                    <span className="font-mono text-sm text-brand">
                      {String(index + 1).padStart(2, "0")}
                    </span>
                    <p className="text-sm leading-relaxed text-foreground/85">
                      {item}
                    </p>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-xl border border-brand/25 bg-brand/[0.055] p-6">
              <MessageSquareText className="size-6 text-brand" />
              <h2 className="mt-5 text-2xl font-medium">
                Как это сказать в видео
              </h2>
              <p className="mt-4 text-sm leading-relaxed text-muted-foreground">
                “Вот утро владельца. Я не открываю десять отчетов и не пытаюсь
                вспомнить, что вчера произошло. Receptor уже знает цифры,
                смену, людей и полевые заметки. Он говорит, что проверить
                первым и кому это поручить.”
              </p>
              <div className="mt-6 grid gap-2">
                <PilotPoint icon={RadioTower} text="Факты из iiko остаются базой." />
                <PilotPoint icon={NotebookPen} text="Итоги смен объясняют, почему цифры такие." />
                <PilotPoint icon={UsersRound} text="Поручения и стандарты возвращают действие команде." />
              </div>
            </div>
          </div>
        </section>
        <PilotNextStep
          title="Теперь показать работу управляющего."
          text="После решения владельца логично открыть смену: кто отвечает, какие поручения закрыть и какой итог вернуть наверх."
          primaryHref="/pilot/manager"
          primaryLabel="Показать управляющего"
        />
      </main>
      <SiteFooter />
    </>
  );
}

function PilotPoint({
  icon: Icon,
  text,
}: {
  icon: typeof BadgeCheck;
  text: string;
}) {
  return (
    <div className="flex items-start gap-3 rounded-lg border border-border/45 bg-background/35 p-3">
      <Icon className="mt-0.5 size-4 shrink-0 text-brand" />
      <p className="text-[13px] leading-relaxed text-foreground/85">{text}</p>
    </div>
  );
}
