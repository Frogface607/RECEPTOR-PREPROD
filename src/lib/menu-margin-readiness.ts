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
  salePrice: number | null;
  product: Product | null;
  match: "manual" | "auto" | "exact" | "similar" | "missing";
  hasCost: boolean;
  costReference: number | null;
  costSource: "product" | "tech-card" | null;
  grossProfitPerItem: number | null;
  grossProfit: number | null;
  grossMarginPct: number | null;
  techCard: MenuMarginTechCardMatch | null;
  hasUsableTechCard: boolean;
  status: MenuMarginStatus;
};

export type MenuMarginBlocker = {
  dishName: string;
  dishGroup: string;
  revenue: number;
  amount: number;
  reason: "missing-link" | "missing-cost";
  productName: string | null;
  hasTechCard: boolean;
  techCardIngredientRows: number;
  techCardLinkedIngredientRows: number;
  techCardPricedIngredientRows: number;
};

export type MenuMarginNextAction = {
  kind: "ready" | "missing-link" | "missing-cost";
  title: string;
  detail: string;
  action: string;
  blocker: MenuMarginBlocker | null;
};

export type MenuMarginRisk = {
  dishName: string;
  dishGroup: string;
  revenue: number;
  amount: number;
  salePrice: number;
  costReference: number;
  grossProfit: number;
  grossProfitPerItem: number;
  grossMarginPct: number;
  costSource: "product" | "tech-card";
};

export type MenuMarginReadiness = {
  status: MenuMarginStatus;
  totalDishes: number;
  matchedDishes: number;
  costedDishes: number;
  techCardDishes: number;
  usableTechCardDishes: number;
  revenueWithCost: number;
  revenueWithTechCards: number;
  grossProfit: number;
  averageGrossMarginPct: number | null;
  blockedRevenue: number;
  missingLinkRevenue: number;
  missingCostRevenue: number;
  revenueCoveragePct: number;
  blockedRevenuePct: number;
  matchCoveragePct: number;
  costCoveragePct: number;
  techCardCoveragePct: number;
  usableTechCardCoveragePct: number;
  topBlockers: MenuMarginBlocker[];
  topMarginRisks: MenuMarginRisk[];
  items: MenuMarginItem[];
};

export type MenuMarginTechCardIngredient = {
  productId?: string;
  productName?: string;
  article?: string;
  amount?: number;
  unit?: string;
};

export type MenuMarginTechCard = {
  id?: string;
  productId?: string;
  productName?: string;
  name?: string;
  items: MenuMarginTechCardIngredient[];
};

export type MenuMarginTechCardMatch = {
  id?: string;
  productId?: string;
  productName?: string;
  ingredientRows: number;
  linkedIngredientRows: number;
  ingredientRowsWithAmount: number;
  pricedIngredientRows: number;
  costReference: number | null;
  usable: boolean;
  fullyCosted: boolean;
};

