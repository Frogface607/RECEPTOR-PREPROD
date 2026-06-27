"use client";

import { useActionState, useMemo, useState } from "react";
import {
  Check,
  CircleDollarSign,
  Filter,
  Link2,
  Search,
  TriangleAlert,
} from "lucide-react";
import {
  saveAutoMenuItemMappingsStateAction,
  saveMenuItemMappingStateAction,
  type MenuMappingActionState,
} from "@/app/dashboard/[venueId]/menu-mapping-actions";
import { formatInteger, formatRubles } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { Product } from "@/lib/iiko/models";
import { getProductCostReference } from "@/lib/menu-margin-readiness";
import type {
  MenuMarginItem,
  MenuMarginReadiness,
} from "@/lib/menu-margin-readiness";

const INITIAL_STATE: MenuMappingActionState = { ok: false, message: "" };
const PAGE_SIZE = 10;

type MappingFilter = "todo" | "noCost" | "matched" | "all";

const FILTERS: Array<{ id: MappingFilter; label: string }> = [
  { id: "todo", label: "Требуют связи" },
  { id: "noCost", label: "Без цены" },
  { id: "matched", label: "Связано" },
  { id: "all", label: "Все" },
];

export function MarginMappingWorkspace({
  venueId,
  readiness,
  products,
}: {
  venueId: string;
  readiness: MenuMarginReadiness;
  products: Product[];
}) {
  const [filter, setFilter] = useState<MappingFilter>(() =>
    initialFilter(readiness.items),
  );
  const [query, setQuery] = useState("");
  const [limit, setLimit] = useState(PAGE_SIZE);
  const activeProducts = useMemo(
    () => products.filter((product) => product.active !== false),
    [products],
  );
  const autoItems = useMemo(
    () =>
      readiness.items.filter(
        (item) => item.product && item.match !== "manual",
      ),
    [readiness.items],
  );
  const filteredItems = useMemo(
    () => filterItems(readiness.items, filter, query),
    [readiness.items, filter, query],
  );
  const visibleItems = filteredItems.slice(0, limit);
  const hasLinkedItemsWithoutCost =
    readiness.matchedDishes > 0 && readiness.costedDishes === 0;

  return (
    <div
      id="margin-mapping-workspace"
      className="mt-5 scroll-mt-24 overflow-hidden rounded-lg border border-border/45 bg-background/25"
    >
      <div className="grid gap-2 border-b border-border/40 p-2 lg:grid-cols-[1fr_auto] lg:items-center">
        <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
          <Metric
            label="Связано"
            value={`${readiness.matchedDishes}/${readiness.totalDishes}`}
            detail={`${readiness.matchCoveragePct}% топа`}
          />
          <Metric
            label="С ценой"
            value={`${readiness.costedDishes}/${readiness.totalDishes}`}
            detail={`${readiness.costCoveragePct}% топа`}
          />
          <Metric
            label="Покрытая выручка"
            value={`${readiness.revenueCoveragePct}%`}
            detail={formatRubles(readiness.revenueWithCost)}
          />
          <Metric
            label="Техкарты"
            value={`${readiness.usableTechCardDishes}/${readiness.totalDishes}`}
            detail={`${readiness.usableTechCardCoveragePct}% состава`}
          />
        </div>

        <AutoMappingAction venueId={venueId} items={autoItems} />
      </div>

      {hasLinkedItemsWithoutCost && readiness.usableTechCardDishes > 0 ? (
        <div className="border-b border-border/40 px-3 py-2 text-[12px] leading-relaxed text-muted-foreground">
          Техкарты найдены для {readiness.usableTechCardDishes} позиций.
          Закупочные цены ингредиентов пока не пришли из RMS, поэтому маржа еще
          не считается.
        </div>
      ) : null}

      {hasLinkedItemsWithoutCost && readiness.usableTechCardDishes === 0 ? (
        <div className="border-b border-border/40 px-3 py-2 text-[12px] leading-relaxed text-muted-foreground">
          Связи с iiko сохранены. Закупочные цены пока не пришли из RMS, поэтому
          маржа не считается: нужно проверить права/endpoint себестоимости в
          диагностике iiko.
        </div>
      ) : null}

      <div className="grid gap-2 border-b border-border/40 p-2 xl:grid-cols-[1fr_auto] xl:items-center">
        <label className="relative block">
          <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <input
            value={query}
            onChange={(event) => {
              setQuery(event.target.value);
              setLimit(PAGE_SIZE);
            }}
            placeholder="Найти блюдо, товар или артикул"
            className="h-9 w-full rounded-lg border border-border/60 bg-background/70 pl-9 pr-3 text-sm text-foreground outline-none transition-colors placeholder:text-muted-foreground/60 focus:border-brand/60"
          />
        </label>

        <div className="flex flex-wrap items-center gap-2">
          <span className="inline-flex h-7 items-center gap-1.5 text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
            <Filter className="size-3.5" />
            Фильтр
          </span>
          {FILTERS.map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => {
                setFilter(item.id);
                setLimit(PAGE_SIZE);
              }}
              className={cn(
                "h-7 rounded-lg border px-2.5 text-[12px] transition-colors",
                filter === item.id
                  ? "border-brand/50 bg-brand/12 text-brand"
                  : "border-border/50 bg-background/35 text-muted-foreground hover:text-foreground",
              )}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>

      <div className="divide-y divide-border/35">
        {visibleItems.length > 0 ? (
          visibleItems.map((item) => (
            <MappingRow
              key={`${item.dishGroup}-${item.dishName}`}
              venueId={venueId}
              item={item}
              products={activeProducts}
            />
          ))
        ) : (
          <div className="p-6 text-sm text-muted-foreground">
            По этому фильтру пока пусто.
          </div>
        )}
      </div>

      {filteredItems.length > visibleItems.length ? (
        <div className="border-t border-border/35 p-3">
          <button
            type="button"
            onClick={() => setLimit((value) => value + PAGE_SIZE)}
            className="h-9 rounded-lg border border-border/55 bg-background/35 px-3 text-sm text-foreground transition-colors hover:bg-muted/35"
          >
            Показать еще {Math.min(PAGE_SIZE, filteredItems.length - visibleItems.length)}
          </button>
        </div>
      ) : null}
    </div>
  );
}

