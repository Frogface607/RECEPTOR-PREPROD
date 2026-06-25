import type { Metadata } from "next";
import { redirect } from "next/navigation";
import { SiteFooter } from "@/components/marketing/site-footer";
import { SiteHeader } from "@/components/marketing/site-header";
import { ContextBuilder } from "./context-builder";
import { getCurrentUser, type SessionUser } from "@/lib/auth/session";
import { getVenueAccess } from "@/lib/auth/venue-access";
import { isSupabaseConfigured } from "@/lib/db/env";
import { getServerSupabase } from "@/lib/db/server";
import { listKnownVenues } from "@/lib/venues/get-venue";
import type { VenueContextAnswers } from "@/lib/venues/context-questionnaire";

export const metadata: Metadata = {
  title: "Память заведения — RECEPTOR",
  description:
    "Анкета ресторана для советника Receptor: формат, экономика, команда, системы и ограничения AI.",
};

type ContextVenueOption = {
  id: string;
  name: string;
  city: string;
};

async function listContextVenues(
  user: SessionUser | null,
): Promise<ContextVenueOption[]> {
  if (!user || user.isDemo) {
    return listKnownVenues().map((venue) => ({
      id: venue.id,
      name: venue.name,
      city: venue.city,
    }));
  }

  const supabase = await getServerSupabase();
  if (!supabase) return [];

  const { data } = await supabase
    .from("venues")
    .select("id,name,city")
    .eq("owner_user_id", user.id)
    .order("created_at", { ascending: false });

  return (
    (data ?? []) as Array<{ id: string; name: string; city: string | null }>
  ).map((venue) => ({
    id: venue.id,
    name: venue.name,
    city: venue.city ?? "",
  }));
}

export default async function ContextPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const user = await getCurrentUser();
  if (isSupabaseConfigured() && !user) {
    redirect("/auth?next=/context");
  }

  const venues = await listContextVenues(user);
  const sp = await searchParams;
  const requestedVenueId = Array.isArray(sp.venueId) ? sp.venueId[0] : sp.venueId;
  const selectedVenueId = requestedVenueId || venues[0]?.id || "";
  const access = selectedVenueId ? await getVenueAccess(selectedVenueId) : null;

  if (selectedVenueId && access && !access.ok) {
    redirect("/context");
  }

  const venue = access && access.ok ? access.venue : null;
  const initialAnswers: VenueContextAnswers = venue?.context ?? {};

  return (
    <>
      <SiteHeader />
      <main className="flex-1">
        <ContextBuilder
          initialAnswers={initialAnswers}
          venueId={venue?.id ?? ""}
          venueName={venue?.name ?? "Заведение не выбрано"}
          venues={venues}
          canPersist={Boolean(venue)}
          sandboxMode={Boolean(user?.isDemo)}
        />
      </main>
      <SiteFooter />
    </>
  );
}
