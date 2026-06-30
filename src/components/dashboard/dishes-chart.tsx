"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { formatRubles } from "@/lib/format";

type Dish = {
  dishName: string;
  dishGroup: string;
  dishSumInt: number;
  dishAmountInt: number;
};

const CATEGORY_COLOR: Record<string, string> = {
  "Горячая кухня": "var(--chart-1)",
  "Закуски и салаты": "var(--chart-2)",
  "Барная карта": "var(--chart-3)",
  Десерты: "var(--chart-5)",
  "Безалкогольные напитки": "var(--chart-4)",
};

function ChartTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: Array<{ payload: Dish }>;
}) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className="rounded-lg border border-border/80 bg-popover/95 px-3 py-2 shadow-xl backdrop-blur">
      <p className="text-[13px] font-medium text-foreground">{d.dishName}</p>
      <p className="text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
        {d.dishGroup}
      </p>
      <p className="numeric mt-1 font-mono text-sm text-foreground">
        {formatRubles(d.dishSumInt)}
      </p>
      <p className="text-[11px] text-muted-foreground">
        {d.dishAmountInt} порций
      </p>
    </div>
  );
}

export function DishesChart({ dishes }: { dishes: Dish[] }) {
  const data = dishes.slice(0, 10);
  return (
    <div className="rounded-xl border border-border/60 bg-card/55 p-6">
      <div className="flex items-baseline justify-between">
        <div>
          <p className="text-[11px] uppercase tracking-[0.2em] text-brand">
            Топ-{data.length} блюд
          </p>
          <h3 className="mt-1 text-[18px] font-medium tracking-[-0.01em]">
            По выручке
          </h3>
        </div>
        <span className="hidden font-mono text-[10px] uppercase tracking-widest text-muted-foreground sm:inline">
          iiko OLAP
        </span>
      </div>

      <div className="mt-6 h-[420px] w-full">
        <ResponsiveContainer width="100%" height="100%" minWidth={1} minHeight={1}>
          <BarChart
            data={data}
            layout="vertical"
            margin={{ top: 4, right: 16, left: 0, bottom: 0 }}
          >
            <CartesianGrid
              stroke="var(--border)"
              strokeOpacity={0.3}
              horizontal={false}
            />
            <XAxis
              type="number"
              tickFormatter={(v) =>
                v >= 1000 ? `${Math.round(v / 1000)}к` : `${v}`
              }
              stroke="var(--muted-foreground)"
              tick={{ fontSize: 11 }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              type="category"
              dataKey="dishName"
              stroke="var(--muted-foreground)"
              tick={{ fontSize: 12, fill: "var(--foreground)" }}
              axisLine={false}
              tickLine={false}
              width={170}
            />
            <Tooltip
              content={<ChartTooltip />}
              cursor={{ fill: "var(--accent)", fillOpacity: 0.25 }}
            />
            <Bar dataKey="dishSumInt" radius={[0, 6, 6, 0]}>
              {data.map((d) => (
                <Cell
                  key={d.dishName}
                  fill={CATEGORY_COLOR[d.dishGroup] ?? "var(--chart-1)"}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