function Metric({
  label,
  value,
  detail,
}: {
  label: string;
  value: string;
  detail: string;
}) {
  return (
    <div className="rounded-lg border border-border/40 bg-card/30 px-3 py-2">
      <p className="text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
        {label}
      </p>
      <div className="mt-1 flex items-baseline gap-2">
        <span className="text-base font-medium text-foreground">{value}</span>
        <span className="truncate text-[11px] text-muted-foreground">{detail}</span>
      </div>
    </div>
  );
}

export function AutoMappingAction({
  venueId,
  items,
}: {
  venueId: string;
  items: MenuMarginItem[];
}) {
  const [state, action, pending] = useActionState(
    saveAutoMenuItemMappingsStateAction,
    INITIAL_STATE,
  );
  const mappings = items
    .filter((item) => item.product && item.match !== "manual")
    .map((item) => ({
      dishName: item.dishName,
      dishGroup: item.dishGroup,
      product: {
        id: item.product?.id ?? "",
        name: item.product?.name ?? "",
        article: item.product?.article ?? "",
      },
    }));

  return (
    <form action={action} className="min-w-0">
      <input type="hidden" name="venueId" value={venueId} />
      <input type="hidden" name="mappings" value={JSON.stringify(mappings)} />
      <div className="flex flex-wrap items-center justify-end gap-2">
        <button
          type="submit"
          disabled={pending || mappings.length === 0}
          className="inline-flex h-9 items-center gap-2 rounded-lg border border-brand/45 bg-brand/10 px-3 text-sm font-medium text-brand transition-colors hover:bg-brand/15 disabled:cursor-not-allowed disabled:opacity-45"
        >
          <Check className="size-4" />
          {pending ? "Сохраняю..." : `Принять авто-связи: ${mappings.length}`}
        </button>
        {state.message ? <ActionStateText state={state} /> : null}
      </div>
    </form>
  );
}

