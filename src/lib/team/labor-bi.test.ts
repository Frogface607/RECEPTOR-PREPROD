import { describe, expect, test } from "vitest";
import {
  buildLaborBi,
  buildLaborEmployeeDiagnostics,
  buildLaborInsights,
  buildLaborNextAction,
  buildLaborShiftDiagnostics,
} from "./labor-bi";
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
      pricedStaffShifts: 2,
      unpricedStaffShifts: 0,
      pricedRevenue: 120000,
      unpricedRevenue: 0,
      revenueCoveragePct: 100,
      laborReadinessStatus: "ready",
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
      pricedStaffShifts: 0,
      unpricedStaffShifts: 1,
      pricedRevenue: 0,
      unpricedRevenue: 80000,
      revenueCoveragePct: 0,
      laborReadinessStatus: "blocked",
    });
    expect(labor.employees[0]).toMatchObject({
      name: "Кассир",
      missingRate: true,
    });
  });

  test("shows partial FOT readiness by covered revenue", () => {
    const labor = buildLaborBi({
      staff: [
        {
          id: "waiter",
          name: "Илья",
          roleId: "service",
          venueId: "venue-1",
          status: "active",
          shiftLabel: "16:00-00:00",
          hourlyRate: 350,
        },
      ],
      shifts: [
        {
          shiftId: "shift-partial",
          openTime: "2026-06-26T16:00:00",
          closeTime: "2026-06-27T00:00:00",
          revenue: 100000,
          items: 220,
          employee: "Смена",
          workers: [
            {
              memberId: "waiter",
              name: "Илья",
              hours: 8,
              sales: 60000,
            },
            {
              name: "Петр",
              hours: 8,
              sales: 40000,
            },
          ],
        },
      ],
    });

    expect(labor).toMatchObject({
      laborReadinessStatus: "partial",
      pricedStaffShifts: 1,
      unpricedStaffShifts: 1,
      pricedRevenue: 60000,
      unpricedRevenue: 40000,
      revenueCoveragePct: 60,
      missingRates: 1,
    });
  });

  test("matches iiko shift employee name to Team OS labor rate", () => {
    const labor = buildLaborBi({
      staff: [
        {
          id: "waiter",
          name: "Илья",
          roleId: "service",
          venueId: "venue-1",
          status: "active",
          shiftLabel: "16:00-00:00",
          hourlyRate: 350,
        },
      ],
      shifts: [
        {
          shiftId: "shift-ilya",
          openTime: "2026-06-26T16:00:00",
          closeTime: "2026-06-27T00:00:00",
          revenue: 90000,
          items: 210,
          employee: "Илья",
        },
      ],
    });

    expect(labor.laborCost).toBe(2800);
    expect(labor.missingRates).toBe(0);
    expect(labor.employees[0]).toMatchObject({
      memberId: "waiter",
      laborCost: 2800,
      hours: 8,
    });
  });

  test("prioritizes missing labor blockers from real shift employees", () => {
    const labor = buildLaborBi({
      staff: [
        {
          id: "ivan",
          name: "Иван",
          roleId: "service",
          venueId: "venue-1",
          status: "active",
          shiftLabel: "12:00-22:00",
        },
      ],
      shifts: [
        {
          shiftId: "shift-ivan",
          openTime: "2026-06-26T12:00:00",
          closeTime: "2026-06-26T20:00:00",
          revenue: 30000,
          items: 80,
          employee: "Иван",
        },
        {
          shiftId: "shift-petr",
          openTime: "2026-06-26T18:00:00",
          closeTime: "2026-06-27T02:00:00",
          revenue: 90000,
          items: 210,
          employee: "Петр",
        },
      ],
    });

    expect(labor.topBlockers).toEqual([
      expect.objectContaining({
        name: "Петр",
        reason: "missing-member",
        sales: 90000,
      }),
      expect.objectContaining({
        name: "Иван",
        reason: "missing-rate",
        memberId: "ivan",
        sales: 30000,
      }),
    ]);
    expect(buildLaborInsights(labor)[0]).toMatchObject({
      title: "Не все ставки заведены",
      action: "Добавьте этого сотрудника в Team OS или выровняйте имя с iiko.",
    });
    expect(buildLaborNextAction(labor)).toMatchObject({
      kind: "missing-member",
      title: "Добавить сотрудника из iiko",
      blocker: expect.objectContaining({
        name: "Петр",
        reason: "missing-member",
      }),
    });
  });

  test("creates actionable insights for expensive labor", () => {
    const labor = buildLaborBi({
      shifts: [
        {
          shiftId: "shift-expensive",
          openTime: "2026-06-26T12:00:00",
          closeTime: "2026-06-26T22:00:00",
          revenue: 50000,
          items: 120,
          employee: "Смена",
          workers: [
            {
              name: "Мария",
              hours: 10,
              shiftPay: 18000,
              sales: 50000,
            },
          ],
        },
      ],
    });

    const insights = buildLaborInsights(labor, {
      targetLaborCostPct: 25,
      minimumRevenuePerLaborHour: 6000,
    });

    expect(insights.map((item) => item.title)).toContain(
      "ФОТ выше целевой нормы",
    );
    expect(insights.some((item) => item.title.startsWith("Дорогая смена"))).toBe(
      true,
    );
    expect(insights.some((item) => item.title.includes("человеко-час"))).toBe(
      true,
    );
    expect(buildLaborNextAction(labor)).toMatchObject({
      kind: "expensive-labor",
      title: "Разобрать дорогую смену",
      shift: expect.objectContaining({
        shiftId: "shift-expensive",
      }),
    });
  });

  test("ranks employee diagnostics by missing rates and personal labor pressure", () => {
    const labor = buildLaborBi({
      shifts: [
        {
          shiftId: "shift-team",
          openTime: "2026-06-26T12:00:00",
          closeTime: "2026-06-26T22:00:00",
          revenue: 90000,
          items: 180,
          employee: "Смена",
          workers: [
            {
              memberId: "manager",
              name: "Мария",
              hours: 10,
              shiftPay: 28000,
              sales: 50000,
            },
            {
              memberId: "waiter",
              name: "Илья",
              hours: 8,
              hourlyRate: 350,
              sales: 30000,
            },
            {
              name: "Петр",
              hours: 8,
              sales: 10000,
            },
          ],
        },
      ],
    });

    const diagnostics = buildLaborEmployeeDiagnostics(labor, {
      targetLaborCostPct: 25,
      minimumRevenuePerLaborHour: 6000,
    });

    expect(diagnostics.map((item) => item.kind)).toEqual([
      "missing-rate",
      "expensive-employee",
      "low-productivity",
    ]);
    expect(diagnostics[0]).toMatchObject({
      name: "Петр",
      title: "Сотрудник без ставки ФОТ",
      tone: "setup",
    });
    expect(diagnostics[1]).toMatchObject({
      name: "Мария",
      title: "Сотрудник дорогой к выручке",
      tone: "risk",
    });
    expect(diagnostics[2]).toMatchObject({
      name: "Илья",
      title: "Низкая выручка на час сотрудника",
      tone: "watch",
    });
  });

  test("creates setup insight when rates are missing", () => {
    const labor = buildLaborBi({
      shifts: [
        {
          shiftId: "shift-missing-rate",
          openTime: "2026-06-26T18:00:00",
          closeTime: "2026-06-27T02:00:00",
          revenue: 80000,
          items: 180,
          employee: "Кассир",
        },
      ],
    });

    expect(buildLaborInsights(labor)[0]).toMatchObject({
      tone: "setup",
      title: "Не все ставки заведены",
    });
    expect(buildLaborNextAction(labor)).toMatchObject({
      kind: "missing-member",
      action: expect.stringContaining("Team OS"),
    });
  });

  test("focuses known Team OS member when only labor rate is missing", () => {
    const labor = buildLaborBi({
      staff,
      shifts: [
        {
          shiftId: "shift-known-member",
          openTime: "2026-06-26T16:00:00",
          closeTime: "2026-06-27T00:00:00",
          revenue: 60000,
          items: 120,
          employee: "Илья",
        },
      ],
    });

    expect(buildLaborNextAction(labor)).toMatchObject({
      kind: "missing-rate",
      title: "Заполнить ставку ФОТ",
      blocker: expect.objectContaining({
        memberId: "waiter",
        name: "Илья",
      }),
    });
  });

  test("orders shift diagnostics by labor risk", () => {
    const labor = buildLaborBi({
      shifts: [
        {
          shiftId: "healthy",
          openTime: "2026-06-26T12:00:00",
          closeTime: "2026-06-26T22:00:00",
          revenue: 120000,
          items: 260,
          employee: "Смена",
          workers: [
            {
              name: "Мария",
              hours: 10,
              shiftPay: 4000,
              sales: 120000,
            },
          ],
        },
        {
          shiftId: "expensive",
          openTime: "2026-06-27T12:00:00",
          closeTime: "2026-06-27T22:00:00",
          revenue: 50000,
          items: 110,
          employee: "Смена",
          workers: [
            {
              name: "Илья",
              hours: 10,
              shiftPay: 18000,
              sales: 50000,
            },
          ],
        },
        {
          shiftId: "missing",
          openTime: "2026-06-28T12:00:00",
          closeTime: "2026-06-28T22:00:00",
          revenue: 40000,
          items: 90,
          employee: "Петр",
        },
      ],
    });

    expect(buildLaborShiftDiagnostics(labor).map((item) => item.kind)).toEqual([
      "missing-rates",
      "expensive-labor",
      "healthy",
    ]);
  });
});
