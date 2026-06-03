/**
 * Server-side Supabase client (RSC / route handlers / server actions).
 *
 * Uses @supabase/ssr cookie wiring so auth sessions flow through Next.js
 * cookies. Returns null when Supabase is not configured — callers must
 * handle the demo-mode (null) path.
 */

import { cookies } from "next/headers";
import { createServerClient } from "@supabase/ssr";
import { isSupabaseConfigured, supabaseUrl, supabaseAnonKey } from "./env";

export async function getServerSupabase() {
  if (!isSupabaseConfigured()) return null;

  const cookieStore = await cookies();

  return createServerClient(supabaseUrl(), supabaseAnonKey(), {
    cookies: {
      getAll() {
        return cookieStore.getAll();
      },
      setAll(cookiesToSet) {
        try {
          for (const { name, value, options } of cookiesToSet) {
            cookieStore.set(name, value, options);
          }
        } catch {
          // setAll from a Server Component — safe to ignore; middleware
          // refreshes the session cookie on the next request.
        }
      },
    },
  });
}
