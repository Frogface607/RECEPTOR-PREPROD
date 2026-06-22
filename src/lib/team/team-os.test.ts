import { describe, expect, test } from "vitest";
import {
  buildRoleHome,
  getTeamRole,
  listAnnouncementsForRole,
  listCommentsForTask,
  listRolePermissions,
  listTasksForMember,
  listTasksForRole,
  roleCan,
} from "./team-os";

describe("Team OS roles and permissions", () => {
  test("keeps owner-level cockpit hidden from service staff", () => {
    expect(roleCan("owner", "view_owner_cockpit")).toBe(true);
    expect(roleCan("service", "view_owner_cockpit")).toBe(false);
    expect(roleCan("service", "complete_own_tasks")).toBe(true);
  });

  test("builds role home from permissions and visible tasks", () => {
    const home = buildRoleHome("venue_manager");

    expect(home.role.title).toBe("Управляющий");
    expect(home.sections).toContain("Задачи");
    expect(home.permissions.map((permission) => permission.id)).toContain(
      "assign_tasks",
    );
    expect(home.visibleTasks.some((task) => task.id === "task-menu-1")).toBe(
      true,
    );
  });

  test("limits line cooks to venue-wide, role and direct tasks", () => {
    const cookTasks = listTasksForMember("staff-cook");

    expect(cookTasks.map((task) => task.id)).toEqual([
      "task-cook-1",
      "task-venue-1",
    ]);
    expect(listTasksForRole("line_cook").map((task) => task.id)).toEqual([
      "task-venue-1",
    ]);
  });

  test("throws for unknown roles", () => {
    expect(() => getTeamRole("bad" as never)).toThrow("Unknown team role");
  });

  test("returns readable permission descriptions", () => {
    const permissions = listRolePermissions("chef");

    expect(permissions.map((permission) => permission.title)).toContain("Меню");
  });

  test("lists comments for a concrete task", () => {
    const comments = listCommentsForTask("task-menu-1");

    expect(comments).toHaveLength(1);
    expect(comments[0]?.authorName).toBe("Роман");
  });

  test("filters announcements by role visibility", () => {
    const serviceAnnouncements = listAnnouncementsForRole("service");
    const chefAnnouncements = listAnnouncementsForRole("chef");

    expect(serviceAnnouncements.map((item) => item.id)).toEqual([
      "announcement-venue-1",
      "announcement-service-1",
    ]);
    expect(chefAnnouncements.map((item) => item.id)).toContain(
      "announcement-kitchen-1",
    );
  });
});
