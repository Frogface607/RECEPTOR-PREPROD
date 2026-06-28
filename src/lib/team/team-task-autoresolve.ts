import type { TeamTask } from "./team-os";

type AutoClosableTask = Pick<TeamTask, "id" | "title" | "status" | "audience">;

const CLOSED_STATUSES = new Set<TeamTask["status"]>(["done", "verified"]);

export function isLaborRateSetupTaskTitle(title: string): boolean {
  const normalized = title.toLowerCase();
  const isRussianLaborRate =
    normalized.includes("фот") && normalized.includes("став");
  const isEnglishLaborRate =
    normalized.includes("labor") && normalized.includes("rate");

  return isRussianLaborRate || isEnglishLaborRate;
}

export function selectLaborRateTasksToClose(
  tasks: AutoClosableTask[],
  memberIds: string[],
): AutoClosableTask[] {
  const targetMemberIds = new Set(memberIds.filter(Boolean));
  if (targetMemberIds.size === 0) return [];

  return tasks.filter(
    (task) =>
      !CLOSED_STATUSES.has(task.status) &&
      task.audience.type === "member" &&
      targetMemberIds.has(task.audience.memberId) &&
      isLaborRateSetupTaskTitle(task.title),
  );
}
