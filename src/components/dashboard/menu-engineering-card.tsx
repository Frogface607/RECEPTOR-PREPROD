import { BarChart3, ChefHat, CircleDollarSign, TriangleAlert } from "lucide-react";
import { formatInteger, formatRubles } from "@/lib/format";
import {
  buildMenuEngineering,
  type MenuEngineeringItem,
} from "@/lib/menu-engineering";
import type { DishStat } from "@/lib/iiko/models";

export function MenuEngineeringCard({ dishes }: { dishes: DishStat[] }) {
  const report = buildMenuEngineering(dishes);
  const focusItems = [
    { label: "A", title: "Ядро выручки", items: report.aItems },
    { label: "B", title: "Кандидаты", items: report.bItems },
    { label: "C", title: "Хвост меню", items: report.cItems },
  ];

  return (
    <section className="rounded-xl border border-border/60 bg-card/50 p-5 sm:p-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex items-start gap-4">
          <div className="flex size-10 shrink-0 items-center justify-center rounded-lg border border-border/60 bg-background/45 text-brand">
            <BarChart3 className="size-5" />
          </div>
          <div>
            <p className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
              Menu intelligence
            </p>
            <h2 className="mt-2 text-xl font-medium leading-tight tracking-[-0.01em] text-foreground">
              ABC-карта блюд для шефа и владельца
            </h2>
            <p className="mt-2 max-w-2xl text-[14px] leading-relaxed text-muted-foreground">
              {report.marginCaveat}
            </p>
          </div>
        </div>
        <div className="rounded-lg border border-border/60 bg-background/45 px-3 py-2 text-right">
          <p className="font-mono text-[15px] text-foreground">
            {report.aRevenueShare.toFixed(1)}%
          </p>
          <p className="text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
            дают A-позиции
          </p>
        </div>
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-3">
        {focusItems.map((group) => (
          <AbcColumn
            key={group.label}
            label={group.label}
            title={group.title}
            items={group.items}
          />
        ))}
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-3">
        <Signal
          icon={CircleDollarSign}
          title="Главный денежный якорь"
          value={report.hero?.dishName ?? "Нет данных"}
          detail={
            report.hero
              ? `${formatRubles(report.hero.dishSumInt)} · ${formatInteger(report.hero.dishAmountInt)} порций`
              : "Нужны продажи из iiko"
          }
        />
        <Signal
          icon={TriangleAlert}
          title="Ловушка объёма"
          value={report.volumeTrap?.dishName ?? "Не выявлена"}
          detail={
            report.volumeTrap
              ? `${report.volumeTrap.amountShare.toFixed(1)}% порций при ${report.volumeTrap.revenueShare.toFixed(1)}% выручки`
              : "Появится при перекосе количества и выручки"
          }
        />
        <Signal
          icon={ChefHat}
          title="Повестка шефу"
          value={`${report.actions.length} действия`}
          detail="Проверка маржи, апсейла и C-хвоста без ручной таблицы"
        />
      </div>

      <ol className="mt-6 grid gap-3 lg:grid-cols-3">
        {report.actions.map((action, index) => (
          <li
            key={action}
            className="flex gap-3 rounded-lg bg-background/35 px-3 py-2 text-[13px] leading-relaxed text-foreground/85"
          >
            <span className="font-mono text-[11px] text-brand">{index + 1}</span>
            <span>{action}</span>
          </li>
        ))}
      </ol>
    </section>
  );
}

function AbcColumn({
  label,
  title,
  items,
}: {
  label: string;
  title: string;
  items: MenuEngineeringItem[];
}) {
  return (
    <div className="rounded-lg border border-border/45 bg-background/30 p-3">
      <div className="mb-3 flex items-center justify-between gap-3">
        <div>
          <p className="font-mono text-[15px] text-brand">{label}</p>
          <p className="text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
            {title}
          </p>
        </div>
        <span className="rounded-md border border-border/50 bg-card/50 px-2 py-0.5 font-mono text-[11px] text-muted-foreground">
          {items.length}
        </span>
      </div>
      <ul className="space-y-2">
        {items.slice(0, 3).map((item) => (
          <li key={item.dishName} className="min-w-0">
            <div className="flex items-center justify-between gap-3">
              <span className="min-w-0 truncate text-[13px] text-foreground/90">
                {item.dishName}
              </span>
              <span className="shrink-0 font-mono text-[11px] text-muted-foreground">
                {item.revenueShare.toFixed(1)}%
              </span>
            </div>
            <p className="mt-0.5 truncate text-[11px] text-muted-foreground">
              {item.dishGroup}
            </p>
          </li>
        ))}
        {!items.length ? (
          <li className="text-[12px] leading-relaxed text-muted-foreground">
            Появится после первой выгрузки продаж.
          </li>
        ) : null}
      </ul>
    </div>
  );
}

function Signal({
  icon: Icon,
  title,
  value,
  detail,
}: {
  icon: typeof BarChart3;
  title: string;
  value: string;
  detail: string;
}) {
  return (
    <div className="rounded-lg bg-background/35 px-3 py-3">
      <div className="flex items-center gap-2 text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
        <Icon className="size-3.5 text-brand" />
        {title}
      </div>
      <p className="mt-2 truncate text-[14px] font-medium text-foreground">
        {value}
      </p>
      <p className="mt-1 text-[12px] leading-relaxed text-muted-foreground">
        {detail}
      </p>
    </div>
  );
}
