import type { Metadata } from "next";
import Link from "next/link";
import { redirect } from "next/navigation";
import { OnboardingWizard } from "./wizard";
import { isSupabaseConfigured } from "@/lib/db/env";
import { getCurrentUser } from "@/lib/auth/session";
import { getServerSupabase } from "@/lib/db/server";

export const metadata: Metadata = {
  title: "Настройка — RECEPTOR",
};

export const dynamic = "force-dynamic";

type OnboardingSearchParams = Record<string, string | string[] | undefined>;

function searchParamFlag(
  params: OnboardingSearchParams,
  key: string,
): boolean {
  const value = params[key];
  return Array.isArray(value) ? value.includes("1") : value === "1";
}

async function getFirstOwnedVenueId(userId: string): Promise<string | null> {
  const supabase = await getServerSupabase();
  if (!supabase) return null;

  const { data } = await supabase
    .from("venues")
    .select("id")
    .eq("owner_user_id", userId)
    .order("created_at", { ascending: false })
    .limit(1)
    .maybeSingle<{ id: string }>();

  return data?.id ?? null;
}

export default async function OnboardingPage({
  searchParams,
}: {
  searchParams: Promise<OnboardingSearchParams>;
}) {
  const sp = await searchParams;
  const forceNewVenue = searchParamFlag(sp, "new");
  const demoMode = !isSupabaseConfigured();
  const user = await getCurrentUser();

  if (!demoMode && !user) {
    const nextPath = forceNewVenue ? "/onboarding?new=1" : "/onboarding";
    redirect(`/auth?next=${encodeURIComponent(nextPath)}`);
  }

  if (!demoMode && user && !user.isDemo && !forceNewVenue) {
    const venueId = await getFirstOwnedVenueId(user.id);
    if (venueId) {
      redirect(`/dashboard/${venueId}`);
    }
  }

  const previewMode = demoMode || Boolean(user?.isDemo);

  return (
    <main className="relative min-h-screen overflow-hidden px-6 py-14">
      <div aria-hidden className="pointer-events-none absolute inset-0 -z-10">
      </div>

      <div className="mx-auto max-w-xl">
        <Link href="/" className="mb-10 flex items-baseline gap-2">
          <span className="text-[14px] font-medium tracking-[0.22em] text-foreground">
            RECEPTOR
          </span>
          <span className="text-[12px] uppercase tracking-[0.16em] text-muted-foreground">
            рабочий кабинет ресторана
          </span>
        </Link>

        <p className="text-[11px] uppercase tracking-[0.22em] text-brand">
          Настройка · 1 минута
        </p>
        <h1 className="mt-3 mb-9 text-balance text-3xl font-medium tracking-[-0.02em]">
          Давайте подключим ваш ресторан
        </h1>

        <OnboardingWizard demoMode={previewMode} />
      </div>
    </main>
  );
}
