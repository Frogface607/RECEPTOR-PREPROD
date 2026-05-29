import Link from "next/link";
import { LayoutDashboard, MessageSquare, Settings, BookOpen, LogOut } from "lucide-react";

type NavItem = {
  href: string;
  icon: typeof LayoutDashboard;
  label: string;
  hint?: string;
};

const TOP_NAV: NavItem[] = [
  { href: "/dashboard/edison-demo", icon: LayoutDashboard, label: "Dashboard" },
  { href: "/dashboard/edison-demo?chat=1", icon: MessageSquare, label: "AI чат" },
  { href: "/settings", icon: Settings, label: "Настройки" },
  { href: "/#что-делает", icon: BookOpen, label: "Помощь" },
];

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

      <nav className="flex-1 px-3 py-6">
        <p className="px-3 pb-2 text-[10px] uppercase tracking-[0.2em] text-muted-foreground">
          Заведение
        </p>
        <div className="rounded-lg border border-border/50 bg-card/60 px-3 py-2.5">
          <p className="text-[13px] font-medium text-foreground">Edison Bar</p>
          <p className="text-[11px] uppercase tracking-widest text-muted-foreground">
            Иркутск · Cloud
          </p>
        </div>

        <p className="mt-7 px-3 pb-2 text-[10px] uppercase tracking-[0.2em] text-muted-foreground">
          Меню
        </p>
        <ul className="space-y-0.5">
          {TOP_NAV.map((item) => {
            const Icon = item.icon;
            const isActive = activeHref === item.href;
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={
                    "flex items-center gap-3 rounded-md px-3 py-2 text-[13px] transition-colors " +
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
        <Link
          href="/auth?signout=1"
          className="flex items-center gap-3 rounded-md px-3 py-2 text-[13px] text-muted-foreground transition-colors hover:bg-sidebar-accent/60 hover:text-foreground"
        >
          <LogOut className="size-4 shrink-0" />
          <span>Выйти</span>
        </Link>
      </div>
    </aside>
  );
}
