import { type NextRequest, NextResponse } from "next/server";
import { createServerClient } from "@supabase/ssr";
import { isSupabaseConfigured, supabaseUrl, supabaseAnonKey } from "@/lib/db/env";

/**
 * Refreshes the Supabase auth session cookie on every request so server
 * components always see a fresh session. No-op in demo mode (Supabase env
 * absent), so local dev and pre-keys deploys pass straight through.
 *
 * We deliberately do NOT hard-gate /dashboard here — the demo must stay open.
 * Page-level guards can redirect when a real session is required.
 */
export async function middleware(request: NextRequest) {
  if (!isSupabaseConfigured()) {
    return NextResponse.next();
  }

  const authCode = request.nextUrl.searchParams.get("code");
  if (authCode && request.nextUrl.pathname !== "/auth/callback") {
    const callbackUrl = request.nextUrl.clone();
    callbackUrl.pathname = "/auth/callback";
    callbackUrl.search = "";
    callbackUrl.searchParams.set("code", authCode);
    callbackUrl.searchParams.set(
      "next",
      request.nextUrl.searchParams.get("next") ?? "/me",
    );
    return NextResponse.redirect(callbackUrl);
  }

  let response = NextResponse.next({ request });

  const supabase = createServerClient(supabaseUrl(), supabaseAnonKey(), {
    cookies: {
      getAll() {
        return request.cookies.getAll();
      },
      setAll(cookiesToSet) {
        for (const { name, value } of cookiesToSet) {
          request.cookies.set(name, value);
        }
        response = NextResponse.next({ request });
        for (const { name, value, options } of cookiesToSet) {
          response.cookies.set(name, value, options);
        }
      },
    },
  });

  // Touch the session so @supabase/ssr can rotate the cookie if needed.
  await supabase.auth.getUser();

  return response;
}

export const config = {
  matcher: [
    // Run on everything except static assets and image optimisation.
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};