export function buildMenuMarginReadiness(input: {
  dishes: DishStat[];
  products: Product[];
  mappings?: MenuItemMapping[];
  techCards?: MenuMarginTechCard[];
}): MenuMarginReadiness {
  const products = input.products.filter((product) => product.active !== false);
  const mappings = input.mappings ?? [];
  const techCards = input.techCards ?? [];
  const totalRevenue = input.dishes.reduce(
    (sum, dish) => sum + dish.dishSumInt,
    0,
  );
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
    const productCostReference = getProductCostReference(match.product);
    const techCard = findTechCardMatch(
      dish.dishName,
      match.product,
      techCards,
      products,
    );
    const costReference =
      productCostReference ?? techCard?.costReference ?? null;
    const hasCost = costReference !== null;
    const costSource =
      productCostReference !== null
        ? ("product" as const)
        : techCard?.costReference !== null &&
            techCard?.costReference !== undefined
          ? ("tech-card" as const)
          : null;
    const salePrice =
      dish.dishAmountInt > 0 ? dish.dishSumInt / dish.dishAmountInt : null;
    const grossProfitPerItem =
      salePrice !== null && costReference !== null
        ? roundMoney(salePrice - costReference)
        : null;
    const grossProfit =
      grossProfitPerItem !== null
        ? roundMoney(grossProfitPerItem * dish.dishAmountInt)
        : null;
    const grossMarginPct =
      salePrice !== null && salePrice > 0 && grossProfitPerItem !== null
        ? pct(grossProfitPerItem, salePrice)
        : null;
    return {
      dishName: dish.dishName,
      dishGroup: dish.dishGroup,
      revenue: dish.dishSumInt,
      amount: dish.dishAmountInt,
      salePrice,
      product: match.product,
      match: match.kind,
      hasCost,
      costReference,
      costSource,
      grossProfitPerItem,
      grossProfit,
      grossMarginPct,
      techCard,
      hasUsableTechCard: Boolean(techCard?.usable),
      status: !match.product ? "blocked" : hasCost ? "ready" : "partial",
    } satisfies MenuMarginItem;
  });

  const matchedDishes = items.filter((item) => item.product).length;
  const costedDishes = items.filter((item) => item.hasCost).length;
  const techCardDishes = items.filter((item) => item.techCard).length;
  const usableTechCardDishes = items.filter(
    (item) => item.hasUsableTechCard,
  ).length;
  const revenueWithCost = items
    .filter((item) => item.hasCost)
    .reduce((sum, item) => sum + item.revenue, 0);
  const revenueWithTechCards = items
    .filter((item) => item.hasUsableTechCard)
    .reduce((sum, item) => sum + item.revenue, 0);
  const grossProfit = roundMoney(
    items.reduce((sum, item) => sum + (item.grossProfit ?? 0), 0),
  );
  const missingLinkRevenue = items
    .filter((item) => !item.product)
    .reduce((sum, item) => sum + item.revenue, 0);
  const missingCostRevenue = items
    .filter((item) => item.product && !item.hasCost)
    .reduce((sum, item) => sum + item.revenue, 0);
  const blockedRevenue = missingLinkRevenue + missingCostRevenue;
  const revenueCoveragePct = pct(revenueWithCost, totalRevenue);
  const blockedRevenuePct = pct(blockedRevenue, totalRevenue);
  const matchCoveragePct = pct(matchedDishes, input.dishes.length);
  const costCoveragePct = pct(costedDishes, input.dishes.length);
  const averageGrossMarginPct =
    revenueWithCost > 0 ? pct(grossProfit, revenueWithCost) : null;
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
      hasTechCard: item.hasUsableTechCard,
      techCardIngredientRows: item.techCard?.ingredientRows ?? 0,
      techCardLinkedIngredientRows: item.techCard?.linkedIngredientRows ?? 0,
      techCardPricedIngredientRows: item.techCard?.pricedIngredientRows ?? 0,
    }))
    .sort((a, b) => b.revenue - a.revenue)
    .slice(0, 5);
  const topMarginRisks: MenuMarginRisk[] = items
    .filter(
      (item) =>
        item.hasCost &&
        item.costReference !== null &&
        item.costSource !== null &&
        item.salePrice !== null &&
        item.grossProfit !== null &&
        item.grossProfitPerItem !== null &&
        item.grossMarginPct !== null &&
        item.grossMarginPct < 60,
    )
    .map((item) => ({
      dishName: item.dishName,
      dishGroup: item.dishGroup,
      revenue: item.revenue,
      amount: item.amount,
      salePrice: item.salePrice ?? 0,
      costReference: item.costReference ?? 0,
      grossProfit: item.grossProfit ?? 0,
      grossProfitPerItem: item.grossProfitPerItem ?? 0,
      grossMarginPct: item.grossMarginPct ?? 0,
      costSource: item.costSource ?? "product",
    }))
    .sort(
      (a, b) => a.grossMarginPct - b.grossMarginPct || b.revenue - a.revenue,
    )
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
    techCardDishes,
    usableTechCardDishes,
    revenueWithCost,
    revenueWithTechCards,
    grossProfit,
    averageGrossMarginPct,
    blockedRevenue,
    missingLinkRevenue,
    missingCostRevenue,
    revenueCoveragePct,
    blockedRevenuePct,
    matchCoveragePct,
    costCoveragePct,
    techCardCoveragePct: pct(techCardDishes, input.dishes.length),
    usableTechCardCoveragePct: pct(usableTechCardDishes, input.dishes.length),
    topBlockers,
    topMarginRisks,
    items,
  };
}

