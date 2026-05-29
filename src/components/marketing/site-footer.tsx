import Link from "next/link";

export function SiteFooter() {
  return (
    <footer className="border-t border-border/40 bg-background">
      <div className="mx-auto max-w-7xl px-6 py-12">
        <div className="grid grid-cols-1 gap-10 md:grid-cols-4">
          <div className="md:col-span-2">
            <div className="flex items-baseline gap-2">
              <span className="text-sm font-medium tracking-[0.22em]">RECEPTOR</span>
              <span className="font-display italic text-muted-foreground text-base">
                чувствует кухню
              </span>
            </div>
            <p className="mt-4 max-w-sm text-sm text-muted-foreground leading-relaxed">
              AI-копайлот владельца ресторана. Подключение к iiko, живая
              аналитика и чат с цифрами вечера.
            </p>
          </div>

          <div>
            <h3 className="mb-3 text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">
              Продукт
            </h3>
            <ul className="space-y-2 text-sm">
              <li>
                <Link href="/#что-делает" className="text-foreground/80 transition-colors hover:text-foreground">
                  Возможности
                </Link>
              </li>
              <li>
                <Link href="/#цены" className="text-foreground/80 transition-colors hover:text-foreground">
                  Цены
                </Link>
              </li>
              <li>
                <Link href="/dashboard/edison-demo" className="text-foreground/80 transition-colors hover:text-foreground">
                  Живое демо
                </Link>
              </li>
            </ul>
          </div>

          <div>
            <h3 className="mb-3 text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">
              Студия
            </h3>
            <ul className="space-y-2 text-sm">
              <li>
                <a
                  href="https://frogface.space"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-foreground/80 transition-colors hover:text-foreground"
                >
                  frogface.space
                </a>
              </li>
              <li>
                <a
                  href="mailto:bro@frogface.space"
                  className="text-foreground/80 transition-colors hover:text-foreground"
                >
                  bro@frogface.space
                </a>
              </li>
            </ul>
          </div>
        </div>

        <div className="mt-12 flex flex-col gap-2 border-t border-border/40 pt-6 text-xs text-muted-foreground sm:flex-row sm:items-center sm:justify-between">
          <p>
            Сделано в студии{" "}
            <a
              href="https://frogface.space"
              target="_blank"
              rel="noopener noreferrer"
              className="text-foreground/80 transition-colors hover:text-brand"
            >
              Frogface
            </a>{" "}
            · Иркутск ⟷ Бангкок
          </p>
          <p>© 2026 Frogface Studio. Все права защищены.</p>
        </div>
      </div>
    </footer>
  );
}
