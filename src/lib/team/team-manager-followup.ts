import type { TeamLaborReadiness } from "./team-labor-readiness";
import type { TeamLearningMemberSummary } from "./team-learning-progress";
import type { TeamShiftPlanVarianceSummary } from "./team-shift-plan-variance";
import type {
  StaffMember,
  TeamAnnouncement,
  TeamAnnouncementRead,
  TeamTask,
} from "./team-os";
import type { SurvivalTaskDraft } from "@/lib/survival-score";

export type TeamManagerFollowUpStatus = "ready" | "attention" | "blocked";
export type TeamManagerFollowUpTone = "risk" | "watch" | "good";

export type TeamManagerFollowUpItem = {
  id: string;
  title: string;
  detail: string;
  tone: TeamManagerFollowUpTone;
  href: string;
  metric: string;
  taskDraft: SurvivalTaskDraft | null;
};

export type TeamManagerFollowUp = {
  status: TeamManagerFollowUpStatus;
  title: string;
  detail: string;
  openTasks: number;
  urgentTasks: number;
  blockedAdmissions: number;
  laborCoveragePct: number;
  planCoveragePct: number;
  unreadImportantAnnouncements: number;
  items: TeamManagerFollowUpItem[];
};

function isOpenTask(task: TeamTask): boolean {
  return task.status !== "done" && task.status !== "verified";
}

function rubles(value: number): string {
  return `${Math.round(value).toLocaleString("ru-RU")} ₽`;
}

function managerTaskDraft(input: {
  title: string;
  priority: TeamTask["priority"];
  dueLabel?: string;
  sourceLabel: string;
}): SurvivalTaskDraft {
  return {
    title: input.title,
    priority: input.priority,
    roleId: "venue_manager",
    dueLabel: input.dueLabel ?? "сегодня",
    sourceLabel: input.sourceLabel,
  };
}

function topBlockedAdmission(
  summaries: TeamLearningMemberSummary[],
): TeamLearningMemberSummary | undefined {
  return summaries
    .filter(
      (summary) => summary.member.status !== "paused" && !summary.canWorkShift,
    )
    .sort((a, b) => {
      if (a.admissionStatus !== b.admissionStatus) {
        return a.admissionStatus === "not_started" ? -1 : 1;
      }
      if (a.requiredMissing !== b.requiredMissing) {
        return b.requiredMissing - a.requiredMissing;
      }
      return a.averageBest - b.averageBest;
    })[0];
}

function planFactDetail(variance: TeamShiftPlanVarianceSummary): string | null {
  const issue = variance.issues[0];
  if (!issue) return null;

  if (issue.status === "day_off_worked") {
    return `${issue.member.name}: вышел в выходной ${issue.dateLabel}.`;
  }
  if (issue.status === "missed_plan") {
    return `${issue.member.name}: не вышел по плану ${issue.dateLabel}.`;
  }
  if (issue.status === "unplanned_actual") {
    return `${issue.member.name}: фактическая смена без плана ${issue.dateLabel}.`;
  }
  if (issue.status === "missing_rate") {
    return `${issue.member.name}: смена без ставки ФОТ ${issue.dateLabel}.`;
  }
  return `${issue.member.name}: расхождение ${issue.hoursDelta > 0 ? "+" : ""}${issue.hoursDelta} ч. ${issue.dateLabel}.`;
}

function announcementRecipients(
  announcement: TeamAnnouncement,
  staff: StaffMember[],
): StaffMember[] {
  return staff.filter((member) => {
    if (member.status === "paused") return false;
    if (announcement.audience.type === "venue") return true;
    return member.roleId === announcement.audience.roleId;
  });
}

function topUnreadImportantAnnouncement(input: {
  staff: StaffMember[];
  announcements: TeamAnnouncement[];
  announcementReads: TeamAnnouncementRead[];
}): {
  announcement: TeamAnnouncement;
  recipients: number;
  unread: number;
} | null {
  const readKeys = new Set(
    input.announcementReads.map(
      (read) => `${read.announcementId}:${read.memberId}`,
    ),
  );

  return (
    input.announcements
      .filter((announcement) => announcement.priority === "important")
      .map((announcement) => {
        const recipients = announcementRecipients(announcement, input.staff);
        const unread = recipients.filter(
          (member) => !readKeys.has(`${announcement.id}:${member.id}`),
        );
        return {
          announcement,
          recipients: recipients.length,
          unread: unread.length,
        };
      })
      .filter((item) => item.recipients > 0 && item.unread > 0)
      .sort((a, b) => {
        if (a.unread !== b.unread) return b.unread - a.unread;
        return b.recipients - a.recipients;
      })[0] ?? null
  );
}

