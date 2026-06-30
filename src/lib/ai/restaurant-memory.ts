import { buildTeamFieldContextDigest } from "@/lib/team/team-field-context";
import { summarizeFieldNoteReadiness } from "@/lib/team/field-note-input";
import { buildTeamLearningSummaries } from "@/lib/team/team-learning-progress";
import {
  getTeamRole,
  type StaffMember,
  type TeamTask,
  type TeamTaskComment,
} from "@/lib/team/team-os";
import { isLikelySameTeamMemberName } from "@/lib/team/team-member-match";
import type { TeamLearningProgress } from "@/lib/team/team-learning-progress";
import type { TeamLearningStandardOverride } from "@/lib/team/team-learning-standards";

export type RestaurantAdvisorMemory = {
  teamSummary: string;
  fieldSummary: string | null;
  fieldSignals: string[];
  fieldMemoryQuality: string | null;
  memberSignals: string[];
  openTasks: string[];
  learningGaps: string[];
};

type RestaurantMemoryInput = {
  staff: StaffMember[];
  tasks: TeamTask[];
  comments: TeamTaskComment[];
  learningProgress: TeamLearningProgress[];
  learningStandards: TeamLearningStandardOverride[];
};

const OPEN_TASK_STATUSES = new Set<TeamTask["status"]>([
  "new",
  "accepted",
  "in_progress",
]);

function roleSummary(staff: StaffMember[]): string {
  const active = staff.filter((member) => member.status !== "paused");
  if (active.length === 0) return "команда пока не заведена";

  const counts = new Map<string, number>();
  for (const member of active) {
    const role = getTeamRole(member.roleId).title;
    counts.set(role, (counts.get(role) ?? 0) + 1);
  }

  const roles = Array.from(counts.entries())
    .map(([role, count]) => `${role}: ${count}`)
    .join(", ");
  return `${active.length} активных сотрудников (${roles})`;
}

function taskPriorityScore(task: TeamTask): number {
  if (task.priority === "high") return 3;
  if (task.priority === "medium") return 2;
  return 1;
}

function openTaskLines(tasks: TeamTask[]): string[] {
  return tasks
    .filter((task) => OPEN_TASK_STATUSES.has(task.status))
    .sort((left, right) => taskPriorityScore(right) - taskPriorityScore(left))
    .slice(0, 4)
    .map((task) =>
      [
        task.title,
        task.impactLabel ? `(${task.impactLabel})` : "",
        task.dueLabel ? `— ${task.dueLabel}` : "",
      ]
        .filter(Boolean)
        .join(" "),
    );
}

function learningGapLines(input: RestaurantMemoryInput): string[] {
  return buildTeamLearningSummaries(
    input.staff,
    input.learningProgress,
    input.learningStandards,
  )
    .filter((summary) => summary.admissionStatus !== "admitted")
    .slice(0, 4)
    .map((summary) => {
      const next = summary.nextItem?.title ?? "базовый допуск";
      return `${summary.member.name}: ${next}`;
    });
}

function memberMemoryLines(input: RestaurantMemoryInput): string[] {
  const learningByMemberId = new Map(
    buildTeamLearningSummaries(
      input.staff,
      input.learningProgress,
      input.learningStandards,
    ).map((summary) => [summary.member.id, summary]),
  );

  return input.staff
    .filter((member) => member.status !== "paused")
    .flatMap((member) => {
      const role = getTeamRole(member.roleId).title;
      const notes = input.comments.filter((comment) =>
        isLikelySameTeamMemberName(comment.authorName, member.name),
      );
      const readiness = summarizeFieldNoteReadiness(
        notes.map((note) => note.body),
      );
      const learning = learningByMemberId.get(member.id);
      const parts: string[] = [];

      if (learning && !learning.canWorkShift) {
        parts.push(
          `обучение: ${learning.nextItem?.title ?? "базовый допуск"}`,
        );
      }

      if (readiness.total === 0) {
        parts.push("нет итога смены");
      } else if (readiness.complete === 0) {
        parts.push(
          `итог неполный: не хватает ${readiness.bestMissing.join(", ")}`,
        );
      } else {
        parts.push(`итоги смены: ${readiness.complete}/${readiness.total}`);
      }

      return parts.length > 0 ? [`${member.name} (${role}): ${parts.join(", ")}`] : [];
    })
    .slice(0, 6);
}

