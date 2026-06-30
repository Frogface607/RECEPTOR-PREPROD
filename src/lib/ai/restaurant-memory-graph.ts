import { buildTeamFieldContextDigest } from "@/lib/team/team-field-context";
import {
  getTeamRole,
  type StaffMember,
  type TeamTask,
  type TeamTaskComment,
} from "@/lib/team/team-os";

export type RestaurantMemoryRelationSource = "team" | "field" | "task";

export type RestaurantMemoryRelation = {
  subject: string;
  predicate: string;
  object: string;
  source: RestaurantMemoryRelationSource;
};

type RestaurantMemoryGraphInput = {
  staff: StaffMember[];
  tasks: TeamTask[];
  comments: TeamTaskComment[];
};

const OPEN_TASK_STATUSES = new Set<TeamTask["status"]>([
  "new",
  "accepted",
  "in_progress",
]);
const SYSTEM_COMMENT_MARKERS = [
  "урок для команды:",
  "стандарт:",
  "стандарт задачи:",
  "чеклист:",
  "зачем:",
  "receptor",
];

function compact(value: string, maxLength = 150): string {
  const normalized = value.trim().replace(/\s+/g, " ");
  if (normalized.length <= maxLength) return normalized;
  return `${normalized.slice(0, maxLength - 1).trim()}…`;
}

function isSystemComment(body: string): boolean {
  const normalized = body.toLocaleLowerCase("ru-RU");
  return SYSTEM_COMMENT_MARKERS.some((marker) => normalized.includes(marker));
}

function taskLabel(task: TeamTask | undefined): string {
  return task?.sourceLabel || task?.title || "заметка";
}

function taskObject(task: TeamTask): string {
  return compact(
    [
      task.title,
      task.impactLabel ? `вес: ${task.impactLabel}` : "",
      task.dueLabel ? `срок: ${task.dueLabel}` : "",
    ]
      .filter(Boolean)
      .join("; "),
  );
}

function taskPredicate(task: TeamTask): string {
  if (task.sourceLabel === "Память смены") return "добирает контекст";
  if (task.learningChecklistTitle) return "закрывает стандарт";
  return "открытая задача";
}

function relationLine(relation: RestaurantMemoryRelation): string {
  return `${relation.subject} -> ${relation.predicate} -> ${relation.object}`;
}

export function buildRestaurantMemoryGraph(
  input: RestaurantMemoryGraphInput,
): RestaurantMemoryRelation[] {
  const tasksById = new Map(input.tasks.map((task) => [task.id, task]));
  const relations: RestaurantMemoryRelation[] = [];

  for (const member of input.staff.filter((item) => item.status !== "paused")) {
    relations.push({
      subject: member.name,
      predicate: "роль",
      object: getTeamRole(member.roleId).title,
      source: "team",
    });
  }

  for (const comment of input.comments) {
    if (!comment.body.trim() || isSystemComment(comment.body)) continue;

    const task = tasksById.get(comment.taskId);
    relations.push({
      subject: comment.authorName,
      predicate: /итог смен/i.test(comment.body)
        ? "оставил(а) итог смены"
        : "сообщил(а)",
      object: `${taskLabel(task)}: ${compact(comment.body)}`,
      source: "field",
    });
  }

  for (const task of input.tasks.filter((item) =>
    OPEN_TASK_STATUSES.has(item.status),
  )) {
    relations.push({
      subject: task.sourceLabel || "Задача",
      predicate: taskPredicate(task),
      object: taskObject(task),
      source: "task",
    });
  }

  const fieldContext = buildTeamFieldContextDigest({
    comments: input.comments,
    tasks: input.tasks,
  });
  for (const signal of fieldContext?.signals ?? []) {
    relations.push({
      subject: signal.title,
      predicate: "связано с",
      object: compact(signal.detail),
      source: "field",
    });
  }

  return relations.slice(0, 12);
}

export function formatRestaurantMemoryGraph(
  relations: RestaurantMemoryRelation[],
): string[] {
  return relations.map(relationLine);
}
