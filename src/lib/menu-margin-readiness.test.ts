import { describe, expect, test } from "vitest";
import {
  buildMenuMarginReadiness,
  buildMenuMarginNextAction,
  getProductCostReference,
} from "./menu-margin-readiness";

describe("buildMenuMarginReadiness", () => {
  test("uses manual mapping before fuzzy product matching", () => {
    const readiness = buildMenuMarginReadiness({
      dishes: [
        {
          dishName: "Chef steak",
          dishGroup: "Kitchen",
          dishAmountInt: 10,
          dishSumInt: 10000,
        },
      ],
      products: [
        {
          id: "wrong",
          name: "Chef steak",
          sizePrices: [],
        },
        {
          id: "beef",
          name: "Beef tenderloin semi-finished",
          article: "B-10",
          purchasePrice: 1900,
          pricePerKg: 1900,
          sizePrices: [],
        },
      ],
      mappings: [
        {
          id: "m-1",
          venueId: "venue-1",
          dishKey: "chef steak",
          dishName: "Chef steak",
          dishGroup: "Kitchen",
          iikoProductId: "beef",
          iikoProductName: "Beef tenderloin semi-finished",
          iikoArticle: "B-10",
          mappingType: "manual",
          status: "active",
          confidence: 1,
          note: "",
        },
      ],
    });

    expect(readiness.items[0].product?.id).toBe("beef");
    expect(readiness.items[0].match).toBe("manual");
    expect(readiness.costCoveragePct).toBe(100);
    expect(readiness.revenueCoveragePct).toBe(100);
  });

  test("does not treat menu selling price as proven cost", () => {
    const readiness = buildMenuMarginReadiness({
      dishes: [
        {
          dishName: "Chef steak",
          dishGroup: "Kitchen",
          dishAmountInt: 10,
          dishSumInt: 10000,
        },
      ],
      products: [
        {
          id: "steak",
          name: "Chef steak",
          price: 1200,
          sizePrices: [{ price: { currentPrice: 1200 } }],
        },
      ],
    });

    expect(readiness.items[0].product?.id).toBe("steak");
    expect(readiness.items[0].hasCost).toBe(false);
    expect(readiness.costCoveragePct).toBe(0);
    expect(readiness.revenueCoveragePct).toBe(0);
  });

  test("normalizes legacy purchase price per gram into a kg reference", () => {
    expect(
      getProductCostReference({
        id: "tomato",
        name: "Tomato",
        unit: "g",
        purchasePricePerUnit: 0.32,
        sizePrices: [],
      }),
    ).toBe(320);
  });

  test("prioritizes missing margin blockers by revenue", () => {
    const readiness = buildMenuMarginReadiness({
      dishes: [
        {
          dishName: "Low revenue dish",
          dishGroup: "Kitchen",
          dishAmountInt: 4,
          dishSumInt: 4000,
        },
        {
          dishName: "High revenue dish",
          dishGroup: "Kitchen",
          dishAmountInt: 20,
          dishSumInt: 50000,
        },
        {
          dishName: "Mapped without cost",
          dishGroup: "Bar",
          dishAmountInt: 10,
          dishSumInt: 20000,
        },
      ],
      products: [
        {
          id: "mapped-no-cost",
          name: "Mapped product",
          sizePrices: [],
        },
      ],
      mappings: [
        {
          id: "m-1",
          venueId: "venue-1",
          dishKey: "mapped without cost",
          dishName: "Mapped without cost",
          dishGroup: "Bar",
          iikoProductId: "mapped-no-cost",
          iikoProductName: "Mapped product",
          iikoArticle: "",
          mappingType: "manual",
          status: "active",
          confidence: 1,
          note: "",
        },
      ],
    });

    expect(readiness.topBlockers.map((item) => item.dishName)).toEqual([
      "High revenue dish",
      "Mapped without cost",
      "Low revenue dish",
    ]);
    expect(readiness).toMatchObject({
      blockedRevenue: 74000,
      blockedRevenuePct: 100,
      missingLinkRevenue: 54000,
      missingCostRevenue: 20000,
      revenueWithCost: 0,
    });
    expect(readiness.topBlockers[0]).toMatchObject({
      reason: "missing-link",
      revenue: 50000,
    });
    expect(readiness.topBlockers[1]).toMatchObject({
      reason: "missing-cost",
      productName: "Mapped product",
    });
    expect(buildMenuMarginNextAction(readiness)).toMatchObject({
      kind: "missing-link",
      title: "Блюдо не связано с iiko",
      blocker: expect.objectContaining({
        dishName: "High revenue dish",
        reason: "missing-link",
      }),
    });
  });

  test("explains linked product without RMS cost as the next action", () => {
    const readiness = buildMenuMarginReadiness({
      dishes: [
        {
          dishName: "Pasta",
          dishGroup: "Kitchen",
          dishAmountInt: 10,
          dishSumInt: 30000,
        },
      ],
      products: [
        {
          id: "pasta-base",
          name: "Pasta semi-finished",
          sizePrices: [],
        },
      ],
      mappings: [
        {
          id: "m-1",
          venueId: "venue-1",
          dishKey: "pasta",
          dishName: "Pasta",
          dishGroup: "Kitchen",
          iikoProductId: "pasta-base",
          iikoProductName: "Pasta semi-finished",
          iikoArticle: "",
          mappingType: "manual",
          status: "active",
          confidence: 1,
          note: "",
        },
      ],
    });

    const nextAction = buildMenuMarginNextAction(readiness);

    expect(nextAction).toMatchObject({
      kind: "missing-cost",
      title: "RMS не отдает закупочную цену",
      blocker: expect.objectContaining({
        dishName: "Pasta",
        productName: "Pasta semi-finished",
      }),
    });
    expect(nextAction.detail).toContain("Pasta");
    expect(nextAction.detail).toContain("Pasta semi-finished");
    expect(nextAction.detail).toContain("purchasePrice");
    expect(nextAction.action).toContain("RMS-права");
  });

  test("uses readable tech-card composition as the next margin step", () => {
    const readiness = buildMenuMarginReadiness({
      dishes: [
        {
          dishName: "Pasta",
          dishGroup: "Kitchen",
          dishAmountInt: 10,
          dishSumInt: 30000,
        },
      ],
      products: [
        {
          id: "pasta-base",
          name: "Pasta",
          sizePrices: [],
        },
      ],
      techCards: [
        {
          id: "chart-pasta",
          productId: "pasta-base",
          productName: "Pasta",
          items: [
            {
              productId: "flour",
              productName: "Flour",
              amount: 0.12,
              unit: "kg",
            },
            {
              productId: "egg",
              productName: "Egg",
              amount: 1,
              unit: "pcs",
            },
          ],
        },
      ],
    });

    expect(readiness).toMatchObject({
      techCardDishes: 1,
      usableTechCardDishes: 1,
      revenueWithTechCards: 30000,
      usableTechCardCoveragePct: 100,
    });
    expect(readiness.items[0]).toMatchObject({
      hasCost: false,
      hasUsableTechCard: true,
    });
    expect(readiness.topBlockers[0]).toMatchObject({
      reason: "missing-cost",
      hasTechCard: true,
      techCardIngredientRows: 2,
      techCardLinkedIngredientRows: 2,
    });
    expect(buildMenuMarginNextAction(readiness)).toMatchObject({
      kind: "missing-cost",
      title: "Техкарта есть, не хватает цен ингредиентов",
    });
  });

  test("calculates proven food cost from priced tech-card ingredients", () => {
    const readiness = buildMenuMarginReadiness({
      dishes: [
        {
          dishName: "Pasta",
          dishGroup: "Kitchen",
          dishAmountInt: 10,
          dishSumInt: 30000,
        },
      ],
      products: [
        {
          id: "pasta-base",
          name: "Pasta",
          sizePrices: [],
        },
        {
          id: "flour",
          name: "Flour",
          unit: "g",
          pricePerKg: 100,
          sizePrices: [],
        },
        {
          id: "egg",
          name: "Egg",
          unit: "pcs",
          purchasePricePerUnit: 12,
          sizePrices: [],
        },
      ],
      techCards: [
        {
          id: "chart-pasta",
          productId: "pasta-base",
          productName: "Pasta",
          items: [
            {
              productId: "flour",
              productName: "Flour",
              amount: 0.12,
              unit: "kg",
            },
            {
              productId: "egg",
              productName: "Egg",
              amount: 2,
              unit: "pcs",
            },
          ],
        },
      ],
    });

    expect(readiness).toMatchObject({
      status: "ready",
      costedDishes: 1,
      revenueWithCost: 30000,
      revenueCoveragePct: 100,
    });
    expect(readiness.items[0]).toMatchObject({
      hasCost: true,
      costSource: "tech-card",
      costReference: 36,
      grossMarginPct: 98.8,
      grossProfit: 29640,
      techCard: expect.objectContaining({
        pricedIngredientRows: 2,
        costReference: 36,
        fullyCosted: true,
      }),
    });
    expect(buildMenuMarginNextAction(readiness)).toMatchObject({
      kind: "ready",
    });
  });

  test("calculates tech-card cost from Russian unit aliases", () => {
    const readiness = buildMenuMarginReadiness({
      dishes: [
        {
          dishName: "Soup",
          dishGroup: "Kitchen",
          dishAmountInt: 10,
          dishSumInt: 5000,
        },
      ],
      products: [
        {
          id: "soup-base",
          name: "Soup",
          sizePrices: [],
        },
        {
          id: "potato",
          name: "Potato",
          unit: "g",
          pricePerKg: 80,
          sizePrices: [],
        },
        {
          id: "cream",
          name: "Cream",
          unit: "ml",
          pricePerKg: 160,
          sizePrices: [],
        },
        {
          id: "egg",
          name: "Egg",
          unit: "pcs",
          purchasePricePerUnit: 12,
          sizePrices: [],
        },
      ],
      techCards: [
        {
          id: "chart-soup",
          productId: "soup-base",
          productName: "Soup",
          items: [
            {
              productId: "potato",
              productName: "Potato",
              amount: 250,
              unit: "гр.",
            },
            {
              productId: "cream",
              productName: "Cream",
              amount: 0.1,
              unit: "литра",
            },
            {
              productId: "egg",
              productName: "Egg",
              amount: 1,
              unit: "шт.",
            },
          ],
        },
      ],
    });

    expect(readiness.items[0]).toMatchObject({
      hasCost: true,
      costSource: "tech-card",
      costReference: 48,
      techCard: expect.objectContaining({
        pricedIngredientRows: 3,
        fullyCosted: true,
      }),
    });
  });

  test("falls back to product units when tech-card ingredients omit units", () => {
    const readiness = buildMenuMarginReadiness({
      dishes: [
        {
          dishName: "Sauce",
          dishGroup: "Kitchen",
          dishAmountInt: 10,
          dishSumInt: 5000,
        },
      ],
      products: [
        {
          id: "sauce-base",
          name: "Sauce",
          sizePrices: [],
        },
        {
          id: "tomato",
          name: "Tomato",
          unit: "g",
          pricePerKg: 80,
          sizePrices: [],
        },
        {
          id: "cream",
          name: "Cream",
          unit: "ml",
          pricePerKg: 160,
          sizePrices: [],
        },
      ],
      techCards: [
        {
          id: "chart-sauce",
          productId: "sauce-base",
          productName: "Sauce",
          items: [
            {
              productId: "tomato",
              productName: "Tomato",
              amount: 250,
            },
            {
              productId: "cream",
              productName: "Cream",
              amount: 100,
            },
          ],
        },
      ],
    });

    expect(readiness.items[0]).toMatchObject({
      hasCost: true,
      costSource: "tech-card",
      costReference: 36,
      techCard: expect.objectContaining({
        pricedIngredientRows: 2,
        fullyCosted: true,
      }),
    });
  });

  test("counts tech-card ingredient links resolved by article and name", () => {
    const readiness = buildMenuMarginReadiness({
      dishes: [
        {
          dishName: "Pasta",
          dishGroup: "Kitchen",
          dishAmountInt: 10,
          dishSumInt: 6000,
        },
      ],
      products: [
        {
          id: "pasta-base",
          name: "Pasta",
          sizePrices: [],
        },
        {
          id: "flour",
          name: "Flour",
          article: "F-10",
          unit: "g",
          pricePerKg: 100,
          sizePrices: [],
        },
        {
          id: "sauce",
          name: "Tomato sauce",
          unit: "g",
          pricePerKg: 200,
          sizePrices: [],
        },
      ],
      techCards: [
        {
          id: "chart-pasta",
          productId: "pasta-base",
          productName: "Pasta",
          items: [
            {
              article: "F-10",
              productName: "Wheat flour",
              amount: 200,
              unit: "g",
            },
            {
              productName: "Tomato sauce",
              amount: 100,
              unit: "g",
            },
          ],
        },
      ],
    });

    expect(readiness.items[0].techCard).toMatchObject({
      linkedIngredientRows: 2,
      pricedIngredientRows: 2,
      costReference: 40,
      usable: true,
      fullyCosted: true,
    });
    expect(readiness.usableTechCardDishes).toBe(1);
  });

  test("surfaces low proven margin as an owner risk", () => {
    const readiness = buildMenuMarginReadiness({
      dishes: [
        {
          dishName: "Cheap pasta",
          dishGroup: "Kitchen",
          dishAmountInt: 10,
          dishSumInt: 1000,
        },
        {
          dishName: "Healthy steak",
          dishGroup: "Kitchen",
          dishAmountInt: 10,
          dishSumInt: 10000,
        },
        {
          dishName: "Unknown dessert",
          dishGroup: "Kitchen",
          dishAmountInt: 10,
          dishSumInt: 2000,
        },
      ],
      products: [
        {
          id: "cheap-pasta",
          name: "Cheap pasta",
          purchasePrice: 55,
          sizePrices: [],
        },
        {
          id: "healthy-steak",
          name: "Healthy steak",
          purchasePrice: 250,
          sizePrices: [],
        },
        {
          id: "unknown-dessert",
          name: "Unknown dessert",
          sizePrices: [],
        },
      ],
    });

    expect(readiness).toMatchObject({
      costedDishes: 2,
      grossProfit: 7950,
      averageGrossMarginPct: 72.3,
    });
    expect(readiness.topMarginRisks).toEqual([
      expect.objectContaining({
        dishName: "Cheap pasta",
        grossMarginPct: 45,
        costReference: 55,
        salePrice: 100,
        grossProfit: 450,
        costSource: "product",
      }),
    ]);
    expect(readiness.topMarginRisks).not.toEqual(
      expect.arrayContaining([
        expect.objectContaining({ dishName: "Unknown dessert" }),
      ]),
    );
  });

  test("does not prove food cost from partially priced tech-card ingredients", () => {
    const readiness = buildMenuMarginReadiness({
      dishes: [
        {
          dishName: "Pasta",
          dishGroup: "Kitchen",
          dishAmountInt: 10,
          dishSumInt: 30000,
        },
      ],
      products: [
        {
          id: "pasta-base",
          name: "Pasta",
          sizePrices: [],
        },
        {
          id: "flour",
          name: "Flour",
          unit: "g",
          pricePerKg: 100,
          sizePrices: [],
        },
        {
          id: "egg",
          name: "Egg",
          unit: "pcs",
          sizePrices: [],
        },
      ],
      techCards: [
        {
          id: "chart-pasta",
          productId: "pasta-base",
          productName: "Pasta",
          items: [
            {
              productId: "flour",
              productName: "Flour",
              amount: 0.12,
              unit: "kg",
            },
            {
              productId: "egg",
              productName: "Egg",
              amount: 2,
              unit: "pcs",
            },
          ],
        },
      ],
    });

    expect(readiness.items[0]).toMatchObject({
      hasCost: false,
      costSource: null,
      costReference: null,
      hasUsableTechCard: true,
      techCard: expect.objectContaining({
        pricedIngredientRows: 1,
        costReference: null,
        fullyCosted: false,
      }),
    });
    expect(buildMenuMarginNextAction(readiness)).toMatchObject({
      kind: "missing-cost",
      title: "Техкарта есть, не хватает цен ингредиентов",
    });
  });

  test("marks margin as ready when all key dishes have proven cost", () => {
    const readiness = buildMenuMarginReadiness({
      dishes: [
        {
          dishName: "Chef steak",
          dishGroup: "Kitchen",
          dishAmountInt: 10,
          dishSumInt: 10000,
        },
      ],
      products: [
        {
          id: "steak",
          name: "Chef steak",
          purchasePrice: 700,
          sizePrices: [],
        },
      ],
    });

    expect(buildMenuMarginNextAction(readiness)).toMatchObject({
      kind: "ready",
      title: "Маржу можно разбирать",
      blocker: null,
    });
  });
});
