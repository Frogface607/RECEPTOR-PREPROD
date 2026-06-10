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
          <span className="hidden font-display italic text-muted-foreground text-[15px] leading-none transition-colors group-hover:text-brand sm:inline">
            · чувствует кухню
          </span>
        </Link>

        <nav className="ml-auto flex items-center gap-5 text-sm text-muted-foreground sm:gap-7">
          <Link
            href="/#что-делает"
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
            href="/#цены"
            className="hidden transition-colors hover:text-foreground sm:inline"
          >
            Цены
          </Link>
          <Link
            href="/dashboard/dev-venue"
            className="transition-colors hover:text-foreground"
          >
            Preview
          </Link>
          <Link
            href="/auth"
            className="hidden transition-colors hover:text-foreground sm:inline"
          >
            Войти
          </Link>
          <LinkButton
            href="/auth"
            size="sm"
            className="bg-brand text-primary-foreground hover:bg-brand-hover"
          >
            <span className="hidden sm:inline">Начать бесплатно</span>
            <span className="sm:hidden">Начать</span>
          </LinkButton>
        </nav>
      </div>
    </header>
  );
}
