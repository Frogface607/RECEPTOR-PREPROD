import type { TeamTaskComment } from "./team-os";
import type {
  TeamLearningMemberSummary,
  TeamLearningProgress,
} from "./team-learning-progress";
import { isLikelySameTeamMemberName } from "./team-member-match";

export type TeamLearningAdoptionStatus =
  | "not_ready"
  | "needs_memory"
  | "returned_memory";

export type TeamLearningAdoptionSignal = {
  status: TeamLearningAdoptionStatus;
  label: string;
  detail: string;
  moduleId: string | null;
  moduleTitle: string | null;
  memoryCommentId: string | null;
};

function normalizeText(value: string): string {
  return value
    .toLocaleLowerCase("ru-RU")
    .replace(/[«»“”]/g, '"')
    .replace(/[‐‑‒–—]/g, "-")
    .replace(/\s+/g, " ")
    .trim();
}

function commentReturnsStandardMemory(
  comment: TeamTaskComment,
  moduleTitle: string,
): boolean {
  const body = normalizeText(comment.body);
  const title = normalizeText(moduleTitle);
  if (!body || !title) return false;

  const exactNeedle = normalizeText(`Итог смены по стандарту "${moduleTitle}"`);
  return (
    body.includes(exactNeedle) ||
    (body.includes("итог смены") &&
      body.includes("стандарт") &&
      body.includes(title))
  );
}

function timestamp(value: string): number {
  const parsed = new Date(value).getTime();
  return Number.isNaN(parsed) ? 0 : parsed;
}

export function buildTeamLearningAdoptionSignal(input: {
  summary: TeamLearningMemberSummary;
  progress: TeamLearningProgress[];
  comments: TeamTaskComment[];
}): TeamLearningAdoptionSignal {
  const itemById = new Map(input.summary.items.map((item) => [item.id, item]));
  const latestPassed = input.progress
    .filter((item) => {
      const learningItem = itemById.get(item.moduleId);
      if (!learningItem) return false;
      if (item.venueId !== input.summary.member.venueId) return false;
      if (item.membershipId !== input.summary.member.id) return false;
      return item.passed || item.bestPercentage >= learningItem.passPercentage;
    })
    .sort((left, right) => timestamp(right.completedAt) - timestamp(left.completedAt))[0];

  if (!latestPassed) {
    const nextTitle = input.summary.nextItem?.title ?? "обязательный стандарт";
    return {
      status: "not_ready",
      label: "Сначала обучение",
      detail: `После "${nextTitle}" нужен короткий итог смены.`,
      moduleId: input.summary.nextItem?.id ?? null,
      moduleTitle: input.summary.nextItem?.title ?? null,
      memoryCommentId: null,
    };
  }

  const moduleTitle = itemById.get(latestPassed.moduleId)?.title ?? latestPassed.moduleId;
  const memoryComment = input.comments
    .filter(
      (comment) =>
        comment.venueId === input.summary.member.venueId &&
        isLikelySameTeamMemberName(
          comment.authorName,
          input.summary.member.name,
        ) &&
        commentReturnsStandardMemory(comment, moduleTitle),
    )
    .at(-1);

  if (memoryComment) {
    return {
      status: "returned_memory",
      label: "Внедрение видно",
      detail: `"${moduleTitle}" вернулся в память смены.`,
      moduleId: latestPassed.moduleId,
      moduleTitle,
      memoryCommentId: memoryComment.id,
    };
  }

  return {
    status: "needs_memory",
    label: "Нужен факт смены",
    detail: `"${moduleTitle}" сдан, но еще не подтвержден итогом смены.`,
    moduleId: latestPassed.moduleId,
    moduleTitle,
    memoryCommentId: null,
  };
}
