import { describe, expect, test } from "vitest";
import {
  buildMenuMarginReadiness,
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
});
