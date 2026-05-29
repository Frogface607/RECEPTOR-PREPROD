/**
 * Minimal CSV writer for the dashboard's "Export" buttons.
 *
 * Design choices:
 *  - Prepend UTF-8 BOM ('﻿') so Excel auto-detects Cyrillic correctly.
 *  - Use ';' as delimiter (Russian/European Excel default).
 *  - Quote every cell to make escaping uniform and reduce edge cases.
 *  - Escape internal " by doubling it, per RFC 4180.
 *
 * Phase 1.5 may grow this into streamed responses for huge venues; for now
 * this is enough for top-10 dishes and weekly shift tables.
 */

const BOM = "﻿";

export type CsvCell = string | number | boolean | null | undefined;

export type CsvColumn<Row> = {
  header: string;
  value: (row: Row) => CsvCell;
};

function escapeCell(input: CsvCell): string {
  if (input === null || input === undefined) return '""';
  const text = String(input).replace(/"/g, '""');
  return `"${text}"`;
}

export function toCsv<Row>(rows: Row[], columns: CsvColumn<Row>[]): string {
  const header = columns.map((c) => escapeCell(c.header)).join(";");
  const body = rows
    .map((row) => columns.map((col) => escapeCell(col.value(row))).join(";"))
    .join("\n");
  return body.length > 0
    ? `${BOM}${header}\n${body}`
    : `${BOM}${header}`;
}
