import type { ReactNode } from "react";
import { ChatDrawer } from "@/components/chat/chat-drawer";
import { DashboardSidebar } from "./sidebar";
import { MobileTopbar } from "./mobile-topbar";

export function AppShell({
  activeHref,
  children,
  venueId = "dev-venue",
  venueName = "Рабочий кабинет",
  venueMeta = "Restaurant OS",
  chat = true,
}: {
  activeHref?: string;
  children: ReactNode;
  venueId?: string;
  venueName?: string;
  venueMeta?: string;
  chat?: boolean;
}) {
  return (
    <div className="flex min-h-screen bg-background">
      <DashboardSidebar
        activeHref={activeHref}
        venueId={venueId}
        venueName={venueName}
        venueMeta={venueMeta}
      />
      <div className="flex min-w-0 flex-1 flex-col">
        <MobileTopbar
          activeHref={activeHref}
          venueId={venueId}
          venueName={venueName}
          venueMeta={venueMeta}
        />
        {children}
      </div>
      {chat ? <ChatDrawer venueId={venueId} venueName={venueName} /> : null}
    </div>
  );
}
