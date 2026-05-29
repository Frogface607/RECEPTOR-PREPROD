import { Download, Sparkles } from "lucide-react";
import { PeriodSelector } from "./period-selector";
import type { ResolvedVenue } from "@/lib/venues/get-venue";
import type { PeriodType } from "@/lib/iiko/models";

export function DashboardHeader({
  venue,
  period,
}: {
  venue: ResolvedVenue;
  period: PeriodType;
}) {
  const exportHref = `/api/export/dishes?venueId=${venue.id}&period=${period}`;

  return (
    <header className="sticky top-0 z-30 border-b border-border/40 bg-background/85 backdrop-blur-xl">
      <div className="flex h-16 items-center gap-4 px-6 lg:px-10">
        <div className="flex items-baseline gap-3">
          <h1 className="text-[15px] font-medium text-foreground">{venue.name}</h1>
          <span className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
            {venue.city} · {venue.type === "bar" ? "Бар" : venue.type}
          </span>
          <span className="hidden font-mono text-[10px] uppercase tracking-widest text-[color:var(--iiko)] md:inline">
            · iiko {venue.iiko.channel === "cloud" ? "Cloud" : "RMS"} connected
          </span>
        </div>

        <div className="ml-auto flex items-center gap-2">
          <PeriodSelector current={period} />

          <a
            href={exportHref}
            download
            className="hidden md:inline-flex items-center gap-2 rounded-lg border border-border/60 bg-card/60 px-3.5 py-2 text-sm text-foreground transition-colors hover:bg-card"
          >
            <Download className="size-4 text-muted-foreground" />
            Экспорт CSV
          </a>

          <button
            type="button"
            className="inline-flex items-center gap-2 rounded-lg bg-brand px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-brand-hover"
          >
            <Sparkles className="size-4" />
            Спросить Receptor
          </button>
        </div>
      </div>
    </header>
  );
}
