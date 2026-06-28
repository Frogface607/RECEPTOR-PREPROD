import { describe, expect, test } from "vitest";
import { buildLaborBi, type LaborShiftInput } from "./labor-bi";
import {
  buildTeamShiftPlanSummary,
  type TeamShiftPlan,
} from "./team-shift-plan";
import { buildTeamShiftPlanVariance } from "./team-shift-plan-variance";
import { buildTeamShiftRoster } from "./team-shift-roster";
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
    hourlyRate: 300,
  },
  {
    id: "bartender",
    name: "Олег",
    roleId: "service",
    venueId: "venue-1",
    status: "active",
    shiftLabel: "18:00-02:00",
    shiftPay: 3000,
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
    updatedAt: "2026-06-28T10:00:00.000Z",
  },
  {
    id: "plan-waiter-off",
    venueId: "venue-1",
    memberId: "waiter",
    shiftDate: "2026-06-29",
    shiftStart: null,
    shiftEnd: null,
    isDayOff: true,
    note: "",
    updatedAt: "2026-06-28T10:00:00.000Z",
  },
  {
    id: "plan-cook",
    venueId: "venue-1",
    memberId: "cook",
    shiftDate: "2026-06-30",
    shiftStart: "10:00",
    shiftEnd: "22:00",
    isDayOff: false,
    note: "",
    updatedAt: "2026-06-28T10:00:00.000Z",
  },
];

const shifts: LaborShiftInput[] = [
  {
    shiftId: "manager-fact",
    openTime: "2026-06-29T12:00:00",
    closeTime: "2026-06-29T23:00:00",
    revenue: 120000,
    items: 260,
    employee: "Смена",
    workers: [
      {
        memberId: "manager",
        name: "Мария",
        hours: 11,
        sales: 120000,
      },
    ],
  },
  {
    shiftId: "waiter-day-off",
    openTime: "2026-06-29T16:00:00",
    closeTime: "2026-06-30T00:00:00",
    revenue: 90000,
    items: 190,
    employee: "Илья",
  },
  {
    shiftId: "bartender-unplanned",
    openTime: "2026-06-29T18:00:00",
    closeTime: "2026-06-30T02:00:00",
    revenue: 70000,
    items: 140,
    employee: "Олег",
  },
];

describe("buildTeamShiftPlanVariance", () => {
  test("compares planned roster with actual iiko shifts", () => {
    const plan = buildTeamShiftPlanSummary({ staff, plans });
    const labor = buildLaborBi({ staff, shifts });
    const roster = buildTeamShiftRoster({ staff, shifts, labor });
    const variance = buildTeamShiftPlanVariance({ plan, roster });

    expect(variance).toMatchObject({
      plannedShifts: 2,
      actualShifts: 3,
      coveredActualShifts: 1,
      planCoveragePct: 33,
      plannedHours: 23,
      actualHours: 27,
      hoursDelta: 4,
      plannedLaborCost: 7600,
      actualLaborCost: 9800,
      laborDelta: 2200,
      unplannedActualShifts: 1,
      missedPlanShifts: 1,
      dayOffWorkedShifts: 1,
    });

    expect(variance.issues.map((issue) => issue.status)).toEqual([
      "day_off_worked",
      "missed_plan",
      "unplanned_actual",
    ]);
  });

  test("flags hour variance when plan and fact both exist", () => {
    const plan = buildTeamShiftPlanSummary({
      staff,
      plans: [
        {
          id: "short-plan",
          venueId: "venue-1",
          memberId: "waiter",
          shiftDate: "2026-06-29",
          shiftStart: "16:00",
          shiftEnd: "22:00",
          isDayOff: false,
          note: "",
          updatedAt: "2026-06-28T10:00:00.000Z",
        },
      ],
    });
    const labor = buildLaborBi({ staff, shifts: [shifts[1]] });
    const roster = buildTeamShiftRoster({
      staff,
      shifts: [shifts[1]],
      labor,
    });
    const variance = buildTeamShiftPlanVariance({ plan, roster });

    expect(variance.issues).toHaveLength(1);
    expect(variance.issues[0]).toMatchObject({
      status: "over_hours",
      plannedHours: 6,
      actualHours: 8,
      hoursDelta: 2,
      plannedLaborCost: 2100,
      actualLaborCost: 2800,
      laborDelta: 700,
    });
  });
});
