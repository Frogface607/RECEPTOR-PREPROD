/**
 * Zod schemas for the iiko data shapes used in Receptor v2.
 *
 * Port of selected Pydantic models from v1 (`docs/v1-iiko-reference/iiko_models.py`
 * and `iiko_rms_models.py`), reduced to the fields actually rendered in the
 * Phase 2 dashboard and exposed to the Phase 4 AI tools.
 *
 * The same schemas validate both:
 *   1. Real iiko Cloud / RMS API responses (in `cloud-client.ts` / `rms-client.ts`)
 *   2. Edison-shaped fixtures (in `lib/mock/`)
 *
 * Why Zod (vs hand-rolled types):
 *   - Single source of truth for type + runtime validation.
 *   - Cheap defence against schema drift in the iiko API.
 *   - Fixtures stay honest: if we drift the fixture shape, tests fail loudly.
 */

import { z } from "zod";

// ---------------------------------------------------------------------------
// Primitive helpers
// ---------------------------------------------------------------------------

/** Strict ISO date "YYYY-MM-DD". */
const IsoDate = z.string().regex(/^\d{4}-\d{2}-\d{2}$/, {
  message: "expected ISO date YYYY-MM-DD",
});

/** Loose ISO datetime (Y-M-DTH:M:S, no timezone enforcement) — iiko returns local. */
const IsoDateTime = z
  .string()
  .regex(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/, {
    message: "expected ISO datetime YYYY-MM-DDTHH:MM:SS",
  });

/** Non-negative number (revenue, items, prices). */
const NonNegative = z.number().nonnegative();

// ---------------------------------------------------------------------------
// Organization / Product / Group (nomenclature side)
// ---------------------------------------------------------------------------

export const OrganizationSchema = z.object({
  id: z.string().min(1),
  name: z.string().min(1),
  timezone: z.string().optional(),
});
export type Organization = z.infer<typeof OrganizationSchema>;

const ProductPriceSchema = z.object({
  currentPrice: NonNegative,
});

const ProductSizePriceSchema = z.object({
  price: ProductPriceSchema,
});

export const ProductSchema = z.object({
  id: z.string().min(1),
  name: z.string().min(1),
  parentGroupId: z.string().optional(),
  sizePrices: z.array(ProductSizePriceSchema).default([]),
});
export type Product = z.infer<typeof ProductSchema>;

export const GroupSchema = z.object({
  id: z.string().min(1),
  name: z.string().min(1),
  parentId: z.string().optional(),
});
export type Group = z.infer<typeof GroupSchema>;

// ---------------------------------------------------------------------------
// Period selection (UI ↔ client ↔ AI tools)
// ---------------------------------------------------------------------------

const PRESET_PERIOD_TYPES = [
  "TODAY",
  "YESTERDAY",
  "CURRENT_WEEK",
  "LAST_WEEK",
  "CURRENT_MONTH",
  "LAST_MONTH",
] as const;

export const PeriodTypeSchema = z.enum([
  ...PRESET_PERIOD_TYPES,
  "CUSTOM",
]);
export type PeriodType = z.infer<typeof PeriodTypeSchema>;

const PresetPeriodSchema = z.object({
  type: z.enum(PRESET_PERIOD_TYPES),
});

const CustomPeriodSchema = z.object({
  type: z.literal("CUSTOM"),
  from: IsoDate,
  to: IsoDate,
});

export const PeriodSchema = z.discriminatedUnion("type", [
  PresetPeriodSchema,
  CustomPeriodSchema,
]);
export type Period = z.infer<typeof PeriodSchema>;

// ---------------------------------------------------------------------------
// BI shapes — what the dashboard renders
// ---------------------------------------------------------------------------

export const RevenuePointSchema = z.object({
  date: IsoDate,
  revenue: NonNegative,
});
export type RevenuePoint = z.infer<typeof RevenuePointSchema>;

export const RevenueSummarySchema = z.object({
  revenue: NonNegative,
  averageCheck: NonNegative,
  itemsSold: NonNegative,
  uniqueDishes: NonNegative,
  points: z.array(RevenuePointSchema),
});
export type RevenueSummary = z.infer<typeof RevenueSummarySchema>;

export const DishStatSchema = z.object({
  dishName: z.string().min(1),
  dishGroup: z.string().min(1),
  dishAmountInt: z.number().int().nonnegative(),
  dishSumInt: NonNegative,
});
export type DishStat = z.infer<typeof DishStatSchema>;

export const CategoryStatSchema = z.object({
  categoryName: z.string().min(1),
  dishSumInt: NonNegative,
});
export type CategoryStat = z.infer<typeof CategoryStatSchema>;

export const ShiftStatSchema = z.object({
  shiftId: z.string().min(1),
  openTime: IsoDateTime,
  closeTime: IsoDateTime.optional(),
  revenue: NonNegative,
  items: z.number().int().nonnegative(),
  employee: z.string().min(1),
});
export type ShiftStat = z.infer<typeof ShiftStatSchema>;
