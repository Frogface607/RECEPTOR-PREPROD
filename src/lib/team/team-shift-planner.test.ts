import { describe, expect, test } from "vitest";
import type { StaffMember, TeamTask } from "./team-os";
import { buildShiftOverview } from "./team-shift-planner";

const staff: StaffMember[] = [
  {
    id: "manager-1",
    name: "Alina",
    roleId: "venue_manager",
    venueId: "venue-1",
    status: "active",
    shiftLabel: "12:00-23:00",
  },
  {
    id: "service-1",
    name: "Masha",
    roleId: "service",
    venueId: "venue-1",
    status: "active",
    shiftLabel: "зал 16:00-00:00",
  },
  {
    id: "chef-1",
    name: "Roman",
    roleId: "chef",
    venueId: "venue-1",
    status: "paused",
    shiftLabel: "кухня 10:00-22:00",
  },
  {
    id: "cook-1",
    name: "Ilya",
    roleId: "line_cook",
    venueId: "venue-1",
    status: "invited",
    shiftLabel: "горячий цех 14:00-23:00",
  },
];

const tasks: TeamTask[] = [
  {
    id: "task-service",
    title: "Focus service",
    source: "manager",
    priority: "high",
    status: "new",
    venueId: "venue-1",
    audience: { type: "role", roleId: "service" },
    dueLabel: "today",
  },
  {
    id: "task-venue",
    title: "Read announcement",
    source: "manager",
    priority: "low",
    status: "accepted",
    venueId: "venue-1",
    audience: { type: "venue", venueId: "venue-1" },
    dueLabel: "today",
  },
  {
    id: "task-done",
    title: "Closed",
    source: "manager",
    priority: "high",
    status: "done",
    venueId: "venue-1",
    audience: { type: "role", roleId: "service" },
    dueLabel: "today",
  },
];

describe("buildShiftOverview", () => {
  test("summarizes active staff, tasks and role coverage", () => {
    const overview = buildShiftOverview(staff, tasks);

    expect(overview.activeStaff).toBe(2);
    expect(overview.invitedStaff).toBe(1);
    expect(overview.pausedStaff).toBe(1);
    expect(overview.openTasks).toBe(2);
    expect(overview.importantTasks).toBe(1);

    const service = overview.coverage.find((item) => item.roleId === "service");
    expect(service).toMatchObject({
      status: "covered",
      openTasks: 2,
      importantTasks: 1,
      shiftLabels: ["зал 16:00-00:00"],
    });

    const cook = overview.coverage.find((item) => item.roleId === "line_cook");
    expect(cook?.status).toBe("invited");

    const chef = overview.coverage.find((item) => item.roleId === "chef");
    expect(chef?.status).toBe("empty");
  });
});
