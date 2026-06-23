"use client";

import { useState } from "react";
import Link from "next/link";
import { Menu } from "lucide-react";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { NavContent } from "./nav-content";

/**
 * Mobile-only top bar with a hamburger that opens the dashboard nav as a
 * left Sheet drawer. Hidden on lg+ where the persistent <aside> takes over.
 */
export function MobileTopbar({
  activeHref,
  venueId,
  venueName,
  venueMeta,
}: {
  activeHref?: string;
  venueId?: string;
  venueName?: string;
  venueMeta?: string;
}) {
  const [open, setOpen] = useState(false);

  return (
    <div className="sticky top-0 z-40 flex h-14 items-center gap-3 border-b border-border/40 bg-background/85 px-4 backdrop-blur-xl lg:hidden">
      <Sheet open={open} onOpenChange={setOpen}>
        <SheetTrigger
          className="inline-flex size-9 items-center justify-center rounded-md border border-border/60 bg-card/60 text-foreground transition-colors hover:bg-card"
          aria-label="Открыть меню"
        >
          <Menu className="size-4" />
        </SheetTrigger>
        <SheetContent
          side="left"
          className="flex w-[280px] flex-col gap-0 border-r border-border/60 bg-sidebar p-0"
        >
          <SheetHeader className="h-14 justify-center border-b border-border/40 px-6">
            <SheetTitle className="text-[14px] font-medium tracking-[0.22em] text-foreground">
              RECEPTOR
            </SheetTitle>
          </SheetHeader>
          <NavContent
            activeHref={activeHref}
            venueId={venueId}
            venueName={venueName}
            venueMeta={venueMeta}
            onNavigate={() => setOpen(false)}
          />
        </SheetContent>
      </Sheet>

      <Link href="/" className="flex items-baseline gap-2">
        <span className="text-[13px] font-medium tracking-[0.22em] text-foreground">
          RECEPTOR
        </span>
      </Link>
    </div>
  );
}
