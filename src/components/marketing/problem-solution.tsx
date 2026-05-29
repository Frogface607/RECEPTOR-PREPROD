const COLUMNS = [
  {
    eyebrow: "Раньше",
    title: "Восемнадцать окон бэк-офиса.",
    body: "Отчёт по выручке, OLAP, смены, фудкост — каждый утром заново. Excel, копипаст, нервы.",
    tone: "muted" as const,
  },
  {
    eyebrow: "Сейчас",
    title: "Один экран. Цифры вечера.",
    body: "Receptor подключается к iiko и собирает только то, что важно владельцу. KPI, графики, смены — без шума.",
    tone: "brand" as const,
  },
  {
    eyebrow: "Завтра",
    title: "Чат с цифрами.",
    body: "Спросил «почему вчера упало» — получил ответ на основе реальных tool-calls к iiko OLAP. Без галлюцинаций.",
    tone: "iiko" as const,
  },
];

export function ProblemSolution() {
  return (
    <section
      id="что-делает"
      className="border-b border-border/40 bg-background"
    >
      <div className="mx-auto max-w-7xl px-6 py-24">
        <div className="max-w-2xl">
          <p className="text-xs uppercase tracking-[0.22em] text-brand">
            01 · Идея
          </p>
          <h2 className="mt-4 text-balance text-4xl font-medium leading-[1.05] tracking-[-0.02em] sm:text-[44px]">
            Управлять рестораном можно с
            <span className="font-display italic text-brand"> одного экрана.</span>
          </h2>
          <p className="mt-5 max-w-xl text-[16px] leading-relaxed text-muted-foreground">
            20+ инструментов BI и AI собраны вокруг одного вопроса:
            что происходит в зале прямо сейчас и что с этим делать к завтрашнему
            утру.
          </p>
        </div>

        <div className="mt-16 grid gap-px overflow-hidden rounded-2xl border border-border/60 bg-border/40 md:grid-cols-3">
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
              <h3 className="mt-6 text-balance text-[22px] font-medium leading-[1.15] tracking-[-0.01em]">
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
