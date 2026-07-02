import Link from "next/link";
import { LinkButton } from "@/components/ui/link-button";

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-40 border-b border-border/40 bg-background/70 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-7xl items-center gap-8 px-6">
        <Link href="/" className="flex items-center gap-2 group">
          <span className="text-[15px] font-medium tracking-[0.22em] text-foreground">
            RECEPTOR
          </span>
          <span className="hidden text-[12px] uppercase tracking-[0.16em] text-muted-foreground transition-colors group-hover:text-foreground sm:inline">
            restaurant OS
          </span>
        </Link>

        <nav className="ml-auto flex items-center gap-5 text-sm text-muted-foreground sm:gap-7">
          <Link
            href="/#features"
            className="hidden transition-colors hover:text-foreground md:inline"
          >
            Что делает
          </Link>
          <Link
            href="/tools"
            className="hidden transition-colors hover:text-foreground md:inline"
          >
            Инструменты
          </Link>
          <Link
            href="/platform"
            className="hidden transition-colors hover:text-foreground md:inline"
          >
            Платформа
          </Link>
          <Link
            href="/pilot"
            className="hidden transition-colors hover:text-foreground lg:inline"
          >
            Пилот
          </Link>
          <Link
            href="/#pricing"
            className="hidden transition-colors hover:text-foreground sm:inline"
          >
            Цены
          </Link>
          <Link
            href="/auth?next=/me"
            className="hidden transition-colors hover:text-foreground sm:inline"
          >
            Войти
          </Link>
          <LinkButton
            href="/pilot"
            size="sm"
            className="bg-brand text-primary-foreground hover:bg-brand-hover"
          >
            <span className="hidden sm:inline">Смотреть показ</span>
            <span className="sm:hidden">Показ</span>
          </LinkButton>
        </nav>
      </div>
    </header>
  );
}

