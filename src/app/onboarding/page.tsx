import type { Metadata } from "next";
import Link from "next/link";
import { redirect } from "next/navigation";
import { OnboardingWizard } from "./wizard";
import { isSupabaseConfigured } from "@/lib/db/env";
import { getCurrentUser } from "@/lib/auth/session";

export const metadata: Metadata = {
  title: "Настройка — RECEPTOR",
};

export const dynamic = "force-dynamic";

export default async function OnboardingPage() {
  const demoMode = !isSupabaseConfigured();
  const user = await getCurrentUser();
  if (!demoMode && !user) {
    redirect("/auth?next=/onboarding");
  }
  const previewMode = demoMode || Boolean(user?.isDemo);

  return (
    <main className="relative min-h-screen overflow-hidden px-6 py-14">
      <div aria-hidden className="pointer-events-none absolute inset-0 -z-10">
        <div className="absolute left-1/2 top-[-25%] h-[520px] w-[760px] -translate-x-1/2 rounded-full bg-brand/10 blur-[150px]" />
      </div>

      <div className="mx-auto max-w-xl">
        <Link href="/" className="mb-10 flex items-baseline gap-2">
          <span className="text-[14px] font-medium tracking-[0.22em] text-foreground">
            RECEPTOR
          </span>
          <span className="font-display italic text-muted-foreground text-[14px]">
            чувствует кухню
          </span>
        </Link>

        <p className="text-[11px] uppercase tracking-[0.22em] text-brand">
          Настройка · 1 минута
        </p>
        <h1 className="mt-3 mb-9 text-balance text-3xl font-medium tracking-[-0.02em]">
          Давайте подключим ваш{" "}
          <span className="font-display italic text-brand">ресторан</span>
        </h1>

        <OnboardingWizard demoMode={previewMode} />
      </div>
    </main>
  );
}
