import type { OwnerReviewTone } from "@/lib/owner-review";
import { summarizeFieldNoteReadiness } from "@/lib/team/field-note-input";
import { buildTeamFieldContextDigest } from "@/lib/team/team-field-context";
import type { TeamLearningMemberSummary } from "@/lib/team/team-learning-progress";
import { summarizeTeamLearning } from "@/lib/team/team-learning-progress";
import type { StaffMember, TeamTask, TeamTaskComment } from "@/lib/team/team-os";
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

export type OwnerBrainReadiness = {
  score: number;
  tone: OwnerReviewTone;
  title: string;
  summary: string;
  nextSource: OwnerBrainSource;
  sources: OwnerBrainSource[];
};

type BuildOwnerBrainReadinessInput = {
  context: unknown;
  staff: StaffMember[];
  tasks: TeamTask[];
  comments: TeamTaskComment[];
  learningSummaries: TeamLearningMemberSummary[];
  dataMode: "live" | "mock";
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
  return "советник пока слепой";
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

function fieldSource({
  comments,
  tasks,
}: {
  comments: TeamTaskComment[];
  tasks: TeamTask[];
}): OwnerBrainSource {
  const digest = buildTeamFieldContextDigest({ comments, tasks });
  const noteReadiness = summarizeFieldNoteReadiness(
    comments.map((comment) => comment.body),
  );
  const status: OwnerBrainSourceStatus = !digest
    ? "missing"
    : noteReadiness.complete > 0
      ? "ready"
      : "work";

  return {
    id: "field",
    label: "Смена",
    status,
    value: digest ? `${noteReadiness.complete}/${noteReadiness.total}` : "0",
    detail: digest
      ? noteReadiness.complete > 0
        ? `Есть полный итог смены. ${digest.summary}`
        : `Заметка есть, но не хватает: ${noteReadiness.bestMissing.join(", ")}. ${digest.summary}`
      : "После смены нужен короткий итог: гости, событие, стоп-лист, конфликт, погода, что мешало продавать.",
    actionLabel: digest ? "Дополнить" : "Оставить итог",
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

export function buildOwnerBrainReadiness(
  input: BuildOwnerBrainReadinessInput,
): OwnerBrainReadiness {
  const sources: OwnerBrainSource[] = [
    contextSource(input.context),
    teamSource(input.staff),
    fieldSource({ comments: input.comments, tasks: input.tasks }),
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

  return {
    score,
    tone,
    title: statusTitle(tone),
    summary:
      tone === "good"
        ? "Можно спрашивать советника о причинах, людях, меню и действиях на день."
        : tone === "watch"
          ? "Дособерите следующий источник памяти, чтобы советы опирались не только на цифры."
          : "Сначала докормите систему живым контекстом: профиль, команда, итог смены и допуск.",
    nextSource,
    sources,
  };
}