export function buildTeamManagerFollowUp(input: {
  staff?: StaffMember[];
  tasks: TeamTask[];
  laborReadiness: TeamLaborReadiness;
  learningSummaries: TeamLearningMemberSummary[];
  shiftPlanVariance: TeamShiftPlanVarianceSummary;
  announcements?: TeamAnnouncement[];
  announcementReads?: TeamAnnouncementRead[];
}): TeamManagerFollowUp {
  const openTasks = input.tasks.filter(isOpenTask);
  const urgentTasks = openTasks.filter((task) => task.priority === "high");
  const blockedAdmissions = input.learningSummaries.filter(
    (summary) => summary.member.status !== "paused" && !summary.canWorkShift,
  );
  const communicationGap = topUnreadImportantAnnouncement({
    staff: input.staff ?? [],
    announcements: input.announcements ?? [],
    announcementReads: input.announcementReads ?? [],
  });
  const items: TeamManagerFollowUpItem[] = [];

  if (urgentTasks.length > 0) {
    const firstTask = urgentTasks[0];
    items.push({
      id: "urgent-tasks",
      title: "Закрыть срочные задачи",
      detail: `${firstTask.title}${urgentTasks.length > 1 ? ` и еще ${urgentTasks.length - 1}` : ""}.`,
      tone: "risk",
      href: "#team-actions",
      metric: `${urgentTasks.length} срочно`,
      taskDraft: managerTaskDraft({
        title: `Разобрать срочную задачу: ${firstTask.title}`,
        priority: "high",
        dueLabel: firstTask.dueLabel,
        sourceLabel: "Контроль смены",
      }),
    });
  }

  if (communicationGap) {
    items.push({
      id: "announcement-reads",
      title: "Дожать подтверждение объявления",
      detail: `${communicationGap.announcement.title}: ${communicationGap.unread} из ${communicationGap.recipients} еще не подтвердили.`,
      tone:
        communicationGap.unread === communicationGap.recipients
          ? "risk"
          : "watch",
      href: `#team-announcement-${encodeURIComponent(
        communicationGap.announcement.id,
      )}`,
      metric: `${communicationGap.unread} без ответа`,
      taskDraft: managerTaskDraft({
        title: `Дожать подтверждение объявления: ${communicationGap.announcement.title} — ${communicationGap.unread} без прочтения`,
        priority:
          communicationGap.unread === communicationGap.recipients
            ? "high"
            : "medium",
        sourceLabel: "Связь",
      }),
    });
  }

  const iikoBlocker = input.laborReadiness.iikoBlockers[0];
  const firstMissingRate = input.laborReadiness.missingStaff[0];
  if (
    input.laborReadiness.iikoStatus === "blocked" &&
    input.laborReadiness.iikoStaffShifts === 0
  ) {
    items.push({
      id: "labor-shifts",
      title: "Проверить смены iiko",
      detail: "Team OS не видит сотрудников и часы за выбранный период.",
      tone: "risk",
      href: "#iiko-shift-diagnostics",
      metric: "нет смен",
      taskDraft: managerTaskDraft({
        title: "Проверить выгрузку смен iiko для расчета ФОТ",
        priority: "high",
        sourceLabel: "ФОТ и смены",
      }),
    });
  } else if (iikoBlocker) {
    const taskTitle =
      iikoBlocker.action === "add-member"
        ? `Создать карточку Team OS из iiko: ${iikoBlocker.name}`
        : `Заполнить ставку ФОТ: ${iikoBlocker.name}`;
    items.push({
      id: "labor-iiko",
      title:
        iikoBlocker.action === "add-member"
          ? "Создать сотрудника из iiko"
          : "Заполнить ставку ФОТ",
      detail: `${iikoBlocker.name}: ${rubles(iikoBlocker.sales)} выручки без точного ФОТ.`,
      tone: input.laborReadiness.status === "blocked" ? "risk" : "watch",
      href:
        iikoBlocker.action === "add-member" ? "#team-actions" : "#labor-rates",
      metric: `${input.laborReadiness.coveragePct}% ФОТ`,
      taskDraft: {
        ...managerTaskDraft({
          title: taskTitle,
          priority:
            input.laborReadiness.status === "blocked" ? "high" : "medium",
          sourceLabel: "ФОТ и смены",
        }),
        roleId: iikoBlocker.roleId ?? "venue_manager",
        audienceMemberId:
          iikoBlocker.action === "set-rate" ? iikoBlocker.memberId : undefined,
        audienceMemberName:
          iikoBlocker.action === "set-rate" ? iikoBlocker.name : undefined,
      },
    });
  } else if (firstMissingRate) {
    items.push({
      id: "labor-rate",
      title: "Закрыть ставку ФОТ",
      detail: `${firstMissingRate.name}: ставка нужна для управленческого ФОТ.`,
      tone: input.laborReadiness.status === "blocked" ? "risk" : "watch",
      href: "#labor-rates",
      metric: `${input.laborReadiness.coveragePct}% ФОТ`,
      taskDraft: {
        ...managerTaskDraft({
          title: `Заполнить ставку ФОТ: ${firstMissingRate.name}`,
          priority:
            input.laborReadiness.status === "blocked" ? "high" : "medium",
          sourceLabel: "ФОТ и смены",
        }),
        roleId: firstMissingRate.roleId,
        audienceMemberId: firstMissingRate.id,
        audienceMemberName: firstMissingRate.name,
      },
    });
  }

  const learningBlocker = topBlockedAdmission(input.learningSummaries);
  if (learningBlocker) {
    items.push({
      id: "learning-admission",
      title: "Дать допуск к смене",
      detail: `${learningBlocker.member.name}: ${learningBlocker.nextItem?.title ?? "закрыть обязательные материалы"}.`,
      tone:
        learningBlocker.admissionStatus === "not_started" ? "watch" : "risk",
      href: "#learning-progress",
      metric: `${blockedAdmissions.length} без допуска`,
      taskDraft: {
        ...managerTaskDraft({
          title: `Закрыть допуск к смене: ${learningBlocker.member.name} — ${
            learningBlocker.nextItem?.title ?? "обязательные материалы"
          }`,
          priority:
            learningBlocker.admissionStatus === "not_started"
              ? "medium"
              : "high",
          sourceLabel: "Обучение",
        }),
        roleId: learningBlocker.member.roleId,
        audienceMemberId: learningBlocker.member.id,
        audienceMemberName: learningBlocker.member.name,
      },
    });
  }

  const varianceDetail = planFactDetail(input.shiftPlanVariance);
  if (varianceDetail) {
    items.push({
      id: "plan-fact",
      title: "Разобрать план/факт",
      detail: varianceDetail,
      tone:
        input.shiftPlanVariance.issues[0]?.tone === "risk" ? "risk" : "watch",
      href: "#shift-plan-variance",
      metric: `${input.shiftPlanVariance.planCoveragePct}% план`,
      taskDraft: managerTaskDraft({
        title: `Разобрать план/факт: ${varianceDetail}`,
        priority:
          input.shiftPlanVariance.issues[0]?.tone === "risk"
            ? "high"
            : "medium",
        sourceLabel: "План/факт",
      }),
    });
  }

  if (urgentTasks.length === 0 && openTasks.length > 0) {
    const firstTask = openTasks[0];
    items.push({
      id: "open-tasks",
      title: "Дожать открытые задачи",
      detail: `${firstTask.title}${openTasks.length > 1 ? ` и еще ${openTasks.length - 1}` : ""}.`,
      tone: "watch",
      href: "#team-actions",
      metric: `${openTasks.length} открыто`,
      taskDraft: managerTaskDraft({
        title: `Дожать открытую задачу: ${firstTask.title}`,
        priority: firstTask.priority,
        dueLabel: firstTask.dueLabel,
        sourceLabel: "Контроль смены",
      }),
    });
  }

  const visibleItems = items.slice(0, 3);

  if (visibleItems.length === 0) {
    return {
      status: "ready",
      title: "Команда под контролем",
      detail:
        "Срочных задач, ФОТ-блокеров, провалов допуска и план/факт риска не видно.",
      openTasks: openTasks.length,
      urgentTasks: urgentTasks.length,
      blockedAdmissions: blockedAdmissions.length,
      laborCoveragePct: input.laborReadiness.coveragePct,
      planCoveragePct: input.shiftPlanVariance.planCoveragePct,
      unreadImportantAnnouncements: 0,
      items: [
        {
          id: "ready",
          title: "Поддерживать ритм",
          detail:
            "Следующий шаг — обновлять план смен и закрывать задачи в день появления.",
          tone: "good",
          href: "#shift-coverage",
          metric: "готово",
          taskDraft: null,
        },
      ],
    };
  }

  const blocked =
    urgentTasks.length > 0 ||
    input.laborReadiness.status === "blocked" ||
    input.shiftPlanVariance.issues.some((issue) => issue.tone === "risk");

  return {
    status: blocked ? "blocked" : "attention",
    title: blocked ? "Есть блокеры перед сменой" : "Есть рабочий follow-up",
    detail:
      "Закройте эти пункты, чтобы владелец видел не только BI, но и управляемую смену.",
    openTasks: openTasks.length,
    urgentTasks: urgentTasks.length,
    blockedAdmissions: blockedAdmissions.length,
    laborCoveragePct: input.laborReadiness.coveragePct,
    planCoveragePct: input.shiftPlanVariance.planCoveragePct,
    unreadImportantAnnouncements: communicationGap?.unread ?? 0,
    items: visibleItems,
  };
}
