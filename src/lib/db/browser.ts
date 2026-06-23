"use client";

/**
 * Browser-side Supabase client (client components — auth forms, etc.).
 * Returns null when Supabase is not configured (demo mode).
 */

import { createBrowserClient } from "@supabase/ssr";

const PLACEHOLDERS = new Set([
  "your-url-here",
  "your_url_here",
  "your-anon-key",
  "your_anon_key",
  "changeme",
  "todo",
]);

const browserSupabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL ?? "";
const browserSupabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? "";

function isBrowserSupabaseConfigured(): boolean {
  const url = browserSupabaseUrl.trim();
  const anon = browserSupabaseAnonKey.trim();

  if (!url || !anon) return false;
  if (PLACEHOLDERS.has(url.toLowerCase()) || PLACEHOLDERS.has(anon.toLowerCase())) {
    return false;
  }

  return /^https:\/\/.+\.supabase\.(co|in|net)/i.test(url);
}

export function getBrowserSupabase() {
  if (!isBrowserSupabaseConfigured()) return null;
  return createBrowserClient(
    browserSupabaseUrl.trim(),
    browserSupabaseAnonKey.trim(),
  );
}
