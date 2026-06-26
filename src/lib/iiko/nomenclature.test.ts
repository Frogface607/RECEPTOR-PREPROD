import { describe, expect, test } from "vitest";
import {
  normalizeIikoProduct,
  normalizeIikoProducts,
  searchIikoProducts,
} from "./nomenclature";

describe("normalizeIikoProduct", () => {
  test("uses num as article and keeps quick dial code separate", () => {
    const product = normalizeIikoProduct({
      id: "p-1",
      name: "Beef tenderloin",
      num: "ART-777",
      code: "42",
      unit: "kg",
      purchasePrice: 1800,
      price: 2500,
    });

    expect(product?.article).toBe("ART-777");
    expect(product?.quickDialCode).toBe("42");
    expect(product?.unit).toBe("g");
    expect(product?.purchasePrice).toBe(1800);
    expect(product?.purchasePricePerUnit).toBe(1.8);
    expect(product?.pricePerKg).toBe(1800);
  });

  test("does not treat quick dial code as article", () => {
    const product = normalizeIikoProduct({
      id: "p-2",
      name: "House lemonade",
      code: "15",
      unit: "pcs",
      cost: 90,
    });

    expect(product?.article).toBeUndefined();
    expect(product?.quickDialCode).toBe("15");
    expect(product?.pricePerKg).toBe(90);
  });

  test("extracts products from Cloud-style payload", () => {
    const products = normalizeIikoProducts({
      products: [
        { id: "p-1", name: "Pasta", sizePrices: [{ price: { currentPrice: 790 } }] },
        { id: "", name: "Broken" },
      ],
    });

    expect(products).toHaveLength(1);
    expect(products[0].price).toBe(790);
  });

  test("keeps legacy RMS normalized per-unit prices", () => {
    const product = normalizeIikoProduct({
      id: "r-legacy",
      name: "Tomato legacy",
      num: "T-10",
      unit: "kg",
      purchase_price_per_unit: 0.32,
      price_per_unit: 0.45,
    });

    expect(product?.purchasePricePerUnit).toBe(0.32);
    expect(product?.pricePerUnit).toBe(0.45);
    expect(product?.pricePerKg).toBe(320);
  });
});

describe("searchIikoProducts", () => {
  test("prioritizes exact article and name matches", () => {
    const products = normalizeIikoProducts([
      { id: "1", name: "Shrimp salad", num: "A-10", price: 700 },
      { id: "2", name: "Warm shrimp salad", num: "B-20", price: 900 },
    ]);

    expect(searchIikoProducts(products, "B-20")[0].name).toBe(
      "Warm shrimp salad",
    );
    expect(searchIikoProducts(products, "shrimp")).toHaveLength(2);
  });
});
