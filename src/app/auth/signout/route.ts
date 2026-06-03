import { NextResponse } from "next/server";
import { getServerSupabase } from "@/lib/db/server";

/** Sign the user out and return to the landing page. No-op in demo mode. */
export async function GET(request: Request) {
  const supabase = await getServerSupabase();
  if (supabase) {
    await supabase.auth.signOut();
  }
  return NextResponse.redirect(new URL("/", new URL(request.url).origin));
}
