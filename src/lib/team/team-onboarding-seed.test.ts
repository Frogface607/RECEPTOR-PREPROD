import { describe, expect, test } from "vitest";
import { listLearningItemsForRole } from "./team-learning";
import { buildTeamOnboardingSeed } from "./team-onboarding-seed";

describe("buildTeamOnboardingSeed", () => {
  test("creates an owner workspace and first operational tasks", () => {
    const seed = buildTeamOnboardingSeed({
      venueId: "venue-1",
      venueName: "Edison",
      venueType: "bar",
      ownerUserId: "user-1",
      ownerEmail: "owner@example.com",
      createdAt: "2026-06-28T06:00:00.000Z",
    });

    expect(seed.ownerMembership).toMatchObject({
      venue_id: "venue-1",
      user_id: "user-1",
      role: "owner",
      status: "active",
    });
    expect(seed.tasks.map((task) => task.title)).toEqual([
      "Добавить управляющего и ключевых сотрудников в Team OS",
      "Заполнить ставки ФОТ для сотрудников из iiko",
      "Проверить техкарты и закупочные цены для маржи",
      "Утвердить стандарты допуска к смене по ролям",
    ]);
    expect(seed.tasks.every((task) => task.source === "copilot")).toBe(true);
    expect(seed.announcement.body).toContain("команда, ставки ФОТ");
  });

  test("builds only valid role learning standards", () => {
    const seed = buildTeamOnboardingSeed({
      venueId: "venue-1",
      venueName: "Edison",
      venueType: "restaurant",
      ownerUserId: "user-1",
      ownerEmail: null,
      createdAt: "2026-06-28T06:00:00.000Z",
    });
    const pairs = new Set<string>();

    for (const standard of seed.learningStandards) {
      const itemIds = new Set(
        listLearningItemsForRole(standard.role).map((item) => item.id),
      );
      expect(itemIds.has(standard.module_id)).toBe(true);
      expect(standard.status).toBe("required");
      expect(pairs.has(`${standard.role}:${standard.module_id}`)).toBe(false);
      pairs.add(`${standard.role}:${standard.module_id}`);
    }

    expect(pairs).toEqual(
      new Set([
        "owner:owner-morning",
        "operations_manager:shift-brief",
        "venue_manager:shift-brief",
        "chef:kitchen-stop-list",
        "chef:tech-card-discipline",
        "line_cook:kitchen-stop-list",
        "service:service-recommendation",
        "service:guest-feedback",
        "marketing:guest-feedback",
      ]),
    );
  });

  test("keeps coffee onboarding lean when kitchen roles are not assumed", () => {
    const seed = buildTeamOnboardingSeed({
      venueId: "venue-1",
      venueName: "Small Coffee",
      venueType: "coffee",
      ownerUserId: "user-1",
      ownerEmail: null,
      createdAt: "2026-06-28T06:00:00.000Z",
    });

    expect(seed.learningStandards.map((standard) => standard.role)).not.toEqual(
      expect.arrayContaining(["chef", "line_cook"]),
    );
    expect(seed.learningStandards).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          role: "service",
          module_id: "service-recommendation",
        }),
        expect.objectContaining({
          role: "service",
          module_id: "guest-feedback",
        }),
      ]),
    );
  });
});
