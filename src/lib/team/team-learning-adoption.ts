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

export type TeamLearningAdoptionRow = {
  summary: TeamLearningMemberSummary;
  signal: TeamLearningAdoptionSignal;
  draft: TeamLearningAdoptionTaskDraft | null;
  existingTask: TeamTask | null;
  move: TeamLearningAdoptionNextMove | null;
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
      label: "Стандарт работает",
      detail: `"${moduleTitle}" уже применили в смене. Receptor запомнил живой итог и может показывать руководителю, где правило помогло в работе.`,
      moduleId: latestPassed.moduleId,
      moduleTitle,
      memoryCommentId: memoryComment.id,
      evidenceLabel: "Открыть память смены",
      evidenceHref: "#shift-summary",
    };
  }

  return {
    status: "needs_memory",
    label: "Стандарт сдан — нужен итог",
    detail: `"${moduleTitle}" сдан. Теперь сотруднику нужно один раз попробовать это в смене и коротко написать: где применил, что получилось и что проверить утром.`,
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
      label: "Стандарт работает",
      detail: `${title}: есть итог из смены, можно открыть живой пример.`,
      action: signal.evidenceHref ? "open_evidence" : "none",
      actionLabel: signal.evidenceHref ? "Открыть итог" : null,
    };
  }

  if (signal.status === "needs_memory") {
    if (input.taskExists) {
      return {
        label: "Ждем итог смены",
        detail: `${title}: ждем итог смены от сотрудника.`,
        action: "none",
        actionLabel: null,
      };
    }

    return {
      label: "Нужен короткий итог",
      detail: `${title}: попросите сотрудника попробовать стандарт в смене и оставить короткий итог.`,
      action: "assign_fact",
      actionLabel: "Попросить итог",
    };
  }

  return {
    label: "Сначала стандарт",
    detail: `${title}: после проверки попросите короткий итог смены.`,
    action: "none",
    actionLabel: null,
  };
}

export function buildTeamLearningAdoptionRows(input: {
  summaries: TeamLearningMemberSummary[];
  progress: TeamLearningProgress[];
  comments: TeamTaskComment[];
  tasks: TeamTask[];
}): TeamLearningAdoptionRow[] {
  return input.summaries.map((summary) => {
    const signal = buildTeamLearningAdoptionSignal({
      summary,
      progress: input.progress,
      comments: input.comments,
    });
    const draft = buildTeamLearningAdoptionTaskDraft(summary, signal);
    const existingTask = draft
      ? findOpenLearningAdoptionTask(input.tasks, draft)
      : null;
    const move = buildTeamLearningAdoptionNextMove({
      signal,
      taskExists: Boolean(existingTask),
    });

    return {
      summary,
      signal,
      draft,
      existingTask,
      move,
    };
  });
}

export function pickTeamLearningAdoptionFocus<
  T extends Pick<TeamLearningAdoptionRow, "signal" | "move">,
>(rows: T[]): T | null {
  return (
    rows.find((row) => row.move?.action === "assign_fact") ??
    rows.find(
      (row) =>
        row.signal.status === "needs_memory" &&
        row.move?.label === "Ждем итог смены",
    ) ??
    null
  );
}

function normalizeTaskTitle(value: string): string {
  return value.trim().replace(/\s+/g, " ").toLocaleLowerCase("ru-RU");
}

function learningAdoptionTaskTitleNeedles(
  draft: TeamLearningAdoptionTaskDraft,
): string[] {
  const titles = [
    draft.title,
    `Вернуть факт смены: ${draft.memberName} — ${draft.moduleTitle ?? "стандарт"}`,
  ];

  return Array.from(new Set(titles.map(normalizeTaskTitle)));
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
  const checklistTitle = "Если стандарт сдан, но нет итога смены";
  const shiftCard = item
    ? buildTeamLearningShiftCard(item, checklistTitle)
    : {
        action:
          "На смене применить сданный стандарт в одной реальной ситуации.",
        fieldNote:
          "После смены оставить короткий итог: что применил, где помогло, что мешало и что проверить утром.",
      };
  const contextNote = [
    `Проверка: ${summary.member.name} сдал(а) стандарт "${moduleTitle}", но еще не оставил(а) итог из реальной смены.`,
    `В смене: ${shiftCard.action}`,
    `В память: ${shiftCard.fieldNote}`,
    "Зачем: Receptor не угадывает по тесту, работает ли правило. Ему нужен короткий итог из смены.",
    `Стандарт: ${moduleTitle}.`,
    `Чеклист: ${checklistTitle}.`,
  ].join("\n");

  return {
    title: `Оставить итог смены: ${summary.member.name} — ${moduleTitle}`,
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
  const draftTitles = learningAdoptionTaskTitleNeedles(draft);

  return (
    tasks.find(
      (task) =>
        OPEN_TASK_STATUSES.has(task.status) &&
        task.audience.type === "member" &&
        task.audience.memberId === draft.audienceMemberId &&
        draftTitles.includes(normalizeTaskTitle(task.title)),
    ) ?? null
  );
}
