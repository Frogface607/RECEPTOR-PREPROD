import { AlertTriangle, CheckCircle2, ReceiptText } from "lucide-react";
import { MarginMappingWorkspace } from "./margin-mapping-actions";
import type { Product } from "@/lib/iiko/models";
import { formatInteger, formatRubles } from "@/lib/format";
import type {
  MenuMarginBlocker,
  MenuMarginReadiness,
} from "@/lib/menu-margin-readiness";

const STATUS_COPY = {
  ready: {
    title: "Техкарты готовы к проверке маржи",
    detail: "Связи и цены есть по ключевым позициям. Можно искать слабую маржу.",
    className: "border-brand/35 bg-brand/10 text-brand",
  },
  partial: {
    title: "Нужно закрыть связи и себестоимость",
    detail: "Сначала связываем блюда с iiko, потом проверяем позиции без цены.",
    className: "border-amber-400/35 bg-amber-400/10 text-amber-200",
  },
  blocked: {
    title: "Маржа пока не считается",
    detail: "Нет достаточной связки между продажами и номенклатурой iiko.",
    className: "border-destructive/35 bg-destructive/10 text-destructive",
  },
} as const;

export function MarginReadinessCard({
  venueId,
  readiness,
  error,
  products = [],
}: {
  venueId: string;
  readiness: MenuMarginReadiness;
  error: string | null;
  products?: Product[];
}) {
  const copy = STATUS_COPY[readiness.status];
  const topBlockers = readiness.topBlockers.slice(0, 3);

  return (
    <section className="rounded-xl border border-border/60 bg-card/50 p-5 sm:p-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex min-w-0 items-start gap-4">
          <div className="flex size-10 shrink-0 items-center justify-center rounded-lg border border-border/60 bg-background/45 text-brand">
            <ReceiptText className="size-5" />
          </div>
          <div className="min-w-0">
            <p className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
              Техкарты и маржа
            </p>
            <h2 className="mt-2 text-xl font-medium leading-tight text-foreground">
              {copy.title}
            </h2>
            <p className="mt-2 max-w-2xl text-[13px] leading-relaxed text-muted-foreground">
              {error ?? copy.detail}
            </p>
          </div>
        </div>

        <span
          className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-[11px] uppercase tracking-[0.14em] ${copy.className}`}
        >
          {readiness.status === "ready" ? (
            <CheckCircle2 className="size-3.5" />
          ) : (
            <AlertTriangle className="size-3.5" />
          )}
          {readiness.costCoveragePct}% с ценой
        </span>
      </div>

      {topBlockers.length > 0 ? (
        <div className="mt-5 border-y border-border/45 py-4">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
                Сначала закрыть
              </p>
              <h3 className="mt-1 text-base font-medium text-foreground">
                Топ-позиции без доказанной себестоимости
              </h3>
            </div>
            <p className="max-w-md text-xs leading-relaxed text-muted-foreground">
              Эти блюда сильнее всего искажают прибыльность периода.
            </p>
          </div>

          <div className="mt-3 grid gap-2 sm:grid-cols-3">
            <MarginDebtMetric
              label="Не покрыто выручки"
              value={`${readiness.blockedRevenuePct}%`}
              detail={formatRubles(readiness.blockedRevenue)}
            />
            <MarginDebtMetric
              label="Нет связи"
              value={formatRubles(readiness.missingLinkRevenue)}
              detail="связать блюда с iiko"
            />
            <MarginDebtMetric
              label="Нет цены RMS"
              value={formatRubles(readiness.missingCostRevenue)}
              detail="проверить закупочные цены"
            />
          </div>

          <div className="mt-3 grid gap-2 lg:grid-cols-3">
            {topBlockers.map((item) => (
              <MarginBlockerCard
                key={`${item.dishGroup}-${item.dishName}`}
                item={item}
              />
            ))}
          </div>
        </div>
      ) : null}

      <MarginMappingWorkspace
        venueId={venueId}
        readiness={readiness}
        products={products}
      />
    </section>
  );
}

function MarginDebtMetric({
  label,
  value,
  detail,
}: {
  label: string;
  value: string;
  detail: string;
}) {
  return (
    <div className="rounded-lg border border-border/40 bg-card/25 px-3 py-2">
      <p className="text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
        {label}
      </p>
      <p className="numeric mt-1 text-base font-medium text-foreground">{value}</p>
      <p className="mt-1 truncate text-[11px] text-muted-foreground">{detail}</p>
    </div>
  );
}

function reasonLabel(reason: MenuMarginBlocker["reason"]): string {
  if (reason === "missing-cost") return "нет закупочной цены";
  return "нужна связь с iiko";
}

function MarginBlockerCard({ item }: { item: MenuMarginBlocker }) {
  return (
    <div className="rounded-lg border border-border/45 bg-background/30 p-3">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="truncate text-[13px] font-medium text-foreground">
            {item.dishName}
          </p>
          <p className="mt-1 text-[11px] text-muted-foreground">
            {item.dishGroup} · {formatInteger(item.amount)} порц.
          </p>
        </div>
        <span className="shrink-0 rounded-md border border-amber-400/35 bg-amber-400/10 px-2 py-1 text-[10px] uppercase tracking-[0.12em] text-amber-200">
          {reasonLabel(item.reason)}
        </span>
      </div>
      <p className="numeric mt-3 text-lg font-medium text-foreground">
        {formatRubles(item.revenue)}
      </p>
      <p className="mt-1 truncate text-[11px] text-muted-foreground">
        {item.productName ?? "товар не выбран"}
      </p>
    </div>
  );
}
