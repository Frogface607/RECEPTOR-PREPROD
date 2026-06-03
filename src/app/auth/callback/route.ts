import { NextResponse } from "next/server";
import { getServerSupabase } from "@/lib/db/server";

/**
 * Magic-link / OAuth callback. Supabase redirects here with a `code` (PKCE)
 * which we exchange for a session, then forward the user to `next`
 * (onboarding by default).
 */
export async function GET(request: Request) {
  const url = new URL(request.url);
  const code = url.searchParams.get("code");
  const next = url.searchParams.get("next") ?? "/onboarding";

  if (code) {
    const supabase = await getServerSupabase();
    if (supabase) {
      await supabase.auth.exchangeCodeForSession(code);
    }
  }

  return NextResponse.redirect(new URL(next, url.origin));
}
