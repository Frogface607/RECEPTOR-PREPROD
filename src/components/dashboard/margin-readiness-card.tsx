import { AlertTriangle, CheckCircle2, ReceiptText } from "lucide-react";
import { MarginMappingWorkspace } from "./margin-mapping-actions";
import type { Product } from "@/lib/iiko/models";
import type { MenuMarginReadiness } from "@/lib/menu-margin-readiness";

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

      <MarginMappingWorkspace
        venueId={venueId}
        readiness={readiness}
        products={products}
      />
    </section>
  );
}
