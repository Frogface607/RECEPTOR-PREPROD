import { describe, expect, test } from "vitest";
import { buildLaborBi } from "./labor-bi";
import type { StaffMember } from "./team-os";

const staff: StaffMember[] = [
  {
    id: "manager",
    name: "Мария",
    roleId: "venue_manager",
    venueId: "venue-1",
    status: "active",
    shiftLabel: "12:00-23:00",
  },
  {
    id: "waiter",
    name: "Илья",
    roleId: "service",
    venueId: "venue-1",
    status: "active",
    shiftLabel: "16:00-00:00",
  },
];

describe("buildLaborBi", () => {
  test("calculates labor cost, labor percent and revenue per labor hour", () => {
    const labor = buildLaborBi({
      staff,
      rates: [
        { roleId: "venue_manager", shiftPay: 4000 },
        { roleId: "service", hourlyRate: 350, revenueBonusPct: 1 },
      ],
      shifts: [
        {
          shiftId: "shift-1",
          openTime: "2026-06-26T12:00:00",
          closeTime: "2026-06-26T23:00:00",
          revenue: 120000,
          items: 300,
          employee: "Смена",
          workers: [
            {
              memberId: "manager",
              name: "Мария",
              startedAt: "2026-06-26T12:00:00",
              endedAt: "2026-06-26T23:00:00",
              sales: 0,
            },
            {
              memberId: "waiter",
              name: "Илья",
              hours: 8,
              sales: 120000,
            },
          ],
        },
      ],
    });

    expect(labor).toMatchObject({
      revenue: 120000,
      items: 300,
      shifts: 1,
      staffShifts: 2,
      staffHours: 19,
      laborCost: 8000,
      laborCostPct: 6.7,
      revenuePerLaborHour: 6316,
      averageStaffPerShift: 2,
      missingRates: 0,
    });
    expect(labor.employees[0]).toMatchObject({
      name: "Илья",
      roleId: "service",
      hours: 8,
      sales: 120000,
      laborCost: 4000,
      laborCostPct: 3.3,
    });
  });

  test("still counts shift staffing when rates are missing", () => {
    const labor = buildLaborBi({
      shifts: [
        {
          shiftId: "shift-2",
          openTime: "2026-06-26T18:00:00",
          closeTime: "2026-06-27T02:00:00",
          revenue: 80000,
          items: 180,
          employee: "Кассир",
        },
      ],
    });

    expect(labor).toMatchObject({
      revenue: 80000,
      staffShifts: 1,
      staffHours: 8,
      laborCost: 0,
      laborCostPct: 0,
      revenuePerLaborHour: 10000,
      missingRates: 1,
    });
    expect(labor.employees[0]).toMatchObject({
      name: "Кассир",
      missingRate: true,
    });
  });
});
