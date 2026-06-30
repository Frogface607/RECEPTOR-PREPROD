import type { OwnerReviewTone } from "@/lib/owner-review";
import { summarizeFieldNoteReadiness } from "@/lib/team/field-note-input";
import { buildTeamFieldContextDigest } from "@/lib/team/team-field-context";
import type { TeamLearningMemberSummary } from "@/lib/team/team-learning-progress";
import { summarizeTeamLearning } from "@/lib/team/team-learning-progress";
import {
  isShiftMemoryFollowUpTask,
  type StaffMember,
  type TeamTask,
  type TeamTaskComment,
} from "@/lib/team/team-os";
import { buildContextMemoryReadiness } from "@/lib/venues/context-questionnaire";

export type OwnerBrainSourceId =
  | "context"
  | "team"
  | "field"
  | "learning"
  | "iiko";

export type OwnerBrainSourceStatus = "ready" | "work" | "missing";

export type OwnerBrainSource = {
  id: OwnerBrainSourceId;
  label: string;
  status: OwnerBrainSourceStatus;
  value: string;
  detail: string;
  actionLabel: string;
};

export type OwnerBrainMemorySnapshotId = "known" | "missing" | "next";

export type OwnerBrainMemorySnapshot = {
  id: OwnerBrainMemorySnapshotId;
  label: string;
  value: string;
  detail: string;
  tone: OwnerReviewTone;
  sourceId?: OwnerBrainSourceId;
};

export type OwnerBrainFieldMemory = {
  status: OwnerBrainSourceStatus;
  title: string;
  value: string;
  detail: string;
  actionLabel: string;
  nextQuestion: string | null;
  followUpQuestions: string[];
  followUpTask: OwnerBrainFieldMemoryTask | null;
  answerSource: OwnerBrainFieldMemoryTask | null;
};

export type OwnerBrainFieldMemoryTask = {
  title: string;
  statusLabel: string;
  dueLabel: string;
  done: boolean;
  verified: boolean;
};

export type OwnerBrainReadiness = {
  score: number;
  tone: OwnerReviewTone;
  title: string;
  summary: string;
  nextSource: OwnerBrainSource;
  sources: OwnerBrainSource[];
  snapshot: OwnerBrainMemorySnapshot[];
  fieldMemory: OwnerBrainFieldMemory;
};

type BuildOwnerBrainReadinessInput = {
  context: unknown;
  staff: StaffMember[];
  tasks: TeamTask[];
  comments: TeamTaskComment[];
  learningSummaries: TeamLearningMemberSummary[];
  dataMode: "live" | "mock";
};

type FieldOwnerBrainSource = OwnerBrainSource & {
  followUpQuestions: string[];
  followUpTask: OwnerBrainFieldMemoryTask | null;
  answerTask: OwnerBrainFieldMemoryTask | null;
};

function sourceWeight(status: OwnerBrainSourceStatus): number {
  if (status === "ready") return 1;
  if (status === "work") return 0.5;
  return 0;
}

function scoreTone(score: number): OwnerReviewTone {
  if (score >= 90) return "good";
  if (score >= 50) return "watch";
  return "risk";
}

function statusTitle(tone: OwnerReviewTone): string {
  if (tone === "good") return "советник видит ресторан";
  if (tone === "watch") return "память почти собрана";
  return "советнику не хватает памяти";
}

function contextSource(context: unknown): OwnerBrainSource {
  const readiness = buildContextMemoryReadiness(context);
  const status: OwnerBrainSourceStatus =
    readiness.status === "strong"
      ? "ready"
      : readiness.status === "usable"
        ? "work"
        : "missing";

  return {
    id: "context",
    label: "Профиль",
    status,
    value: `${readiness.percentage}%`,
    detail: readiness.nextQuestion
      ? `Следующий ответ: ${readiness.nextQuestion.label}.`
      : "Формат, цели, боли и правила смены уже описаны.",
    actionLabel: readiness.nextQuestion ? "Заполнить" : "Открыть",
  };
}

function teamSource(staff: StaffMember[]): OwnerBrainSource {
  const active = staff.filter((member) => member.status !== "paused");
  const status: OwnerBrainSourceStatus =
    active.length >= 2 ? "ready" : active.length === 1 ? "work" : "missing";

  return {
    id: "team",
    label: "Люди",
    status,
    value: `${active.length}`,
    detail:
      active.length === 0
        ? "Заведите хотя бы управляющего и ключевые роли, чтобы задачи попадали людям."
        : active.length === 1
          ? "Есть первый сотрудник. Добавьте роли зала, кухни или управления."
          : "Команда заведена, можно связывать роли, задачи и обучение.",
    actionLabel: active.length === 0 ? "Добавить" : "Открыть",
  };
}

function isOpenTask(task: TeamTask): boolean {
  return task.status !== "done" && task.status !== "verified";
}

