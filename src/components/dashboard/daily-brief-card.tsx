import { ExternalLink, Sparkles, TrendingDown, TrendingUp } from "lucide-react";
import { formatRubles } from "@/lib/format";
import type { DailyBrief } from "@/lib/brief/daily-brief";
import { SendBriefButton } from "./send-brief-button";

export function DailyBriefCard({
  brief,
  venueId,
}: {
  brief: DailyBrief;
  venueId: string;
}) {
  const isDown = brief.revenue.deltaPct < 0;
  const DeltaIcon = isDown ? TrendingDown : TrendingUp;
  const textBriefHref = `/api/brief?venueId=${encodeURIComponent(venueId)}&period=${brief.period}&format=text`;

  return (
    <section className="rounded-2xl border border-border/60 bg-card/55 p-5 sm:p-6">
      <div className="flex flex-wrap items-start gap-4">
        <div className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-brand/15 text-brand">
          <Sparkles className="size-5" />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
              Daily Brief
            </p>
            <div className="flex flex-wrap items-center gap-2">
              <SendBriefButton venueId={venueId} period={brief.period} />
              <a
                href={textBriefHref}
                target="_blank"
                rel="noreferrer"
                className="inline-flex h-7 items-center gap-1 rounded-lg border border-border/60 bg-background/50 px-2.5 text-[0.8rem] font-medium text-foreground/80 transition hover:border-brand/50 hover:text-foreground"
              >
                <ExternalLink className="size-3.5" />
                Текст
              </a>
            </div>
          </div>
          <h2 className="mt-2 text-xl font-medium leading-tight tracking-[-0.01em] text-foreground">
            {brief.headline}
          </h2>
          <div className="mt-3 inline-flex items-center gap-2 rounded-lg border border-border/50 bg-background/50 px-3 py-1.5 text-[12px] text-muted-foreground">
            <DeltaIcon
              className={
                "size-3.5 " + (isDown ? "text-destructive" : "text-brand")
              }
            />
            <span className="font-mono">
              {brief.revenue.deltaPct > 0 ? "+" : ""}
              {brief.revenue.deltaPct}%
            </span>
            <span>к сравнению</span>
            <span className="font-mono">
              {formatRubles(brief.revenue.previous)}
            </span>
          </div>
        </div>
      </div>

      <div className="mt-6 grid gap-5 lg:grid-cols-2">
        <div>
          <p className="mb-3 text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
            Что важно
          </p>
          <ul className="space-y-2.5 text-[13px] leading-relaxed text-foreground/85">
            {brief.highlights.map((item) => (
              <li key={item} className="rounded-lg bg-background/35 px-3 py-2">
                {item}
              </li>
            ))}
          </ul>
        </div>

        <div>
          <p className="mb-3 text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
            Что сделать сегодня
          </p>
          <ol className="space-y-2.5 text-[13px] leading-relaxed text-foreground/85">
            {brief.actions.map((item, index) => (
              <li
                key={item}
                className="flex gap-3 rounded-lg bg-background/35 px-3 py-2"
              >
                <span className="font-mono text-[11px] text-brand">
                  {index + 1}
                </span>
                <span>{item}</span>
              </li>
            ))}
          </ol>
        </div>
      </div>
    </section>
  );
}
