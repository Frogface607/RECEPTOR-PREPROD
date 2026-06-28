import { describe, expect, test } from "vitest";
import { buildLaborBi } from "./labor-bi";
import {
  buildBulkLaborRateTargets,
  buildTeamLaborReadiness,
  hasLaborRate,
} from "./team-labor-readiness";
import type { StaffMember } from "./team-os";

const baseMember: StaffMember = {
  id: "staff-1",
  name: "Мария",
  roleId: "service",
  venueId: "venue-1",
  status: "active",
  shiftLabel: "12:00-22:00",
};

describe("buildTeamLaborReadiness", () => {
  test("counts active staff with labor rates and ignores paused staff", () => {
    const staff: StaffMember[] = [
      { ...baseMember, id: "ready", name: "Мария", hourlyRate: 400 },
      { ...baseMember, id: "missing", name: "Илья" },
      {
        ...baseMember,
        id: "paused",
        name: "Пауза",
        status: "paused",
      },
    ];

    expect(hasLaborRate(staff[0])).toBe(true);
    expect(hasLaborRate(staff[1])).toBe(false);
    expect(buildTeamLaborReadiness(staff)).toMatchObject({
      status: "partial",
      totalStaff: 3,
      activeStaff: 2,
      readyStaff: 1,
      coveragePct: 50,
      source: "team",
      iikoBlockers: [],
    });
    expect(
      buildTeamLaborReadiness(staff).missingStaff.map((item) => item.id),
    ).toEqual(["missing"]);
  });

  test("marks labor readiness as blocked when no active rate exists", () => {
    expect(buildTeamLaborReadiness([{ ...baseMember }])).toMatchObject({
      status: "blocked",
      activeStaff: 1,
      readyStaff: 0,
      coveragePct: 0,
    });
  });

  test("uses real iiko shift coverage when labor BI is available", () => {
    const staff: StaffMember[] = [
      {
        ...baseMember,
        id: "waiter",
        name: "Илья",
        hourlyRate: 350,
      },
    ];
    const labor = buildLaborBi({
      staff,
      shifts: [
        {
          shiftId: "shift-1",
          openTime: "2026-06-26T16:00:00",
          closeTime: "2026-06-27T00:00:00",
          revenue: 100000,
          items: 180,
          employee: "Смена",
          workers: [
            { memberId: "waiter", name: "Илья", hours: 8, sales: 65000 },
            { name: "Петр", hours: 8, sales: 35000 },
          ],
        },
      ],
    });

    expect(buildTeamLaborReadiness(staff, labor)).toMatchObject({
      status: "partial",
      coveragePct: 65,
      source: "iiko",
      iikoRevenueCoveragePct: 65,
      iikoUnpricedRevenue: 35000,
      iikoBlockers: [
        expect.objectContaining({
          name: "Петр",
          action: "add-member",
        }),
      ],
    });
  });

  test("builds bulk labor rate targets only from active missing-rate staff", () => {
    const targets = buildBulkLaborRateTargets(
      [
        { ...baseMember, id: "priced", name: "Мария", hourlyRate: 400 },
        { ...baseMember, id: "missing-b", name: "Борис" },
        { ...baseMember, id: "missing-a", name: "Анна", shiftLabel: "iiko" },
        { ...baseMember, id: "paused", name: "Пауза", status: "paused" },
      ],
      { limit: 1 },
    );

    expect(targets).toEqual([
      expect.objectContaining({
        id: "missing-a",
        name: "Анна",
        shiftLabel: "iiko",
      }),
    ]);
  });
});
