import { z } from "zod";
import { PeriodTypeSchema as BasePeriodTypeSchema } from "@/lib/iiko/models";
import type { IikoClient } from "@/lib/iiko/types";

export const PeriodTypeSchema = BasePeriodTypeSchema;
export type { PeriodType, Period } from "@/lib/iiko/models";

/** Alias used internally so future replacements (Cloud, Supabase-backed) don't break tool sigs. */
export type IikoClientWithTools = IikoClient;