function MappingRow({
  venueId,
  item,
  products,
}: {
  venueId: string;
  item: MenuMarginItem;
  products: Product[];
}) {
  const [productQuery, setProductQuery] = useState("");
  const candidates = useMemo(
    () => getProductCandidates(item, products, productQuery),
    [item, products, productQuery],
  );
  const defaultCandidates = useMemo(
    () => getProductCandidates(item, products, ""),
    [item, products],
  );
  const topCandidate = defaultCandidates[0] ?? null;
  const salePrice = item.amount > 0 ? item.revenue / item.amount : 0;
  const cost = item.costReference;
  const markup =
    cost && salePrice > 0 ? Math.round(((salePrice - cost) / salePrice) * 100) : null;

  return (
    <div className="p-2">
      <div className="grid gap-2 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,1fr)_auto] lg:items-center">
        <div className="min-w-0">
          <div className="flex min-w-0 items-center gap-2">
            <StatusBadge item={item} />
            <p className="min-w-0 truncate text-[14px] font-medium text-foreground">
              {item.dishName}
            </p>
          </div>
          <p className="mt-1 truncate text-[12px] text-muted-foreground">
            {item.dishGroup} · {formatInteger(item.amount)} порц. ·{" "}
            {formatRubles(item.revenue)} · ср. {formatRubles(salePrice)}
          </p>
        </div>

        <CandidateSummary
          product={topCandidate}
          currentProduct={item.product}
          cost={cost}
          markup={markup}
          match={item.match}
          hasUsableTechCard={item.hasUsableTechCard}
        />

        {topCandidate ? (
          <CandidateMappingForm
            venueId={venueId}
            item={item}
            product={topCandidate}
            compact
          />
        ) : (
          <span className="text-[12px] text-muted-foreground">
            Нет кандидата
          </span>
        )}
      </div>

      <details className="mt-2 group">
        <summary className="cursor-pointer select-none text-[12px] text-muted-foreground hover:text-foreground">
          Выбрать другой товар
        </summary>
        <div className="mt-2 rounded-lg border border-border/40 bg-card/30 p-2">
          <label className="relative block flex-1">
            <Search className="pointer-events-none absolute left-2.5 top-1/2 size-3.5 -translate-y-1/2 text-muted-foreground" />
            <input
              value={productQuery}
              onChange={(event) => setProductQuery(event.target.value)}
              placeholder="Поиск товара iiko"
              className="h-9 w-full rounded-lg border border-border/55 bg-background/65 pl-8 pr-2 text-sm text-foreground outline-none transition-colors placeholder:text-muted-foreground/60 focus:border-brand/60"
            />
          </label>

          <div className="mt-2 grid gap-2">
            {candidates.length > 0 ? (
              candidates.map((product) => (
                <CandidateMappingForm
                  key={`${item.dishName}-${product.id}`}
                  venueId={venueId}
                  item={item}
                  product={product}
                />
              ))
            ) : (
              <p className="text-[12px] text-muted-foreground">
                Введите часть названия или артикул товара.
              </p>
            )}
          </div>
        </div>
      </details>
    </div>
  );
}

function CandidateSummary({
  product,
  currentProduct,
  cost,
  markup,
  match,
  hasUsableTechCard,
}: {
  product: Product | null;
  currentProduct: Product | null;
  cost: number | null;
  markup: number | null;
  match: MenuMarginItem["match"];
  hasUsableTechCard: boolean;
}) {
  const shownProduct = product ?? currentProduct;
  const costText = cost
    ? ` · себ. ${formatRubles(cost)}`
    : shownProduct
      ? " · закупочная цена не пришла"
      : " · цены нет";

  return (
    <div className="min-w-0 text-[12px] text-muted-foreground">
      <div className="flex min-w-0 items-center gap-2">
        <Link2 className="size-3.5 shrink-0 text-brand" />
        <span className="min-w-0 truncate">
          {shownProduct
            ? `${shownProduct.name}${shownProduct.article ? ` · ${shownProduct.article}` : ""}`
            : "Нужно связать с товаром iiko"}
        </span>
      </div>
      <p className="mt-1 truncate">
        {matchLabel(match)}
        {costText}
        {!cost && shownProduct && hasUsableTechCard ? " · техкарта есть" : ""}
        {markup !== null ? ` · маржа ${markup}%` : ""}
      </p>
    </div>
  );
}

function CandidateMappingForm({
  venueId,
  item,
  product,
  compact = false,
}: {
  venueId: string;
  item: MenuMarginItem;
  product: Product;
  compact?: boolean;
}) {
  const [state, action, pending] = useActionState(
    saveMenuItemMappingStateAction,
    INITIAL_STATE,
  );
  const isCurrentProduct = item.product?.id === product.id;

  return (
    <form
      action={action}
      className={compact ? "min-w-[132px]" : "rounded-lg border border-border/35 bg-background/35 p-2"}
    >
      <input type="hidden" name="venueId" value={venueId} />
      <input type="hidden" name="dishName" value={item.dishName} />
      <input type="hidden" name="dishGroup" value={item.dishGroup} />
      <input type="hidden" name="product" value={JSON.stringify(productValue(product))} />
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        {!compact ? (
          <div className="min-w-0">
            <p className="truncate text-[13px] font-medium text-foreground">
              {product.name}
            </p>
            <p className="mt-0.5 truncate text-[11px] text-muted-foreground">
              {product.article ? `Артикул ${product.article}` : "без артикула"}
              {productCost(product) ? ` · ${formatRubles(productCost(product) ?? 0)}` : ""}
            </p>
          </div>
        ) : null}
        <button
          type="submit"
          disabled={pending || isCurrentProduct}
          className={cn(
            "inline-flex h-8 shrink-0 items-center justify-center rounded-lg px-3 text-sm font-medium transition-colors disabled:cursor-wait disabled:opacity-55",
            isCurrentProduct
              ? "border border-brand/35 bg-brand/10 text-brand"
              : compact
              ? "w-full border border-brand/45 bg-brand/10 text-brand hover:bg-brand/15"
              : "bg-brand text-primary-foreground hover:bg-brand-hover",
          )}
        >
          {pending ? "..." : isCurrentProduct ? "Связано" : "Связать"}
        </button>
      </div>
      {state.message && !isCurrentProduct ? (
        <div className="mt-2">
          <ActionStateText state={state} />
        </div>
      ) : null}
    </form>
  );
}

