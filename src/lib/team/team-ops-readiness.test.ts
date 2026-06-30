import { describe, expect, test } from "vitest";
import { buildLaborBi } from "./labor-bi";
import { listLearningItemsForRole } from "./team-learning";
import { buildTeamLearningSummaries } from "./team-learning-progress";
import { buildTeamLaborReadiness } from "./team-labor-readiness";
import { buildTeamOpsReadiness } from "./team-ops-readiness";
import { buildShiftOverview } from "./team-shift-planner";
import type { StaffMember, TeamTask } from "./team-os";
import type { TeamLearningStandardOverride } from "./team-learning-standards";

const baseMember: StaffMember = {
  id: "service-1",
  name: "Мария",
  roleId: "service",
  venueId: "venue-1",
  status: "active",
  shiftLabel: "зал 16:00-00:00",
};

describe("buildTeamOpsReadiness", () => {
  test("prioritizes labor, role, learning and task blockers", () => {
    const staff: StaffMember[] = [
      { ...baseMember, id: "service-1", name: "Мария" },
      {
        ...baseMember,
        id: "manager-1",
        name: "Алина",
        roleId: "venue_manager",
        shiftPay: 4500,
      },
      {
        ...baseMember,
        id: "chef-1",
        name: "Роман",
        roleId: "chef",
        status: "paused",
        shiftLabel: "кухня",
      },
    ];
    const tasks: TeamTask[] = [
      {
        id: "task-1",
        title: "Проверить стоп-лист до посадки",
        source: "manager",
        priority: "high",
        status: "new",
        venueId: "venue-1",
        audience: { type: "role", roleId: "chef" },
        dueLabel: "сегодня",
      },
    ];
    const readiness = buildTeamOpsReadiness({
      shiftOverview: buildShiftOverview(staff, tasks),
      laborReadiness: buildTeamLaborReadiness(staff),
      learningSummaries: buildTeamLearningSummaries(staff, []),
      tasks,
    });

    expect(readiness.status).toBe("blocked");
    expect(readiness.actions.map((action) => action.id)).toEqual([
      "labor-rate",
      "role-coverage",
      "learning",
      "task",
    ]);
    expect(readiness.actions[0]).toMatchObject({
      title: "Закрыть ставку ФОТ",
      href: "#labor-rates",
    });
    expect(readiness.actions[1].detail).toContain("Шеф");
    expect(readiness.actions[2]).toMatchObject({
      id: "learning",
      learningModuleId: "service-recommendation",
      learningModuleTitle: "Как рекомендовать блюдо без давления",
    });
  });

  test("returns a ready action when operational basics are closed", () => {
    const staff: StaffMember[] = [
      {
        ...baseMember,
        id: "owner",
        roleId: "owner",
        name: "Сергей",
        shiftPay: 1,
      },
      {
        ...baseMember,
        id: "ops",
        roleId: "operations_manager",
        name: "Ольга",
        shiftPay: 1,
      },
      {
        ...baseMember,
        id: "manager",
        roleId: "venue_manager",
        name: "Алина",
        shiftPay: 4500,
      },
      {
        ...baseMember,
        id: "chef",
        roleId: "chef",
        name: "Роман",
        shiftPay: 5000,
      },
      {
        ...baseMember,
        id: "cook",
        roleId: "line_cook",
        name: "Илья",
        hourlyRate: 380,
      },
      {
        ...baseMember,
        id: "service",
        roleId: "service",
        name: "Мария",
        hourlyRate: 350,
      },
      {
        ...baseMember,
        id: "marketing",
        roleId: "marketing",
        name: "Катя",
        shiftPay: 1,
      },
    ];
    const progress = buildTeamLearningSummaries(staff, []).flatMap((summary) =>
      summary.items.map((item) => ({
        venueId: "venue-1",
        membershipId: summary.member.id,
        userId: null,
        moduleId: item.id,
        bestPercentage: 100,
        lastPercentage: 100,
        correct: 1,
        total: 1,
        passed: true,
        answers: [0],
        completedAt: "2026-06-27T10:00:00.000Z",
        updatedAt: "2026-06-27T10:00:00.000Z",
      })),
    );
    const readiness = buildTeamOpsReadiness({
      shiftOverview: buildShiftOverview(staff, []),
      laborReadiness: buildTeamLaborReadiness(staff),
      learningSummaries: buildTeamLearningSummaries(staff, progress),
      tasks: [],
    });

    expect(readiness.status).toBe("ready");
    expect(readiness.score).toBe(100);
    expect(readiness.actions).toEqual([
      expect.objectContaining({ id: "ready", tone: "good" }),
    ]);
  });

  test("uses required learning as shift admission instead of blocking on optional modules", () => {
    const staff: StaffMember[] = [
      {
        ...baseMember,
        id: "service",
        roleId: "service",
        name: "Мария",
        hourlyRate: 350,
      },
      {
        ...baseMember,
        id: "chef",
        roleId: "chef",
        name: "Роман",
        shiftPay: 5000,
      },
      {
        ...baseMember,
        id: "manager",
        roleId: "venue_manager",
        name: "Алина",
        shiftPay: 4500,
      },
      {
        ...baseMember,
        id: "cook",
        roleId: "line_cook",
        name: "Илья",
        hourlyRate: 380,
      },
    ];
    const progress = staff.flatMap((member) =>
      listLearningItemsForRole(member.roleId)
        .filter((item) => item.status === "required")
        .map((item) => ({
          venueId: "venue-1",
          membershipId: member.id,
          userId: null,
          moduleId: item.id,
          bestPercentage: item.passPercentage,
          lastPercentage: item.passPercentage,
          correct: 1,
          total: 1,
          passed: true,
          answers: [0],
          completedAt: "2026-06-27T10:00:00.000Z",
          updatedAt: "2026-06-27T10:00:00.000Z",
        })),
    );

    const readiness = buildTeamOpsReadiness({
      shiftOverview: buildShiftOverview(staff, []),
      laborReadiness: buildTeamLaborReadiness(staff),
      learningSummaries: buildTeamLearningSummaries(staff, progress),
      tasks: [],
    });

    expect(readiness.learningAdmissionPct).toBe(100);
    expect(readiness.actions).not.toEqual(
      expect.arrayContaining([expect.objectContaining({ id: "learning" })]),
    );
  });

  test("uses venue learning standards for owner-facing team readiness", () => {
    const staff: StaffMember[] = [
      {
        ...baseMember,
        id: "service",
        roleId: "service",
        name: "Maria",
        hourlyRate: 350,
      },
    ];
    const progress = listLearningItemsForRole("service")
      .filter((item) => item.status === "required")
      .map((item) => ({
        venueId: "venue-1",
        membershipId: "service",
        userId: null,
        moduleId: item.id,
        bestPercentage: item.passPercentage,
        lastPercentage: item.passPercentage,
        correct: 1,
        total: 1,
        passed: true,
        answers: [0],
        completedAt: "2026-06-27T10:00:00.000Z",
        updatedAt: "2026-06-27T10:00:00.000Z",
      }));
    const standards: TeamLearningStandardOverride[] = [
      {
        venueId: "venue-1",
        roleId: "service",
        moduleId: "guest-feedback",
        status: "required",
        updatedAt: "2026-06-27T10:00:00.000Z",
      },
    ];

    const readiness = buildTeamOpsReadiness({
      shiftOverview: buildShiftOverview(staff, []),
      laborReadiness: buildTeamLaborReadiness(staff),
      learningSummaries: buildTeamLearningSummaries(
        staff,
        progress,
        standards,
      ),
      tasks: [],
    });

    expect(readiness.learningAdmissionPct).toBe(0);
    expect(readiness.actions).toEqual(
      expect.arrayContaining([expect.objectContaining({ id: "learning" })]),
    );
  });

  test("prioritizes real iiko staff blockers over internal rate checklist", () => {
    const staff: StaffMember[] = [
      {
        ...baseMember,
        id: "service-1",
        name: "Мария",
        hourlyRate: 350,
      },
    ];
    const labor = buildLaborBi({
      staff,
      shifts: [
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
    const readiness = buildTeamOpsReadiness({
      shiftOverview: buildShiftOverview(staff, []),
      laborReadiness: buildTeamLaborReadiness(staff, labor),
      learningSummaries: buildTeamLearningSummaries(staff, []),
      tasks: [],
    });

    expect(readiness.actions[0]).toMatchObject({
      id: "iiko-labor-member",
      title: "Добавить сотрудника из iiko",
      href: "#team-actions",
    });
    expect(readiness.actions[0].detail).toContain("Петр");
  });
});
