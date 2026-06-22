const COLUMNS = [
  {
    eyebrow: "Раньше",
    title: "Отчеты живут отдельно от действий.",
    body: "Выручка, OLAP, смены, себестоимость, техкарты, стоп-лист и задачи команды каждый день собираются вручную. В итоге владелец видит цифры поздно, а команда работает в разных каналах.",
    tone: "muted" as const,
  },
  {
    eyebrow: "Сейчас",
    title: "Одна система. Цифры, контекст и задачи.",
    body: "Receptor подключается к iiko, хранит профиль заведения и показывает не только показатели, но и понятные действия для владельца, управляющего, кухни и маркетинга.",
    tone: "brand" as const,
  },
  {
    eyebrow: "Дальше",
    title: "AI знает ресторан, а не просто отвечает в чат.",
    body: "Ответы строятся на продажах, меню, контексте заведения, ролях команды и реальных интеграциях. Это рабочий помощник внутри операционной системы.",
    tone: "iiko" as const,
  },
];

export function ProblemSolution() {
  return (
    <section id="features" className="border-b border-border/40 bg-background">
      <div className="mx-auto max-w-7xl px-6 py-24">
        <div className="max-w-2xl">
          <p className="text-xs uppercase tracking-[0.22em] text-brand">
            01 · Идея
          </p>
          <h2 className="mt-4 text-balance text-4xl font-medium leading-[1.05] sm:text-[44px]">
            Управлять рестораном можно из одной системы.
          </h2>
          <p className="mt-5 max-w-xl text-[16px] leading-relaxed text-muted-foreground">
            BI, AI-помощник, техкарты, меню, команда и ежедневные разборы
            собраны вокруг одного вопроса: что происходит в бизнесе и что
            делать дальше.
          </p>
        </div>

        <div className="mt-16 grid gap-px overflow-hidden rounded-xl border border-border/60 bg-border/40 md:grid-cols-3">
          {COLUMNS.map((col, idx) => (
            <article
              key={col.eyebrow}
              className="bg-card/60 p-8 transition-colors hover:bg-card/90"
            >
              <div className="flex items-center justify-between">
                <span
                  className={
                    "text-[11px] uppercase tracking-[0.2em] " +
                    (col.tone === "brand"
                      ? "text-brand"
                      : col.tone === "iiko"
                        ? "text-[color:var(--iiko)]"
                        : "text-muted-foreground")
                  }
                >
                  {col.eyebrow}
                </span>
                <span className="font-mono text-[10px] text-muted-foreground">
                  0{idx + 1}
                </span>
              </div>
              <h3 className="mt-6 text-balance text-[22px] font-medium leading-[1.15]">
                {col.title}
              </h3>
              <p className="mt-4 text-[14px] leading-relaxed text-muted-foreground">
                {col.body}
              </p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
