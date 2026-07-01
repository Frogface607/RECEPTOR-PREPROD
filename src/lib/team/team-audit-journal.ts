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
    description: "Все изменения по команде и сменам",
  },
  {
    id: "labor",
    label: "Оплата",
    description: "Оплата смен и стоимость команды",
  },
  {
    id: "learning",
    label: "Правила",
    description: "Правила ролей и допуск к смене",
  },
  {
    id: "plan",
    label: "Смены",
    description: "План смен и фактическая работа",
  },
  {
    id: "tasks",
    label: "Поручения",
    description: "Что поручили, начали или закрыли",
  },
  {
    id: "access",
    label: "Кабинет",
    description: "Люди, роли, вход и статус в команде",
  },
];

export function auditEventTypeLabel(type: TeamAuditEventType): string {
  if (type === "member_invited") return "человек добавлен";
  if (type === "member_status_updated") return "статус человека";
  if (type === "member_password_reset") return "первый вход";
  if (type === "member_labor_rate_updated") return "оплата";
  if (type === "task_created") return "поручение";
  if (type === "task_status_updated") return "движение";
  if (type === "comment_added") return "ответ";
  if (type === "shift_plan_updated") return "смена";
  if (type === "learning_standard_updated") return "правило";
  return "сообщение";
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
  if (event.targetType === "announcement" && event.targetId) {
    return `#team-announcement-${encodeURIComponent(event.targetId)}`;
  }
  if (event.targetType === "announcement") return "#team-journal";

  return "#team-actions";
}

export function auditEventContextLabel(event: TeamAuditEvent): string {
  if (event.targetType === "member") return "К человеку";
  if (event.targetType === "task") return "К поручению";
  if (event.targetType === "shift_plan") return "К сменам";
  if (event.targetType === "learning_standard") return "К правилам";
  if (event.targetType === "announcement") return "К сообщению";
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
      typeLabel: event.sourceLabel ?? auditEventTypeLabel(event.type),
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
