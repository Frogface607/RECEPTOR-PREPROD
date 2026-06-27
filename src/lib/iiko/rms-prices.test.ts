import { describe, expect, test } from "vitest";
import {
  mergeProductsWithRmsPrices,
  normalizeRmsPrice,
  normalizeRmsPrices,
} from "./rms-prices";

describe("normalizeRmsPrice", () => {
  test("normalizes RMS purchase price from kg into per-unit and per-kg references", () => {
    const price = normalizeRmsPrice({
      id: "tomato",
      name: "Tomato",
      num: "T-10",
      unit: "kg",
      purchasePrice: 320,
      vat_pct: 10,
    });

    expect(price).toMatchObject({
      skuId: "tomato",
      article: "T-10",
      unit: "g",
      pricePerUnit: 0.32,
      pricePerKg: 320,
      vatPct: 10,
      rawField: "purchasePrice",
    });
  });

  test("accepts legacy cached price_per_unit as cost", () => {
    const price = normalizeRmsPrice({
      skuId: "legacy-1",
      name: "Legacy tomato",
      original_unit: "kg",
      price_per_unit: 0.45,
      currency: "руб",
    });

    expect(price).toMatchObject({
      currency: "RUB",
      pricePerUnit: 0.45,
      pricePerKg: 450,
      rawField: "price_per_unit",
    });
  });

  test("reads nested RMS purchase cost fields", () => {
    const price = normalizeRmsPrice({
      id: "nested-1",
      name: "Nested tomato",
      unit: "kg",
      purchase: {
        pricePerUnit: 0.52,
      },
    });

    expect(price).toMatchObject({
      skuId: "nested-1",
      pricePerUnit: 0.52,
      pricePerKg: 520,
      rawField: "purchase.pricePerUnit",
    });
  });

  test("reads explicit nested cost fields under RMS price containers", () => {
    const price = normalizeRmsPrice({
      id: "nested-2",
      name: "Nested flour",
      unit: "kg",
      prices: {
        purchasePrice: 92,
      },
    });

    expect(price).toMatchObject({
      skuId: "nested-2",
      pricePerUnit: 0.092,
      pricePerKg: 92,
      rawField: "prices.purchasePrice",
    });
  });

  test("does not treat menu selling price as cost", () => {
    expect(
      normalizeRmsPrice({
        id: "beer",
        name: "Beer 0.5",
        unit: "pcs",
        price: 390,
        currentPrice: 390,
      }),
    ).toBeNull();
  });

  test("does not treat nested menu selling prices as cost", () => {
    expect(
      normalizeRmsPrice({
        id: "beer-nested",
        name: "Beer nested",
        unit: "pcs",
        prices: {
          price: 390,
          currentPrice: 390,
        },
        sizePrices: [{ price: { currentPrice: 390 } }],
      }),
    ).toBeNull();
  });
});

describe("normalizeRmsPrices", () => {
  test("extracts prices from legacy price cache payload", () => {
    const prices = normalizeRmsPrices({
      prices: [
        { skuId: "p-1", name: "Beef", unit: "kg", price_per_unit: 1.8 },
        { skuId: "p-2", name: "Broken", price: 1200 },
      ],
    });

    expect(prices).toHaveLength(1);
    expect(prices[0].pricePerKg).toBe(1800);
  });
});

describe("mergeProductsWithRmsPrices", () => {
  test("enriches matched products with RMS cost references", () => {
    const products = mergeProductsWithRmsPrices(
      [
        {
          id: "dish-1",
          name: "Tomato salad",
          article: "T-10",
          price: 590,
          sizePrices: [{ price: { currentPrice: 590 } }],
        },
      ],
      [
        {
          skuId: "rms-tomato",
          name: "Tomato salad",
          article: "T-10",
          unit: "g",
          originalUnit: "kg",
          pricePerUnit: 0.32,
          pricePerKg: 320,
          currency: "RUB",
          vatPct: 0,
          source: "iiko_rms",
          rawField: "price_per_unit",
          active: true,
        },
      ],
    );

    expect(products[0]).toMatchObject({
      purchasePrice: 320,
      purchasePricePerUnit: 0.32,
      pricePerKg: 320,
    });
    expect(products[0].price).toBe(590);
  });
});
