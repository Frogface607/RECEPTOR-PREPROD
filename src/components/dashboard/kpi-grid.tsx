import { formatRubles, formatInteger } from "@/lib/format";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";

type Kpi = {
  label: string;
  value: string;
  delta?: { value: string; direction: "up" | "down" | "flat" };
  hint?: string;
};

function DeltaPill({ delta }: { delta: Kpi["delta"] }) {
  if (!delta) return null;
  const tone =
    delta.direction === "up"
      ? "text-brand"
      : delta.direction === "down"
        ? "text-destructive"
        : "text-muted-foreground";
  const Icon =
    delta.direction === "up"
      ? TrendingUp
      : delta.direction === "down"
        ? TrendingDown
        : Minus;
  return (
    <span className={`inline-flex items-center gap-1 text-[12px] ${tone}`}>
      <Icon className="size-3.5" />
      <span className="numeric font-mono">{delta.value}</span>
    </span>
  );
}

export function KpiGrid({
  revenue,
  averageCheck,
  itemsSold,
  uniqueDishes,
  periodLabel,
}: {
  revenue: number;
  averageCheck: number;
  itemsSold: number;
  uniqueDishes: number;
  periodLabel: string;
}) {
  const items: Kpi[] = [
    {
      label: "Выручка",
      value: formatRubles(revenue),
      delta: { value: "+8.2%", direction: "up" },
      hint: periodLabel,
    },
    {
      label: "Средний чек",
      value: formatRubles(averageCheck),
      delta: { value: "+2.1%", direction: "up" },
      hint: "По чекам периода",
    },
    {
      label: "Позиций продано",
      value: formatInteger(itemsSold),
      delta: { value: "+5.9%", direction: "up" },
      hint: "По всем сменам",
    },
    {
      label: "Уникальных блюд",
      value: formatInteger(uniqueDishes),
      delta: { value: "−2", direction: "down" },
      hint: "Активный SKU",
    },
  ];

  return (
    <div className="grid gap-px overflow-hidden rounded-2xl border border-border/60 bg-border/40 sm:grid-cols-2 xl:grid-cols-4">
      {items.map((k) => (
        <div
          key={k.label}
          className="flex flex-col justify-between gap-6 bg-card/60 p-6 transition-colors hover:bg-card/95"
        >
          <div className="flex items-start justify-between">
            <p className="text-[11px] uppercase tracking-[0.2em] text-muted-foreground">
              {k.label}
            </p>
            <DeltaPill delta={k.delta} />
          </div>
          <div>
            <p className="numeric font-display text-[40px] leading-none tracking-[-0.02em] text-foreground">
              {k.value}
            </p>
            <p className="mt-3 text-[12px] text-muted-foreground">{k.hint}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
