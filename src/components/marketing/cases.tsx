import Link from "next/link";

const CASES = [
  {
    venue: "Рабочий кабинет",
    city: "Product",
    status: "Product" as const,
    tagline: "BI, copilot и onboarding собраны в один пилотный сценарий.",
    metric: "4.7 млн / 30 дней",
    href: "/dashboard/dev-venue",
  },
  {
    venue: "Первый пилот",
    city: "Ресторанная группа",
    status: "Pilot" as const,
    tagline: "Подключение реального iiko, ежедневный brief и BI по живым данным.",
    metric: "Подключение на этой неделе",
  },
  {
    venue: "Next pilot",
    city: "-",
    status: "Open" as const,
    tagline: "Слот для следующего ресторана или небольшой сети.",
    metric: "Места: 2 из 3",
    href: "mailto:bro@frogface.space?subject=Receptor%20pilot",
  },
] as const;

type Case = (typeof CASES)[number];

function StatusBadge({ status }: { status: Case["status"] }) {
  const styles: Record<Case["status"], string> = {
    Product: "bg-brand/10 text-brand border-brand/35",
    Pilot: "bg-[color:var(--pro)]/12 text-[color:var(--pro)] border-[color:var(--pro)]/35",
    Open: "bg-muted text-muted-foreground border-border",
  };
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-[10px] uppercase tracking-[0.18em] ${styles[status]}`}
    >
      <span className="size-1 rounded-full bg-current" />
      {status}
    </span>
  );
}

export function Cases() {
  return (
    <section className="border-b border-border/40 bg-background">
      <div className="mx-auto max-w-7xl px-6 py-24">
        <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div className="max-w-xl">
            <p className="text-xs uppercase tracking-[0.22em] text-brand">
              03 · Кто уже внутри
            </p>
            <h2 className="mt-4 text-balance text-4xl font-medium leading-[1.05] tracking-[-0.02em] sm:text-[44px]">
              Receptor готовится к первым живым пилотам.
            </h2>
          </div>
          <p className="max-w-sm text-[14px] leading-relaxed text-muted-foreground">
            Сначала подключаем одну-две точки, проверяем реальные цифры,
            ежедневный brief и copilot, потом масштабируем на сеть.
          </p>
        </div>

        <div className="mt-14 grid gap-6 md:grid-cols-3">
          {CASES.map((c) => {
            const inner = (
              <article className="group flex h-full flex-col rounded-xl border border-border/60 bg-card/55 p-8 transition-all hover:border-border hover:bg-card/90">
                <div className="flex items-center justify-between">
                  <StatusBadge status={c.status} />
                  <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                    {c.city}
                  </span>
                </div>
                <h3 className="mt-8 text-balance text-[24px] font-medium leading-[1.1] tracking-[-0.01em]">
                  {c.venue}
                </h3>
                <p className="mt-3 text-[14px] leading-relaxed text-muted-foreground">
                  {c.tagline}
                </p>
                <p className="numeric mt-auto pt-10 text-[22px] font-medium tracking-[-0.01em] text-foreground">
                  {c.metric}
                </p>
              </article>
            );

            if ("href" in c && c.href) {
              return (
                <Link key={c.venue} href={c.href} className="contents">
                  {inner}
                </Link>
              );
            }

            return <div key={c.venue}>{inner}</div>;
          })}
        </div>
      </div>
    </section>
  );
}
