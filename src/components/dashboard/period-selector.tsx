"use client";

import { useRouter, usePathname, useSearchParams } from "next/navigation";
import { useCallback } from "react";
import { Check, ChevronDown } from "lucide-react";
import { PERIOD_LABELS_RU } from "@/lib/venues/period";
import type { PeriodType } from "@/lib/iiko/models";
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

export function PeriodSelector({ current }: { current: PeriodType }) {
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();

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

  return (
    <DropdownMenu>
      <DropdownMenuTrigger className="group inline-flex items-center gap-2 rounded-lg border border-border/60 bg-card/60 px-3.5 py-2 text-sm text-foreground transition-colors hover:bg-card">
        <span className="text-muted-foreground text-[11px] uppercase tracking-[0.18em]">
          Период
        </span>
        <span className="font-medium">{PERIOD_LABELS_RU[current]}</span>
        <ChevronDown className="size-4 text-muted-foreground transition-transform group-data-[state=open]:rotate-180" />
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56">
        <DropdownMenuLabel className="text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
          Пресеты
        </DropdownMenuLabel>
        {ORDER.map((p) => (
          <DropdownMenuItem key={p} onSelect={() => onSelect(p)}>
            <span className="flex-1">{PERIOD_LABELS_RU[p]}</span>
            {current === p ? <Check className="size-4 text-brand" /> : null}
          </DropdownMenuItem>
        ))}
        <DropdownMenuSeparator />
        <DropdownMenuItem disabled className="text-muted-foreground">
          Произвольный диапазон ·{" "}
          <span className="text-[10px] uppercase tracking-widest">скоро</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
