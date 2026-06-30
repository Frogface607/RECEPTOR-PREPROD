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

function taskImpactScore(task: TeamTask): number {
  const label = task.impactLabel?.trim();
  if (!label) return 0;

  const match = label.match(
    /-?\d+(?:[\s\u00a0]\d{3})*(?:[,.]\d+)?|-?\d+(?:[,.]\d+)?/,
  );
  if (!match) return 1;

  const value = Number(match[0].replace(/[\s\u00a0]/g, "").replace(",", "."));
  if (!Number.isFinite(value)) return 1;

  if (label.includes("₽")) return Math.max(value / 1000, 1);
  if (label.includes("%")) return Math.max(value * 100, 1);
  return Math.max(value, 1);
}

export type TeamTaskQueueItem = {
  task: TeamTask;
  focused: boolean;
};

export type TeamTaskQueueContour = {
  label: string;
  count: number;
};

export type TeamTaskQueueSummary = {
  totalCount: number;
  openCount: number;
  urgentOpenCount: number;
  inProgressCount: number;
  completedCount: number;
  openContours: TeamTaskQueueContour[];
  focusedTask: TeamTaskQueueItem | null;
  openTasks: TeamTaskQueueItem[];
};

export function isOpenTeamTask(task: Pick<TeamTask, "status">): boolean {
  return OPEN_STATUSES.has(task.status);
}

export function teamTaskContourLabel(task: TeamTask): string {
  if (task.sourceLabel?.trim()) return task.sourceLabel.trim();
  if (task.source === "copilot") return "Receptor";
  if (task.source === "chef") return "Кухня";
  if (task.source === "owner") return "Владелец";
  return "Команда";
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

      const impactDelta =
        taskImpactScore(right.task) - taskImpactScore(left.task);
      if (impactDelta !== 0) return impactDelta;

      return left.index - right.index;
    })
    .map(({ task, focused }) => ({ task, focused }));

  const openContours = Array.from(
    openTasks.reduce((acc, item) => {
      const label = teamTaskContourLabel(item.task);
      acc.set(label, (acc.get(label) ?? 0) + 1);
      return acc;
    }, new Map<string, number>()),
    ([label, count]) => ({ label, count }),
  ).sort((left, right) => {
    if (right.count !== left.count) return right.count - left.count;
    return left.label.localeCompare(right.label, "ru");
  });

  const focusedTask =
    items.find((item) => item.focused && isOpenTeamTask(item.task)) ??
    items.find((item) => item.focused) ??
    null;

  return {
    totalCount: tasks.length,
    openCount: openTasks.length,
    urgentOpenCount: openTasks.filter((item) => item.task.priority === "high")
      .length,
    inProgressCount: tasks.filter((task) => task.status === "in_progress")
      .length,
    completedCount: tasks.filter(
      (task) => task.status === "done" || task.status === "verified",
    ).length,
    openContours,
    focusedTask: focusedTask
      ? { task: focusedTask.task, focused: focusedTask.focused }
      : null,
    openTasks,
  };
}
