"use client";

import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { formatRubles } from "@/lib/format";

type Cat = { categoryName: string; dishSumInt: number };

const CATEGORY_COLOR: Record<string, string> = {
  Бургеры: "var(--chart-1)",
  "Крафтовое пиво": "var(--chart-2)",
  "Авторские коктейли": "var(--chart-3)",
  Закуски: "var(--chart-4)",
  Десерты: "var(--chart-5)",
};

function ChartTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: Array<{ payload: Cat; value: number }>;
}) {
  if (!active || !payload?.length) return null;
  const p = payload[0];
  return (
    <div className="rounded-lg border border-border/80 bg-popover/95 px-3 py-2 shadow-xl backdrop-blur">
      <p className="text-[13px] font-medium text-foreground">
        {p.payload.categoryName}
      </p>
      <p className="numeric mt-1 font-mono text-sm text-foreground">
        {formatRubles(p.value)}
      </p>
    </div>
  );
}

export function CategoriesChart({ categories }: { categories: Cat[] }) {
  const total = categories.reduce((s, c) => s + c.dishSumInt, 0);

  return (
    <div className="rounded-xl border border-border/60 bg-card/55 p-6">
      <div className="flex items-baseline justify-between">
        <div>
          <p className="text-[11px] uppercase tracking-[0.2em] text-brand">
            Категории
          </p>
          <h3 className="mt-1 text-[18px] font-medium tracking-[-0.01em]">
            Продажи по группам меню
          </h3>
        </div>
        <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
          {categories.length} категорий
        </span>
      </div>

      <div className="mt-6 grid min-w-0 items-center gap-6 xl:grid-cols-2">
        <div className="h-[230px] w-full min-w-0 sm:h-[250px] xl:h-[260px]">
          <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
            <PieChart>
              <Pie
                data={categories}
                dataKey="dishSumInt"
                nameKey="categoryName"
                innerRadius={58}
                outerRadius={96}
                paddingAngle={2}
                stroke="var(--card)"
                strokeWidth={3}
              >
                {categories.map((c) => (
                  <Cell
                    key={c.categoryName}
                    fill={CATEGORY_COLOR[c.categoryName] ?? "var(--chart-1)"}
                  />
                ))}
              </Pie>
              <Tooltip content={<ChartTooltip />} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <ul className="min-w-0 space-y-3">
          {categories.map((c) => {
            const share = total > 0 ? (c.dishSumInt / total) * 100 : 0;
            return (
              <li
                key={c.categoryName}
                className="flex items-center gap-2.5 border-b border-border/30 pb-3 last:border-b-0 last:pb-0"
              >
                <span
                  className="size-2.5 rounded-full"
                  style={{
                    backgroundColor:
                      CATEGORY_COLOR[c.categoryName] ?? "var(--chart-1)",
                  }}
                />
                <span className="min-w-0 flex-1 truncate text-[14px] text-foreground/90">
                  {c.categoryName}
                </span>
                <span className="numeric shrink-0 font-mono text-[12px] text-muted-foreground">
                  {share.toFixed(1)}%
                </span>
                <span className="numeric w-[86px] shrink-0 text-right font-mono text-[13px] text-foreground">
                  {formatRubles(c.dishSumInt)}
                </span>
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
}
