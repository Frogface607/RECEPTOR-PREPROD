import type { TeamAuditEvent, TeamAuditEventType } from "./team-os";

export type TeamAuditJournalCategoryId =
  "all" | "labor" | "learning" | "plan" | "tasks" | "access";

export type TeamAuditJournalCategory = {
  id: TeamAuditJournalCategoryId;
  label: string;
  description: string;
};

export type TeamAuditJournalEntry = TeamAuditEvent & {
  categoryId: Exclude<TeamAuditJournalCategoryId, "all">;
  categoryLabel: string;
  typeLabel: string;
  contextHref: string;
  contextLabel: string;
};

export type TeamAuditJournalSummary = {
  categories: Array<TeamAuditJournalCategory & { count: number }>;
  entries: TeamAuditJournalEntry[];
};

export const TEAM_AUDIT_JOURNAL_CATEGORIES: TeamAuditJournalCategory[] = [
  {
    id: "all",
    label: "Все",
    description: "Вся операционная лента",
  },
  {
    id: "labor",
    label: "ФОТ",
    description: "Ставки и экономика команды",
  },
  {
    id: "learning",
    label: "Обучение",
    description: "Допуск и стандарты ролей",
  },
  {
    id: "plan",
    label: "План",
    description: "График, план/факт и смены",
  },
  {
    id: "tasks",
    label: "Задачи",
    description: "Постановка, статусы и комментарии",
  },
  {
    id: "access",
    label: "Доступ",
    description: "Логины, роли и статусы сотрудников",
  },
];

export function auditEventTypeLabel(type: TeamAuditEventType): string {
  if (type === "member_invited") return "доступ";
  if (type === "member_status_updated") return "статус";
  if (type === "member_password_reset") return "пароль";
  if (type === "member_labor_rate_updated") return "ФОТ";
  if (type === "task_created") return "задача";
  if (type === "task_status_updated") return "статус задачи";
  if (type === "comment_added") return "комментарий";
  if (type === "shift_plan_updated") return "график";
  if (type === "learning_standard_updated") return "обучение";
  return "объявление";
}

export function auditEventJournalCategory(
  type: TeamAuditEventType,
): Exclude<TeamAuditJournalCategoryId, "all"> {
  if (type === "member_labor_rate_updated") return "labor";
  if (type === "learning_standard_updated") return "learning";
  if (type === "shift_plan_updated") return "plan";
  if (
    type === "task_created" ||
    type === "task_status_updated" ||
    type === "comment_added" ||
    type === "announcement_created"
  ) {
    return "tasks";
  }
  return "access";
}

export function auditEventContextHref(event: TeamAuditEvent): string {
  if (event.targetType === "member" && event.targetId) {
    return `#labor-member-${encodeURIComponent(event.targetId)}`;
  }

  if (event.targetType === "task" && event.targetId) {
    return `#team-task-${encodeURIComponent(event.targetId)}`;
  }

  if (event.targetType === "shift_plan") return "#shift-plan";
  if (event.targetType === "learning_standard") return "#learning-progress";
  if (event.targetType === "announcement") return "#team-journal";

  return "#team-actions";
}

export function auditEventContextLabel(event: TeamAuditEvent): string {
  if (event.targetType === "member") return "К сотруднику";
  if (event.targetType === "task") return "К задаче";
  if (event.targetType === "shift_plan") return "К плану";
  if (event.targetType === "learning_standard") return "К обучению";
  return "Открыть";
}

export function buildTeamAuditJournal(
  events: TeamAuditEvent[],
): TeamAuditJournalSummary {
  const entries = events.map((event) => {
    const categoryId = auditEventJournalCategory(event.type);
    const category = TEAM_AUDIT_JOURNAL_CATEGORIES.find(
      (item) => item.id === categoryId,
    );

    return {
      ...event,
      categoryId,
      categoryLabel: category?.label ?? "Действие",
      typeLabel: auditEventTypeLabel(event.type),
      contextHref: auditEventContextHref(event),
      contextLabel: auditEventContextLabel(event),
    };
  });

  const categories = TEAM_AUDIT_JOURNAL_CATEGORIES.map((category) => ({
    ...category,
    count:
      category.id === "all"
        ? entries.length
        : entries.filter((entry) => entry.categoryId === category.id).length,
  }));

  return { categories, entries };
}
