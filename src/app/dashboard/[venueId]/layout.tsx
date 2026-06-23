import { notFound, redirect } from "next/navigation";
import { AppShell } from "@/components/dashboard/app-shell";
import { getVenueAccess } from "@/lib/auth/venue-access";

export default async function DashboardLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ venueId: string }>;
}) {
  const { venueId } = await params;
  const access = await getVenueAccess(venueId);
  if (!access.ok) {
    if (access.status === 401) {
      redirect(`/auth?next=/dashboard/${encodeURIComponent(venueId)}`);
    }
    notFound();
  }

  return (
    <AppShell
      activeHref={`/dashboard/${venueId}`}
      venueId={access.venue.id}
      venueName={access.venue.name}
      venueMeta={`${access.venue.city} · ${access.venue.type}`}
    >
      {children}
    </AppShell>
  );
}
