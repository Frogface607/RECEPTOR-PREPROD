"use client";

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { formatRubles } from "@/lib/format";

type Point = { date: string; revenue: number };

function shortDate(iso: string): string {
  const d = new Date(iso + "T00:00:00Z");
  return d.toLocaleDateString("ru-RU", { day: "numeric", month: "short" });
}

function ChartTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: Array<{ value: number }>;
  label?: string;
}) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border border-border/80 bg-popover/95 px-3 py-2 shadow-xl backdrop-blur">
      <p className="text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
        {label ? shortDate(label) : ""}
      </p>
      <p className="numeric mt-1 font-mono text-sm text-foreground">
        {formatRubles(payload[0].value)}
      </p>
    </div>
  );
}

export function RevenueChart({ points }: { points: Point[] }) {
  return (
    <div className="rounded-xl border border-border/60 bg-card/55 p-6">
      <div className="flex items-baseline justify-between">
        <div>
          <p className="text-[11px] uppercase tracking-[0.2em] text-brand">
            Динамика выручки
          </p>
          <h3 className="mt-1 text-[18px] font-medium tracking-[-0.01em]">
            По дням
          </h3>
        </div>
        <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
          {points.length} точек
        </span>
      </div>

      <div className="mt-6 h-[260px] w-full sm:h-[280px]">
        <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
          <AreaChart
            data={points}
            margin={{ top: 8, right: 6, left: 0, bottom: 0 }}
          >
            <defs>
              <linearGradient id="rev-grad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="var(--chart-1)" stopOpacity={0.4} />
                <stop offset="100%" stopColor="var(--chart-1)" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid
              stroke="var(--border)"
              strokeOpacity={0.35}
              vertical={false}
            />
            <XAxis
              dataKey="date"
              tickFormatter={shortDate}
              stroke="var(--muted-foreground)"
              tick={{ fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              padding={{ left: 8, right: 8 }}
            />
            <YAxis
              tickFormatter={(v) =>
                v >= 1000 ? `${Math.round(v / 1000)}к` : `${v}`
              }
              stroke="var(--muted-foreground)"
              tick={{ fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              width={40}
            />
            <Tooltip
              content={<ChartTooltip />}
              cursor={{
                stroke: "var(--border)",
                strokeWidth: 1,
                strokeDasharray: "4 4",
              }}
            />
            <Area
              type="monotone"
              dataKey="revenue"
              stroke="var(--chart-1)"
              strokeWidth={2}
              fill="url(#rev-grad)"
              activeDot={{ r: 4, fill: "var(--chart-1)" }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
