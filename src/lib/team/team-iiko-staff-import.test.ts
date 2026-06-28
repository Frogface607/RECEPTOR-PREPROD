import { describe, expect, test } from "vitest";
import { buildIikoStaffImportCandidates } from "./team-iiko-staff-import";
import type { TeamLaborIikoBlocker } from "./team-labor-readiness";

const baseBlocker: TeamLaborIikoBlocker = {
  name: "Мария",
  shifts: 2,
  hours: 14,
  sales: 50000,
  reason: "missing-member",
  action: "add-member",
};

describe("buildIikoStaffImportCandidates", () => {
  test("returns only missing iiko members ranked by revenue", () => {
    const candidates = buildIikoStaffImportCandidates([
      { ...baseBlocker, name: "Иван", sales: 20000 },
      {
        ...baseBlocker,
        name: "Петр",
        sales: 90000,
        shifts: 3,
        hours: 21.5,
      },
      {
        ...baseBlocker,
        name: "Ольга",
        sales: 70000,
        memberId: "olga",
        reason: "missing-rate",
        action: "set-rate",
      },
    ]);

    expect(candidates).toEqual([
      expect.objectContaining({
        name: "Петр",
        roleId: "service",
        shiftLabel: "3 смен · 21,5 ч",
      }),
      expect.objectContaining({ name: "Иван" }),
    ]);
  });

  test("deduplicates names and preserves suggested roles", () => {
    const candidates = buildIikoStaffImportCandidates([
      { ...baseBlocker, name: "  Мария Иванова  ", roleId: "venue_manager" },
      { ...baseBlocker, name: "мария   иванова", sales: 90000 },
    ]);

    expect(candidates).toEqual([
      expect.objectContaining({
        name: "Мария Иванова",
        roleId: "venue_manager",
      }),
    ]);
  });

  test("limits import candidates", () => {
    const candidates = buildIikoStaffImportCandidates(
      [
        { ...baseBlocker, name: "A", sales: 4 },
        { ...baseBlocker, name: "B", sales: 3 },
        { ...baseBlocker, name: "C", sales: 2 },
      ],
      { limit: 2 },
    );

    expect(candidates.map((candidate) => candidate.name)).toEqual(["A", "B"]);
  });
});
