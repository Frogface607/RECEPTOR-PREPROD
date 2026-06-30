import { describe, expect, test } from "vitest";
import { DEMO_CONTEXT_ANSWERS } from "@/lib/venues/context-questionnaire";
import type { TeamLearningMemberSummary } from "@/lib/team/team-learning-progress";
import type { StaffMember, TeamTask, TeamTaskComment } from "@/lib/team/team-os";
import { buildOwnerBrainReadiness } from "./owner-brain-readiness";

const staff: StaffMember[] = [
  {
    id: "manager",
    name: "Маша",
    roleId: "venue_manager",
    venueId: "venue",
    status: "active",
    shiftLabel: "вечер",
  },
  {
    id: "service",
    name: "Алина",
    roleId: "service",
    venueId: "venue",
    status: "active",
    shiftLabel: "зал",
  },
];

const tasks: TeamTask[] = [
  {
    id: "field",
    title: "Полевой контекст смены",
    source: "manager",
    sourceLabel: "Поле",
    priority: "medium",
    status: "in_progress",
    venueId: "venue",
    audience: { type: "venue", venueId: "venue" },
    dueLabel: "после смены",
  },
];

const comments: TeamTaskComment[] = [
  {
    id: "note",
    venueId: "venue",
    taskId: "field",
    authorName: "Маша",
    body:
      "Итог смены: ливень, гости отменяли брони, закончилась мята, утром проверить стоп-лист.",
    createdAtLabel: "22:30",
  },
];

function learningSummary(
  member: StaffMember,
  canWorkShift = true,
): TeamLearningMemberSummary {
  return {
    member,
    items: [],
    totalCount: 1,
    requiredCount: 1,
    requiredMissing: canWorkShift ? 0 : 1,
    completedCount: canWorkShift ? 1 : 0,
    requiredCompleted: canWorkShift ? 1 : 0,
    averageBest: canWorkShift ? 100 : 0,
    status: canWorkShift ? "complete" : "not_started",
    admissionStatus: canWorkShift ? "admitted" : "not_started",
    canWorkShift,
    nextItem: null,
    lastCompletedAt: canWorkShift ? "2026-06-30T10:00:00.000Z" : "",
  };
}

describe("owner brain readiness", () => {
  test("asks for restaurant profile first when the advisor has no context", () => {
    const readiness = buildOwnerBrainReadiness({
      context: {},
      staff: [],
      tasks: [],
      comments: [],
      learningSummaries: [],
      dataMode: "mock",
    });

    expect(readiness.tone).toBe("risk");
    expect(readiness.nextSource.id).toBe("context");
    expect(readiness.summary).toContain("докормите");
  });

  test("marks the restaurant brain usable when context, field notes and team are present", () => {
    const readiness = buildOwnerBrainReadiness({
      context: DEMO_CONTEXT_ANSWERS,
      staff,
      tasks,
      comments,
      learningSummaries: staff.map((member) => learningSummary(member)),
      dataMode: "live",
    });

    expect(readiness.score).toBeGreaterThanOrEqual(80);
    expect(readiness.tone).toBe("good");
    expect(readiness.nextSource.id).toBe("context");
    expect(readiness.sources.find((source) => source.id === "field")?.status).toBe(
      "ready",
    );
  });

  test("shows learning as the next source when staff is not admitted to shifts", () => {
    const readiness = buildOwnerBrainReadiness({
      context: DEMO_CONTEXT_ANSWERS,
      staff,
      tasks,
      comments,
      learningSummaries: staff.map((member, index) =>
        learningSummary(member, index === 0),
      ),
      dataMode: "live",
    });

    expect(readiness.nextSource.id).toBe("learning");
    expect(readiness.nextSource.detail).toContain("Не допущены");
  });
});
