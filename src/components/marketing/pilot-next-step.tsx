import { ArrowRight } from "lucide-react";
import { LinkButton } from "@/components/ui/link-button";

export function PilotNextStep({
  eyebrow = "Дальше в демо",
  title,
  text,
  primaryHref,
  primaryLabel,
  secondaryHref = "/pilot",
  secondaryLabel = "Весь маршрут",
}: {
  eyebrow?: string;
  title: string;
  text: string;
  primaryHref: string;
  primaryLabel: string;
  secondaryHref?: string;
  secondaryLabel?: string;
}) {
  return (
    <section className="border-b border-border/40">
      <div className="mx-auto flex max-w-7xl flex-col gap-6 px-6 py-10 md:flex-row md:items-center md:justify-between">
        <div className="max-w-2xl">
          <p className="text-[11px] uppercase tracking-[0.22em] text-brand">
            {eyebrow}
          </p>
          <h2 className="mt-3 text-2xl font-medium">{title}</h2>
          <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
            {text}
          </p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-3">
          <LinkButton
            href={primaryHref}
            className="bg-brand text-primary-foreground hover:bg-brand-hover"
          >
            {primaryLabel}
            <ArrowRight className="size-4" />
          </LinkButton>
          <LinkButton href={secondaryHref} variant="outline">
            {secondaryLabel}
          </LinkButton>
        </div>
      </div>
    </section>
  );
}
