import { describe, expect, test } from "vitest";
import type { StaffMember, TeamTaskComment } from "./team-os";
import { buildTeamLearningAdoptionSignal } from "./team-learning-adoption";
import {
  buildTeamLearningSummaries,
  type TeamLearningProgress,
} from "./team-learning-progress";

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
    id: "chef-1",
    name: "Роман",
    roleId: "chef",
    venueId: "venue-1",
    status: "active",
    shiftLabel: "кухня",
  },
];

const serviceProgress: TeamLearningProgress = {
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
};

const matchingComment: TeamTaskComment = {
  id: "comment-1",
  venueId: "venue-1",
  taskId: "field-note",
  authorName: "Маша",
  body: 'Итог смены по стандарту "Как рекомендовать блюдо без давления": факт - гости чаще спрашивали лимонад; контекст - жара; когда/сколько - вечер; что проверить - апселл десерта.',
  createdAtLabel: "21:40",
};

describe("team learning adoption", () => {
  test("marks a passed standard as returned when a shift-memory note exists", () => {
    const [summary] = buildTeamLearningSummaries(staff, [serviceProgress]);

    const signal = buildTeamLearningAdoptionSignal({
      summary,
      progress: [serviceProgress],
      comments: [matchingComment],
    });

    expect(signal).toMatchObject({
      status: "returned_memory",
      moduleId: "service-recommendation",
      memoryCommentId: "comment-1",
    });
  });

  test("asks for a shift fact when the latest passed standard has no memory", () => {
    const [summary] = buildTeamLearningSummaries(staff, [serviceProgress]);

    const signal = buildTeamLearningAdoptionSignal({
      summary,
      progress: [serviceProgress],
      comments: [],
    });

    expect(signal).toMatchObject({
      status: "needs_memory",
      moduleId: "service-recommendation",
      memoryCommentId: null,
    });
    expect(signal.detail).toContain("не подтвержден итогом смены");
  });

  test("waits for learning before asking for operational adoption", () => {
    const [, summary] = buildTeamLearningSummaries(staff, []);

    const signal = buildTeamLearningAdoptionSignal({
      summary,
      progress: [],
      comments: [],
    });

    expect(signal).toMatchObject({
      status: "not_ready",
      moduleId: "kitchen-stop-list",
      memoryCommentId: null,
    });
  });
});
