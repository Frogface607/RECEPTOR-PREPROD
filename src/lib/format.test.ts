import { describe, expect, test } from "vitest";
import { formatRubles, formatInteger } from "./format";

// NBSP (U+00A0) used as digit-group separator AND between number and ₽
// so values don't wrap awkwardly in KPI cards / tooltips.
const NBSP = " ";

describe("formatRubles", () => {
  test("formats whole rubles with ru-RU grouping and trailing ₽", () => {
    expect(formatRubles(1500)).toBe(`1${NBSP}500${NBSP}₽`);
  });

  test("formats six-figure values", () => {
    expect(formatRubles(150000)).toBe(`150${NBSP}000${NBSP}₽`);
  });

  test("formats zero as '0 ₽'", () => {
    expect(formatRubles(0)).toBe(`0${NBSP}₽`);
  });

  test("rounds fractional values to whole rubles", () => {
    expect(formatRubles(1234.56)).toBe(`1${NBSP}235${NBSP}₽`);
  });

  test("handles negative values", () => {
    expect(formatRubles(-500)).toBe(`-500${NBSP}₽`);
  });
});

describe("formatInteger", () => {
  test("formats with ru-RU grouping", () => {
    expect(formatInteger(12345)).toBe(`12${NBSP}345`);
  });

  test("formats zero as '0'", () => {
    expect(formatInteger(0)).toBe("0");
  });

  test("rounds fractional values", () => {
    expect(formatInteger(99.7)).toBe("100");
  });
});
