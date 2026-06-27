import type { DishStat, Product } from "@/lib/iiko/models";
import {
  findMappedProduct,
  type MenuItemMapping,
} from "@/lib/menu-item-mapping";

export type MenuMarginStatus = "ready" | "partial" | "blocked";

export type MenuMarginItem = {
  dishName: string;
  dishGroup: string;
  revenue: number;
  amount: number;
  product: Product | null;
  match: "manual" | "auto" | "exact" | "similar" | "missing";
  hasCost: boolean;
  costReference: number | null;
  status: MenuMarginStatus;
};

export type MenuMarginBlocker = {
  dishName: string;
  dishGroup: string;
  revenue: number;
  amount: number;
  reason: "missing-link" | "missing-cost";
  productName: string | null;
};

export type MenuMarginReadiness = {
  status: MenuMarginStatus;
  totalDishes: number;
  matchedDishes: number;
  costedDishes: number;
  revenueWithCost: number;
  revenueCoveragePct: number;
  matchCoveragePct: number;
  costCoveragePct: number;
  topBlockers: MenuMarginBlocker[];
  items: MenuMarginItem[];
};

export function buildMenuMarginReadiness(input: {
  dishes: DishStat[];
  products: Product[];
  mappings?: MenuItemMapping[];
}): MenuMarginReadiness {
  const products = input.products.filter((product) => product.active !== false);
  const mappings = input.mappings ?? [];
  const totalRevenue = input.dishes.reduce((sum, dish) => sum + dish.dishSumInt, 0);
  const items = input.dishes.map((dish) => {
    const mapped = findMappedProduct({
      dishName: dish.dishName,
      mappings,
      products,
    });
    const match =
      mapped.product !== null
        ? { product: mapped.product, kind: mapped.source }
        : findProductMatch(dish.dishName, products);
    const costReference = getProductCostReference(match.product);
    const hasCost = costReference !== null;
    return {
      dishName: dish.dishName,
      dishGroup: dish.dishGroup,
      revenue: dish.dishSumInt,
      amount: dish.dishAmountInt,
      product: match.product,
      match: match.kind,
      hasCost,
      costReference,
      status: !match.product ? "blocked" : hasCost ? "ready" : "partial",
    } satisfies MenuMarginItem;
  });

  const matchedDishes = items.filter((item) => item.product).length;
  const costedDishes = items.filter((item) => item.hasCost).length;
  const revenueWithCost = items
    .filter((item) => item.hasCost)
    .reduce((sum, item) => sum + item.revenue, 0);
  const revenueCoveragePct = pct(revenueWithCost, totalRevenue);
  const matchCoveragePct = pct(matchedDishes, input.dishes.length);
  const costCoveragePct = pct(costedDishes, input.dishes.length);
  const topBlockers: MenuMarginBlocker[] = items
    .filter((item) => !item.hasCost)
    .map((item) => ({
      dishName: item.dishName,
      dishGroup: item.dishGroup,
      revenue: item.revenue,
      amount: item.amount,
      reason: item.product
        ? ("missing-cost" as const)
        : ("missing-link" as const),
      productName: item.product?.name ?? null,
    }))
    .sort((a, b) => b.revenue - a.revenue)
    .slice(0, 5);

  return {
    status:
      costCoveragePct >= 80
        ? "ready"
        : matchCoveragePct > 0 || costCoveragePct > 0
          ? "partial"
          : "blocked",
    totalDishes: input.dishes.length,
    matchedDishes,
    costedDishes,
    revenueWithCost,
    revenueCoveragePct,
    matchCoveragePct,
    costCoveragePct,
    topBlockers,
    items,
  };
}

function findProductMatch(
  dishName: string,
  products: Product[],
): { product: Product | null; kind: MenuMarginItem["match"] } {
  const normalizedDish = normalize(dishName);
  const exact = products.find((product) => normalize(product.name) === normalizedDish);
  if (exact) return { product: exact, kind: "exact" };

  const dishTokens = tokenSet(normalizedDish);
  const similar = products
    .map((product) => ({
      product,
      score: tokenScore(dishTokens, tokenSet(normalize(product.name))),
    }))
    .filter((item) => item.score >= 0.65)
    .sort((a, b) => b.score - a.score)[0]?.product;

  return similar
    ? { product: similar, kind: "similar" }
    : { product: null, kind: "missing" };
}

function tokenScore(a: Set<string>, b: Set<string>): number {
  if (a.size === 0 || b.size === 0) return 0;
  let intersection = 0;
  a.forEach((token) => {
    if (b.has(token)) intersection += 1;
  });
  return intersection / Math.max(a.size, b.size);
}

function tokenSet(value: string): Set<string> {
  return new Set(value.split(" ").filter((token) => token.length > 2));
}

function normalize(value: string): string {
  return value
    .trim()
    .toLowerCase()
    .replace(/[^\p{L}\p{N}\s]/gu, " ")
    .replace(/\s+/g, " ");
}

function pct(part: number, total: number): number {
  if (total <= 0) return 0;
  return Math.round((part / total) * 1000) / 10;
}

export function getProductCostReference(product: Product | null): number | null {
  if (!product) return null;
  const pricePerKg = positive(product.pricePerKg);
  if (pricePerKg !== null) return pricePerKg;

  const purchasePrice = positive(product.purchasePrice);
  if (purchasePrice !== null) return purchasePrice;

  const purchasePricePerUnit = positive(product.purchasePricePerUnit);
  if (purchasePricePerUnit === null) return null;
  return product.unit === "pcs" ? purchasePricePerUnit : purchasePricePerUnit * 1000;
}

function positive(value: number | undefined): number | null {
  return typeof value === "number" && Number.isFinite(value) && value > 0
    ? value
    : null;
}
