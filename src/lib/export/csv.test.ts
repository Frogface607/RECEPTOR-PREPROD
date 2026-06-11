import { describe, expect, test } from "vitest";
import { toCsv, type CsvColumn } from "./csv";

const BOM = "﻿";

type Dish = {
  dishName: string;
  dishGroup: string;
  dishAmountInt: number;
  dishSumInt: number;
};

const dishColumns: CsvColumn<Dish>[] = [
  { header: "Блюдо", value: (d) => d.dishName },
  { header: "Группа", value: (d) => d.dishGroup },
  { header: "Количество", value: (d) => d.dishAmountInt },
  { header: "Сумма (₽)", value: (d) => d.dishSumInt },
];

describe("toCsv", () => {
  test("starts with UTF-8 BOM for Excel", () => {
    const csv = toCsv([], dishColumns);
    expect(csv.startsWith(BOM)).toBe(true);
  });

  test("emits header row first with ; separator", () => {
    const csv = toCsv([], dishColumns);
    const firstLine = csv.slice(BOM.length).split("\n")[0];
    expect(firstLine).toBe(
      '"Блюдо";"Группа";"Количество";"Сумма (₽)"',
    );
  });

  test("emits one data row per dish", () => {
    const rows: Dish[] = [
      {
        dishName: "Стейк из говядины",
        dishGroup: "Горячая кухня",
        dishAmountInt: 240,
        dishSumInt: 165600,
      },
      {
        dishName: "Авторский коктейль",
        dishGroup: "Барная карта",
        dishAmountInt: 198,
        dishSumInt: 75240,
      },
    ];
    const csv = toCsv(rows, dishColumns);
    const lines = csv.slice(BOM.length).split("\n");
    expect(lines).toHaveLength(3); // header + 2 rows
    expect(lines[1]).toBe('"Стейк из говядины";"Горячая кухня";"240";"165600"');
    expect(lines[2]).toBe(
      '"Авторский коктейль";"Барная карта";"198";"75240"',
    );
  });

  test("escapes double quotes by doubling them", () => {
    const rows = [{ note: 'Coca-Cola "classic" 0.33л' }];
    const csv = toCsv(rows, [
      { header: "Позиция", value: (r) => r.note },
    ]);
    const line = csv.slice(BOM.length).split("\n")[1];
    expect(line).toBe('"Coca-Cola ""classic"" 0.33л"');
  });

  test("treats null and undefined as empty quoted cells", () => {
    const rows = [{ a: null as unknown as string, b: undefined as unknown as string }];
    const csv = toCsv(rows, [
      { header: "A", value: (r) => r.a },
      { header: "B", value: (r) => r.b },
    ]);
    const line = csv.slice(BOM.length).split("\n")[1];
    expect(line).toBe('"";""');
  });

  test("handles cells that contain ; and newline safely", () => {
    const rows = [{ raw: "часть 1; часть 2\nновая строка" }];
    const csv = toCsv(rows, [{ header: "X", value: (r) => r.raw }]);
    const line = csv.slice(BOM.length).split("\n")[1];
    // Cell wrapped in quotes preserves ; and \n inside.
    expect(line.startsWith('"часть 1; часть 2')).toBe(true);
  });
});
