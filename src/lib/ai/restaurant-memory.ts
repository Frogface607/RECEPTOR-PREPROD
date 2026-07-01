import { buildTeamFieldContextDigest } from "@/lib/team/team-field-context";
import { summarizeFieldNoteReadiness } from "@/lib/team/field-note-input";
import {
  buildRestaurantMemoryGraphModel,
  explainRestaurantMemoryGraph,
  formatRestaurantMemoryGraph,
  summarizeRestaurantMemoryGraph,
  type RestaurantMemoryGraphBrief,
} from "@/lib/ai/restaurant-memory-graph";
import { buildTeamLearningSummaries } from "@/lib/team/team-learning-progress";
import { buildTeamLearningAdoptionSignal } from "@/lib/team/team-learning-adoption";
import {
  getTeamRole,
  type StaffMember,
  type TeamAuditEvent,
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
  fieldMemoryTaskStatus: string | null;
  fieldMemoryFollowUpQuestions: string[];
  memberSignals: string[];
  openTasks: string[];
  learningGaps: string[];
  learningAdoptionGaps: string[];
  closedStandardFollowUps?: string[];
  memoryGraph: string[];
  memoryGraphMarkdown?: string;
  memoryGraphTrace?: string[];
  memoryGraphBrief?: RestaurantMemoryGraphBrief;
};

