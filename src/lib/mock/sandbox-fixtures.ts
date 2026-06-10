/**
 * Sandbox restaurant — deterministic fixtures that shape the mock iiko data.
 *
 * Numbers are anchored on a plausible casual restaurant operating profile:
 * - 9.5 years operating, ₽150–300k daily revenue, weekend swing.
 * - Menu skewed toward burgers ("Нечто" signature) + crafted beer + cocktails.
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
  name: "Ресторан Премьера",
  timezone: "Asia/Irkutsk",
};

/** Menu category split — must sum to 1.0 so category stats reconcile with revenue. */
export const SANDBOX_CATEGORY_MIX: Record<string, number> = {
  Бургеры: 0.35,
  "Крафтовое пиво": 0.25,
  "Авторские коктейли": 0.18,
  Закуски: 0.15,
  Десерты: 0.07,
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
  // Бургеры (5 items, weights sum to 1)
  { id: "d-1", name: "Бургер Нечто", category: "Бургеры", price: 690, weight: 0.38 },
  { id: "d-2", name: "Бургер Двойной Нечто", category: "Бургеры", price: 890, weight: 0.22 },
  { id: "d-3", name: "Бургер Чёрный", category: "Бургеры", price: 720, weight: 0.18 },
  { id: "d-4", name: "Чикен бургер", category: "Бургеры", price: 590, weight: 0.14 },
  { id: "d-5", name: "Веган бургер", category: "Бургеры", price: 640, weight: 0.08 },

  // Крафтовое пиво (4 items)
  { id: "d-6", name: "Крафт IPA 0.5л", category: "Крафтовое пиво", price: 380, weight: 0.4 },
  { id: "d-7", name: "Крафт Стаут 0.5л", category: "Крафтовое пиво", price: 420, weight: 0.25 },
  { id: "d-8", name: "Сидр яблочный 0.5л", category: "Крафтовое пиво", price: 350, weight: 0.2 },
  { id: "d-9", name: "Лагер крафт 0.5л", category: "Крафтовое пиво", price: 340, weight: 0.15 },

  // Авторские коктейли (4 items)
  { id: "d-10", name: "Signature Sour", category: "Авторские коктейли", price: 590, weight: 0.32 },
  { id: "d-11", name: "Old Fashioned", category: "Авторские коктейли", price: 690, weight: 0.28 },
  { id: "d-12", name: "House Negroni", category: "Авторские коктейли", price: 650, weight: 0.22 },
  { id: "d-13", name: "Tom Collins", category: "Авторские коктейли", price: 580, weight: 0.18 },

  // Закуски (4 items)
  { id: "d-14", name: "Картофель фри", category: "Закуски", price: 290, weight: 0.32 },
  { id: "d-15", name: "Куриные крылья", category: "Закуски", price: 490, weight: 0.28 },
  { id: "d-16", name: "Сырные палочки", category: "Закуски", price: 390, weight: 0.22 },
  { id: "d-17", name: "Начос с сальсой", category: "Закуски", price: 450, weight: 0.18 },

  // Десерты (3 items)
  { id: "d-18", name: "Чизкейк", category: "Десерты", price: 380, weight: 0.42 },
  { id: "d-19", name: "Брауни", category: "Десерты", price: 320, weight: 0.33 },
  { id: "d-20", name: "Мороженое в карамели", category: "Десерты", price: 290, weight: 0.25 },
];

/** Convert dishes to iiko-style `Product` objects (with sizePrices). */
export const SANDBOX_PRODUCTS: Product[] = SANDBOX_DISHES.map((d) => ({
  id: d.id,
  name: d.name,
  parentGroupId:
    SANDBOX_GROUPS.find((g) => g.name === d.category)?.id ?? "g-misc",
  sizePrices: [{ price: { currentPrice: d.price } }],
}));

/** Three shift cashiers cycling through the week (deterministic). */
export const SANDBOX_SHIFT_EMPLOYEES = ["Маша", "Дима", "Аня"] as const;

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
