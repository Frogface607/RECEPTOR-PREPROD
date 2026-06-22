import Link from "next/link";
import {
  LayoutDashboard,
  MessageSquare,
  Wrench,
  Settings,
  BookOpen,
  LogOut,
  UsersRound,
  type LucideIcon,
} from "lucide-react";

export type NavItem = {
  href: string;
  icon: LucideIcon;
  label: string;
};

export const DASHBOARD_NAV: NavItem[] = [
  { href: "/dashboard/dev-venue", icon: LayoutDashboard, label: "BI кабинет" },
  { href: "/dashboard/dev-venue?chat=1", icon: MessageSquare, label: "Copilot" },
  { href: "/team?role=owner", icon: UsersRound, label: "Team OS" },
  { href: "/tools", icon: Wrench, label: "Инструменты" },
  { href: "/settings", icon: Settings, label: "Настройки" },
  { href: "/#что-делает", icon: BookOpen, label: "Помощь" },
];

/**
 * Shared sidebar body — venue card + nav links + sign-out.
 * Rendered by both the desktop <aside> and the mobile Sheet drawer so the
 * two never drift apart.
 */
export function NavContent({
  activeHref,
  onNavigate,
}: {
  activeHref?: string;
  onNavigate?: () => void;
}) {
  return (
    <>
      <nav className="flex-1 px-3 py-6">
        <p className="px-3 pb-2 text-[10px] uppercase tracking-[0.2em] text-muted-foreground">
          Заведение
        </p>
        <div className="rounded-lg border border-border/50 bg-card/50 px-3 py-2.5">
          <p className="text-[13px] font-medium text-foreground">Рабочий кабинет</p>
          <p className="text-[11px] uppercase tracking-widest text-muted-foreground">
            BI · Copilot
          </p>
        </div>

        <p className="mt-7 px-3 pb-2 text-[10px] uppercase tracking-[0.2em] text-muted-foreground">
          Меню
        </p>
        <ul className="space-y-0.5">
          {DASHBOARD_NAV.map((item) => {
            const Icon = item.icon;
            const isActive = activeHref === item.href;
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
