import type { DishStat } from "./iiko/models";

export type AbcTier = "A" | "B" | "C";

export type MenuEngineeringItem = DishStat & {
  tier: AbcTier;
  revenueShare: number;
  cumulativeShare: number;
  amountShare: number;
  averagePrice: number;
};

export type MenuEngineeringReport = {
  totalRevenue: number;
  totalAmount: number;
  aRevenueShare: number;
  aItems: MenuEngineeringItem[];
  bItems: MenuEngineeringItem[];
  cItems: MenuEngineeringItem[];
  hero: MenuEngineeringItem | null;
  volumeTrap: MenuEngineeringItem | null;
  marginCaveat: string;
  actions: string[];
};

const MAIN_REVENUE_CUTOFF = 80;
const MID_REVENUE_CUTOFF = 95;

function roundPct(value: number): number {
  return Math.round(value * 10) / 10;
}

function getTier(cumulativeShare: number, previousShare: number): AbcTier {
  if (previousShare === 0 || cumulativeShare <= MAIN_REVENUE_CUTOFF) return "A";
  if (cumulativeShare <= MID_REVENUE_CUTOFF) return "B";
  return "C";
}

function listNames(items: MenuEngineeringItem[], limit = 2): string {
  return items
    .slice(0, limit)
    .map((item) => `«${item.dishName}»`)
    .join(", ");
}

export function buildMenuEngineering(
  dishes: DishStat[],
): MenuEngineeringReport {
  const totalRevenue = dishes.reduce((sum, dish) => sum + dish.dishSumInt, 0);
  const totalAmount = dishes.reduce((sum, dish) => sum + dish.dishAmountInt, 0);
  const marginCaveat =
    "Это pre-margin ABC: прибыльность станет точной после связи с техкартами, закупочными ценами и iiko-номенклатурой.";

  if (!dishes.length || totalRevenue <= 0) {
    return {
      totalRevenue: 0,
      totalAmount,
      aRevenueShare: 0,
      aItems: [],
      bItems: [],
      cItems: [],
      hero: null,
      volumeTrap: null,
      marginCaveat,
      actions: [
        "Подключить iiko-продажи, чтобы Receptor собрал ABC-карту меню по реальным блюдам.",
        "После подключения техкарт добавить маржинальный слой: выручка, количество, себестоимость и прибыль.",
        "Использовать первую карту как повестку для шефа: что держим, что усиливаем, что убираем.",
      ],
    };
  }

  let cumulativeShare = 0;
  const items = [...dishes]
    .sort((a, b) => b.dishSumInt - a.dishSumInt)
    .map((dish) => {
      const previousShare = cumulativeShare;
      const revenueShare = (dish.dishSumInt / totalRevenue) * 100;
      const amountShare =
        totalAmount > 0 ? (dish.dishAmountInt / totalAmount) * 100 : 0;
      cumulativeShare += revenueShare;

      return {
        ...dish,
        tier: getTier(cumulativeShare, previousShare),
        revenueShare: roundPct(revenueShare),
        cumulativeShare: roundPct(cumulativeShare),
        amountShare: roundPct(amountShare),
        averagePrice:
          dish.dishAmountInt > 0 ? dish.dishSumInt / dish.dishAmountInt : 0,
      };
    });

  const aItems = items.filter((item) => item.tier === "A");
  const bItems = items.filter((item) => item.tier === "B");
  const cItems = items.filter((item) => item.tier === "C");
  const aRevenueShare = roundPct(
    aItems.reduce((sum, item) => sum + item.dishSumInt, 0) / totalRevenue * 100,
  );
  const hero = items[0] ?? null;
  const volumeTrap =
    [...items]
      .filter(
        (item) =>
          item.tier !== "A" && item.amountShare >= item.revenueShare * 1.8,
      )
      .sort((a, b) => b.amountShare - a.amountShare)[0] ?? null;

  const actions = [
    aItems.length
      ? `Проверить маржу A-позиций: ${listNames(aItems)}. Это ядро выручки, но без техкарт оно может скрывать дорогие ингредиенты.`
      : "Выделить A-позиции после первой выгрузки iiko и проверить их техкарты.",
    volumeTrap
      ? `Разобрать ${listNames([volumeTrap], 1)}: продаётся часто, но вклад в выручку ниже объёма. Проверь цену, порцию и апсейл.`
      : bItems.length
        ? `Дожать B-позиции: ${listNames(bItems)}. Проверь подачу, фото, описание и рекомендацию официанта.`
        : "Найти блюда-кандидаты для апсейла после накопления продаж.",
    cItems.length
      ? `Хвост C: ${cItems.length} поз. Решить по каждой: убрать, переименовать, заменить или оставить как сервисную позицию.`
      : "Следить за хвостом меню: слабые позиции должны иметь понятную причину существования.",
  ];

  return {
    totalRevenue,
    totalAmount,
    aRevenueShare,
    aItems,
    bItems,
    cItems,
    hero,
    volumeTrap,
    marginCaveat,
    actions,
  };
}
