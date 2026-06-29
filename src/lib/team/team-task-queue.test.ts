import { describe, expect, it } from "vitest";
import type { TeamTask } from "./team-os";
import {
  buildTeamTaskQueue,
  isOpenTeamTask,
  teamTaskContourLabel,
} from "./team-task-queue";

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

  it("uses task impact inside the same priority and status", () => {
    const queue = buildTeamTaskQueue([
      task({ id: "plain", priority: "high", status: "new" }),
      task({
        id: "medium-impact",
        priority: "high",
        status: "new",
        impactLabel: "ФОТ 20%",
      }),
      task({
        id: "high-impact",
        priority: "high",
        status: "new",
        impactLabel: "ФОТ 35%",
      }),
    ]);

    expect(queue.openTasks.map((item) => item.task.id)).toEqual([
      "high-impact",
      "medium-impact",
      "plain",
    ]);
  });

  it("keeps explicit priority above impact score", () => {
    const queue = buildTeamTaskQueue([
      task({
        id: "medium-money",
        priority: "medium",
        impactLabel: "150 000 ₽",
      }),
      task({ id: "high-plain", priority: "high" }),
    ]);

    expect(queue.openTasks.map((item) => item.task.id)).toEqual([
      "high-plain",
      "medium-money",
    ]);
  });

  it("counts urgent open tasks and groups open contours", () => {
    const queue = buildTeamTaskQueue([
      task({
        id: "fot",
        priority: "high",
        sourceLabel: "ФОТ и маржа",
      }),
      task({
        id: "fot-2",
        priority: "medium",
        sourceLabel: "ФОТ и маржа",
      }),
      task({
        id: "shift",
        priority: "high",
        sourceLabel: "План смен",
      }),
      task({
        id: "closed",
        priority: "high",
        sourceLabel: "ФОТ и маржа",
        status: "done",
      }),
    ]);

    expect(queue.urgentOpenCount).toBe(2);
    expect(queue.openContours).toEqual([
      { label: "ФОТ и маржа", count: 2 },
      { label: "План смен", count: 1 },
    ]);
  });

  it("uses product contour labels when a task has no source label", () => {
    expect(teamTaskContourLabel(task({ source: "copilot" }))).toBe("Receptor");
    expect(teamTaskContourLabel(task({ source: "chef" }))).toBe("Кухня");
    expect(teamTaskContourLabel(task({ source: "owner" }))).toBe("Владелец");
    expect(teamTaskContourLabel(task({ source: "manager" }))).toBe("Team OS");
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
