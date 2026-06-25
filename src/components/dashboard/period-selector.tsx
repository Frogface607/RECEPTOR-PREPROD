"use client";

import { useRouter, usePathname, useSearchParams } from "next/navigation";
import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type FormEvent,
} from "react";
import { Check, ChevronDown } from "lucide-react";
import { formatPeriodLabel, PERIOD_LABELS_RU } from "@/lib/venues/period";
import type { Period, PeriodType } from "@/lib/iiko/models";

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
  const rootRef = useRef<HTMLDivElement | null>(null);
  const [open, setOpen] = useState(false);
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
      setOpen(false);
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
      setOpen(false);
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
    setOpen(false);
    router.push(`${pathname}?${sp.toString()}`, { scroll: false });
  }, [lastYear, router, pathname, params]);

  useEffect(() => {
    if (!open) return;

    const onPointerDown = (event: PointerEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    };
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };

    document.addEventListener("pointerdown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("pointerdown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open]);

  return (
    <div ref={rootRef} className="relative inline-block text-left">
      <button
        type="button"
        aria-haspopup="dialog"
        aria-expanded={open}
        onClick={() => setOpen((value) => !value)}
        className="group inline-flex items-center gap-2 rounded-lg border border-border/60 bg-card/60 px-3.5 py-2 text-sm text-foreground transition-colors hover:bg-card"
      >
        <span className="text-muted-foreground text-[11px] uppercase tracking-[0.18em]">
          Период
        </span>
        <span className="font-medium">{formatPeriodLabel(current)}</span>
        <ChevronDown
          className={
            "size-4 text-muted-foreground transition-transform " +
            (open ? "rotate-180" : "")
          }
        />
      </button>

      {open ? (
        <div
          role="dialog"
          aria-label="Выбор периода"
          className="absolute right-0 top-full z-50 mt-2 w-72 rounded-lg border border-border/60 bg-popover p-1 text-popover-foreground shadow-xl ring-1 ring-foreground/10"
        >
          <p className="px-2 py-1.5 text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
            Пресеты
          </p>
          <div className="grid gap-0.5">
            {ORDER.map((p) => (
              <button
                key={p}
                type="button"
                onClick={() => onSelect(p)}
                className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-sm text-foreground outline-none transition-colors hover:bg-accent hover:text-accent-foreground focus-visible:bg-accent"
              >
                <span className="flex-1">{PERIOD_LABELS_RU[p]}</span>
                {current.type === p ? (
                  <Check className="size-4 text-brand" />
                ) : null}
              </button>
            ))}
          </div>
          <div className="-mx-1 my-1 h-px bg-border" />
          <button
            type="button"
            onClick={onLastYearSelect}
            className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-sm text-foreground outline-none transition-colors hover:bg-accent hover:text-accent-foreground focus-visible:bg-accent"
          >
            <span className="flex-1">Прошлый год ({lastYear})</span>
            {current.type === "CUSTOM" &&
            current.from === `${lastYear}-01-01` &&
            current.to === `${lastYear}-12-31` ? (
              <Check className="size-4 text-brand" />
            ) : null}
          </button>
          <div className="-mx-1 my-1 h-px bg-border" />
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
        </div>
      ) : null}
    </div>
  );
}