function taskStatusLabel(status: TeamTask["status"]): string {
  if (status === "new") return "новая";
  if (status === "accepted") return "принята";
  if (status === "in_progress") return "в работе";
  if (status === "done") return "сделана";
  return "проверена";
}

function fieldMemoryTaskFromTask(task: TeamTask): OwnerBrainFieldMemoryTask {
  return {
    title: task.title,
    statusLabel: taskStatusLabel(task.status),
    dueLabel: task.dueLabel,
    done: task.status === "done" || task.status === "verified",
    verified: task.status === "verified",
  };
}

function fieldFollowUpTask(tasks: TeamTask[]): OwnerBrainFieldMemoryTask | null {
  const task = tasks.find(
    (item) =>
      isOpenTask(item) &&
      isShiftMemoryFollowUpTask(item),
  );

  if (!task) return null;

  return fieldMemoryTaskFromTask(task);
}

function isCompleteShiftMemoryAnswer(comment: TeamTaskComment): boolean {
  if (!comment.body.trim().toLowerCase().startsWith("итог смены:")) {
    return false;
  }

  return summarizeFieldNoteReadiness([comment.body]).complete > 0;
}

function fieldAnswerTask({
  comments,
  tasks,
}: {
  comments: TeamTaskComment[];
  tasks: TeamTask[];
}): OwnerBrainFieldMemoryTask | null {
  const shiftMemoryTasks = tasks.filter(isShiftMemoryFollowUpTask);
  const answeredTasks = shiftMemoryTasks.filter((task) =>
    comments.some(
      (comment) =>
        comment.taskId === task.id && isCompleteShiftMemoryAnswer(comment),
    ),
  );

  const task =
    answeredTasks.find((item) => item.status === "verified") ??
    answeredTasks.find((item) => item.status === "done") ??
    answeredTasks.find((item) => !isOpenTask(item)) ??
    answeredTasks.find(isOpenTask) ??
    null;

  return task ? fieldMemoryTaskFromTask(task) : null;
}

function fieldSource({
  comments,
  tasks,
}: {
  comments: TeamTaskComment[];
  tasks: TeamTask[];
}): FieldOwnerBrainSource {
  const digest = buildTeamFieldContextDigest({ comments, tasks });
  const noteReadiness = summarizeFieldNoteReadiness(
    comments.map((comment) => comment.body),
  );
  const followUpTask = fieldFollowUpTask(tasks);
  const answerTask = fieldAnswerTask({ comments, tasks });
  const status: OwnerBrainSourceStatus = !digest
    ? "missing"
    : noteReadiness.complete > 0
      ? "ready"
      : "work";
  const actionLabel = answerTask && !answerTask.done
    ? "Открыть задачу"
    : followUpTask
    ? "Открыть задачу"
    : !digest || noteReadiness.complete === 0
      ? "Поставить задачу"
      : "Открыть";

  return {
    id: "field",
    label: "Смена",
    status,
    value: digest ? `${noteReadiness.complete}/${noteReadiness.total}` : "0",
    detail: digest
      ? noteReadiness.complete > 0
        ? answerTask
          ? `Ответ по задаче получен. ${digest.summary}`
          : `Есть полный итог смены. ${digest.summary}`
        : `Заметка есть, но не хватает: ${noteReadiness.bestMissing.join(", ")}. ${digest.summary}`
      : "После смены нужен короткий итог: гости, событие, стоп-лист, конфликт, погода, что мешало продавать.",
    actionLabel,
    followUpQuestions: noteReadiness.followUpQuestions,
    followUpTask,
    answerTask,
  };
}

function fieldMemoryFromSource(
  source: FieldOwnerBrainSource,
): OwnerBrainFieldMemory {
  if (source.status === "ready") {
    return {
      status: source.status,
      title: "Последний итог смены",
      value: source.value,
      detail: source.detail,
      actionLabel: source.actionLabel,
      nextQuestion: null,
      followUpQuestions: [],
      followUpTask: null,
      answerSource: source.answerTask,
    };
  }

  if (source.status === "work") {
    return {
      status: source.status,
      title: "Итог смены нужно уточнить",
      value: source.value,
      detail: source.detail,
      actionLabel: source.actionLabel,
      nextQuestion: source.followUpTask ? null : (source.followUpQuestions[0] ?? null),
      followUpQuestions: source.followUpQuestions,
      followUpTask: source.followUpTask,
      answerSource: null,
    };
  }

  return {
    status: source.status,
    title: "Итог смены еще не собран",
    value: source.value,
    detail: source.detail,
    actionLabel: source.actionLabel,
    nextQuestion: source.followUpTask ? null : (source.followUpQuestions[0] ?? null),
    followUpQuestions: source.followUpQuestions,
    followUpTask: source.followUpTask,
    answerSource: null,
  };
}

