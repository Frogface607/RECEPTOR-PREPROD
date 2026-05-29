import { describe, expect, test } from "vitest";
import {
  OrganizationSchema,
  ProductSchema,
  PeriodTypeSchema,
  PeriodSchema,
  RevenuePointSchema,
  RevenueSummarySchema,
  DishStatSchema,
  CategoryStatSchema,
  ShiftStatSchema,
  type Organization,
  type Period,
} from "./models";

describe("OrganizationSchema", () => {
  test("parses minimal valid org", () => {
    const valid = { id: "11111111-2222-3333-4444-555555555555", name: "Edison Bar" };
    const parsed = OrganizationSchema.parse(valid);
    expect(parsed.name).toBe("Edison Bar");
  });

  test("rejects missing name", () => {
    const result = OrganizationSchema.safeParse({ id: "abc" });
    expect(result.success).toBe(false);
  });

  test("accepts optional timezone", () => {
    const parsed: Organization = OrganizationSchema.parse({
      id: "org1",
      name: "Edison",
      timezone: "Asia/Irkutsk",
    });
    expect(parsed.timezone).toBe("Asia/Irkutsk");
  });
});

describe("ProductSchema", () => {
  test("parses product with prices array", () => {
    const parsed = ProductSchema.parse({
      id: "p1",
      name: "Бургер Нечто",
      parentGroupId: "g-burgers",
      sizePrices: [{ price: { currentPrice: 690 } }],
    });
    expect(parsed.name).toBe("Бургер Нечто");
    expect(parsed.sizePrices[0].price.currentPrice).toBe(690);
  });

  test("requires id and name", () => {
    expect(ProductSchema.safeParse({ id: "p1" }).success).toBe(false);
    expect(ProductSchema.safeParse({ name: "x" }).success).toBe(false);
  });
});

describe("PeriodTypeSchema and PeriodSchema", () => {
  test("accepts known period types", () => {
    for (const t of [
      "TODAY",
      "YESTERDAY",
      "CURRENT_WEEK",
      "LAST_WEEK",
      "CURRENT_MONTH",
      "LAST_MONTH",
      "CUSTOM",
    ] as const) {
      expect(PeriodTypeSchema.parse(t)).toBe(t);
    }
  });

  test("rejects unknown period type", () => {
    expect(PeriodTypeSchema.safeParse("WHENEVER").success).toBe(false);
  });

  test("PeriodSchema parses preset type without dates", () => {
    const p: Period = PeriodSchema.parse({ type: "LAST_WEEK" });
    expect(p.type).toBe("LAST_WEEK");
  });

  test("PeriodSchema requires from+to when type is CUSTOM", () => {
    const ok = PeriodSchema.safeParse({
      type: "CUSTOM",
      from: "2026-05-01",
      to: "2026-05-29",
    });
    expect(ok.success).toBe(true);

    const bad = PeriodSchema.safeParse({ type: "CUSTOM" });
    expect(bad.success).toBe(false);
  });
});

describe("RevenuePointSchema", () => {
  test("parses one day point", () => {
    const parsed = RevenuePointSchema.parse({
      date: "2026-05-29",
      revenue: 187500,
    });
    expect(parsed.revenue).toBe(187500);
  });

  test("rejects negative revenue", () => {
    expect(
      RevenuePointSchema.safeParse({ date: "2026-05-29", revenue: -10 }).success,
    ).toBe(false);
  });

  test("rejects malformed date", () => {
    expect(
      RevenuePointSchema.safeParse({ date: "29 мая", revenue: 1000 }).success,
    ).toBe(false);
  });
});

describe("RevenueSummarySchema", () => {
  test("parses summary with all metrics", () => {
    const parsed = RevenueSummarySchema.parse({
      revenue: 4500000,
      averageCheck: 1850,
      itemsSold: 2430,
      uniqueDishes: 78,
      points: [{ date: "2026-05-01", revenue: 150000 }],
    });
    expect(parsed.averageCheck).toBe(1850);
    expect(parsed.points).toHaveLength(1);
  });

  test("accepts empty points array", () => {
    const parsed = RevenueSummarySchema.parse({
      revenue: 0,
      averageCheck: 0,
      itemsSold: 0,
      uniqueDishes: 0,
      points: [],
    });
    expect(parsed.points).toEqual([]);
  });
});

describe("DishStatSchema", () => {
  test("parses one dish stat row", () => {
    const parsed = DishStatSchema.parse({
      dishName: "Бургер Нечто",
      dishGroup: "Бургеры",
      dishAmountInt: 240,
      dishSumInt: 165600,
    });
    expect(parsed.dishSumInt).toBe(165600);
  });

  test("rejects non-integer count", () => {
    expect(
      DishStatSchema.safeParse({
        dishName: "x",
        dishGroup: "y",
        dishAmountInt: 1.5,
        dishSumInt: 100,
      }).success,
    ).toBe(false);
  });
});

describe("CategoryStatSchema", () => {
  test("parses category aggregate", () => {
    const parsed = CategoryStatSchema.parse({
      categoryName: "Крафтовое пиво",
      dishSumInt: 980000,
    });
    expect(parsed.categoryName).toBe("Крафтовое пиво");
  });
});

describe("ShiftStatSchema", () => {
  test("parses one closed shift", () => {
    const parsed = ShiftStatSchema.parse({
      shiftId: "shift-2026-05-29-1",
      openTime: "2026-05-29T18:00:00",
      closeTime: "2026-05-30T03:00:00",
      revenue: 215000,
      items: 168,
      employee: "Маша",
    });
    expect(parsed.revenue).toBe(215000);
  });

  test("allows open shift (no closeTime)", () => {
    const parsed = ShiftStatSchema.parse({
      shiftId: "shift-2026-05-29-2",
      openTime: "2026-05-29T18:00:00",
      revenue: 0,
      items: 0,
      employee: "Маша",
    });
    expect(parsed.closeTime).toBeUndefined();
  });
});
