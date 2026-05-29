import { getIikoClient } from "@/lib/iiko/client";
import { formatRubles, formatInteger } from "@/lib/format";

const ANCHOR = "2026-05-29";

/**
 * Server component — renders REAL numbers from `MockIikoClient` against
 * Edison fixtures. The same data layer that powers the dashboard.
 *
 * Choice: showing actual product data on the landing builds more trust
 * than another mock screenshot.
 */
export async function LiveSnapshot() {
  const client = getIikoClient({
    channel: "cloud",
    apiLogin: "",
    organizationId: "edison",
    today: ANCHOR,
  });

  const [summary, topDishes] = await Promise.all([
    client.getRevenueSummary({ type: "LAST_WEEK" }),
    client.getDishStatistics({ type: "LAST_WEEK" }, 3),
  ]);

  const KPIS = [
    {
      label: "Выручка / 7 дней",
      value: formatRubles(summary.revenue),
      note: "Edison Bar · LAST_WEEK",
    },
    {
      label: "Средний чек",
      value: formatRubles(summary.averageCheck),
      note: "Динамически по чекам",
    },
    {
      label: "Позиций продано",
      value: formatInteger(summary.itemsSold),
      note: "По всем сменам",
    },
    {
      label: "Уникальных блюд",
      value: formatInteger(summary.uniqueDishes),
      note: "В выбранном периоде",
    },
  ];

  return (
    <section className="border-b border-border/40 bg-background">
      <div className="mx-auto max-w-7xl px-6 py-24">
        <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div className="max-w-xl">
            <p className="text-xs uppercase tracking-[0.22em] text-brand">
              02 · Что вы видите
            </p>
            <h2 className="mt-4 text-balance text-4xl font-medium leading-[1.05] tracking-[-0.02em] sm:text-[44px]">
              Живые цифры с{" "}
              <span className="font-display italic text-brand">демо-аккаунта</span>{" "}
              Edison Bar.
            </h2>
          </div>
          <p className="max-w-sm text-[14px] leading-relaxed text-muted-foreground">
            Числа ниже честные — Receptor читает их через стандартный
            интерфейс iiko, тот же, что подключится к вашему ресторану за
            десять минут.
          </p>
        </div>

        <div className="mt-12 grid gap-px overflow-hidden rounded-2xl border border-border/60 bg-border/40 sm:grid-cols-2 lg:grid-cols-4">
          {KPIS.map((k) => (
            <div
              key={k.label}
              className="flex flex-col gap-5 bg-card/60 p-8 transition-colors hover:bg-card/95"
            >
              <p className="text-[11px] uppercase tracking-[0.2em] text-muted-foreground">
                {k.label}
              </p>
              <p className="numeric font-display text-[44px] leading-none tracking-[-0.02em] text-foreground">
                {k.value}
              </p>
              <p className="text-[12px] text-muted-foreground">{k.note}</p>
            </div>
          ))}
        </div>

        <div className="mt-10 grid gap-6 lg:grid-cols-2">
          <article className="rounded-2xl border border-border/60 bg-card/60 p-8">
            <div className="flex items-center justify-between">
              <p className="text-[11px] uppercase tracking-[0.2em] text-brand">
                Топ-3 блюда недели
              </p>
              <span className="font-mono text-[10px] text-muted-foreground">
                MockIikoClient.getDishStatistics()
              </span>
            </div>
            <ol className="mt-6 space-y-4">
              {topDishes.map((d, i) => (
                <li
                  key={d.dishName}
                  className="flex items-baseline gap-4 border-b border-border/30 pb-4 last:border-b-0 last:pb-0"
                >
                  <span className="font-mono text-[12px] text-muted-foreground">
                    0{i + 1}
                  </span>
                  <div className="flex-1">
                    <p className="text-[16px] text-foreground">{d.dishName}</p>
                    <p className="text-[12px] uppercase tracking-[0.16em] text-muted-foreground">
                      {d.dishGroup}
                    </p>
                  </div>
                  <p className="numeric font-mono text-[15px] text-foreground">
                    {formatRubles(d.dishSumInt)}
                  </p>
                </li>
              ))}
            </ol>
          </article>

          <article className="rounded-2xl border border-border/60 bg-card/60 p-8">
            <p className="text-[11px] uppercase tracking-[0.2em] text-brand">
              Что Receptor отвечает
            </p>
            <blockquote className="mt-6 font-display italic text-[24px] leading-[1.25] text-foreground">
              «Бургер Нечто держит топ — 38% выручки бургерной категории. Но
              маржа в коктейлях растёт на 12% к прошлому месяцу. Подумайте о
              переброске продвижения.»
            </blockquote>
            <p className="mt-5 text-[13px] uppercase tracking-[0.16em] text-muted-foreground">
              Claude · tool-calls к iiko OLAP
            </p>
          </article>
        </div>
      </div>
    </section>
  );
}
