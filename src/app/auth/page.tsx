import type { Metadata } from "next";
import Link from "next/link";
import { AuthForm } from "./auth-form";
import { isSupabaseConfigured } from "@/lib/db/env";
import {
  isDeveloperAccessEnabled,
  isPresentationAccessVisible,
} from "@/lib/auth/developer";

export const metadata: Metadata = {
  title: "Вход — RECEPTOR",
};

function safeNextPath(value: string | string[] | undefined): string {
  const raw = Array.isArray(value) ? value[0] : value;
  if (raw?.startsWith("/") && !raw.startsWith("//")) return raw;
  return "/onboarding";
}

export default async function AuthPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const demoMode = !isSupabaseConfigured();
  const sp = await searchParams;
  const nextPath = safeNextPath(sp.next);
  const devError = sp.dev === "invalid";
  const showPresentationAccess = sp.present === "1";

  return (
    <main className="relative flex min-h-screen items-center justify-center overflow-hidden px-6 py-16">
      <div aria-hidden className="pointer-events-none absolute inset-0 -z-10">
      </div>

      <div className="w-full max-w-md">
        <Link
          href="/"
          className="mb-10 flex items-baseline justify-center gap-2"
        >
          <span className="text-[15px] font-medium tracking-[0.22em] text-foreground">
            RECEPTOR
          </span>
          <span className="text-[12px] uppercase tracking-[0.16em] text-muted-foreground">
            ресторанный copilot
          </span>
        </Link>

        <AuthForm
          demoMode={demoMode}
          developerMode={
            isDeveloperAccessEnabled() ||
            (showPresentationAccess && isPresentationAccessVisible())
          }
          developerError={devError}
          nextPath={nextPath}
        />

        <p className="mt-8 text-center text-[12px] text-muted-foreground">
          Нажимая «Прислать ссылку», вы соглашаетесь с условиями использования.
        </p>
      </div>
    </main>
  );
}
