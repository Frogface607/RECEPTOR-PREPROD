import type { TeamTask } from "./team-os";

const OPEN_STATUSES = new Set<TeamTask["status"]>([
  "new",
  "accepted",
  "in_progress",
]);

const PRIORITY_RANK: Record<TeamTask["priority"], number> = {
  high: 0,
  medium: 1,
  low: 2,
};

const STATUS_RANK: Record<TeamTask["status"], number> = {
  new: 0,
  accepted: 1,
  in_progress: 2,
  done: 3,
  verified: 4,
};

export type TeamTaskQueueItem = {
  task: TeamTask;
  focused: boolean;
};

export type TeamTaskQueueSummary = {
  totalCount: number;
  openCount: number;
  inProgressCount: number;
  completedCount: number;
  focusedTask: TeamTaskQueueItem | null;
  openTasks: TeamTaskQueueItem[];
};

export function isOpenTeamTask(task: Pick<TeamTask, "status">): boolean {
  return OPEN_STATUSES.has(task.status);
}

export function buildTeamTaskQueue(
  tasks: TeamTask[],
  focusTaskId = "",
): TeamTaskQueueSummary {
  const items = tasks.map((task, index) => ({
    task,
    focused: focusTaskId === task.id,
    index,
  }));

  const openTasks = items
    .filter((item) => isOpenTeamTask(item.task))
    .sort((left, right) => {
      if (left.focused !== right.focused) return left.focused ? -1 : 1;

      const priorityDelta =
        PRIORITY_RANK[left.task.priority] - PRIORITY_RANK[right.task.priority];
      if (priorityDelta !== 0) return priorityDelta;

      const statusDelta =
        STATUS_RANK[left.task.status] - STATUS_RANK[right.task.status];
      if (statusDelta !== 0) return statusDelta;

      return left.index - right.index;
    })
    .map(({ task, focused }) => ({ task, focused }));

  const focusedTask =
    items.find((item) => item.focused && isOpenTeamTask(item.task)) ??
    items.find((item) => item.focused) ??
    null;

  return {
    totalCount: tasks.length,
    openCount: openTasks.length,
    inProgressCount: tasks.filter((task) => task.status === "in_progress")
      .length,
    completedCount: tasks.filter(
      (task) => task.status === "done" || task.status === "verified",
    ).length,
    focusedTask: focusedTask
      ? { task: focusedTask.task, focused: focusedTask.focused }
      : null,
    openTasks,
  };
}
