import { describe, expect, test } from "vitest";
import {
  buildTeamShiftPlanSummary,
  getShiftHours,
  type TeamShiftPlan,
} from "./team-shift-plan";
import type { StaffMember } from "./team-os";

const staff: StaffMember[] = [
  {
    id: "manager",
    name: "Мария",
    roleId: "venue_manager",
    venueId: "venue-1",
    status: "active",
    shiftLabel: "12:00-23:00",
    shiftPay: 4000,
  },
  {
    id: "waiter",
    name: "Илья",
    roleId: "service",
    venueId: "venue-1",
    status: "active",
    shiftLabel: "16:00-00:00",
    hourlyRate: 350,
  },
  {
    id: "cook",
    name: "Петр",
    roleId: "line_cook",
    venueId: "venue-1",
    status: "active",
    shiftLabel: "10:00-22:00",
  },
];

const plans: TeamShiftPlan[] = [
  {
    id: "plan-manager",
    venueId: "venue-1",
    memberId: "manager",
    shiftDate: "2026-06-29",
    shiftStart: "12:00",
    shiftEnd: "23:00",
    isDayOff: false,
    note: "",
    updatedAt: "2026-06-27T10:00:00.000Z",
  },
  {
    id: "plan-waiter",
    venueId: "venue-1",
    memberId: "waiter",
    shiftDate: "2026-06-29",
    shiftStart: "16:00",
    shiftEnd: "00:00",
    isDayOff: false,
    note: "",
    updatedAt: "2026-06-27T10:00:00.000Z",
  },
  {
    id: "plan-cook",
    venueId: "venue-1",
    memberId: "cook",
    shiftDate: "2026-06-29",
    shiftStart: "10:00",
    shiftEnd: "22:00",
    isDayOff: false,
    note: "",
    updatedAt: "2026-06-27T10:00:00.000Z",
  },
  {
    id: "plan-manager-off",
    venueId: "venue-1",
    memberId: "manager",
    shiftDate: "2026-06-30",
    shiftStart: null,
    shiftEnd: null,
    isDayOff: true,
    note: "после банкета",
    updatedAt: "2026-06-27T10:00:00.000Z",
  },
];

describe("team shift plan", () => {
  test("calculates hours, planned FOT and missing rates", () => {
    const summary = buildTeamShiftPlanSummary({ staff, plans });

    expect(summary).toMatchObject({
      plannedShifts: 3,
      dayOffs: 1,
      hours: 31,
      laborCost: 6800,
      missingRateShifts: 1,
    });

    const cook = summary.rows.find((row) => row.member.id === "cook");
    expect(cook).toMatchObject({
      plannedShifts: 1,
      hours: 12,
      laborCost: 0,
      missingRateShifts: 1,
    });
  });

  test("supports overnight shifts", () => {
    expect(getShiftHours("18:30", "02:00")).toBe(7.5);
  });

  test("ignores paused staff in the planning summary", () => {
    const summary = buildTeamShiftPlanSummary({
      staff: [{ ...staff[0], status: "paused" }],
      plans,
    });

    expect(summary.rows).toEqual([]);
    expect(summary.plannedShifts).toBe(0);
  });
});
