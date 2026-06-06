# Receptor — Design System (source of truth)

> Validated against `ui-ux-pro-max` (design intelligence skill). Direction
> confirmed: **Dark Mode (OLED)** — WCAG-AAA-capable, excellent performance,
> the right archetype for a premium restaurant BI copilot.

## Identity

- **Archetype:** Premium Dark / OLED. Dark-only (no light theme in v1).
- **Voice:** «чувствует кухню» — confident, calm, data-first, no marketing fluff, no emoji.

## Typography (deliberately distinctive — not the generic Fira/Inter default)

| Role | Family | Use |
|---|---|---|
| Display | **Cormorant Garamond** (italic) | hero taglines, signature emerald moments, pull-quotes |
| Body / UI | **Geist Sans** (cyrillic) | everything functional |
| Mono / numeric | **Geist Mono** + `.numeric` (tabular-nums) | KPI numbers, tables, prices, code labels |

`--font-display`, `--font-sans`, `--font-mono` exposed via next/font.

## Color tokens (OKLCH, dark surface)

Brand-led emerald with a restrained functional accent set. Defined in `globals.css`.

| Token | Meaning |
|---|---|
| `--brand` / `--brand-hover` | emerald-500/400 — primary, CTAs, success, signature |
| `--background` `#0a0a0a` · `--card` · `--popover` | OLED surface ladder |
| `--iiko` (cyan) | iiko/integration surfaces |
| `--pro` (amber) | Pro badge, demo-mode marker |
| `--ai` (purple) | AI chat |
| `--bi` (blue) | analytics accent |
| `--destructive` (red) | errors only |
| chart-1..5 | emerald → cyan → amber → blue → purple (category palette) |

All chart colors meet ≥3:1 vs surface; foreground/secondary text meet 4.5:1 / 3:1.

## Effects & motion

- **OLED minimal glow** — `.glow-brand` / `.glow-brand-soft` (text-shadow halo) on
  signature emerald display moments only (1 per view, restraint).
- **Atmosphere** — focused emerald radial glow + faint masked grid behind heroes.
- **Press** — `.press` (active:scale .97), reduced-motion safe.
- **Page-load reveal** — `.reveal` staggered (dashboard sections).
- **Durations** 150–300ms, ease-out enter; `prefers-reduced-motion` honoured everywhere.

## Accessibility (CRITICAL — ui-ux-pro-max §1/§2)

- **Global `:focus-visible`** ring (brand, offset, keyboard-only) on every interactive
  element — `globals.css` base layer. Single source, never on mouse click.
- **cursor** affordances: pointer for links/buttons/summary/labels; not-allowed for disabled.
- **aria-label** on every icon-only control (chat close/send, export, hamburger).
- **Touch targets** ≥40–44px on interactive controls (filter chips, nav, CTAs).
- **Reduced motion** disables scroll-smooth, reveals, press scale.
- No emoji as icons — Lucide vector set throughout, consistent stroke.

## Components

shadcn/ui (`base-nova`) primitives + custom `LinkButton`, dashboard charts (Recharts,
`minWidth/minHeight={0}` to prevent CLS), `Markdown` renderer, tools browser/runner.

## Responsive

Mobile-first. Verified at 375 / 768 / 1280. KPI grid 2×2 on mobile → 4-up desktop;
charts reflow; pricing table → horizontal scroll with hint; nav → drawer.

---
*Apply this file as the master design reference. Page-specific deviations, if any,
go in a short note next to the page.*
