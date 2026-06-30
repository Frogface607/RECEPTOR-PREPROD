import type { TeamLearningItem } from "./team-learning";
import type { TeamLearningProgressSnapshot } from "./team-learning-progress";

export type TeamLearningAdmissionStatus =
  | "admitted"
  | "needs_training"
  | "not_started";

export type TeamLearningAdmission = {
  status: TeamLearningAdmissionStatus;
  title: string;
  detail: string;
  requiredCompleted: number;
  requiredCount: number;
  completedCount: number;
  totalCount: number;
  averageBest: number;
  nextItem: TeamLearningItem | null;
};

export function buildTeamLearningAdmission({
  items,
  progress,
}: {
  items: TeamLearningItem[];
  progress: Record<string, TeamLearningProgressSnapshot | undefined>;
}): TeamLearningAdmission {
  const requiredItems = items.filter((item) => item.status === "required");
  const completedItems = items.filter((item) => isItemPassed(item, progress));
  const requiredCompleted = requiredItems.filter((item) =>
    isItemPassed(item, progress),
  ).length;
  const requiredCount = requiredItems.length;
  const nextItem =
    requiredItems.find((item) => !isItemPassed(item, progress)) ??
    items.find((item) => !isItemPassed(item, progress)) ??
    null;
  const attemptedCount = items.filter((item) => progress[item.id]).length;
  const averageBest =
    items.length > 0
      ? Math.round(
          items.reduce(
            (sum, item) => sum + (progress[item.id]?.bestPercentage ?? 0),
            0,
          ) / items.length,
        )
      : 0;
  const admitted = requiredCount === 0 || requiredCompleted >= requiredCount;
  const status = admitted
    ? "admitted"
    : attemptedCount === 0
      ? "not_started"
      : "needs_training";

  return {
    status,
    title:
      status === "admitted"
        ? "К смене допущен"
        : status === "needs_training"
          ? "Нужно закрыть обязательный стандарт"
          : "Допуск к смене еще не начат",
    detail:
      status === "admitted"
        ? "Обязательные стандарты закрыты. Можно продолжать обучение и закреплять слабые места."
        : nextItem
          ? `Следующий стандарт: ${nextItem.title}.`
          : "Назначьте обязательный стандарт для этой роли.",
    requiredCompleted,
    requiredCount,
    completedCount: completedItems.length,
    totalCount: items.length,
    averageBest,
    nextItem,
  };
}

function isItemPassed(
  item: TeamLearningItem,
  progress: Record<string, TeamLearningProgressSnapshot | undefined>,
): boolean {
  return (progress[item.id]?.bestPercentage ?? 0) >= item.passPercentage;
}