function findTechCardMatch(
  dishName: string,
  product: Product | null,
  techCards: MenuMarginTechCard[],
  products: Product[],
): MenuMarginTechCardMatch | null {
  if (techCards.length === 0) return null;

  const normalizedDish = normalize(dishName);
  const normalizedProduct = product ? normalize(product.name) : "";
  const productId = product?.id;

  const chart = techCards.find((item) => {
    if (productId && item.productId === productId) return true;

    const chartName = normalize(item.productName ?? item.name ?? "");
    if (!chartName) return false;
    if (normalizedProduct && chartName === normalizedProduct) return true;
    if (chartName === normalizedDish) return true;

    const dishScore = tokenScore(tokenSet(normalizedDish), tokenSet(chartName));
    const productScore = normalizedProduct
      ? tokenScore(tokenSet(normalizedProduct), tokenSet(chartName))
      : 0;
    return Math.max(dishScore, productScore) >= 0.75;
  });

  if (!chart) return null;

  const ingredientRows = chart.items.length;
  const linkedIngredientRows = chart.items.filter((item) =>
    Boolean(item.productId || findIngredientProduct(item, products)),
  ).length;
  const ingredientRowsWithAmount = chart.items.filter(
    (item) => item.amount !== undefined,
  ).length;
  const pricedRows = chart.items
    .map((item) => calculateIngredientCost(item, products))
    .filter((cost): cost is number => cost !== null);
  const costReference =
    ingredientRowsWithAmount > 0 &&
    pricedRows.length === ingredientRowsWithAmount
      ? roundMoney(pricedRows.reduce((sum, cost) => sum + cost, 0))
      : null;

  return {
    id: chart.id,
    productId: chart.productId,
    productName: chart.productName ?? chart.name,
    ingredientRows,
    linkedIngredientRows,
    ingredientRowsWithAmount,
    pricedIngredientRows: pricedRows.length,
    costReference,
    usable: linkedIngredientRows > 0 && ingredientRowsWithAmount > 0,
    fullyCosted: costReference !== null,
  };
}

function calculateIngredientCost(
  ingredient: MenuMarginTechCardIngredient,
  products: Product[],
): number | null {
  const amount = positive(ingredient.amount);
  if (amount === null) return null;

  const product = findIngredientProduct(ingredient, products);
  if (!product) return null;

  const costReference = getProductCostReference(product);
  if (costReference === null) return null;

  const unit = normalizeIngredientUnit(ingredient.unit) ?? product.unit ?? null;
  if (unit === "pcs") return amount * costReference;
  if (unit === "kg" || unit === "l") return amount * costReference;
  if (unit === "g" || unit === "ml") return (amount / 1000) * costReference;

  return null;
}

function findIngredientProduct(
  ingredient: MenuMarginTechCardIngredient,
  products: Product[],
): Product | null {
  if (ingredient.productId) {
    const byId = products.find(
      (product) => product.id === ingredient.productId,
    );
    if (byId) return byId;
  }

  if (ingredient.article) {
    const article = normalize(ingredient.article);
    const byArticle = products.find(
      (product) => normalize(product.article ?? "") === article,
    );
    if (byArticle) return byArticle;
  }

  if (!ingredient.productName) return null;

  const name = normalize(ingredient.productName);
  const exact = products.find((product) => normalize(product.name) === name);
  if (exact) return exact;

  const nameTokens = tokenSet(name);
  return (
    products
      .map((product) => ({
        product,
        score: tokenScore(nameTokens, tokenSet(normalize(product.name))),
      }))
      .filter((item) => item.score >= 0.8)
      .sort((a, b) => b.score - a.score)[0]?.product ?? null
  );
}

