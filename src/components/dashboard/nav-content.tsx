import Link from "next/link";
import {
  LayoutDashboard,
  MessageSquare,
  Wrench,
  Settings,
  LogOut,
  UsersRound,
  UserRound,
  CircleHelp,
  type LucideIcon,
} from "lucide-react";

export type NavItem = {
  href: string;
  matchHref: string;
  icon: LucideIcon;
  label: string;
};

export function getDashboardNav(venueId = "dev-venue"): NavItem[] {
  const dashboardHref = `/dashboard/${encodeURIComponent(venueId)}`;

  return [
    { href: "/me", matchHref: "/me", icon: UserRound, label: "Мой кабинет" },
    {
      href: dashboardHref,
      matchHref: dashboardHref,
      icon: LayoutDashboard,
      label: "Owner Cockpit",
    },
    {
      href: `${dashboardHref}?chat=1`,
      matchHref: "/copilot",
      icon: MessageSquare,
      label: "Copilot",
    },
    {
      href: `/team?role=owner&venueId=${encodeURIComponent(venueId)}`,
      matchHref: "/team",
      icon: UsersRound,
      label: "Team OS",
    },
    { href: "/tools", matchHref: "/tools", icon: Wrench, label: "Инструменты" },
    {
      href: "/settings",
      matchHref: "/settings",
      icon: Settings,
      label: "Настройки",
    },
    { href: "/#что-делает", matchHref: "/help", icon: CircleHelp, label: "Помощь" },
  ];
}

/**
 * Shared sidebar body — venue card + nav links + sign-out.
 * Rendered by both the desktop <aside> and the mobile Sheet drawer so the
 * two never drift apart.
 */
export function NavContent({
  activeHref,
  venueId = "dev-venue",
  venueName = "Рабочий кабинет",
  venueMeta = "Restaurant OS",
  onNavigate,
}: {
  activeHref?: string;
  venueId?: string;
  venueName?: string;
  venueMeta?: string;
  onNavigate?: () => void;
}) {
  const nav = getDashboardNav(venueId);

  return (
    <>
      <nav className="flex-1 px-3 py-6">
        <p className="px-3 pb-2 text-[10px] uppercase tracking-[0.2em] text-muted-foreground">
          Заведение
        </p>
        <div className="rounded-lg border border-border/50 bg-card/50 px-3 py-2.5">
          <p className="truncate text-[13px] font-medium text-foreground">
            {venueName}
          </p>
          <p className="text-[11px] uppercase tracking-widest text-muted-foreground">
            {venueMeta}
          </p>
        </div>

        <p className="mt-7 px-3 pb-2 text-[10px] uppercase tracking-[0.2em] text-muted-foreground">
          Меню
        </p>
        <ul className="space-y-0.5">
          {nav.map((item) => {
            const Icon = item.icon;
            const isActive =
              activeHref === item.matchHref || activeHref === item.href;
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  onClick={onNavigate}
                  className={
                    "flex items-center gap-3 rounded-md px-3 py-2.5 text-[13px] transition-colors " +
                    (isActive
                      ? "bg-sidebar-accent text-foreground"
                      : "text-muted-foreground hover:bg-sidebar-accent/60 hover:text-foreground")
                  }
                >
                  <Icon className="size-4 shrink-0" />
                  <span>{item.label}</span>
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      <div className="border-t border-border/40 px-3 py-4">
        <a
          href="/auth/signout"
          onClick={onNavigate}
          className="flex items-center gap-3 rounded-md px-3 py-2.5 text-[13px] text-muted-foreground transition-colors hover:bg-sidebar-accent/60 hover:text-foreground"
        >
          <LogOut className="size-4 shrink-0" />
          <span>Выйти</span>
        </a>
      </div>
    </>
  );
}
