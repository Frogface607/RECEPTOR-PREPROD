import { NextResponse } from "next/server";
import {
  DEVELOPER_SESSION_COOKIE,
  developerSessionCookieValue,
  isDeveloperAccessEnabled,
  verifyDeveloperAccessKey,
} from "@/lib/auth/developer";

function safeNextPath(value: FormDataEntryValue | null): string {
  const raw = typeof value === "string" ? value : "";
  if (raw.startsWith("/") && !raw.startsWith("//")) return raw;
  return "/dashboard/dev-venue";
}

export async function POST(request: Request) {
  const form = await request.formData();
  const accessKey = String(form.get("accessKey") ?? "");
  const next = safeNextPath(form.get("next"));
  const url = new URL(request.url);

  if (!isDeveloperAccessEnabled() || !verifyDeveloperAccessKey(accessKey)) {
    return NextResponse.redirect(
      new URL(`/auth?dev=invalid&next=${encodeURIComponent(next)}`, url.origin),
    );
  }

  const response = NextResponse.redirect(new URL(next, url.origin));
  response.cookies.set(DEVELOPER_SESSION_COOKIE, developerSessionCookieValue(), {
    httpOnly: true,
    sameSite: "lax",
    secure: url.protocol === "https:",
    path: "/",
    maxAge: 60 * 60 * 24 * 14,
  });

  return response;
}
