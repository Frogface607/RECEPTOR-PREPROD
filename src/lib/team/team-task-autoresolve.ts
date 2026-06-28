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

export function selectLearningAdmissionTasksToClose(
  tasks: AutoClosableTask[],
  input: { memberId: string; moduleTitle: string },
): AutoClosableTask[] {
  const memberId = input.memberId.trim();
  const moduleTitle = input.moduleTitle.trim();
  if (!memberId || !moduleTitle) return [];

  const expectedTitle = normalizeTaskTitle(`Пройти обучение: ${moduleTitle}`);

  return tasks.filter(
    (task) =>
      !CLOSED_STATUSES.has(task.status) &&
      task.audience.type === "member" &&
      task.audience.memberId === memberId &&
      normalizeTaskTitle(task.title) === expectedTitle,
  );
}

function normalizeTaskTitle(value: string): string {
  return value.trim().replace(/\s+/g, " ").toLocaleLowerCase("ru-RU");
}
