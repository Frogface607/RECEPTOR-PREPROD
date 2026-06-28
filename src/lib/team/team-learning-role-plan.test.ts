import { describe, expect, test } from "vitest";
import type { StaffMember } from "./team-os";
import {
  buildTeamLearningSummaries,
  type TeamLearningProgress,
} from "./team-learning-progress";
import {
  buildLearningAdmissionTaskDraft,
  buildTeamLearningRolePlans,
} from "./team-learning-role-plan";

const staff: StaffMember[] = [
  {
    id: "service-1",
    name: "Маша",
    roleId: "service",
    venueId: "venue-1",
    status: "active",
    shiftLabel: "зал",
  },
  {
    id: "service-2",
    name: "Петр",
    roleId: "service",
    venueId: "venue-1",
    status: "active",
    shiftLabel: "зал",
  },
  {
    id: "chef-1",
    name: "Роман",
    roleId: "chef",
    venueId: "venue-1",
    status: "paused",
    shiftLabel: "кухня",
  },
];

const progress: TeamLearningProgress[] = [
  {
    venueId: "venue-1",
    membershipId: "service-1",
    userId: null,
    moduleId: "service-recommendation",
    bestPercentage: 100,
    lastPercentage: 100,
    correct: 3,
    total: 3,
    passed: true,
    answers: [1, 0, 2],
    completedAt: "2026-06-27T10:00:00.000Z",
    updatedAt: "2026-06-27T10:00:00.000Z",
  },
];

describe("buildTeamLearningRolePlans", () => {
  test("summarizes admission and next role lesson from member progress", () => {
    const summaries = buildTeamLearningSummaries(staff, progress);
    const plans = buildTeamLearningRolePlans(summaries);
    const service = plans.find((plan) => plan.roleId === "service");

    expect(service).toMatchObject({
      roleTitle: "Официант",
      members: 2,
      totalItems: 2,
      requiredItems: 1,
      requiredProgressPct: 50,
      admissionPct: 50,
    });
    expect(service?.blockedMembers).toEqual([
      {
        memberId: "service-2",
        memberName: "Петр",
        nextItemTitle: "Как рекомендовать блюдо без давления",
      },
    ]);
    expect(service?.nextItem?.id).toBe("service-recommendation");
  });

  test("creates a task draft for the first blocked admission", () => {
    const summaries = buildTeamLearningSummaries(staff, progress);
    const service = buildTeamLearningRolePlans(summaries).find(
      (plan) => plan.roleId === "service",
    );

    expect(service).toBeDefined();
    const draft = buildLearningAdmissionTaskDraft(service!);

    expect(draft).toEqual({
      title: "Пройти обучение: Как рекомендовать блюдо без давления",
      priority: "medium",
      audienceType: "member",
      audienceMemberId: "service-2",
      memberName: "Петр",
      moduleTitle: "Как рекомендовать блюдо без давления",
      roleTitle: "Официант",
      dueLabel: "до смены",
    });
  });

  test("keeps role lesson catalog visible even before staff is created", () => {
    const plans = buildTeamLearningRolePlans([]);
    const owner = plans.find((plan) => plan.roleId === "owner");

    expect(owner).toMatchObject({
      roleTitle: "Владелец",
      members: 0,
      totalItems: 3,
      admissionPct: 100,
      requiredProgressPct: 100,
    });
  });
});
