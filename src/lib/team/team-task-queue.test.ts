import { describe, expect, it } from "vitest";
import type { TeamTask } from "./team-os";
import { buildTeamTaskQueue, isOpenTeamTask } from "./team-task-queue";

describe("team task queue", () => {
  it("classifies operationally open tasks", () => {
    expect(isOpenTeamTask(task({ status: "new" }))).toBe(true);
    expect(isOpenTeamTask(task({ status: "in_progress" }))).toBe(true);
    expect(isOpenTeamTask(task({ status: "done" }))).toBe(false);
    expect(isOpenTeamTask(task({ status: "verified" }))).toBe(false);
  });

  it("keeps only open tasks in the operational queue", () => {
    const queue = buildTeamTaskQueue([
      task({ id: "new", status: "new" }),
      task({ id: "accepted", status: "accepted" }),
      task({ id: "progress", status: "in_progress" }),
      task({ id: "done", status: "done" }),
      task({ id: "verified", status: "verified" }),
    ]);

    expect(queue.openTasks.map((item) => item.task.id)).toEqual([
      "new",
      "accepted",
      "progress",
    ]);
    expect(queue.openCount).toBe(3);
    expect(queue.completedCount).toBe(2);
  });

  it("puts the focused task first even when it has lower priority", () => {
    const queue = buildTeamTaskQueue(
      [
        task({ id: "high", priority: "high" }),
        task({ id: "low-focused", priority: "low" }),
      ],
      "low-focused",
    );

    expect(queue.openTasks.map((item) => item.task.id)).toEqual([
      "low-focused",
      "high",
    ]);
    expect(queue.focusedTask?.task.id).toBe("low-focused");
  });

  it("uses priority before status for the default queue order", () => {
    const queue = buildTeamTaskQueue([
      task({ id: "medium-new", priority: "medium", status: "new" }),
      task({ id: "high-progress", priority: "high", status: "in_progress" }),
      task({ id: "low-new", priority: "low", status: "new" }),
    ]);

    expect(queue.openTasks.map((item) => item.task.id)).toEqual([
      "high-progress",
      "medium-new",
      "low-new",
    ]);
  });
});

function task(overrides: Partial<TeamTask>): TeamTask {
  return {
    id: "task",
    title: "Проверить смену",
    source: "manager",
    priority: "medium",
    status: "new",
    venueId: "venue",
    audience: { type: "venue", venueId: "venue" },
    dueLabel: "сегодня",
    ...overrides,
  };
}