function learningSource(
  learningSummaries: TeamLearningMemberSummary[],
): OwnerBrainSource {
  const active = learningSummaries.filter(
    (summary) => summary.member.status !== "paused",
  );
  const learning = summarizeTeamLearning(learningSummaries);
  const status: OwnerBrainSourceStatus =
    active.length === 0
      ? "missing"
      : learning.admissionPct >= 90
        ? "ready"
        : learning.admissionPct > 0
          ? "work"
          : "missing";

  return {
    id: "learning",
    label: "Допуск",
    status,
    value:
      active.length === 0
        ? "0/0"
        : `${learning.admittedMembers}/${active.length}`,
    detail:
      active.length === 0
        ? "Когда команда появится, Receptor покажет, кто допущен к смене и чему учиться."
        : learning.blockedMembers > 0
          ? `Не допущены к смене: ${learning.blockedMembers}. Сначала закрываем базовые стандарты.`
          : "Обязательное обучение закрыто, можно разбирать цифры с командой.",
    actionLabel: "Открыть обучение",
  };
}

function iikoSource(dataMode: "live" | "mock"): OwnerBrainSource {
  const live = dataMode === "live";
  return {
    id: "iiko",
    label: "Факты",
    status: live ? "ready" : "work",
    value: live ? "live" : "demo",
    detail: live
      ? "iiko дает факты для проверки гипотез: выручка, блюда, категории и смены."
      : "Можно строить контекст и обучение, но факты iiko пока тестовые или неполные.",
    actionLabel: live ? "Проверить" : "Настроить iiko",
  };
}

function sourceStatusLabel(status: OwnerBrainSourceStatus): string {
  if (status === "ready") return "готово";
  if (status === "work") return "нужно дописать";
  return "нет данных";
}

function buildMemorySnapshot({
  sources,
  nextSource,
}: {
  sources: OwnerBrainSource[];
  nextSource: OwnerBrainSource;
}): OwnerBrainMemorySnapshot[] {
  const readySources = sources.filter((source) => source.status === "ready");
  const weakSources = sources.filter((source) => source.status !== "ready");
  const firstWeak = weakSources[0] ?? null;

  const known: OwnerBrainMemorySnapshot = {
    id: "known",
    label: "Уже знает",
    value:
      readySources.length > 0
        ? readySources.map((source) => source.label).join(", ")
        : "пока ничего надежного",
    detail:
      readySources.length > 0
        ? "На эти источники советник уже может опираться в ответах."
        : "Сначала нужен профиль заведения, команда и хотя бы один итог смены.",
    tone: readySources.length > 0 ? "good" : "risk",
  };

  const missing: OwnerBrainMemorySnapshot = {
    id: "missing",
    label: "Не хватает",
    value:
      weakSources.length > 0
        ? weakSources
            .map((source) => `${source.label}: ${sourceStatusLabel(source.status)}`)
            .join(", ")
        : "критичных пробелов нет",
    detail:
      firstWeak?.detail ??
      "Базовая память собрана. Дальше можно задавать вопросы о причинах, людях, меню и действиях.",
    tone: weakSources.length > 0 ? "watch" : "good",
    sourceId: firstWeak?.id,
  };

  const next: OwnerBrainMemorySnapshot = firstWeak
    ? {
        id: "next",
        label: "Следующий сбор",
        value: `${nextSource.label}: ${nextSource.value}`,
        detail: nextSource.detail,
        tone:
          nextSource.status === "missing"
            ? "risk"
            : nextSource.status === "work"
              ? "watch"
              : "good",
        sourceId: nextSource.id,
      }
    : {
        id: "next",
        label: "Готово к вопросам",
        value: "советник в контексте",
        detail:
          "Спросите, почему просела смена, кого обучить, что проверить утром или какую гипотезу дать управляющему.",
        tone: "good",
      };

  return [known, missing, next];
}

export function buildOwnerBrainReadiness(
  input: BuildOwnerBrainReadinessInput,
): OwnerBrainReadiness {
  const field = fieldSource({ comments: input.comments, tasks: input.tasks });
  const sources: OwnerBrainSource[] = [
    contextSource(input.context),
    teamSource(input.staff),
    field,
    learningSource(input.learningSummaries),
    iikoSource(input.dataMode),
  ];
  const rawScore =
    sources.reduce((sum, source) => sum + sourceWeight(source.status), 0) /
    sources.length;
  const score = Math.round(rawScore * 100);
  const tone = scoreTone(score);
  const nextSource =
    sources.find((source) => source.status === "missing") ??
    sources.find((source) => source.status === "work") ??
    sources[0];
  const snapshot = buildMemorySnapshot({ sources, nextSource });

  return {
    score,
    tone,
    title: statusTitle(tone),
    summary:
      tone === "good"
        ? "Можно спрашивать советника о причинах, людях, меню и действиях на день."
        : tone === "watch"
          ? "Доберите следующий источник памяти, чтобы советы опирались не только на цифры."
          : "Сначала соберите живой контекст: профиль заведения, команда, итог смены и допуск.",
    nextSource,
    sources,
    snapshot,
    fieldMemory: fieldMemoryFromSource(field),
  };
}
