import type { Product } from "@/lib/iiko/models";

export type MenuItemMappingStatus = "active" | "ignored" | "needs_review";
export type MenuItemMappingType = "manual" | "auto" | "imported";

export type MenuItemMapping = {
  id: string;
  venueId: string;
  dishKey: string;
  dishName: string;
  dishGroup: string;
  iikoProductId?: string;
  iikoProductName?: string;
  iikoArticle?: string;
  techCardId?: string;
  mappingType: MenuItemMappingType;
  status: MenuItemMappingStatus;
  confidence: number;
  note: string;
};

export type ProductMatch =
  | {
      product: Product;
      source: "manual" | "auto";
    }
  | {
      product: null;
      source: "none";
    };

export function createDishKey(dishName: string): string {
  return normalizeMappingText(dishName);
}

export function findMappedProduct(input: {
  dishName: string;
  mappings: MenuItemMapping[];
  products: Product[];
}): ProductMatch {
  const dishKey = createDishKey(input.dishName);
  const mapping = input.mappings.find(
    (item) => item.status === "active" && item.dishKey === dishKey,
  );
  if (!mapping) return { product: null, source: "none" };

  const product =
    findProductById(input.products, mapping.iikoProductId) ??
    findProductByArticle(input.products, mapping.iikoArticle) ??
    syntheticProductFromMapping(mapping);

  return product
    ? { product, source: mapping.mappingType === "auto" ? "auto" : "manual" }
    : { product: null, source: "none" };
}

function findProductById(
  products: Product[],
  productId: string | undefined,
): Product | null {
  if (!productId) return null;
  return products.find((product) => product.id === productId) ?? null;
}

function findProductByArticle(
  products: Product[],
  article: string | undefined,
): Product | null {
  if (!article) return null;
  const normalized = normalizeMappingText(article);
  return (
    products.find(
      (product) => normalizeMappingText(product.article ?? "") === normalized,
    ) ?? null
  );
}

function syntheticProductFromMapping(mapping: MenuItemMapping): Product | null {
  if (!mapping.iikoProductId || !mapping.iikoProductName) return null;
  return {
    id: mapping.iikoProductId,
    name: mapping.iikoProductName,
    article: mapping.iikoArticle,
    sizePrices: [],
  };
}

function normalizeMappingText(value: string): string {
  return value
    .trim()
    .toLowerCase()
    .replace(/[^\p{L}\p{N}\s]/gu, " ")
    .replace(/\s+/g, " ");
}
