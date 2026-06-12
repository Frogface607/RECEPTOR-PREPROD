import { describe, expect, test } from "vitest";
import { buildMenuEngineering } from "./menu-engineering";
import type { DishStat } from "./iiko/models";

const dishes: DishStat[] = [
  {
    dishName: "Стейк",
    dishGroup: "Горячая кухня",
    dishAmountInt: 20,
    dishSumInt: 100_000,
  },
  {
    dishName: "Бургер",
    dishGroup: "Горячая кухня",
    dishAmountInt: 40,
    dishSumInt: 60_000,
  },
  {
    dishName: "Салат",
    dishGroup: "Закуски и салаты",
    dishAmountInt: 30,
    dishSumInt: 25_000,
  },
  {
    dishName: "Чай",
    dishGroup: "Безалкогольные напитки",
    dishAmountInt: 70,
    dishSumInt: 10_000,
  },
  {
    dishName: "Десерт",
    dishGroup: "Десерты",
    dishAmountInt: 12,
    dishSumInt: 5_000,
  },
];

describe("buildMenuEngineering", () => {
  test("splits dishes into ABC tiers by cumulative revenue contribution", () => {
    const report = buildMenuEngineering(dishes);

    expect(report.totalRevenue).toBe(200_000);
    expect(report.aItems.map((item) => item.dishName)).toEqual([
      "Стейк",
      "Бургер",
    ]);
    expect(report.bItems.map((item) => item.dishName)).toEqual(["Салат"]);
    expect(report.cItems.map((item) => item.dishName)).toEqual([
      "Чай",
      "Десерт",
    ]);
    expect(report.aRevenueShare).toBe(80);
  });

  test("highlights volume traps and keeps margin caveat explicit", () => {
    const report = buildMenuEngineering(dishes);

    expect(report.volumeTrap?.dishName).toBe("Чай");
    expect(report.hero?.dishName).toBe("Стейк");
    expect(report.marginCaveat).toContain("техкарт");
    expect(report.actions).toHaveLength(3);
  });

  test("returns an empty report for no dishes", () => {
    const report = buildMenuEngineering([]);

    expect(report.totalRevenue).toBe(0);
    expect(report.aItems).toEqual([]);
    expect(report.actions[0]).toContain("iiko");
  });
});
