import { notFound, redirect } from "next/navigation";
import { DashboardSidebar } from "@/components/dashboard/sidebar";
import { MobileTopbar } from "@/components/dashboard/mobile-topbar";
import { ChatDrawer } from "@/components/chat/chat-drawer";
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
    <div className="flex min-h-screen">
      <DashboardSidebar activeHref={`/dashboard/${venueId}`} />
      <div className="flex-1 min-w-0 flex flex-col">
        <MobileTopbar activeHref={`/dashboard/${venueId}`} />
        {children}
      </div>
      <ChatDrawer venueId={access.venue.id} venueName={access.venue.name} />
    </div>
  );
}
