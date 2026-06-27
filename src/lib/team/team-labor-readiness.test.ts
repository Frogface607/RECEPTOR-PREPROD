import { describe, expect, test } from "vitest";
import { buildTeamLaborReadiness, hasLaborRate } from "./team-labor-readiness";
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
    });
    expect(buildTeamLaborReadiness(staff).missingStaff.map((item) => item.id)).toEqual([
      "missing",
    ]);
  });

  test("marks labor readiness as blocked when no active rate exists", () => {
    expect(buildTeamLaborReadiness([{ ...baseMember }])).toMatchObject({
      status: "blocked",
      activeStaff: 1,
      readyStaff: 0,
      coveragePct: 0,
    });
  });
});