function StatusBadge({ item }: { item: MenuMarginItem }) {
  if (!item.product) {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full border border-destructive/35 bg-destructive/10 px-2 py-1 text-[11px] text-destructive">
        <TriangleAlert className="size-3.5" />
        нет связи
      </span>
    );
  }

  if (!item.hasCost && item.hasUsableTechCard) {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full border border-amber-400/35 bg-amber-400/10 px-2 py-1 text-[11px] text-amber-200">
        <CircleDollarSign className="size-3.5" />
        техкарта есть
      </span>
    );
  }

  if (!item.hasCost) {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full border border-amber-400/35 bg-amber-400/10 px-2 py-1 text-[11px] text-amber-200">
        <CircleDollarSign className="size-3.5" />
        нет цены
      </span>
    );
  }

  return (
    <span className="inline-flex items-center gap-1.5 rounded-full border border-brand/35 bg-brand/10 px-2 py-1 text-[11px] text-brand">
      <Check className="size-3.5" />
      готово
    </span>
  );
}

function ActionStateText({ state }: { state: MenuMappingActionState }) {
  return (
    <span
      className={cn(
        "text-[11px] leading-tight",
        state.mode === "sandbox"
          ? "text-amber-200"
          : state.ok
            ? "text-brand"
            : "text-destructive",
      )}
    >
      {state.message}
    </span>
  );
}

function filterItems(
  items: MenuMarginItem[],
  filter: MappingFilter,
  query: string,
): MenuMarginItem[] {
  const normalizedQuery = normalize(query);
  return items.filter((item) => {
    const matchesFilter =
      filter === "all" ||
      (filter === "todo" && !item.product) ||
      (filter === "noCost" && item.product && !item.hasCost) ||
      (filter === "matched" && item.product);

    if (!matchesFilter) return false;
    if (!normalizedQuery) return true;

    return normalize(
      `${item.dishName} ${item.dishGroup} ${item.product?.name ?? ""} ${
        item.product?.article ?? ""
      }`,
    ).includes(normalizedQuery);
  });
}

function initialFilter(items: MenuMarginItem[]): MappingFilter {
  if (items.some((item) => !item.product)) return "todo";
  if (items.some((item) => item.product && !item.hasCost)) return "noCost";
  return "all";
}

function getProductCandidates(
  item: MenuMarginItem,
  products: Product[],
  query: string,
): Product[] {
  const normalizedQuery = normalize(query);
  const base = normalizedQuery || normalize(item.dishName);
  const scored = products
    .map((product) => ({
      product,
      score: productScore(product, base, item),
    }))
    .filter((entry) => entry.score > 0)
    .sort((a, b) => b.score - a.score)
    .map((entry) => entry.product);

  return uniqueProducts([item.product, ...scored]).slice(0, 5);
}

function productScore(product: Product, query: string, item: MenuMarginItem): number {
  const productText = normalize(`${product.name} ${product.article ?? ""}`);
  if (!query) return product.id === item.product?.id ? 100 : 0;
  if (product.id === item.product?.id) return 100;
  if (productText.includes(query)) return 80 + Math.min(query.length, 10);

  const queryTokens = query.split(" ").filter((token) => token.length > 2);
  if (queryTokens.length === 0) return 0;
  const hits = queryTokens.filter((token) => productText.includes(token)).length;
  return hits > 0 ? hits / queryTokens.length : 0;
}

function uniqueProducts(products: Array<Product | null>): Product[] {
  const seen = new Set<string>();
  const result: Product[] = [];
  products.forEach((product) => {
    if (!product || seen.has(product.id)) return;
    seen.add(product.id);
    result.push(product);
  });
  return result;
}

function productValue(product: Product): { id: string; name: string; article: string } {
  return {
    id: product.id,
    name: product.name,
    article: product.article ?? "",
  };
}

function productCost(product: Product | null): number | null {
  return getProductCostReference(product);
}

function matchLabel(match: MenuMarginItem["match"]): string {
  if (match === "manual") return "Ручная связь";
  if (match === "auto") return "Авто-связь сохранена";
  if (match === "exact") return "Точное совпадение";
  if (match === "similar") return "Похожее совпадение";
  return "Связи нет";
}

function normalize(value: string): string {
  return value
    .trim()
    .toLowerCase()
    .replace(/[^\p{L}\p{N}\s]/gu, " ")
    .replace(/\s+/g, " ");
}
