import { describe, expect, test } from "vitest";
import { buildLaborBi } from "./labor-bi";
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
    revenueBonusPct: 1,
  },
  {
    id: "cook",
    name: "Петр",
    roleId: "line_cook",
    venueId: "venue-1",
    status: "active",
    shiftLabel: "кухня",
  },
];

describe("buildTeamShiftRoster", () => {
  test("builds a day roster from iiko shifts and Team OS rates", () => {
    const shifts = [
      {
        shiftId: "shift-1",
        openTime: "2026-06-26T12:00:00",
        closeTime: "2026-06-26T23:00:00",
        revenue: 140000,
        items: 320,
        employee: "Смена",
        workers: [
          {
            memberId: "manager",
            name: "Мария",
            hours: 11,
            sales: 0,
          },
          {
            memberId: "waiter",
            name: "Илья",
            hours: 8,
            sales: 90000,
          },
        ],
      },
      {
        shiftId: "shift-2",
        openTime: "2026-06-27T16:00:00",
        closeTime: "2026-06-28T00:00:00",
        revenue: 70000,
        items: 150,
        employee: "Илья",
      },
    ];
    const labor = buildLaborBi({ staff, shifts });
    const roster = buildTeamShiftRoster({ staff, shifts, labor });

    expect(roster.days.map((day) => day.dateKey)).toEqual([
      "2026-06-26",
      "2026-06-27",
    ]);
    expect(roster).toMatchObject({
      rowsWithShifts: 2,
      rowsMissingRates: 0,
      totalShifts: 3,
      totalHours: 27,
      totalRevenue: 160000,
      totalLaborCost: 11200,
    });

    const waiter = roster.rows.find((row) => row.member.id === "waiter");
    expect(waiter).toMatchObject({
      status: "ready",
      shifts: 2,
      hours: 16,
      revenue: 160000,
      laborCost: 7200,
      laborCostPct: 4.5,
      revenuePerHour: 10000,
    });
    expect(waiter?.cells.map((cell) => cell.status)).toEqual([
      "ready",
      "ready",
    ]);
  });

  test("prioritizes rows with missing FOT rates", () => {
    const shifts = [
      {
        shiftId: "shift-cook",
        openTime: "2026-06-26T10:00:00",
        closeTime: "2026-06-26T22:00:00",
        revenue: 80000,
        items: 180,
        employee: "Петр",
      },
      {
        shiftId: "shift-waiter",
        openTime: "2026-06-26T16:00:00",
        closeTime: "2026-06-27T00:00:00",
        revenue: 60000,
        items: 120,
        employee: "Илья",
      },
    ];
    const labor = buildLaborBi({ staff, shifts });
    const roster = buildTeamShiftRoster({ staff, shifts, labor });

    expect(roster.rows[0]).toMatchObject({
      member: expect.objectContaining({ id: "cook" }),
      status: "missing_rate",
      shifts: 1,
      revenue: 80000,
      laborCost: 0,
    });
    expect(roster.rows[0]?.cells[0]).toMatchObject({
      status: "missing_rate",
      hours: 12,
    });
    expect(roster.rowsMissingRates).toBe(1);
  });

  test("keeps active staff without shifts visible", () => {
    const roster = buildTeamShiftRoster({
      staff,
      shifts: [],
      labor: null,
    });

    expect(roster.days).toEqual([]);
    expect(roster.rows).toHaveLength(3);
    expect(roster.rows.every((row) => row.status === "no_shifts")).toBe(true);
  });
});
