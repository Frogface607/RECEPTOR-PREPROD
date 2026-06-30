import { describe, expect, test } from "vitest";
import { buildLaborMarginBridge } from "./labor-margin-bridge";
import { buildMenuMarginReadiness } from "./menu-margin-readiness";
import { buildLaborBi } from "./team/labor-bi";

describe("buildLaborMarginBridge", () => {
  test("keeps employee labor risk tied to missing margin proof", () => {
    const labor = buildLaborBi({
      shifts: [
        {
          shiftId: "shift-1",
          openTime: "2026-06-26T12:00:00",
          closeTime: "2026-06-26T22:00:00",
          revenue: 50000,
          items: 100,
          employee: "Смена",
          workers: [
            {
              memberId: "chef",
              name: "Мария",
              hours: 10,
              shiftPay: 18000,
              sales: 50000,
            },
          ],
        },
      ],
    });
    const margin = buildMenuMarginReadiness({
      dishes: [
        {
          dishName: "Burger",
          dishGroup: "Kitchen",
          dishAmountInt: 10,
          dishSumInt: 20000,
        },
      ],
      products: [{ id: "burger", name: "Burger", sizePrices: [] }],
    });

    const bridge = buildLaborMarginBridge({ labor, margin });

    expect(bridge).toMatchObject({
      tone: "watch",
      title: "ФОТ по Мария требует маржу рядом",
      employee: expect.objectContaining({ name: "Мария" }),
      marginCoveragePct: 0,
    });
    expect(bridge.detail).toContain("себестоимость покрывает только 0%");
    expect(bridge.action).toContain("график");
  });

  test("connects expensive employee with proven weak margin dish", () => {
    const labor = buildLaborBi({
      shifts: [
        {
          shiftId: "shift-1",
          openTime: "2026-06-26T12:00:00",
          closeTime: "2026-06-26T22:00:00",
          revenue: 50000,
          items: 100,
          employee: "Смена",
          workers: [
            {
              memberId: "chef",
              name: "Мария",
              hours: 10,
              shiftPay: 18000,
              sales: 50000,
            },
          ],
        },
      ],
    });
    const margin = buildMenuMarginReadiness({
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
      ],
    });

    const bridge = buildLaborMarginBridge({ labor, margin });

    expect(bridge).toMatchObject({
      tone: "risk",
      title: "Проверить смену: Мария и слабая маржа",
      marginRiskDish: "Cheap pasta",
      marginRiskGrossMarginPct: 45,
      marginRiskGrossProfitGap: 150,
      averageGrossMarginPct: 72.3,
    });
    expect(bridge.detail).toContain("Cheap pasta");
    expect(bridge.detail).toContain("Недобор валовой прибыли");
    expect(bridge.detail).toMatch(/150 ₽/);
    expect(bridge.action).toContain("цену");
  });

  test("marks labor and margin ready when there are no personal FOT risks", () => {
    const labor = buildLaborBi({
      shifts: [
        {
          shiftId: "shift-1",
          openTime: "2026-06-26T12:00:00",
          closeTime: "2026-06-26T22:00:00",
          revenue: 90000,
          items: 180,
          employee: "Смена",
          workers: [
            {
              memberId: "waiter",
              name: "Илья",
              hours: 10,
              shiftPay: 5000,
              sales: 90000,
            },
          ],
        },
      ],
    });
    const margin = buildMenuMarginReadiness({
      dishes: [
        {
          dishName: "Steak",
          dishGroup: "Kitchen",
          dishAmountInt: 10,
          dishSumInt: 10000,
        },
      ],
      products: [
        {
          id: "steak",
          name: "Steak",
          purchasePrice: 250,
          sizePrices: [],
        },
      ],
    });

    expect(buildLaborMarginBridge({ labor, margin })).toMatchObject({
      tone: "good",
      title: "ФОТ и маржа можно разбирать вместе",
      employee: null,
      marginCoveragePct: 100,
    });
  });
});
