/**
 * Supabase configuration gate.
 *
 * Receptor degrades gracefully: with real Supabase env vars it runs full
 * auth; without them (local dev, or a fresh deploy before keys land) it falls
 * into "demo mode" where the dashboard stays open via a synthetic session.
 * This keeps the Михно demo bulletproof regardless of env state.
 */

const PLACEHOLDERS = new Set([
  "your-url-here",
  "your_url_here",
  "your-anon-key",
  "your_anon_key",
  "changeme",
  "todo",
]);

export function isSupabaseConfigured(
  env: Record<string, string | undefined> = process.env,
): boolean {
  const url = (env.NEXT_PUBLIC_SUPABASE_URL ?? "").trim();
  const anon = (env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? "").trim();

  if (!url || !anon) return false;
  if (PLACEHOLDERS.has(url.toLowerCase()) || PLACEHOLDERS.has(anon.toLowerCase()))
    return false;

  // Must be an https supabase-style endpoint.
  return /^https:\/\/.+\.supabase\.(co|in|net)/i.test(url);
}

export function supabaseUrl(): string {
  return (process.env.NEXT_PUBLIC_SUPABASE_URL ?? "").trim();
}

export function supabaseAnonKey(): string {
  return (process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? "").trim();
}
