import { NextResponse } from "next/server";
import { getServerSupabase } from "@/lib/db/server";
import { DEVELOPER_SESSION_COOKIE } from "@/lib/auth/developer";

/** Sign the user out and return to the landing page. No-op in demo mode. */
export async function GET(request: Request) {
  const supabase = await getServerSupabase();
  if (supabase) {
    await supabase.auth.signOut();
  }
  const response = NextResponse.redirect(
    new URL("/", new URL(request.url).origin),
  );
  response.cookies.delete(DEVELOPER_SESSION_COOKIE);
  return response;
}
