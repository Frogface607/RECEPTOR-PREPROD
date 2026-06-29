import { describe, expect, test } from "vitest";
import type { StaffMember } from "./team-os";
import {
  buildTeamLearningSummaries,
  summarizeTeamLearning,
  type TeamLearningProgress,
} from "./team-learning-progress";
import type { TeamLearningStandardOverride } from "./team-learning-standards";

const staff: StaffMember[] = [
  {
    id: "service-1",
    name: "Masha",
    roleId: "service",
    venueId: "venue-1",
    status: "active",
    shiftLabel: "зал",
  },
  {
    id: "chef-1",
    name: "Roman",
    roleId: "chef",
    venueId: "venue-1",
    status: "active",
    shiftLabel: "кухня",
  },
];

const progress: TeamLearningProgress[] = [
  {
    venueId: "venue-1",
    membershipId: "service-1",
    userId: "user-1",
    moduleId: "service-recommendation",
    bestPercentage: 100,
    lastPercentage: 100,
    correct: 3,
    total: 3,
    passed: true,
    answers: [1, 0, 2],
    completedAt: "2026-06-26T10:00:00.000Z",
    updatedAt: "2026-06-26T10:00:00.000Z",
  },
  {
    venueId: "venue-1",
    membershipId: "chef-1",
    userId: "user-2",
    moduleId: "kitchen-stop-list",
    bestPercentage: 67,
    lastPercentage: 67,
    correct: 2,
    total: 3,
    passed: false,
    answers: [0, 1, 0],
    completedAt: "2026-06-26T11:00:00.000Z",
    updatedAt: "2026-06-26T11:00:00.000Z",
  },
];

describe("team learning progress", () => {
  test("builds member learning summaries", () => {
    const summaries = buildTeamLearningSummaries(staff, progress);
    const service = summaries.find(
      (summary) => summary.member.id === "service-1",
    );
    const chef = summaries.find((summary) => summary.member.id === "chef-1");

    expect(service).toMatchObject({
      completedCount: 1,
      requiredCompleted: 1,
      requiredMissing: 0,
      status: "attention",
      admissionStatus: "admitted",
      canWorkShift: true,
    });
    expect(service?.nextItem?.id).toBe("sales-eight-upsell");
    expect(chef).toMatchObject({
      completedCount: 0,
      requiredCompleted: 0,
      requiredMissing: 1,
      status: "not_started",
      admissionStatus: "not_started",
      canWorkShift: false,
    });
    expect(chef?.nextItem?.id).toBe("kitchen-stop-list");
  });

  test("summarizes team-wide learning state", () => {
    const summaries = buildTeamLearningSummaries(staff, progress);
    const overview = summarizeTeamLearning(summaries);

    expect(overview).toEqual({
      completedMembers: 0,
      attentionMembers: 1,
      notStartedMembers: 1,
      admittedMembers: 1,
      blockedMembers: 1,
      admissionPct: 50,
      averageBest: 17,
    });
  });

  test("uses venue learning standards for shift admission", () => {
    const standards: TeamLearningStandardOverride[] = [
      {
        venueId: "venue-1",
        roleId: "service",
        moduleId: "guest-feedback",
        status: "required",
        updatedAt: "2026-06-28T00:00:00.000Z",
      },
    ];
    const summaries = buildTeamLearningSummaries(staff, progress, standards);
    const service = summaries.find(
      (summary) => summary.member.id === "service-1",
    );

    expect(service).toMatchObject({
      requiredCount: 2,
      requiredCompleted: 1,
      requiredMissing: 1,
      admissionStatus: "needs_training",
      canWorkShift: false,
    });
    expect(service?.nextItem?.id).toBe("guest-feedback");
  });
});
