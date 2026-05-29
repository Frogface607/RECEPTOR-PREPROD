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

        <nav className="ml-auto flex items-center gap-7 text-sm text-muted-foreground">
          <Link href="/#что-делает" className="transition-colors hover:text-foreground">
            Что делает
          </Link>
          <Link href="/#цены" className="transition-colors hover:text-foreground">
            Цены
          </Link>
          <Link href="/dashboard/edison-demo" className="transition-colors hover:text-foreground">
            Демо
          </Link>
          <Link href="/auth" className="transition-colors hover:text-foreground hidden sm:inline">
            Войти
          </Link>
          <LinkButton
            href="/auth"
            size="sm"
            className="bg-brand text-primary-foreground hover:bg-brand-hover"
          >
            Начать бесплатно
          </LinkButton>
        </nav>
      </div>
    </header>
  );
}
