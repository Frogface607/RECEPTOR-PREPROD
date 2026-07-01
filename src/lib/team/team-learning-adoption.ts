import type { TeamTask, TeamTaskComment } from "./team-os";
import type {
  TeamLearningMemberSummary,
  TeamLearningProgress,
} from "./team-learning-progress";
import { buildTeamLearningShiftCard } from "./team-learning-shift-card";
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
  evidenceLabel: string | null;
  evidenceHref: string | null;
};

export type TeamLearningAdoptionTaskDraft = {
  title: string;
  priority: "high" | "medium";
  audienceType: "member";
  audienceMemberId: string;
  memberName: string;
  moduleId: string | null;
  moduleTitle: string;
  checklistTitle: string;
  practiceAction: string;
  memoryPrompt: string;
  contextNote: string;
  dueLabel: string;
};

export type TeamLearningAdoptionNextMoveAction =
  | "assign_fact"
  | "open_evidence"
  | "none";

export type TeamLearningAdoptionNextMove = {
  label: string;
  detail: string;
  action: TeamLearningAdoptionNextMoveAction;
  actionLabel: string | null;
};

const OPEN_TASK_STATUSES = new Set<TeamTask["status"]>([
  "new",
  "accepted",
  "in_progress",
]);

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
      evidenceLabel: null,
      evidenceHref: null,
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
      label: "Стандарт доказан сменой",
      detail: `"${moduleTitle}" вернулся фактом из смены. Теперь видно, где стандарт сработал в реальной работе, а не только в тесте.`,
      moduleId: latestPassed.moduleId,
      moduleTitle,
      memoryCommentId: memoryComment.id,
      evidenceLabel: "Открыть память смены",
      evidenceHref: "#shift-summary",
    };
  }

  return {
    status: "needs_memory",
    label: "Стандарт сдан — нужен факт",
    detail: `"${moduleTitle}" сдан. Чтобы Receptor считал стандарт внедренным, нужен итог смены: где применили, что изменилось и что проверить утром.`,
    moduleId: latestPassed.moduleId,
    moduleTitle,
    memoryCommentId: null,
    evidenceLabel: null,
    evidenceHref: null,
  };
}

export function buildTeamLearningAdoptionNextMove(input: {
  signal?: TeamLearningAdoptionSignal | null;
  taskExists?: boolean;
}): TeamLearningAdoptionNextMove | null {
  const signal = input.signal ?? null;
  if (!signal) return null;

  const title = signal.moduleTitle ?? "стандарт";

  if (signal.status === "returned_memory") {
    return {
      label: "Доказан сменой",
      detail: `${title}: есть факт из смены, можно открыть доказательство.`,
      action: signal.evidenceHref ? "open_evidence" : "none",
      actionLabel: signal.evidenceHref ? "Открыть факт" : null,
    };
  }

  if (signal.status === "needs_memory") {
    if (input.taskExists) {
      return {
        label: "Факт назначен",
        detail: `${title}: ждем итог смены от сотрудника.`,
        action: "none",
        actionLabel: null,
      };
    }

    return {
      label: "Нужен факт",
      detail: `${title}: назначьте один итог смены после практики.`,
      action: "assign_fact",
      actionLabel: "Назначить факт",
    };
  }

  return {
    label: "Сначала стандарт",
    detail: `${title}: после проверки попросите факт смены.`,
    action: "none",
    actionLabel: null,
  };
}

function normalizeTaskTitle(value: string): string {
  return value.trim().replace(/\s+/g, " ").toLocaleLowerCase("ru-RU");
}

export function buildTeamLearningAdoptionTaskDraft(
  summary: TeamLearningMemberSummary,
  signal: TeamLearningAdoptionSignal,
): TeamLearningAdoptionTaskDraft | null {
  if (signal.status !== "needs_memory") return null;

  const item = summary.items.find(
    (candidate) => candidate.id === signal.moduleId,
  );
  const moduleTitle = signal.moduleTitle ?? item?.title ?? "стандарт";
  const checklistTitle = "Если стандарт сдан, но нет факта смены";
  const shiftCard = item
    ? buildTeamLearningShiftCard(item, checklistTitle)
    : {
        action:
          "На смене применить сданный стандарт в одной реальной ситуации.",
        fieldNote:
          "После смены оставить факт: что применил, где помогло, что мешало и что проверить утром.",
      };
  const contextNote = [
    `Проверка: ${summary.member.name} сдал(а) стандарт "${moduleTitle}", но в памяти смены нет факта применения.`,
    `В смене: ${shiftCard.action}`,
    `В память: ${shiftCard.fieldNote}`,
    "Зачем: обучение становится операционной ценностью только когда стандарт возвращается живым фактом с поля.",
    `Стандарт: ${moduleTitle}.`,
    `Чеклист: ${checklistTitle}.`,
  ].join("\n");

  return {
    title: `Вернуть факт смены: ${summary.member.name} — ${moduleTitle}`,
    priority: summary.canWorkShift ? "medium" : "high",
    audienceType: "member",
    audienceMemberId: summary.member.id,
    memberName: summary.member.name,
    moduleId: signal.moduleId,
    moduleTitle,
    checklistTitle,
    practiceAction: shiftCard.action,
    memoryPrompt: shiftCard.fieldNote,
    contextNote,
    dueLabel: "после ближайшей смены",
  };
}

export function findOpenLearningAdoptionTask(
  tasks: TeamTask[],
  draft: TeamLearningAdoptionTaskDraft,
): TeamTask | null {
  const draftTitle = normalizeTaskTitle(draft.title);

  return (
    tasks.find(
      (task) =>
        OPEN_TASK_STATUSES.has(task.status) &&
        task.audience.type === "member" &&
        task.audience.memberId === draft.audienceMemberId &&
        normalizeTaskTitle(task.title) === draftTitle,
    ) ?? null
  );
}
