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

export type RestaurantMemoryNodeKind =
  | "person"
  | "role"
  | "shift_note"
  | "task"
  | "signal";

export type RestaurantMemoryNode = {
  id: string;
  kind: RestaurantMemoryNodeKind;
  label: string;
  source: RestaurantMemoryRelationSource;
};

export type RestaurantMemoryEdge = {
  id: string;
  from: string;
  to: string;
  predicate: string;
  source: RestaurantMemoryRelationSource;
  evidence: string;
};

export type RestaurantMemoryGraphModel = {
  relations: RestaurantMemoryRelation[];
  nodes: RestaurantMemoryNode[];
  edges: RestaurantMemoryEdge[];
  markdownSnapshot: string;
};

export type RestaurantMemoryGraphBrief = {
  relationCount: number;
  sourceLabels: string[];
  missingLabels: string[];
  status: "ready" | "work" | "missing";
  summary: string;
  nextAction: string;
};

type RestaurantMemoryGraphInput = {
  staff: StaffMember[];
  tasks: TeamTask[];
  comments: TeamTaskComment[];
};

const SOURCE_ORDER: RestaurantMemoryRelationSource[] = ["team", "field", "task"];
const SOURCE_LABELS: Record<RestaurantMemoryRelationSource, string> = {
  team: "люди",
  field: "смена",
  task: "задачи",
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

function nodeId(kind: RestaurantMemoryNodeKind, label: string): string {
  const slug = compact(label, 70)
    .toLocaleLowerCase("ru-RU")
    .replace(/[^\p{L}\p{N}]+/gu, "-")
    .replace(/^-+|-+$/g, "");

  return `${kind}:${slug || "node"}`;
}

function subjectNodeKind(
  relation: RestaurantMemoryRelation,
): RestaurantMemoryNodeKind {
  if (relation.source === "task") return "task";
  if (relation.source === "field" && relation.predicate === "связано с") {
    return "signal";
  }

  return "person";
}

function objectNodeKind(
  relation: RestaurantMemoryRelation,
): RestaurantMemoryNodeKind {
  if (relation.predicate === "роль") return "role";
  if (relation.source === "task") return "task";
  if (relation.source === "field" && relation.predicate === "связано с") {
    return "signal";
  }

  return "shift_note";
}

function ensureNode(
  nodes: Map<string, RestaurantMemoryNode>,
  kind: RestaurantMemoryNodeKind,
  label: string,
  source: RestaurantMemoryRelationSource,
): RestaurantMemoryNode {
  const id = nodeId(kind, label);
  const existing = nodes.get(id);
  if (existing) return existing;

  const node = {
    id,
    kind,
    label: compact(label),
    source,
  };
  nodes.set(id, node);
  return node;
}

function relationCountLabel(count: number): string {
  const mod10 = count % 10;
  const mod100 = count % 100;
  const word =
    mod10 === 1 && mod100 !== 11
      ? "связь"
      : mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)
        ? "связи"
        : "связей";

  return `${count} ${word}`;
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

export function formatRestaurantMemoryGraphMarkdown({
  nodes,
  edges,
}: Pick<RestaurantMemoryGraphModel, "nodes" | "edges">): string {
  const nodeLines =
    nodes.length > 0
      ? nodes.map((node) => `- ${node.id}: ${node.label}`).join("\n")
      : "- пока нет узлов";
  const edgeLines =
    edges.length > 0
      ? edges
          .map((edge) => `- ${edge.from} -> ${edge.predicate} -> ${edge.to}`)
          .join("\n")
      : "- пока нет связей";

  return [
    "# Карта памяти ресторана",
    "",
    "## Узлы",
    nodeLines,
    "",
    "## Связи",
    edgeLines,
  ].join("\n");
}

export function buildRestaurantMemoryGraphModel(
  input: RestaurantMemoryGraphInput,
): RestaurantMemoryGraphModel {
  const relations = buildRestaurantMemoryGraph(input);
  const nodes = new Map<string, RestaurantMemoryNode>();
  const edges = relations.map((relation, index) => {
    const from = ensureNode(
      nodes,
      subjectNodeKind(relation),
      relation.subject,
      relation.source,
    );
    const to = ensureNode(
      nodes,
      objectNodeKind(relation),
      relation.object,
      relation.source,
    );

    return {
      id: `edge:${index + 1}`,
      from: from.id,
      to: to.id,
      predicate: relation.predicate,
      source: relation.source,
      evidence: relationLine(relation),
    };
  });
  const model = {
    relations,
    nodes: Array.from(nodes.values()),
    edges,
    markdownSnapshot: "",
  };

  return {
    ...model,
    markdownSnapshot: formatRestaurantMemoryGraphMarkdown(model),
  };
}

export function summarizeRestaurantMemoryGraph(
  relations: RestaurantMemoryRelation[],
): RestaurantMemoryGraphBrief {
  const sources = new Set(relations.map((relation) => relation.source));
  const sourceLabels = SOURCE_ORDER.filter((source) => sources.has(source)).map(
    (source) => SOURCE_LABELS[source],
  );
  const missingLabels = SOURCE_ORDER.filter((source) => !sources.has(source)).map(
    (source) => SOURCE_LABELS[source],
  );
  const status =
    relations.length === 0
      ? "missing"
      : missingLabels.length === 0
        ? "ready"
        : "work";
  const summary =
    relations.length === 0
      ? "связей пока нет"
      : `${relationCountLabel(relations.length)}: ${sourceLabels.join(", ")}`;
  const nextAction = missingLabels.includes("люди")
    ? "добавить людей и роли"
    : missingLabels.includes("смена")
      ? "собрать итог смены"
      : missingLabels.includes("задачи")
        ? "связать память с задачей"
        : "можно спрашивать советника о причинах и действиях";

  return {
    relationCount: relations.length,
    sourceLabels,
    missingLabels,
    status,
    summary,
    nextAction,
  };
}