type RestaurantMemoryInput = {
  staff: StaffMember[];
  tasks: TeamTask[];
  comments: TeamTaskComment[];
  auditEvents?: TeamAuditEvent[];
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

function taskStatusLabel(status: TeamTask["status"]): string {
  if (status === "new") return "новая";
  if (status === "accepted") return "принята";
  if (status === "in_progress") return "в работе";
  return "ожидает проверки";
}

function fieldMemoryTaskStatus(tasks: TeamTask[]): string | null {
  const task = tasks.find(
    (item) =>
      OPEN_TASK_STATUSES.has(item.status) &&
      item.sourceLabel === "Память смены" &&
      item.learningChecklistTitle === "Если итог смены неполный",
  );

  if (!task) return null;

  return `${task.title} (${taskStatusLabel(task.status)}${task.dueLabel ? `, ${task.dueLabel}` : ""})`;
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

function learningAdoptionGapLines(input: RestaurantMemoryInput): string[] {
  return buildTeamLearningSummaries(
    input.staff,
    input.learningProgress,
    input.learningStandards,
  )
    .map((summary) => ({
      summary,
      signal: buildTeamLearningAdoptionSignal({
        summary,
        progress: input.learningProgress,
        comments: input.comments,
      }),
    }))
    .filter(({ signal }) => signal.status === "needs_memory")
    .slice(0, 4)
    .map(({ summary, signal }) => {
      const title = signal.moduleTitle ?? "стандарт";
      return `${summary.member.name}: ${title} сдан, нужен факт смены после практики`;
    });
}

function extractClosedStandardTitle(summary: string): string | null {
  const patterns = [
    /задач[аи]\s+стандарта\s+после\s+сдачи:\s*(.+?)(?:\.|$)/iu,
    /задач[аи]\s+обучения\s+после\s+сдачи\s+модуля:\s*(.+?)(?:\.|$)/iu,
  ];

  for (const pattern of patterns) {
    const title = summary.match(pattern)?.[1]?.trim();
    if (title) return title;
  }

  return null;
}

function taskAudienceMemberName(
  task: TeamTask | undefined,
  staff: StaffMember[],
): string | null {
  if (!task || task.audience.type !== "member") return null;
  const memberId = task.audience.memberId;
  return (
    staff.find((member) => member.id === memberId)?.name ?? null
  );
}

function closedStandardFollowUpLines(input: RestaurantMemoryInput): string[] {
  const tasksById = new Map(input.tasks.map((task) => [task.id, task]));

  return (input.auditEvents ?? [])
    .filter(
      (event) =>
        event.type === "task_status_updated" && event.targetType === "task",
    )
    .map((event) => {
      const title = extractClosedStandardTitle(event.summary);
      if (!title) return null;

      const memberName = taskAudienceMemberName(
        event.targetId ? tasksById.get(event.targetId) : undefined,
        input.staff,
      );
      const owner = memberName ? `${memberName}: ` : "";

      return `${owner}${title} закрыт; после смены нужен факт: где применили стандарт, что изменилось и что проверить утром`;
    })
    .filter((line): line is string => Boolean(line))
    .slice(0, 3);
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
  const fieldTaskStatus = fieldMemoryTaskStatus(input.tasks);
  const fieldMemoryFollowUpQuestions =
    fieldReadiness.complete === 0 && !fieldTaskStatus
      ? fieldReadiness.followUpQuestions
      : [];
  const memoryGraphModel = buildRestaurantMemoryGraphModel({
    staff: input.staff,
    tasks: input.tasks,
    comments: input.comments,
  });
  const memoryGraph = formatRestaurantMemoryGraph(memoryGraphModel.relations);
  const memoryGraphTrace = explainRestaurantMemoryGraph(
    memoryGraphModel.relations,
  );
  const memoryGraphBrief = summarizeRestaurantMemoryGraph(
    memoryGraphModel.relations,
  );

  return {
    teamSummary: roleSummary(input.staff),
    fieldSummary: fieldContext?.summary ?? null,
    fieldSignals:
      fieldContext?.signals.map(
        (signal) =>
          `${signal.title}: ${signal.detail} (${signal.sourceCount})`,
      ) ?? [],
    fieldMemoryQuality,
    fieldMemoryTaskStatus: fieldTaskStatus,
    fieldMemoryFollowUpQuestions,
    memberSignals: memberMemoryLines(input),
    openTasks: openTaskLines(input.tasks),
    learningGaps: learningGapLines(input),
    learningAdoptionGaps: learningAdoptionGapLines(input),
    closedStandardFollowUps: closedStandardFollowUpLines(input),
    memoryGraph,
    memoryGraphMarkdown:
      memoryGraphModel.edges.length > 0 ? memoryGraphModel.markdownSnapshot : undefined,
    memoryGraphTrace,
    memoryGraphBrief,
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

  if (memory.fieldMemoryTaskStatus) {
    lines.push(`Добор памяти смены уже поставлен: ${memory.fieldMemoryTaskStatus}.`);
  }

  if (!memory.fieldMemoryTaskStatus && memory.fieldMemoryFollowUpQuestions.length > 0) {
    lines.push(
      `Вопросы для добора памяти смены: ${memory.fieldMemoryFollowUpQuestions.join("; ")}.`,
    );
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

  if (memory.learningAdoptionGaps.length > 0) {
    lines.push(
      `Стандарты без факта смены: ${memory.learningAdoptionGaps.join("; ")}`,
    );
  }

  if (memory.closedStandardFollowUps?.length) {
    lines.push(
      `Закрытые стандарты ждут факта смены: ${memory.closedStandardFollowUps.join("; ")}`,
    );
  }

  if (memory.memoryGraph.length > 0) {
    lines.push(`Связи памяти: ${memory.memoryGraph.join("; ")}`);
  }

  if (memory.memoryGraphBrief) {
    lines.push(
      `Карта памяти: ${memory.memoryGraphBrief.summary}. Следующее: ${memory.memoryGraphBrief.nextAction}.`,
    );
  }

  if (memory.memoryGraphTrace && memory.memoryGraphTrace.length > 0) {
    lines.push(`Почему так думаю: ${memory.memoryGraphTrace.join(" ")}`);
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
    memory.fieldMemoryTaskStatus
      ? `• Добор памяти уже в работе: ${memory.fieldMemoryTaskStatus}.`
      : null,
    memory.memoryGraphBrief
      ? `• Карта памяти: ${memory.memoryGraphBrief.summary}. Следующее: ${memory.memoryGraphBrief.nextAction}.`
      : null,
    memory.memoryGraphTrace?.[0]
      ? `• Почему так думаю: ${memory.memoryGraphTrace.slice(0, 3).join(" ")}`
      : null,
    !memory.fieldMemoryTaskStatus && memory.fieldMemoryFollowUpQuestions[0]
      ? `• Следующий вопрос для брифа: ${memory.fieldMemoryFollowUpQuestions[0]}`
      : null,
    memory.learningAdoptionGaps[0]
      ? `• Стандарт нужно проверить в смене: ${memory.learningAdoptionGaps[0]}.`
      : null,
    memory.closedStandardFollowUps?.[0]
      ? `• Закрытый стандарт ждет факт смены: ${memory.closedStandardFollowUps[0]}.`
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
