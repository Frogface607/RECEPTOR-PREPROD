import { buildTeamFieldContextDigest } from "@/lib/team/team-field-context";
import { buildTeamLearningSummaries } from "@/lib/team/team-learning-progress";
import {
  getTeamRole,
  type StaffMember,
  type TeamTask,
  type TeamTaskComment,
} from "@/lib/team/team-os";
import type { TeamLearningProgress } from "@/lib/team/team-learning-progress";
import type { TeamLearningStandardOverride } from "@/lib/team/team-learning-standards";

export type RestaurantAdvisorMemory = {
  teamSummary: string;
  fieldSummary: string | null;
  fieldSignals: string[];
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

export function buildRestaurantAdvisorMemory(
  input: RestaurantMemoryInput,
): RestaurantAdvisorMemory {
  const fieldContext = buildTeamFieldContextDigest({
    comments: input.comments,
    tasks: input.tasks,
  });

  return {
    teamSummary: roleSummary(input.staff),
    fieldSummary: fieldContext?.summary ?? null,
    fieldSignals:
      fieldContext?.signals.map(
        (signal) =>
          `${signal.title}: ${signal.detail} (${signal.sourceCount})`,
      ) ?? [],
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
    memory.learningGaps[0]
      ? `• Первый учебный пробел: ${memory.learningGaps[0]}.`
      : memory.openTasks[0]
        ? `• Первое открытое действие: ${memory.openTasks[0]}.`
        : "• Критичных учебных пробелов сейчас не видно.",
  ].join("\n");
}
