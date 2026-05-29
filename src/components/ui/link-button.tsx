import * as React from "react";
import Link from "next/link";
import { cn } from "@/lib/utils";
import { buttonVariants } from "@/components/ui/button";
import type { VariantProps } from "class-variance-authority";

/**
 * Anchor styled as a Button. Replaces shadcn's `asChild` pattern (the
 * base-nova flavour does not expose it). Use for navigation that should
 * look like a CTA — Next `<Link>` semantics, button visuals.
 */
type LinkButtonProps = React.AnchorHTMLAttributes<HTMLAnchorElement> &
  VariantProps<typeof buttonVariants> & {
    href: string;
    external?: boolean;
  };

export function LinkButton({
  className,
  variant,
  size,
  href,
  external,
  children,
  ...rest
}: LinkButtonProps) {
  const classes = cn(buttonVariants({ variant, size }), className);

  if (external) {
    return (
      <a
        href={href}
        className={classes}
        target="_blank"
        rel="noopener noreferrer"
        {...rest}
      >
        {children}
      </a>
    );
  }

  return (
    <Link href={href} className={classes} {...rest}>
      {children}
    </Link>
  );
}
