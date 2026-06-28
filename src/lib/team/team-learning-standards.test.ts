import { describe, expect, test } from "vitest";
import {
  countCustomLearningStandards,
  listLearningItemsForRoleWithStandards,
  type TeamLearningStandardOverride,
} from "./team-learning-standards";

const standards: TeamLearningStandardOverride[] = [
  {
    venueId: "venue-1",
    roleId: "service",
    moduleId: "guest-feedback",
    status: "required",
    updatedAt: "2026-06-28T00:00:00.000Z",
  },
  {
    venueId: "venue-1",
    roleId: "service",
    moduleId: "service-recommendation",
    status: "hidden",
    updatedAt: "2026-06-28T00:00:00.000Z",
  },
];

describe("team learning standards", () => {
  test("applies venue overrides to role learning items", () => {
    const items = listLearningItemsForRoleWithStandards("service", standards);

    expect(items.map((item) => item.id)).not.toContain(
      "service-recommendation",
    );
    expect(items.find((item) => item.id === "guest-feedback")?.status).toBe(
      "required",
    );
  });

  test("counts only standards that differ from the base catalog", () => {
    expect(countCustomLearningStandards("service", standards)).toBe(2);
    expect(countCustomLearningStandards("chef", standards)).toBe(0);
  });
});
