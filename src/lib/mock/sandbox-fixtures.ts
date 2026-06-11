/**
 * Sandbox restaurant — deterministic fixtures that shape the mock iiko data.
 *
 * Numbers are anchored on a plausible modern restaurant operating profile:
 * - 9.5 years operating, ₽150–300k daily revenue, weekend swing.
 * - Menu split across hot dishes, appetizers, bar, desserts and non-alcoholic drinks.
 * - One operating shift per day, 18:00 → 04:00 next day.
 *
 * Everything here is pure data. The mock client (`lib/iiko/mock-client.ts`)
 * reads from this file and constructs Promise-returning responses.
 */

import type {
  Organization,
  Product,
  Group,
} from "@/lib/iiko/models";

export const SANDBOX_VENUE: Organization = {
  id: "sandbox-restaurant",
  name: "Тестовый ресторан",
  timezone: "Asia/Irkutsk",
};

/** Menu category split — must sum to 1.0 so category stats reconcile with revenue. */
export const SANDBOX_CATEGORY_MIX: Record<string, number> = {
  "Горячая кухня": 0.32,
  "Закуски и салаты": 0.22,
  "Барная карта": 0.21,
  Десерты: 0.1,
  "Безалкогольные напитки": 0.15,
};

export const SANDBOX_CATEGORIES = Object.keys(SANDBOX_CATEGORY_MIX);

export const SANDBOX_GROUPS: Group[] = SANDBOX_CATEGORIES.map((name, i) => ({
  id: `g-${i + 1}`,
  name,
}));

/**
 * Mock menu — realistic restaurant items; prices in ₽; categories
 * align with the mix above. The relative `weight` controls how much of a
 * category's revenue each dish takes (per-category weights sum to 1.0).
 */
type FixtureDish = {
  id: string;
  name: string;
  category: string;
  price: number;
  weight: number;
};

export const SANDBOX_DISHES: FixtureDish[] = [
  // Горячая кухня (5 items, weights sum to 1)
  { id: "d-1", name: "Стейк из говядины", category: "Горячая кухня", price: 1190, weight: 0.3 },
  { id: "d-2", name: "Томлёные говяжьи щёки", category: "Горячая кухня", price: 960, weight: 0.24 },
  { id: "d-3", name: "Паста с морепродуктами", category: "Горячая кухня", price: 890, weight: 0.2 },
  { id: "d-4", name: "Утиная грудка", category: "Горячая кухня", price: 980, weight: 0.16 },
  { id: "d-5", name: "Ризотто с грибами", category: "Горячая кухня", price: 690, weight: 0.1 },

  // Закуски и салаты (4 items)
  { id: "d-6", name: "Тёплый салат с креветками", category: "Закуски и салаты", price: 720, weight: 0.32 },
  { id: "d-7", name: "Тартар из говядины", category: "Закуски и салаты", price: 790, weight: 0.27 },
  { id: "d-8", name: "Брускетта с томатами", category: "Закуски и салаты", price: 420, weight: 0.23 },
  { id: "d-9", name: "Сырная тарелка", category: "Закуски и салаты", price: 860, weight: 0.18 },

  // Барная карта (4 items)
  { id: "d-10", name: "Авторский коктейль", category: "Барная карта", price: 620, weight: 0.34 },
  { id: "d-11", name: "Игристое по бокалам", category: "Барная карта", price: 540, weight: 0.26 },
  { id: "d-12", name: "Винная позиция", category: "Барная карта", price: 690, weight: 0.22 },
  { id: "d-13", name: "Классический коктейль", category: "Барная карта", price: 580, weight: 0.18 },

  // Десерты (3 items)
  { id: "d-14", name: "Медовик", category: "Десерты", price: 390, weight: 0.42 },
  { id: "d-15", name: "Шоколадный фондан", category: "Десерты", price: 460, weight: 0.33 },
  { id: "d-16", name: "Сезонный десерт", category: "Десерты", price: 430, weight: 0.25 },

  // Безалкогольные напитки (4 items)
  { id: "d-17", name: "Домашний лимонад", category: "Безалкогольные напитки", price: 310, weight: 0.36 },
  { id: "d-18", name: "Фильтр-кофе", category: "Безалкогольные напитки", price: 220, weight: 0.26 },
  { id: "d-19", name: "Чай авторский", category: "Безалкогольные напитки", price: 360, weight: 0.22 },
  { id: "d-20", name: "Минеральная вода", category: "Безалкогольные напитки", price: 240, weight: 0.16 },
];

/** Convert dishes to iiko-style `Product` objects (with sizePrices). */
export const SANDBOX_PRODUCTS: Product[] = SANDBOX_DISHES.map((d) => ({
  id: d.id,
  name: d.name,
  parentGroupId:
    SANDBOX_GROUPS.find((g) => g.name === d.category)?.id ?? "g-misc",
  sizePrices: [{ price: { currentPrice: d.price } }],
}));

/** Three shift managers cycling through the week (deterministic). */
export const SANDBOX_SHIFT_EMPLOYEES = ["Анна", "Илья", "Мария"] as const;

/**
 * Deterministic per-day revenue for the sandbox restaurant.
 *
 * Weekend > Friday > weekday baseline, with a small ±25k jitter derived from
 * the date string so the same date always returns the same revenue across
 * test runs and screenshots.
 */
export function sandboxDailyRevenue(isoDate: string): number {
  const day = new Date(isoDate + "T00:00:00Z").getUTCDay();
  const isWeekend = day === 0 || day === 6;
  const isFriday = day === 5;
  const base = isWeekend ? 270_000 : isFriday ? 220_000 : 170_000;

  let hash = 0;
  for (let i = 0; i < isoDate.length; i++) {
    hash = (hash * 31 + isoDate.charCodeAt(i)) | 0;
  }
  const jitter = (Math.abs(hash) % 50_000) - 25_000;

  return Math.max(80_000, Math.min(400_000, base + jitter));
}
