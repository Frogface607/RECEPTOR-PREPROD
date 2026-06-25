import { NextResponse, type NextRequest } from "next/server";
import { createServerClient } from "@supabase/ssr";
import { normalizeStaffLoginToEmail } from "@/lib/auth/staff-login";
import { isSupabaseConfigured, supabaseAnonKey, supabaseUrl } from "@/lib/db/env";

function safeNextPath(value: unknown): string {
  return typeof value === "string" &&
    value.startsWith("/") &&
    !value.startsWith("//")
    ? value
    : "/me";
}

function errorResponse(message: string, status = 400) {
  return NextResponse.json({ ok: false, error: message }, { status });
}

export async function POST(request: NextRequest) {
  if (!isSupabaseConfigured()) {
    return errorResponse("Auth is not configured in this environment.", 503);
  }

  let payload: unknown;
  try {
    payload = await request.json();
  } catch {
    return errorResponse("Invalid login request.");
  }

  const body = payload && typeof payload === "object" ? payload : {};
  const login = "login" in body ? body.login : "";
  const password = "password" in body ? body.password : "";
  const next = safeNextPath("next" in body ? body.next : "/me");
  const email = normalizeStaffLoginToEmail(typeof login === "string" ? login : "");

  if (!email || typeof password !== "string" || password.length < 6) {
    return errorResponse("Проверьте логин и пароль.");
  }

  let response = NextResponse.json({ ok: true, next });
  const supabase = createServerClient(supabaseUrl(), supabaseAnonKey(), {
    cookies: {
      getAll() {
        return request.cookies.getAll();
      },
      setAll(cookiesToSet) {
        for (const { name, value } of cookiesToSet) {
          request.cookies.set(name, value);
        }
        response = NextResponse.json({ ok: true, next });
        for (const { name, value, options } of cookiesToSet) {
          response.cookies.set(name, value, options);
        }
      },
    },
  });

  const { error } = await supabase.auth.signInWithPassword({
    email,
    password,
  });

  if (error) {
    return errorResponse(error.message, 401);
  }

  return response;
}
