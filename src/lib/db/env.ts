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

  return /^https:\/\/.+\.supabase\.(co|in|net)/i.test(url);
}

export function supabaseUrl(): string {
  return (process.env.NEXT_PUBLIC_SUPABASE_URL ?? "").trim();
}

export function supabaseAnonKey(): string {
  return (process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? "").trim();
}
