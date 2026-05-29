/**
 * Number formatting helpers for the RU dashboard.
 *
 * All values use U+00A0 (NO-BREAK SPACE) as digit-group separator AND between
 * the number and its unit (₽, шт., etc.) so that strings like "150 000 ₽"
 * do not break across lines inside KPI cards or chart tooltips.
 */

const RUBLE_FORMATTER = new Intl.NumberFormat("ru-RU", {
  maximumFractionDigits: 0,
  minimumFractionDigits: 0,
});

const INTEGER_FORMATTER = new Intl.NumberFormat("ru-RU", {
  maximumFractionDigits: 0,
  minimumFractionDigits: 0,
});

/**
 * Format a number of rubles as "1 500 ₽" using non-breaking spaces.
 * Fractional input is rounded to whole rubles.
 */
export function formatRubles(value: number): string {
  return `${RUBLE_FORMATTER.format(value)} ₽`;
}

/**
 * Format any integer count with ru-RU digit grouping (e.g. "12 345").
 * Fractional input is rounded.
 */
export function formatInteger(value: number): string {
  return INTEGER_FORMATTER.format(value);
}
