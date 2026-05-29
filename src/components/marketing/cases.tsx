import Link from "next/link";

const CASES = [
  {
    venue: "Edison Bar",
    city: "Иркутск",
    status: "Live demo" as const,
    tagline: "Крафтовый бар, 9.5 лет работы. Демо-аккаунт Receptor.",
    metric: "₽4.7 млн / 30 дней",
    href: "/dashboard/edison-demo",
  },
  {
    venue: "Сергей Михно",
    city: "Кафе, Иркутск",
    status: "Pilot" as const,
    tagline: "Пилот №1. ₽19 900 setup + 3 месяца Pro бесплатно.",
    metric: "Подключение на этой неделе",
  },
  {
    venue: "Coming soon",
    city: "—",
    status: "Open" as const,
    tagline: "Слот для второго пилота. Свяжись, если хочешь раннюю цену.",
    metric: "Места: 2 из 3",
    href: "mailto:bro@frogface.space?subject=Receptor%20pilot",
  },
] as const;

type Case = (typeof CASES)[number];

function StatusBadge({ status }: { status: Case["status"] }) {
  const styles: Record<Case["status"], string> = {
    "Live demo": "bg-brand/15 text-brand border-brand/40",
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
              Три места — три истории. Receptor{" "}
              <span className="font-display italic text-brand">не для всех.</span>
            </h2>
          </div>
          <p className="max-w-sm text-[14px] leading-relaxed text-muted-foreground">
            Мы берём в пилот один или два ресторана за раз — чтобы заметить,
            подкрутить и не сломать.
          </p>
        </div>

        <div className="mt-14 grid gap-6 md:grid-cols-3">
          {CASES.map((c) => {
            const inner = (
              <article className="group flex h-full flex-col rounded-2xl border border-border/60 bg-card/60 p-8 transition-all hover:border-border hover:bg-card/95">
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
                <p className="numeric mt-auto pt-10 font-display text-[22px] italic text-foreground">
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
