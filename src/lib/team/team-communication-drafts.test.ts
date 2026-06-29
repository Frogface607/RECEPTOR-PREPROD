import { describe, expect, test } from "vitest";
import { buildTeamCommunicationDrafts } from "./team-communication-drafts";
import type { TeamLaborReadiness } from "./team-labor-readiness";
import type { TeamLearningRolePlan } from "./team-learning-role-plan";
import type { TeamShiftPlanVarianceSummary } from "./team-shift-plan-variance";
import type { StaffMember } from "./team-os";

const waiter: StaffMember = {
  id: "waiter-1",
  name: "Илья",
  roleId: "service",
  venueId: "venue-1",
  status: "active",
  shiftLabel: "зал",
};

const readyLabor: TeamLaborReadiness = {
  status: "ready",
  totalStaff: 1,
  activeStaff: 1,
  readyStaff: 1,
  missingStaff: [],
  coveragePct: 100,
  source: "iiko",
  iikoStatus: "ready",
  iikoStaffShifts: 1,
  iikoRevenueCoveragePct: 100,
  iikoUnpricedStaffShifts: 0,
  iikoUnpricedRevenue: 0,
  iikoBlockers: [],
};

const readyVariance: TeamShiftPlanVarianceSummary = {
  plannedShifts: 1,
  actualShifts: 1,
  coveredActualShifts: 1,
  planCoveragePct: 100,
  plannedHours: 8,
  actualHours: 8,
  hoursDelta: 0,
  plannedLaborCost: 3000,
  actualLaborCost: 3000,
  laborDelta: 0,
  unplannedActualShifts: 0,
  missedPlanShifts: 0,
  dayOffWorkedShifts: 0,
  hourVarianceShifts: 0,
  missingRateShifts: 0,
  issues: [],
};

function learningPlan(
  overrides: Partial<TeamLearningRolePlan> = {},
): TeamLearningRolePlan {
  return {
    roleId: "service",
    roleTitle: "Официант",
    members: 2,
    totalItems: 2,
    requiredItems: 1,
    readyItems: 1,
    soonItems: 0,
    customStandards: 0,
    items: [],
    requiredProgressPct: 50,
    admissionPct: 50,
    blockedMembers: [
      {
        memberId: "waiter-1",
        memberName: "Илья",
        nextItemTitle: "Стандарт сервиса",
      },
    ],
    nextItem: {
      id: "service-standard",
      title: "Стандарт сервиса",
      description: "Короткий материал",
      timeLabel: "5 минут",
      status: "required",
      roles: ["service"],
      passPercentage: 90,
      sections: [],
      quiz: [],
    },
    ...overrides,
  };
}

describe("buildTeamCommunicationDrafts", () => {
  test("creates a role announcement from blocked learning admission", () => {
    const drafts = buildTeamCommunicationDrafts({
      learningRolePlans: [learningPlan()],
      laborReadiness: readyLabor,
      shiftPlanVariance: readyVariance,
    });

    expect(drafts[0]).toMatchObject({
      id: "learning-admission",
      label: "Обучение",
      priority: "important",
      audience: { type: "role", roleId: "service" },
    });
    expect(drafts[0]?.title).toContain("Официант");
    expect(drafts[0]?.body).toContain("Илья");
    expect(drafts[0]?.body).toContain("Стандарт сервиса");
  });

  test("adds labor and plan/fact drafts when operations are not ready", () => {
    const labor: TeamLaborReadiness = {
      ...readyLabor,
      status: "partial",
      readyStaff: 0,
      coveragePct: 40,
      iikoStatus: "partial",
      iikoUnpricedStaffShifts: 2,
      iikoUnpricedRevenue: 120000,
      iikoBlockers: [
        {
          name: "Илья",
          roleId: "service",
          shifts: 2,
          hours: 14,
          sales: 120000,
          reason: "missing-rate",
          action: "set-rate",
        },
      ],
    };
    const variance: TeamShiftPlanVarianceSummary = {
      ...readyVariance,
      planCoveragePct: 50,
      missedPlanShifts: 1,
      issues: [
        {
          id: "waiter-1-2026-06-29-missed",
          member: waiter,
          roleTitle: "Зал",
          dateKey: "2026-06-29",
          dateLabel: "29.06",
          status: "missed_plan",
          tone: "risk",
          plannedShifts: 1,
          actualShifts: 0,
          plannedHours: 8,
          actualHours: 0,
          hoursDelta: -8,
          plannedLaborCost: 3000,
          actualLaborCost: 0,
          laborDelta: -3000,
          revenue: 0,
        },
      ],
    };

    const drafts = buildTeamCommunicationDrafts({
      learningRolePlans: [],
      laborReadiness: labor,
      shiftPlanVariance: variance,
    });

    expect(drafts.map((draft) => draft.id)).toEqual([
      "labor-rates",
      "plan-fact",
    ]);
    expect(drafts[0]).toMatchObject({
      priority: "normal",
      audience: { type: "role", roleId: "venue_manager" },
      reason: "40% покрытия",
    });
    expect(drafts[0]?.body).toContain("2 смен без точного ФОТ");
    expect(drafts[1]).toMatchObject({
      priority: "important",
      title: "План смен требует внимания",
    });
  });

  test("returns no drafts when team operations are clean", () => {
    expect(
      buildTeamCommunicationDrafts({
        learningRolePlans: [learningPlan({ blockedMembers: [] })],
        laborReadiness: readyLabor,
        shiftPlanVariance: readyVariance,
      }),
    ).toEqual([]);
  });
});
