"use client";

/**
 * Browser-side Supabase client (client components — auth forms, etc.).
 * Returns null when Supabase is not configured (demo mode).
 */

import { createBrowserClient } from "@supabase/ssr";
import { isSupabaseConfigured, supabaseUrl, supabaseAnonKey } from "./env";

export function getBrowserSupabase() {
  if (!isSupabaseConfigured()) return null;
  return createBrowserClient(supabaseUrl(), supabaseAnonKey());
}
