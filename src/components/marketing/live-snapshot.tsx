const KPIS = [
  {
    label: "Выручка / период",
    value: "продажи",
    note: "Из подключенного учета",
  },
  {
    label: "Средний чек",
    value: "динамика",
    note: "Сравнение с прошлой неделей",
  },
  {
    label: "Продажи по меню",
    value: "меню",
    note: "По блюдам, категориям и сменам",
  },
  {
    label: "Риски дня",
    value: "разбор",
    note: "Что требует внимания владельца",
  },
];

const FOCUS_ROWS = [
  {
    title: "Категория с сильным оборотом",
    detail: "Проверить маржу, списания и техкарты",
  },
  {
    title: "Смена с просадкой среднего чека",
    detail: "Разобрать состав чеков и работу допродаж",
  },
  {
    title: "Позиции без управленческого контроля",
    detail: "Связать с техкартой, себестоимостью и iiko",
  },
];

export function LiveSnapshot() {
  return (
    <section className="border-b border-border/40 bg-background">
      <div className="mx-auto max-w-7xl px-6 py-24">
        <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div className="max-w-xl">
            <p className="text-xs uppercase tracking-[0.22em] text-brand">
              02 · Рабочий кабинет
            </p>
            <h2 className="mt-4 text-balance text-4xl font-medium leading-[1.05] sm:text-[44px]">
              Данные, которые сразу ведут к действию.
            </h2>
          </div>
          <p className="max-w-sm text-[14px] leading-relaxed text-muted-foreground">
            Один экран показывает продажи, меню, смены, риски и действия.
            Ресторану не нужно собирать отчеты вручную, чтобы понять, где
            сегодня требуется внимание.
          </p>
        </div>

        <div className="mt-12 grid gap-px overflow-hidden rounded-xl border border-border/60 bg-border/40 sm:grid-cols-2 lg:grid-cols-4">
          {KPIS.map((k) => (
            <div
              key={k.label}
              className="flex flex-col gap-5 bg-card/60 p-8 transition-colors hover:bg-card/95"
            >
              <p className="text-[11px] uppercase tracking-[0.2em] text-muted-foreground">
                {k.label}
              </p>
              <p className="text-[30px] font-medium leading-none text-foreground">
                {k.value}
              </p>
              <p className="text-[12px] text-muted-foreground">{k.note}</p>
            </div>
          ))}
        </div>

        <div className="mt-10 grid gap-6 lg:grid-cols-2">
          <article className="rounded-xl border border-border/60 bg-card/55 p-8">
            <div className="flex items-center justify-between">
              <p className="text-[11px] uppercase tracking-[0.2em] text-brand">
                Что проверять первым
              </p>
              <span className="font-mono text-[10px] text-muted-foreground">
                по данным учета
              </span>
            </div>
            <ol className="mt-6 space-y-4">
              {FOCUS_ROWS.map((row, i) => (
                <li
                  key={row.title}
                  className="flex items-baseline gap-4 border-b border-border/30 pb-4 last:border-b-0 last:pb-0"
                >
                  <span className="font-mono text-[12px] text-muted-foreground">
                    0{i + 1}
                  </span>
                  <div className="flex-1">
                    <p className="text-[16px] text-foreground">{row.title}</p>
                    <p className="text-[12px] uppercase tracking-[0.16em] text-muted-foreground">
                      {row.detail}
                    </p>
                  </div>
                </li>
              ))}
            </ol>
          </article>

          <article className="rounded-xl border border-border/60 bg-card/55 p-8">
            <p className="text-[11px] uppercase tracking-[0.2em] text-brand">
              Что отвечает Receptor
            </p>
            <blockquote className="mt-6 text-[22px] font-medium leading-[1.35] text-foreground">
              «Я не просто покажу выручку. Я подсвечу, где теряется маржа,
              какая смена требует разбора и какие позиции надо связать с
              техкартами, чтобы управлять меню как системой».
            </blockquote>
            <p className="mt-5 text-[13px] uppercase tracking-[0.16em] text-muted-foreground">
              AI-помощник с доступом к данным ресторана
            </p>
          </article>
        </div>
      </div>
    </section>
  );
}
