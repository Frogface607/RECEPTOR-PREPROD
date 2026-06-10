import Link from "next/link";
import { Download, MessageSquare } from "lucide-react";
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
  const chatHref = `/dashboard/${venue.id}?period=${period}&chat=1`;

  return (
    <header className="static z-30 border-b border-border/40 bg-background/85 backdrop-blur-xl lg:sticky lg:top-0">
      <div className="flex flex-wrap items-center gap-x-4 gap-y-3 px-4 py-3 sm:px-6 lg:h-16 lg:flex-nowrap lg:py-0 lg:px-10">
        <div className="flex min-w-0 items-baseline gap-2 sm:gap-3">
          <h1 className="truncate text-[15px] font-medium text-foreground">
            {venue.name}
          </h1>
          <span className="whitespace-nowrap text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
            {venue.city} · {venue.type === "bar" ? "Бар" : venue.type}
          </span>
        </div>

        <div className="ml-auto flex items-center gap-2">
          <PeriodSelector current={period} />

          <a
            href={exportHref}
            download
            className="hidden md:inline-flex items-center gap-2 rounded-lg border border-border/60 bg-card/60 px-3.5 py-2 text-sm text-foreground transition-colors hover:bg-card"
            aria-label="Экспорт CSV"
          >
            <Download className="size-4 text-muted-foreground" />
            <span className="hidden lg:inline">Экспорт CSV</span>
          </a>

          <Link
            href={chatHref}
            scroll={false}
            replace
            className="inline-flex items-center gap-2 rounded-lg bg-brand px-3 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-brand-hover sm:px-4"
          >
            <MessageSquare className="size-4" />
            <span className="hidden sm:inline">Открыть Copilot</span>
            <span className="sm:hidden">Receptor</span>
          </Link>
        </div>
      </div>
    </header>
  );
}