export function buildRestaurantAdvisorMemory(
  input: RestaurantMemoryInput,
): RestaurantAdvisorMemory {
  const fieldContext = buildTeamFieldContextDigest({
    comments: input.comments,
    tasks: input.tasks,
  });
  const fieldReadiness = summarizeFieldNoteReadiness(
    input.comments.map((comment) => comment.body),
  );
  const fieldMemoryQuality =
    fieldReadiness.total === 0
      ? null
      : fieldReadiness.complete > 0
        ? `полных итогов смены: ${fieldReadiness.complete}/${fieldReadiness.total}`
        : `память смены неполная: не хватает ${fieldReadiness.bestMissing.join(", ")}`;

  return {
    teamSummary: roleSummary(input.staff),
    fieldSummary: fieldContext?.summary ?? null,
    fieldSignals:
      fieldContext?.signals.map(
        (signal) =>
          `${signal.title}: ${signal.detail} (${signal.sourceCount})`,
      ) ?? [],
    fieldMemoryQuality,
    memberSignals: memberMemoryLines(input),
    openTasks: openTaskLines(input.tasks),
    learningGaps: learningGapLines(input),
  };
}

export function formatRestaurantAdvisorMemoryForPrompt(
  memory: RestaurantAdvisorMemory | undefined,
): string {
  if (!memory) {
    return [
      "Память ресторана:",
      "Команда, итоги смены и обучение пока не загружены в контекст советника.",
    ].join("\n");
  }

  const lines = [
    "Память ресторана:",
    `Команда: ${memory.teamSummary}.`,
    memory.fieldSummary
      ? `Память смены: ${memory.fieldSummary}`
      : "Память смены: нет свежих заметок с поля.",
  ];

  if (memory.fieldSignals.length > 0) {
    lines.push(`Сигналы с поля: ${memory.fieldSignals.join("; ")}`);
  }

  if (memory.fieldMemoryQuality) {
    lines.push(`Качество памяти смены: ${memory.fieldMemoryQuality}.`);
  }

  if (memory.memberSignals.length > 0) {
    lines.push(`Люди и допуск: ${memory.memberSignals.join("; ")}`);
  }

  if (memory.openTasks.length > 0) {
    lines.push(`Открытые действия: ${memory.openTasks.join("; ")}`);
  }

  if (memory.learningGaps.length > 0) {
    lines.push(`Учебные пробелы: ${memory.learningGaps.join("; ")}`);
  }

  return lines.join("\n");
}

export function formatRestaurantAdvisorMemoryForAnswer(
  memory: RestaurantAdvisorMemory | undefined,
): string {
  if (!memory) {
    return [
      "Что уже знаю:",
      "• Команда и итоги смены пока не попали в память советника.",
      "• Чтобы советы стали точнее, попросите управляющего оставить итог смены.",
    ].join("\n");
  }

  return [
    "Что уже знаю:",
    `• Команда: ${memory.teamSummary}.`,
    memory.fieldSummary
      ? `• Последняя память смены: ${memory.fieldSummary}`
      : "• Память смены пока пустая.",
    memory.fieldMemoryQuality?.includes("неполная")
      ? `• Память смены неполная: ${memory.fieldMemoryQuality.replace(
          /^память смены неполная:\s*/i,
          "",
        )}.`
      : null,
    memory.learningGaps[0]
      ? `• Первый учебный пробел: ${memory.learningGaps[0]}.`
      : memory.openTasks[0]
        ? `• Первое открытое действие: ${memory.openTasks[0]}.`
        : "• Критичных учебных пробелов сейчас не видно.",
  ]
    .filter((line): line is string => Boolean(line))
    .join("\n");
}
