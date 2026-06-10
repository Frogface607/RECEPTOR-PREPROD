"use client";

import { useRouter, usePathname, useSearchParams } from "next/navigation";
import { useCallback, useMemo, useState, type FormEvent } from "react";
import { Check, ChevronDown } from "lucide-react";
import { formatPeriodLabel, PERIOD_LABELS_RU } from "@/lib/venues/period";
import type { Period, PeriodType } from "@/lib/iiko/models";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

const ORDER: PeriodType[] = [
  "TODAY",
  "YESTERDAY",
  "CURRENT_WEEK",
  "LAST_WEEK",
  "CURRENT_MONTH",
  "LAST_MONTH",
];

export function PeriodSelector({ current }: { current: Period }) {
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();
  const lastYear = useMemo(() => new Date().getFullYear() - 1, []);
  const [from, setFrom] = useState(
    current.type === "CUSTOM" ? current.from : `${lastYear}-01-01`,
  );
  const [to, setTo] = useState(
    current.type === "CUSTOM" ? current.to : `${lastYear}-12-31`,
  );

  const onSelect = useCallback(
    (next: PeriodType) => {
      const sp = new URLSearchParams(params?.toString() ?? "");
      sp.set("period", next);
      if (next !== "CUSTOM") {
        sp.delete("from");
        sp.delete("to");
      }
      router.push(`${pathname}?${sp.toString()}`, { scroll: false });
    },
    [router, pathname, params],
  );

  const onCustomSubmit = useCallback(
    (event: FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      if (!from || !to || from > to) return;

      const sp = new URLSearchParams(params?.toString() ?? "");
      sp.set("period", "CUSTOM");
      sp.set("from", from);
      sp.set("to", to);
      router.push(`${pathname}?${sp.toString()}`, { scroll: false });
    },
    [from, to, router, pathname, params],
  );

  const onLastYearSelect = useCallback(() => {
    const nextFrom = `${lastYear}-01-01`;
    const nextTo = `${lastYear}-12-31`;
    setFrom(nextFrom);
    setTo(nextTo);

    const sp = new URLSearchParams(params?.toString() ?? "");
    sp.set("period", "CUSTOM");
    sp.set("from", nextFrom);
    sp.set("to", nextTo);
    router.push(`${pathname}?${sp.toString()}`, { scroll: false });
  }, [lastYear, router, pathname, params]);

  return (
    <DropdownMenu>
      <DropdownMenuTrigger className="group inline-flex items-center gap-2 rounded-lg border border-border/60 bg-card/60 px-3.5 py-2 text-sm text-foreground transition-colors hover:bg-card">
        <span className="text-muted-foreground text-[11px] uppercase tracking-[0.18em]">
          Период
        </span>
        <span className="font-medium">{formatPeriodLabel(current)}</span>
        <ChevronDown className="size-4 text-muted-foreground transition-transform group-data-[state=open]:rotate-180" />
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-72">
        <DropdownMenuLabel className="text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
          Пресеты
        </DropdownMenuLabel>
        {ORDER.map((p) => (
          <DropdownMenuItem key={p} onSelect={() => onSelect(p)}>
            <span className="flex-1">{PERIOD_LABELS_RU[p]}</span>
            {current.type === p ? <Check className="size-4 text-brand" /> : null}
          </DropdownMenuItem>
        ))}
        <DropdownMenuSeparator />
        <DropdownMenuItem onSelect={onLastYearSelect}>
          <span className="flex-1">Прошлый год ({lastYear})</span>
          {current.type === "CUSTOM" &&
          current.from === `${lastYear}-01-01` &&
          current.to === `${lastYear}-12-31` ? (
            <Check className="size-4 text-brand" />
          ) : null}
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <form className="space-y-3 px-2 py-2" onSubmit={onCustomSubmit}>
          <div className="grid grid-cols-2 gap-2">
            <label className="space-y-1">
              <span className="block text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
                С даты
              </span>
              <input
                type="date"
                value={from}
                onChange={(event) => setFrom(event.target.value)}
                className="h-9 w-full rounded-md border border-border/70 bg-background px-2 text-xs text-foreground outline-none transition-colors focus:border-brand"
              />
            </label>
            <label className="space-y-1">
              <span className="block text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
                По дату
              </span>
              <input
                type="date"
                value={to}
                onChange={(event) => setTo(event.target.value)}
                className="h-9 w-full rounded-md border border-border/70 bg-background px-2 text-xs text-foreground outline-none transition-colors focus:border-brand"
              />
            </label>
          </div>
          <button
            type="submit"
            disabled={!from || !to || from > to}
            className="h-9 w-full rounded-md bg-brand px-3 text-xs font-medium text-primary-foreground transition-colors hover:bg-brand-hover disabled:cursor-not-allowed disabled:opacity-45"
          >
            Показать период
          </button>
        </form>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
