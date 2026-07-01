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

export function isIikoMemberImportTaskTitle(title: string): boolean {
  const normalized = title.toLocaleLowerCase("ru-RU");
  const mentionsIiko = normalized.includes("iiko");
  const mentionsImport =
    normalized.includes("импорт") || normalized.includes("карточ");
  const mentionsTeam =
    normalized.includes("сотруд") || normalized.includes("team os");

  return mentionsIiko && mentionsImport && mentionsTeam;
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

export function selectIikoMemberImportTasksToClose(
  tasks: AutoClosableTask[],
): AutoClosableTask[] {
  return tasks.filter(
    (task) =>
      !CLOSED_STATUSES.has(task.status) &&
      task.audience.type !== "member" &&
      isIikoMemberImportTaskTitle(task.title),
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

export function extractLearningStandardTitleFromFieldNote(
  body: string,
): string | null {
  const match = body.match(
    /итог\s+смены\s+по\s+стандарту\s*["«“](.+?)["»”]/iu,
  );
  const title = match?.[1]?.trim();
  return title || null;
}

export function selectLearningAdoptionTasksToClose(
  tasks: AutoClosableTask[],
  input: { memberId: string; fieldNoteBody: string },
): AutoClosableTask[] {
  const memberId = input.memberId.trim();
  const moduleTitle = extractLearningStandardTitleFromFieldNote(
    input.fieldNoteBody,
  );
  if (!memberId || !moduleTitle) return [];

  const titlePrefix = normalizeTaskTitle("Вернуть факт смены:");
  const normalizedModuleTitle = normalizeTaskTitle(moduleTitle);

  return tasks.filter((task) => {
    const title = normalizeTaskTitle(task.title);

    return (
      !CLOSED_STATUSES.has(task.status) &&
      task.audience.type === "member" &&
      task.audience.memberId === memberId &&
      title.startsWith(titlePrefix) &&
      title.endsWith(normalizedModuleTitle)
    );
  });
}

function normalizeTaskTitle(value: string): string {
  return value
    .trim()
    .replace(/[‐‑‒–—]/g, "-")
    .replace(/\s+/g, " ")
    .toLocaleLowerCase("ru-RU");
}
