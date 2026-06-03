/**
 * Session resolution with demo-mode fallback.
 *
 * `resolveSessionUser` is the pure decision: given whether Supabase is
 * configured and the (maybe) logged-in Supabase user, return the app's
 * session user. The async glue (`getCurrentUser`) wires it to the real
 * server client.
 *
 * Demo mode (Supabase absent) returns a synthetic user so the dashboard and
 * tools stay open for the Михно demo without a real login.
 */

import { getServerSupabase } from "@/lib/db/server";
import { isSupabaseConfigured } from "@/lib/db/env";

export type SessionUser = {
  id: string;
  email: string;
  isDemo: boolean;
};

export const DEMO_USER: SessionUser = {
  id: "demo-user",
  email: "demo@receptorai.pro",
  isDemo: true,
};

export function resolveSessionUser(input: {
  configured: boolean;
  supabaseUser: { id: string; email?: string | null } | null;
}): SessionUser | null {
  if (!input.configured) return DEMO_USER;
  if (!input.supabaseUser) return null;
  return {
    id: input.supabaseUser.id,
    email: input.supabaseUser.email ?? "",
    isDemo: false,
  };
}

/** Resolve the current session user on the server (RSC / route handlers). */
export async function getCurrentUser(): Promise<SessionUser | null> {
  const configured = isSupabaseConfigured();
  if (!configured) return DEMO_USER;

  const supabase = await getServerSupabase();
  if (!supabase) return DEMO_USER;

  const {
    data: { user },
  } = await supabase.auth.getUser();

  return resolveSessionUser({ configured, supabaseUser: user });
}
