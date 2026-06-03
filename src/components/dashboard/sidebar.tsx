import Link from "next/link";
import { NavContent } from "./nav-content";

export function DashboardSidebar({ activeHref }: { activeHref?: string }) {
  return (
    <aside className="hidden h-screen sticky top-0 w-60 shrink-0 flex-col border-r border-border/40 bg-sidebar lg:flex">
      <div className="flex h-16 items-center gap-2 border-b border-border/40 px-6">
        <Link href="/" className="flex items-baseline gap-2">
          <span className="text-[14px] font-medium tracking-[0.22em] text-foreground">
            RECEPTOR
          </span>
        </Link>
      </div>
      <NavContent activeHref={activeHref} />
    </aside>
  );
}
