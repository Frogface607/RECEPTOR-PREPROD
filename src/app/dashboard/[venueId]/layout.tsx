import { notFound } from "next/navigation";
import { DashboardSidebar } from "@/components/dashboard/sidebar";
import { MobileTopbar } from "@/components/dashboard/mobile-topbar";
import { ChatDrawer } from "@/components/chat/chat-drawer";
import { getVenue } from "@/lib/venues/get-venue";

export default async function DashboardLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ venueId: string }>;
}) {
  const { venueId } = await params;
  const venue = getVenue(venueId);
  if (!venue) notFound();

  return (
    <div className="flex min-h-screen">
      <DashboardSidebar activeHref={`/dashboard/${venueId}`} />
      <div className="flex-1 min-w-0 flex flex-col">
        <MobileTopbar activeHref={`/dashboard/${venueId}`} />
        {children}
      </div>
      <ChatDrawer venueId={venue.id} venueName={venue.name} />
    </div>
  );
}
