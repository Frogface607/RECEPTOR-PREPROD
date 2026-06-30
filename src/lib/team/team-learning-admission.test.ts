import { describe, expect, test } from "vitest";
import { buildTeamLearningAdmission } from "./team-learning-admission";
import type { TeamLearningItem } from "./team-learning";
import type { TeamLearningProgressSnapshot } from "./team-learning-progress";

const items: TeamLearningItem[] = [
  {
    id: "service-required",
    title: "Сервис перед сменой",
    description: "Обязательный стандарт",
    timeLabel: "5 минут",
    status: "required",
    passPercentage: 80,
    sections: [],
    quiz: [],
  },
  {
    id: "upsell-ready",
    title: "Апселл без давления",
    description: "Дополнительный стандарт",
    timeLabel: "7 минут",
    status: "ready",
    passPercentage: 80,
    sections: [],
    quiz: [],
  },
];

describe("team learning admission", () => {
  test("starts blocked by the first required standard", () => {
    const admission = buildTeamLearningAdmission({ items, progress: {} });

    expect(admission).toMatchObject({
      status: "not_started",
      title: "Допуск к смене еще не начат",
      requiredCompleted: 0,
      requiredCount: 1,
      nextItem: expect.objectContaining({ id: "service-required" }),
    });
  });

  test("admits the member after required standards are passed", () => {
    const admission = buildTeamLearningAdmission({
      items,
      progress: {
        "service-required": progress(100),
      },
    });

    expect(admission).toMatchObject({
      status: "admitted",
      title: "К смене допущен",
      requiredCompleted: 1,
      requiredCount: 1,
      completedCount: 1,
      nextItem: expect.objectContaining({ id: "upsell-ready" }),
    });
  });

  test("keeps admission blocked when a required attempt is below pass score", () => {
    const admission = buildTeamLearningAdmission({
      items,
      progress: {
        "service-required": progress(67),
      },
    });

    expect(admission).toMatchObject({
      status: "needs_training",
      requiredCompleted: 0,
      averageBest: 34,
      nextItem: expect.objectContaining({ id: "service-required" }),
    });
  });
});

function progress(bestPercentage: number): TeamLearningProgressSnapshot {
  return {
    bestPercentage,
    lastPercentage: bestPercentage,
    correct: 2,
    total: 3,
    passed: bestPercentage >= 80,
    answers: [],
    completedAt: "2026-06-30T00:00:00.000Z",
  };
}