function normalizeIngredientUnit(
  value: string | undefined,
): "g" | "kg" | "ml" | "l" | "pcs" | null {
  const unit = value
    ?.trim()
    .toLowerCase()
    .replace(/[.\s]+$/g, "")
    .replace(/ё/g, "е");
  if (!unit) return null;

  if (
    [
      "kg",
      "kilogram",
      "kilograms",
      "кило",
      "килограмм",
      "килограмма",
      "килограммы",
      "килограммов",
      "кг",
    ].includes(unit)
  ) {
    return "kg";
  }
  if (
    [
      "g",
      "gr",
      "gram",
      "grams",
      "грамм",
      "грамма",
      "граммы",
      "граммов",
      "гр",
      "г",
    ].includes(unit)
  ) {
    return "g";
  }
  if (
    [
      "l",
      "liter",
      "litre",
      "liters",
      "litres",
      "литр",
      "литра",
      "литры",
      "литров",
      "л",
    ].includes(unit)
  ) {
    return "l";
  }
  if (
    [
      "ml",
      "milliliter",
      "millilitre",
      "milliliters",
      "millilitres",
      "миллилитр",
      "миллилитра",
      "миллилитры",
      "миллилитров",
      "мл",
    ].includes(unit)
  ) {
    return "ml";
  }
  if (
    [
      "pcs",
      "pc",
      "piece",
      "pieces",
      "portion",
      "portions",
      "шт",
      "штук",
      "штука",
      "штуки",
      "порц",
      "порция",
      "порцию",
      "порции",
      "порций",
    ].includes(unit)
  ) {
    return "pcs";
  }

  return null;
}

function roundMoney(value: number): number {
  return Math.round(value * 100) / 100;
}

function findProductMatch(
  dishName: string,
  products: Product[],
): { product: Product | null; kind: MenuMarginItem["match"] } {
  const normalizedDish = normalize(dishName);
  const exact = products.find(
    (product) => normalize(product.name) === normalizedDish,
  );
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

export function getProductCostReference(
  product: Product | null,
): number | null {
  if (!product) return null;
  const pricePerKg = positive(product.pricePerKg);
  if (pricePerKg !== null) return pricePerKg;

  const purchasePrice = positive(product.purchasePrice);
  if (purchasePrice !== null) return purchasePrice;

  const purchasePricePerUnit = positive(product.purchasePricePerUnit);
  if (purchasePricePerUnit === null) return null;
  return product.unit === "pcs"
    ? purchasePricePerUnit
    : purchasePricePerUnit * 1000;
}

export function buildMenuMarginNextAction(
  readiness: MenuMarginReadiness,
): MenuMarginNextAction {
  const blocker = readiness.topBlockers[0] ?? null;

  if (blocker?.reason === "missing-cost" && blocker.hasTechCard) {
    const linkedProduct = blocker.productName ?? "выбранным товаром iiko";
    return {
      kind: "missing-cost",
      title: "Техкарта есть, не хватает цен ингредиентов",
      detail: `«${blocker.dishName}» связано с ${linkedProduct}. RMS отдал состав: ${blocker.techCardIngredientRows} строк, ${blocker.techCardLinkedIngredientRows} связаны с товарами.`,
      action:
        "Проверьте закупочные цены ингредиентов в RMS. После этого Receptor сможет считать food cost по составу техкарты.",
      blocker,
    };
  }

  if (!blocker) {
    return {
      kind: "ready",
      title: "Маржу можно разбирать",
      detail: "Ключевые блюда связаны с iiko и имеют доказанную себестоимость.",
      action: "Ищите слабую маржу, хвост меню и позиции с высоким оборотом.",
      blocker: null,
    };
  }

  if (blocker.reason === "missing-cost") {
    const product = blocker.productName
      ? `«${blocker.productName}»`
      : "выбранным товаром iiko";
    return {
      kind: "missing-cost",
      title: "RMS не отдает закупочную цену",
      detail: `«${blocker.dishName}» связано с ${product}, но у товара нет purchasePrice, cost или price_per_unit.`,
      action:
        "Откройте диагностику iiko и проверьте RMS-права на номенклатуру, закупочные цены или техкарты.",
      blocker,
    };
  }

  return {
    kind: "missing-link",
    title: "Блюдо не связано с iiko",
    detail: `«${blocker.dishName}» продается в BI, но не связано с товаром номенклатуры.`,
    action:
      "Свяжите блюдо с правильным товаром iiko, затем проверьте, пришла ли закупочная цена.",
    blocker,
  };
}

function positive(value: number | undefined): number | null {
  return typeof value === "number" && Number.isFinite(value) && value > 0
    ? value
    : null;
}
