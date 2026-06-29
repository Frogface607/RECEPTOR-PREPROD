import { formatInteger, formatRubles } from "@/lib/format";
import { buildLaborMarginBridge } from "@/lib/labor-margin-bridge";
import { buildMenuEngineering } from "@/lib/menu-engineering";
import type { DailyBrief } from "@/lib/brief/daily-brief";
import type { RevenueDataQuality } from "@/lib/iiko/data-quality";
import {
  buildMenuMarginNextAction,
  type MenuMarginReadiness,
} from "@/lib/menu-margin-readiness";
import {
  buildLaborEmployeeDiagnostics,
  buildLaborInsights,
  buildLaborNextAction,
  buildLaborShiftDiagnostics,
  type LaborBiSummary,
  type LaborInsightTone,
} from "@/lib/team/labor-bi";
import type {
  TeamShiftPlanVarianceIssue,
  TeamShiftPlanVarianceSummary,
  TeamShiftPlanVarianceTone,
} from "@/lib/team/team-shift-plan-variance";
import type {
  TeamOpsActionTone,
  TeamOpsReadiness,
} from "@/lib/team/team-ops-readiness";
import type {
  StaffMember,
  TeamAnnouncement,
  TeamAnnouncementRead,
  TeamAuditEvent,
  TeamTask,
} from "@/lib/team/team-os";
import type { TeamLaborSetupProgress } from "@/lib/team/team-labor-readiness";
import type {
  CategoryStat,
  DishStat,
  RevenuePoint,
  RevenueSummary,
  ShiftStat,
} from "@/lib/iiko/models";
import type { SurvivalTaskDraft } from "@/lib/survival-score";

export type OwnerReviewConfidence = "high" | "medium" | "low";
export type OwnerReviewTone = "risk" | "watch" | "good";
export type OwnerReviewRole = "owner" | "manager" | "chef" | "service";

export type OwnerReviewEvidence = {
  label: string;
  value: string;
  detail: string;
  tone: OwnerReviewTone;
};

export type OwnerReviewHypothesis = {
  title: string;
  why: string;
  check: string;
  role: OwnerReviewRole;
  tone: OwnerReviewTone;
  taskSourceLabel?: string;
  audienceMemberId?: string;
  audienceMemberName?: string;
};

export type OwnerReviewQuestion = {
  role: OwnerReviewRole;
  text: string;
};

export type OwnerReviewActionTarget =
  | "iiko-settings"
  | "labor-member"
  | "labor-rate"
  | "shift-coverage"
  | "shift-diagnostics"
  | "shift-plan"
  | "shift-plan-variance"
  | "margin-diagnostics"
  | "margin-mapping"
  | "margin-risk"
  | "team-actions"
  | "team-journal"
  | "team-learning";

export type OwnerReviewAction = {
  title: string;
  detail: string;
  role: OwnerReviewRole;
  tone: OwnerReviewTone;
  target: OwnerReviewActionTarget;
  memberId?: string;
  memberName?: string;
};

export type OwnerProfitReadinessStatus = "ready" | "partial" | "blocked";

export type OwnerProfitReadiness = {
  status: OwnerProfitReadinessStatus;
  score: number;
  title: string;
  detail: string;
  missing: string[];
  action: OwnerProfitReadinessAction | null;
  tone: OwnerReviewTone;
};

export type OwnerProfitReadinessAction = {
  label: string;
  target: OwnerReviewActionTarget;
};

export type OwnerReview = {
  verdict: string;
  summary: string;
  confidence: OwnerReviewConfidence;
  confidenceReason: string;
  readiness: OwnerProfitReadiness;
  operationalPulse: OwnerOperationalPulse | null;
  evidence: OwnerReviewEvidence[];
  actions: OwnerReviewAction[];
  hypotheses: OwnerReviewHypothesis[];
  questions: OwnerReviewQuestion[];
  tasks: SurvivalTaskDraft[];
};

export type OwnerOperationalPulseEvent = {
  label: string;
  summary: string;
  timeLabel: string;
  tone: OwnerReviewTone;
  target: OwnerReviewActionTarget;
};

export type OwnerOperationalPulse = {
  title: string;
  detail: string;
  tone: OwnerReviewTone;
  openTasks: number;
  urgentOpenTasks: number;
  closedLoops: number;
  recentEvents: OwnerOperationalPulseEvent[];
  action: OwnerProfitReadinessAction;
};

export type OwnerOperationalProof = {
  openTasks: number;
  urgentOpenTasks: number;
  closedLoops: number;
  lastClosedLoop: string | null;
  announcements: number;
  announcementReads: number;
  unreadImportantAnnouncements: number;
  unreadImportantAnnouncementRecipients: number;
  unreadImportantAnnouncementTitle: string | null;
  lastAnnouncement: string | null;
  recentEvents: OwnerOperationalPulseEvent[];
};

type BuildOwnerReviewInput = {
  summary: RevenueSummary;
  dishes: DishStat[];
  categories: CategoryStat[];
  shifts: ShiftStat[];
  brief: DailyBrief;
  dataQuality: RevenueDataQuality;
  dataMode: "live" | "mock";
  labor?: LaborBiSummary;
  laborSetupProgress?: TeamLaborSetupProgress;
  margin?: MenuMarginReadiness;
  team?: TeamOpsReadiness;
  teamTasks?: TeamTask[];
  teamAuditEvents?: TeamAuditEvent[];
  teamStaff?: StaffMember[];
  teamAnnouncements?: TeamAnnouncement[];
  teamAnnouncementReads?: TeamAnnouncementRead[];
  shiftPlanVariance?: TeamShiftPlanVarianceSummary;
};

function pct(part: number, total: number): number {
  if (total <= 0) return 0;
  return Math.round((part / total) * 1000) / 10;
}

function deltaText(brief: DailyBrief): string {
  if (!brief.revenue.comparisonAvailable) return "нет базы";
  const value = brief.revenue.deltaPct;
  return `${value > 0 ? "+" : ""}${value}%`;
}

function topByRevenue(points: RevenuePoint[], direction: "min" | "max") {
  const positive = points.filter((point) => point.revenue > 0);
  if (!positive.length) return null;
  return [...positive].sort((a, b) =>
    direction === "min" ? a.revenue - b.revenue : b.revenue - a.revenue,
  )[0];
}

function roleTask(role: OwnerReviewRole): SurvivalTaskDraft["roleId"] {
  if (role === "manager") return "venue_manager";
  if (role === "chef") return "chef";
  if (role === "service") return "service";
  return "operations_manager";
}

function rolePriority(tone: OwnerReviewTone): SurvivalTaskDraft["priority"] {
  if (tone === "risk") return "high";
  if (tone === "watch") return "medium";
  return "low";
}

function roleDue(role: OwnerReviewRole): string {
  if (role === "service") return "до вечерней смены";
  if (role === "chef") return "до 17:00";
  return "сегодня";
}

function trimTaskTitle(value: string): string {
  const normalized = value.replace(/\s+/g, " ").trim();
  if (normalized.length <= 220) return normalized;
  return `${normalized.slice(0, 217).trim()}...`;
}

function trimEvidenceDetail(value: string): string {
  const normalized = value.replace(/\s+/g, " ").trim();
  if (normalized.length <= 120) return normalized;
  return `${normalized.slice(0, 117).trim()}...`;
}

function actionSourceLabel(action: OwnerReviewAction): string {
  if (
    action.target === "labor-member" ||
    action.target === "labor-rate" ||
    action.target === "shift-coverage" ||
    action.target === "shift-diagnostics" ||
    action.target === "shift-plan" ||
    action.target === "shift-plan-variance"
  ) {
    return "ФОТ и смены";
  }
  if (
    action.target === "margin-diagnostics" ||
    action.target === "margin-mapping" ||
    action.target === "margin-risk"
  ) {
    return "Маржа и техкарты";
  }
  if (
    action.target === "team-actions" ||
    action.target === "team-journal" ||
    action.target === "team-learning"
  ) {
    return "Команда";
  }
  return "Данные iiko";
}

function actionTaskTitle(action: OwnerReviewAction): string {
  return trimTaskTitle(`${action.title}: ${action.detail}`);
}

function taskFromOwnerAction(action: OwnerReviewAction): SurvivalTaskDraft {
  return {
    title: actionTaskTitle(action),
    priority: rolePriority(action.tone),
    roleId: roleTask(action.role),
    dueLabel: roleDue(action.role),
    sourceLabel: actionSourceLabel(action),
  };
}

function taskFromHypothesis(item: OwnerReviewHypothesis): SurvivalTaskDraft {
  return {
    title: trimTaskTitle(item.check),
    priority: rolePriority(item.tone),
    roleId: roleTask(item.role),
    dueLabel: roleDue(item.role),
    sourceLabel: item.taskSourceLabel ?? "Гипотеза",
    audienceMemberId: item.audienceMemberId,
    audienceMemberName: item.audienceMemberName,
  };
}

function taskFromLaborSetupProgress(
  progress: TeamLaborSetupProgress | undefined,
): SurvivalTaskDraft | null {
  if (!progress || progress.status === "ready") return null;

  if (progress.status === "needs-shifts") {
    return {
      title:
        "Проверить выгрузку смен iiko для расчета ФОТ: без смен Receptor не видит сотрудников, часы и стоимость периода.",
      priority: "high",
      roleId: "operations_manager",
      dueLabel: "сегодня",
      sourceLabel: "ФОТ setup",
    };
  }

  if (progress.status === "needs-members") {
    return {
      title: trimTaskTitle(
        `Импортировать сотрудников из iiko в Team OS: ${progress.missingStaffCards} карточек не связано, ${formatRubles(progress.unpricedRevenue)} выручки без точного ФОТ.`,
      ),
      priority: "medium",
      roleId: "venue_manager",
      dueLabel: "сегодня",
      sourceLabel: "ФОТ setup",
    };
  }

  const firstRateTarget = progress.bulkRateTargets[0];
  if (firstRateTarget) {
    const extraTargets = progress.bulkRateTargets.length - 1;
    return {
      title: trimTaskTitle(
        `Заполнить ставку ФОТ: ${firstRateTarget.name}${extraTargets > 0 ? ` и еще ${extraTargets}` : ""}. ${formatRubles(progress.unpricedRevenue)} выручки под вопросом.`,
      ),
      priority: progress.tone === "risk" ? "high" : "medium",
      roleId: firstRateTarget.roleId,
      audienceMemberId: firstRateTarget.id,
      audienceMemberName: firstRateTarget.name,
      dueLabel: "сегодня",
      sourceLabel: "ФОТ setup",
    };
  }

  return {
    title: trimTaskTitle(
      `Заполнить ставки ФОТ в Team OS: ${progress.missingRateCards} сотрудников без ставки, ${formatRubles(progress.unpricedRevenue)} выручки под вопросом.`,
    ),
    priority: progress.tone === "risk" ? "high" : "medium",
    roleId: "venue_manager",
    dueLabel: "сегодня",
    sourceLabel: "ФОТ setup",
  };
}

function isOpenTeamTask(task: TeamTask): boolean {
  return task.status !== "done" && task.status !== "verified";
}

function normalizeTaskTitle(value: string): string {
  return value.trim().replace(/\s+/g, " ").toLocaleLowerCase("ru-RU");
}

function isClosedLoopEvent(event: TeamAuditEvent): boolean {
  if (event.type !== "task_status_updated" || event.targetType !== "task") {
    return false;
  }

  const summary = event.summary.toLocaleLowerCase("ru-RU");
  return (
    summary.includes("закрыт") ||
    summary.includes("done") ||
    summary.includes("verified") ||
    summary.includes("сдачи модуля") ||
    summary.includes("обновления ставок")
  );
}

function auditEventLabel(event: TeamAuditEvent): string {
  if (event.type === "member_labor_rate_updated") return "ФОТ";
  if (event.type === "shift_plan_updated") return "План";
  if (event.type === "learning_standard_updated") return "Обучение";
  if (event.type === "member_invited") return "Доступ";
  if (event.type === "member_status_updated") return "Доступ";
  if (event.type === "member_password_reset") return "Логин";
  if (event.type === "task_created") return "Задача";
  if (event.type === "comment_added") return "Комментарий";
  if (event.type === "announcement_created") return "Объявление";
  if (event.type === "task_status_updated") {
    return isClosedLoopEvent(event) ? "Закрыто" : "Статус";
  }
  return "Team OS";
}

function auditEventTone(event: TeamAuditEvent): OwnerReviewTone {
  if (isClosedLoopEvent(event)) return "good";
  if (
    event.type === "member_labor_rate_updated" ||
    event.type === "shift_plan_updated" ||
    event.type === "learning_standard_updated" ||
    event.type === "member_invited" ||
    event.type === "member_status_updated" ||
    event.type === "member_password_reset"
  ) {
    return "good";
  }
  return "watch";
}

function auditEventTarget(event: TeamAuditEvent): OwnerReviewActionTarget {
  if (event.type === "member_labor_rate_updated") return "labor-rate";
  if (event.type === "shift_plan_updated") return "shift-plan";
  if (event.type === "learning_standard_updated") return "team-learning";
  if (
    event.type === "task_created" ||
    event.type === "task_status_updated" ||
    event.type === "comment_added" ||
    event.type === "announcement_created"
  ) {
    return "team-journal";
  }
  return "team-actions";
}

function operationalPulseEvent(
  event: TeamAuditEvent,
): OwnerOperationalPulseEvent {
  return {
    label: auditEventLabel(event),
    summary: trimEvidenceDetail(event.summary),
    timeLabel: event.createdAtLabel,
    tone: auditEventTone(event),
    target: auditEventTarget(event),
  };
}

function announcementPulseEvent(
  announcement: TeamAnnouncement,
): OwnerOperationalPulseEvent {
  return {
    label: "Объявление",
    summary: trimEvidenceDetail(announcement.title),
    timeLabel: announcement.createdAtLabel,
    tone: announcement.priority === "important" ? "watch" : "good",
    target: "team-journal",
  };
}

function announcementRecipients(
  announcement: TeamAnnouncement,
  staff: StaffMember[] | undefined,
): StaffMember[] {
  return (staff ?? []).filter((member) => {
    if (member.status === "paused") return false;
    if (announcement.audience.type === "venue") return true;
    return member.roleId === announcement.audience.roleId;
  });
}

function topUnreadImportantAnnouncement(input: {
  staff: StaffMember[] | undefined;
  announcements: TeamAnnouncement[] | undefined;
  announcementReads: TeamAnnouncementRead[] | undefined;
}): {
  announcement: TeamAnnouncement;
  recipients: number;
  unread: number;
} | null {
  const readKeys = new Set(
    (input.announcementReads ?? []).map(
      (read) => `${read.announcementId}:${read.memberId}`,
    ),
  );

  return (
    (input.announcements ?? [])
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

function buildOperationalProof(
  tasks: TeamTask[] | undefined,
  auditEvents: TeamAuditEvent[] | undefined,
  staff: StaffMember[] | undefined,
  announcements: TeamAnnouncement[] | undefined,
  announcementReads: TeamAnnouncementRead[] | undefined,
): OwnerOperationalProof | null {
  if (!tasks && !auditEvents && !announcements && !announcementReads) {
    return null;
  }

  const openTasks = (tasks ?? []).filter(isOpenTeamTask);
  const closedLoopEvents = (auditEvents ?? []).filter(isClosedLoopEvent);
  const communicationGap = topUnreadImportantAnnouncement({
    staff,
    announcements,
    announcementReads,
  });
  const auditAnnouncementIds = new Set(
    (auditEvents ?? [])
      .filter(
        (event) =>
          event.type === "announcement_created" &&
          event.targetType === "announcement" &&
          event.targetId,
      )
      .map((event) => event.targetId as string),
  );
  const recentEvents = [
    ...(auditEvents ?? []).slice(0, 3).map(operationalPulseEvent),
    ...(announcements ?? [])
      .filter((announcement) => !auditAnnouncementIds.has(announcement.id))
      .slice(0, 3)
      .map(announcementPulseEvent),
  ].slice(0, 3);

  return {
    openTasks: openTasks.length,
    urgentOpenTasks: openTasks.filter((task) => task.priority === "high")
      .length,
    closedLoops: closedLoopEvents.length,
    lastClosedLoop: closedLoopEvents[0]?.summary ?? null,
    announcements: announcements?.length ?? 0,
    announcementReads: announcementReads?.length ?? 0,
    unreadImportantAnnouncements: communicationGap?.unread ?? 0,
    unreadImportantAnnouncementRecipients: communicationGap?.recipients ?? 0,
    unreadImportantAnnouncementTitle:
      communicationGap?.announcement.title ?? null,
    lastAnnouncement: announcements?.[0]?.title ?? null,
    recentEvents,
  };
}

function operationalPulse(
  proof: OwnerOperationalProof | null,
): OwnerOperationalPulse | null {
  if (!proof) return null;

  if (proof.urgentOpenTasks > 0) {
    return {
      title: "Есть срочные действия команды",
      detail: `${urgentTasksLabel(proof.urgentOpenTasks)} держат контур открытым. Закройте их в Team OS, чтобы выводы владельца стали доказанными.`,
      tone: "risk",
      openTasks: proof.openTasks,
      urgentOpenTasks: proof.urgentOpenTasks,
      closedLoops: proof.closedLoops,
      recentEvents: proof.recentEvents,
      action: { label: "Открыть Team OS", target: "team-actions" },
    };
  }

  if (proof.openTasks > 0) {
    return {
      title: "Контур в работе",
      detail: `${openTasksLabel(proof.openTasks)} еще ждут исполнения. После закрытия задач владелец увидит это как управленческий результат.`,
      tone: "watch",
      openTasks: proof.openTasks,
      urgentOpenTasks: proof.urgentOpenTasks,
      closedLoops: proof.closedLoops,
      recentEvents: proof.recentEvents,
      action: { label: "Открыть задачи", target: "team-actions" },
    };
  }

  if (proof.unreadImportantAnnouncements > 0) {
    return {
      title: "Связь не закрыта",
      detail: `${trimEvidenceDetail(
        proof.unreadImportantAnnouncementTitle ?? "важное объявление",
      )}: ${proof.unreadImportantAnnouncements} из ${
        proof.unreadImportantAnnouncementRecipients
      } еще не подтвердили.`,
      tone:
        proof.unreadImportantAnnouncements ===
        proof.unreadImportantAnnouncementRecipients
          ? "risk"
          : "watch",
      openTasks: proof.openTasks,
      urgentOpenTasks: proof.urgentOpenTasks,
      closedLoops: proof.closedLoops,
      recentEvents: proof.recentEvents,
      action: { label: "Открыть связь", target: "team-journal" },
    };
  }

  if (proof.closedLoops > 0) {
    return {
      title: "Команда закрывает действия",
      detail: `${proof.closedLoops} закрыто недавно. Экран владельца учитывает эти действия в готовности прибыли и операционном контуре.`,
      tone: "good",
      openTasks: proof.openTasks,
      urgentOpenTasks: proof.urgentOpenTasks,
      closedLoops: proof.closedLoops,
      recentEvents: proof.recentEvents,
      action: { label: "Открыть журнал", target: "team-actions" },
    };
  }

  if (proof.announcements > 0) {
    return {
      title: "Команда получила контекст",
      detail: `${announcementCountLabel(proof.announcements)} опубликовано в Team OS. Последнее: ${trimEvidenceDetail(
        proof.lastAnnouncement ?? "командное объявление",
      )}.`,
      tone: "good",
      openTasks: proof.openTasks,
      urgentOpenTasks: proof.urgentOpenTasks,
      closedLoops: proof.closedLoops,
      recentEvents: proof.recentEvents,
      action: { label: "Открыть связь", target: "team-journal" },
    };
  }

  return {
    title: "Открытых задач нет",
    detail:
      "Новых закрытий в последних событиях не было. Если появится риск по ФОТ, марже или смене, он пойдет в Team OS.",
    tone: "good",
    openTasks: proof.openTasks,
    urgentOpenTasks: proof.urgentOpenTasks,
    closedLoops: proof.closedLoops,
    recentEvents: proof.recentEvents,
    action: { label: "Открыть Team OS", target: "team-actions" },
  };
}

function operationalProofEvidence(
  proof: OwnerOperationalProof,
): OwnerReviewEvidence {
  const detail =
    proof.closedLoops > 0
      ? `${proof.closedLoops} закрыто недавно. Последнее: ${trimEvidenceDetail(
          proof.lastClosedLoop ?? "задача закрыта в Team OS",
        )}`
      : proof.openTasks > 0
        ? `${proof.urgentOpenTasks} срочных. Закрытые контуры появятся после выполнения задач в Team OS.`
        : "Открытых задач нет; новых закрытий в последних событиях не было.";

  return {
    label: "Контуры",
    value: `${proof.openTasks} открыто`,
    detail,
    tone:
      proof.urgentOpenTasks > 0
        ? "risk"
        : proof.openTasks > 0
          ? "watch"
          : "good",
  };
}

function operationalCommunicationEvidence(
  proof: OwnerOperationalProof,
): OwnerReviewEvidence | null {
  if (proof.announcements <= 0) return null;

  return {
    label: "Связь",
    value: announcementCountLabel(proof.announcements),
    detail: proof.lastAnnouncement
      ? `${announcementReadLabel(proof.announcementReads)}${
          proof.unreadImportantAnnouncements > 0
            ? `, ${proof.unreadImportantAnnouncements} без подтверждения`
            : ""
        }. Последнее: ${trimEvidenceDetail(proof.lastAnnouncement)}`
      : "Командные объявления опубликованы в Team OS.",
    tone: proof.unreadImportantAnnouncements > 0 ? "watch" : "good",
  };
}

function ownerActionFromCommunication(
  proof: OwnerOperationalProof | null,
): OwnerReviewAction | null {
  if (!proof || proof.unreadImportantAnnouncements <= 0) return null;

  return {
    title: "Дожать связь",
    detail: `${trimEvidenceDetail(
      proof.unreadImportantAnnouncementTitle ?? "важное объявление",
    )}: ${proof.unreadImportantAnnouncements} без подтверждения.`,
    role: "manager",
    tone:
      proof.unreadImportantAnnouncements ===
      proof.unreadImportantAnnouncementRecipients
        ? "risk"
        : "watch",
    target: "team-journal",
  };
}

function compactMissing(items: string[]): string {
  if (items.length === 0) return "ключевые контуры закрыты";
  if (items.length <= 3) return items.join(", ");
  return `${items.slice(0, 3).join(", ")} +${items.length - 3}`;
}

function taskWord(
  count: number,
  one: string,
  few: string,
  many: string,
): string {
  const mod10 = count % 10;
  const mod100 = count % 100;
  if (mod10 === 1 && mod100 !== 11) return one;
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return few;
  return many;
}

function openTasksLabel(count: number): string {
  return `${count} ${taskWord(count, "открытая задача", "открытые задачи", "открытых задач")} Team OS`;
}

function urgentTasksLabel(count: number): string {
  return `${count} ${taskWord(count, "срочная задача", "срочные задачи", "срочных задач")} Team OS`;
}

function announcementCountLabel(count: number): string {
  return `${count} ${taskWord(count, "объявление", "объявления", "объявлений")}`;
}

function announcementReadLabel(count: number): string {
  return `${count} ${taskWord(count, "прочтение", "прочтения", "прочтений")}`;
}

function buildProfitReadiness(input: {
  dataMode: "live" | "mock";
  dataQuality: RevenueDataQuality;
  labor?: LaborBiSummary;
  margin?: MenuMarginReadiness;
  team?: TeamOpsReadiness;
  operationalProof: OwnerOperationalProof | null;
}): OwnerProfitReadiness {
  const missing: string[] = [];
  let action: OwnerProfitReadinessAction | null = null;
  let score = 0;
  const setAction = (next: OwnerProfitReadinessAction) => {
    action ??= next;
  };

  if (input.dataMode === "mock") {
    missing.push("live iiko");
    setAction({ label: "Проверить iiko", target: "iiko-settings" });
  } else if (input.dataQuality.status === "risk") {
    missing.push("полное покрытие периода");
    setAction({ label: "Проверить iiko", target: "iiko-settings" });
  } else {
    score += input.dataQuality.status === "ok" ? 20 : 14;
    if (input.dataQuality.status === "watch") {
      missing.push("проверка покрытия периода");
      setAction({ label: "Проверить iiko", target: "iiko-settings" });
    }
  }

  if (!input.labor) {
    missing.push("ФОТ по сменам");
    setAction({ label: "Проверить смены", target: "shift-coverage" });
  } else if (input.labor.laborReadinessStatus === "ready") {
    score += 25;
  } else if (input.labor.laborReadinessStatus === "partial") {
    score += 14;
    missing.push("точные ставки ФОТ");
    setAction({ label: "Заполнить ФОТ", target: "labor-rate" });
  } else {
    missing.push("сотрудники и ставки ФОТ");
    setAction({
      label:
        input.labor.staffShifts === 0 ? "Проверить смены" : "Заполнить ФОТ",
      target: input.labor.staffShifts === 0 ? "shift-coverage" : "labor-rate",
    });
  }

  if (!input.margin) {
    missing.push("себестоимость блюд");
    setAction({ label: "Связать блюда", target: "margin-mapping" });
  } else if (input.margin.status === "ready") {
    score += 35;
  } else if (input.margin.status === "partial") {
    score += 18;
    missing.push("закупочные цены и техкарты");
    setAction({
      label:
        input.margin.missingCostRevenue >= input.margin.missingLinkRevenue
          ? "Проверить RMS"
          : "Связать блюда",
      target:
        input.margin.missingCostRevenue >= input.margin.missingLinkRevenue
          ? "margin-diagnostics"
          : "margin-mapping",
    });
  } else {
    missing.push("связи блюд с iiko и закупочные цены");
    setAction({ label: "Связать блюда", target: "margin-mapping" });
  }

  if (!input.team) {
    missing.push("Team OS");
    setAction({ label: "Открыть Team OS", target: "team-actions" });
  } else if (input.team.status === "ready") {
    score += 10;
  } else if (input.team.status === "attention") {
    score += 6;
    missing.push("готовность команды");
    setAction({ label: "Открыть Team OS", target: "team-actions" });
  } else {
    missing.push("блокеры Team OS");
    setAction({ label: "Открыть Team OS", target: "team-actions" });
  }

  if (!input.operationalProof) {
    missing.push("закрытые контуры задач");
    setAction({ label: "Открыть задачи", target: "team-actions" });
  } else if (input.operationalProof.urgentOpenTasks > 0) {
    missing.push(urgentTasksLabel(input.operationalProof.urgentOpenTasks));
    setAction({ label: "Открыть задачи", target: "team-actions" });
  } else if (input.operationalProof.openTasks > 0) {
    score += 5;
    missing.push(openTasksLabel(input.operationalProof.openTasks));
    setAction({ label: "Открыть задачи", target: "team-actions" });
  } else if (input.operationalProof.unreadImportantAnnouncements > 0) {
    score += 5;
    missing.push(
      `${input.operationalProof.unreadImportantAnnouncements} неподтвержденных объявлений`,
    );
    setAction({ label: "Открыть связь", target: "team-journal" });
  } else {
    score += 10;
  }

  const hardBlocked =
    input.dataMode === "mock" ||
    input.dataQuality.status === "risk" ||
    !input.labor ||
    input.labor.laborReadinessStatus === "blocked" ||
    !input.margin ||
    input.margin.status === "blocked";
  const hasOpenLoop =
    input.team?.status !== "ready" ||
    !input.operationalProof ||
    input.operationalProof.openTasks > 0 ||
    input.operationalProof.unreadImportantAnnouncements > 0 ||
    input.dataQuality.status === "watch" ||
    input.labor?.laborReadinessStatus === "partial" ||
    input.margin?.status === "partial";
  const status: OwnerProfitReadinessStatus = hardBlocked
    ? "blocked"
    : hasOpenLoop
      ? "partial"
      : "ready";
  const roundedScore = Math.max(0, Math.min(100, Math.round(score)));

  if (status === "ready") {
    return {
      status,
      score: roundedScore,
      title: "Можно считать прибыль",
      detail: "Live-данные, ФОТ, себестоимость и Team OS контуры закрыты.",
      missing: [],
      action: null,
      tone: "good",
    };
  }

  if (status === "partial") {
    return {
      status,
      score: roundedScore,
      title: "Прибыль требует проверки",
      detail: `Проверить: ${compactMissing(missing)}. После закрытия контуров выводы можно превращать в задачи.`,
      missing,
      action,
      tone: "watch",
    };
  }

  return {
    status,
    score: roundedScore,
    title: "Прибыль не доказана",
    detail: `Не хватает: ${compactMissing(missing)}. До этого решения по прибыли лучше держать как гипотезы.`,
    missing,
    action,
    tone: "risk",
  };
}

function draftMatchesOpenTeamTask(
  draft: SurvivalTaskDraft,
  task: TeamTask,
): boolean {
  if (!isOpenTeamTask(task)) return false;
  if (normalizeTaskTitle(task.title) !== normalizeTaskTitle(draft.title)) {
    return false;
  }

  if (draft.audienceMemberId) {
    return (
      task.audience.type === "member" &&
      task.audience.memberId === draft.audienceMemberId
    );
  }

  return task.audience.type === "role" && task.audience.roleId === draft.roleId;
}

function withoutAlreadyOpenTeamTasks(
  drafts: SurvivalTaskDraft[],
  tasks: TeamTask[] | undefined,
): SurvivalTaskDraft[] {
  if (!tasks?.length) return drafts;
  const openTasks = tasks.filter(isOpenTeamTask);
  if (openTasks.length === 0) return drafts;

  return drafts.filter(
    (draft) => !openTasks.some((task) => draftMatchesOpenTeamTask(draft, task)),
  );
}

function uniqueTaskDrafts(drafts: SurvivalTaskDraft[]): SurvivalTaskDraft[] {
  const seen = new Set<string>();
  return drafts.filter((draft) => {
    const audienceKey = draft.audienceMemberId ?? draft.roleId;
    const key = `${audienceKey}:${draft.title.toLowerCase()}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function ownerToneFromLabor(tone: LaborInsightTone): OwnerReviewTone {
  if (tone === "risk") return "risk";
  if (tone === "good") return "good";
  return "watch";
}

function ownerToneFromTeam(tone: TeamOpsActionTone): OwnerReviewTone {
  if (tone === "risk") return "risk";
  if (tone === "good") return "good";
  return "watch";
}

function ownerToneFromShiftPlanVariance(
  tone: TeamShiftPlanVarianceTone,
): OwnerReviewTone {
  if (tone === "risk") return "risk";
  if (tone === "ready") return "good";
  return "watch";
}

function laborEvidence(input: LaborBiSummary): OwnerReviewEvidence {
  const primaryInsight = buildLaborInsights(input)[0];
  const blocker = input.topBlockers[0];
  const pct =
    input.laborCostPct === null
      ? "нет данных"
      : `${input.laborCostPct.toLocaleString("ru-RU", {
          maximumFractionDigits: 1,
        })}%`;
  const coverage =
    input.revenueCoveragePct === null
      ? "покрытие неизвестно"
      : `${input.revenueCoveragePct.toLocaleString("ru-RU", {
          maximumFractionDigits: 1,
        })}% выручки с точным ФОТ`;
  const detail = blocker
    ? `${blocker.name}: ${formatRubles(blocker.sales)} без точного ФОТ, ${coverage}`
    : input.missingRates > 0
      ? `${input.missingRates} ставок не заведено, ${coverage}`
      : `${formatRubles(input.laborCost)} за период`;

  return {
    label: "ФОТ",
    value: pct,
    detail,
    tone: primaryInsight ? ownerToneFromLabor(primaryInsight.tone) : "watch",
  };
}

function marginEvidence(input: MenuMarginReadiness): OwnerReviewEvidence {
  const nextAction = buildMenuMarginNextAction(input);
  const blocker = nextAction.blocker;
  const primaryRisk = input.topMarginRisks[0] ?? null;
  const detail = blocker
    ? blocker.reason === "missing-cost"
      ? `${blocker.dishName}: ${formatRubles(blocker.revenue)} без закупочной цены`
      : `${blocker.dishName}: ${formatRubles(blocker.revenue)} без связи с iiko`
    : `${input.costedDishes}/${input.totalDishes} блюд с себестоимостью`;

  const detailWithRisk =
    !blocker && primaryRisk
      ? `${primaryRisk.dishName}: валовая маржа ${primaryRisk.grossMarginPct}% при цене ${formatRubles(primaryRisk.salePrice)}`
      : detail;

  return {
    label: "Маржа",
    value: `${input.revenueCoveragePct}%`,
    detail: detailWithRisk,
    tone: primaryRisk
      ? primaryRisk.grossMarginPct < 45
        ? "risk"
        : "watch"
      : input.status === "ready"
        ? "good"
        : input.status === "blocked"
          ? "risk"
          : "watch",
  };
}

function formatCoverage(value: number | null): string {
  if (value === null) return "нет данных";
  return `${value.toLocaleString("ru-RU", { maximumFractionDigits: 1 })}%`;
}

function unitEconomicsEvidence(input: {
  labor?: LaborBiSummary;
  margin?: MenuMarginReadiness;
}): OwnerReviewEvidence | null {
  if (!input.labor && !input.margin) return null;

  const labor = input.labor;
  const margin = input.margin;
  const laborIncomplete =
    Boolean(labor) && labor?.laborReadinessStatus !== "ready";
  const marginIncomplete = Boolean(margin) && margin?.status !== "ready";
  const laborPct = labor?.laborCostPct ?? null;
  const laborCoverage = formatCoverage(labor?.revenueCoveragePct ?? null);
  const marginCoverage = margin
    ? `${margin.revenueCoveragePct}%`
    : "нет данных";

  if (laborIncomplete && marginIncomplete) {
    return {
      label: "Экономика",
      value: "не доказана",
      detail: `ФОТ покрыт на ${laborCoverage}, маржа на ${marginCoverage} выручки.`,
      tone: "risk",
    };
  }

  if (laborIncomplete && labor) {
    return {
      label: "Экономика",
      value: "ФОТ не доказан",
      detail: `${formatRubles(labor.unpricedRevenue)} сменной выручки без точного ФОТ.`,
      tone: labor.laborReadinessStatus === "blocked" ? "risk" : "watch",
    };
  }

  if (marginIncomplete && margin) {
    return {
      label: "Экономика",
      value: "маржа не доказана",
      detail: `${formatRubles(margin.blockedRevenue)} выручки без себестоимости.`,
      tone: margin.status === "blocked" ? "risk" : "watch",
    };
  }

  if (laborPct !== null && laborPct >= 25) {
    return {
      label: "Экономика",
      value: "ФОТ давит",
      detail: `ФОТ ${formatCoverage(laborPct)} от выручки, маржа покрыта на ${marginCoverage}.`,
      tone: "risk",
    };
  }

  return {
    label: "Экономика",
    value: "можно считать",
    detail: `ФОТ ${formatCoverage(laborPct)}, маржа покрыта на ${marginCoverage}.`,
    tone: "good",
  };
}

function teamEvidence(input: TeamOpsReadiness): OwnerReviewEvidence {
  const firstAction = input.actions.find((action) => action.id !== "ready");
  const detail = firstAction
    ? `${firstAction.title}: ${firstAction.detail}`
    : `Допуск ${input.learningAdmissionPct}%, роли ${input.roleCoveragePct}%, ФОТ ${input.laborCoveragePct}%.`;

  return {
    label: "Команда",
    value: `${input.score}%`,
    detail,
    tone:
      input.status === "blocked"
        ? "risk"
        : input.status === "ready"
          ? "good"
          : "watch",
  };
}

function shiftPlanVarianceEvidence(
  input: TeamShiftPlanVarianceSummary,
): OwnerReviewEvidence | null {
  if (input.plannedShifts === 0 && input.actualShifts === 0) return null;

  const primaryIssue = input.issues[0] ?? null;
  const detail = primaryIssue
    ? `${primaryIssue.member.name}: ${shiftPlanVarianceIssueDetail(primaryIssue)}`
    : `План закрывает ${input.coveredActualShifts}/${input.actualShifts} фактических смен.`;

  return {
    label: "План/факт",
    value: `${input.planCoveragePct}%`,
    detail,
    tone: primaryIssue
      ? ownerToneFromShiftPlanVariance(primaryIssue.tone)
      : input.planCoveragePct >= 90
        ? "good"
        : "watch",
  };
}

function ownerActionFromShiftPlanVariance(
  input: TeamShiftPlanVarianceSummary,
): OwnerReviewAction | null {
  const primaryIssue = input.issues[0] ?? null;
  if (!primaryIssue) return null;

  return {
    title: shiftPlanVarianceActionTitle(primaryIssue),
    detail: `${primaryIssue.member.name}: ${shiftPlanVarianceIssueDetail(primaryIssue)}`,
    role: "manager",
    tone: ownerToneFromShiftPlanVariance(primaryIssue.tone),
    target: "shift-plan-variance",
  };
}

function shiftPlanVarianceHypothesis(
  input: TeamShiftPlanVarianceSummary,
): OwnerReviewHypothesis | null {
  const primaryIssue = input.issues[0] ?? null;
  if (!primaryIssue) return null;

  return {
    title: shiftPlanVarianceActionTitle(primaryIssue),
    why: `${primaryIssue.member.name}: ${shiftPlanVarianceIssueDetail(primaryIssue)}. План покрывает ${input.planCoveragePct}% фактических смен.`,
    check:
      "Сверить график с фактическими сменами, отметить исключения и обновить ставку/план на следующую неделю.",
    role: "manager",
    tone: ownerToneFromShiftPlanVariance(primaryIssue.tone),
  };
}

function shiftPlanVarianceActionTitle(
  issue: TeamShiftPlanVarianceIssue,
): string {
  if (issue.status === "day_off_worked") return "Разобрать выход в выходной";
  if (issue.status === "missed_plan") return "Разобрать невыход по графику";
  if (issue.status === "unplanned_actual") return "Закрыть смену без плана";
  if (issue.status === "missing_rate") return "Завести ставку для ФОТ";
  if (issue.status === "over_hours") return "Проверить переработку";
  return "Проверить недоработку часов";
}

function shiftPlanVarianceIssueDetail(
  issue: TeamShiftPlanVarianceIssue,
): string {
  const hoursDelta =
    issue.hoursDelta === 0
      ? "часы совпали"
      : `${issue.hoursDelta > 0 ? "+" : ""}${issue.hoursDelta} ч`;
  const laborDelta =
    issue.laborDelta === 0
      ? "ФОТ без отклонения"
      : `${issue.laborDelta > 0 ? "+" : ""}${formatRubles(issue.laborDelta)}`;

  if (issue.status === "day_off_worked") {
    return `${issue.dateLabel}: был выходной, но есть ${issue.actualShifts} факт. смен.`;
  }
  if (issue.status === "missed_plan") {
    return `${issue.dateLabel}: в плане была смена, факта нет.`;
  }
  if (issue.status === "unplanned_actual") {
    return `${issue.dateLabel}: факт есть, в графике смены нет.`;
  }
  if (issue.status === "missing_rate") {
    return `${issue.dateLabel}: смена есть, ставка не заведена.`;
  }
  return `${issue.dateLabel}: ${hoursDelta}, ${laborDelta}.`;
}

function ownerActionFromLabor(input: LaborBiSummary): OwnerReviewAction | null {
  const nextAction = buildLaborNextAction(input);
  const firstLinkedEmployeeIssue = buildLaborEmployeeDiagnostics(input).find(
    (employee) =>
      Boolean(employee.memberId) &&
      employee.kind !== "healthy" &&
      employee.kind !== "missing-rate",
  );

  if (nextAction.kind === "ready") {
    if (firstLinkedEmployeeIssue) {
      return {
        title: firstLinkedEmployeeIssue.title,
        detail: firstLinkedEmployeeIssue.detail,
        role: "manager",
        tone: ownerToneFromLabor(firstLinkedEmployeeIssue.tone),
        target: "labor-member",
        memberId: firstLinkedEmployeeIssue.memberId,
        memberName: firstLinkedEmployeeIssue.name,
      };
    }

    const firstShiftIssue = buildLaborShiftDiagnostics(input).find(
      (shift) => shift.kind !== "healthy",
    );

    if (!firstShiftIssue) return null;

    return {
      title: firstShiftIssue.title,
      detail: firstShiftIssue.detail,
      role: "manager",
      tone: ownerToneFromLabor(firstShiftIssue.tone),
      target: "shift-diagnostics",
    };
  }

  if (nextAction.kind === "missing-shifts") {
    return {
      title: nextAction.title,
      detail: nextAction.detail,
      role: "owner",
      tone: "watch",
      target: "iiko-settings",
    };
  }

  if (nextAction.kind === "missing-member" && nextAction.blocker) {
    return {
      title: nextAction.title,
      detail: nextAction.detail,
      role: "manager",
      tone: "watch",
      target: "labor-member",
      memberName: nextAction.blocker.name,
    };
  }

  if (nextAction.kind === "missing-rate" && nextAction.blocker) {
    return {
      title: nextAction.title,
      detail: nextAction.detail,
      role: "manager",
      tone: "watch",
      target: "labor-rate",
      memberId: nextAction.blocker.memberId,
      memberName: nextAction.blocker.name,
    };
  }

  if (nextAction.kind === "expensive-labor" && firstLinkedEmployeeIssue) {
    return {
      title: firstLinkedEmployeeIssue.title,
      detail: firstLinkedEmployeeIssue.detail,
      role: "manager",
      tone: ownerToneFromLabor(firstLinkedEmployeeIssue.tone),
      target: "labor-member",
      memberId: firstLinkedEmployeeIssue.memberId,
      memberName: firstLinkedEmployeeIssue.name,
    };
  }

  if (nextAction.kind === "expensive-labor") {
    return {
      title: nextAction.title,
      detail: nextAction.detail,
      role: "manager",
      tone: "risk",
      target: "shift-diagnostics",
    };
  }

  return null;
}

function ownerActionFromMargin(
  input: MenuMarginReadiness,
): OwnerReviewAction | null {
  const nextAction = buildMenuMarginNextAction(input);
  const primaryRisk = input.topMarginRisks[0] ?? null;

  if (nextAction.kind === "ready") {
    if (!primaryRisk) return null;
    const source =
      primaryRisk.costSource === "tech-card" ? "по техкарте" : "по товару iiko";

    return {
      title: `Разобрать маржу: ${primaryRisk.dishName}`,
      detail: `Валовая маржа ${primaryRisk.grossMarginPct}%: цена ${formatRubles(primaryRisk.salePrice)}, себестоимость ${formatRubles(primaryRisk.costReference)} ${source}. Проверьте цену, порцию, списания и состав техкарты.`,
      role: "chef",
      tone: primaryRisk.grossMarginPct < 45 ? "risk" : "watch",
      target: "margin-risk",
    };
  }

  return {
    title: nextAction.title,
    detail: nextAction.detail,
    role: nextAction.kind === "missing-cost" ? "owner" : "chef",
    tone: input.status === "blocked" ? "risk" : "watch",
    target:
      nextAction.kind === "missing-cost"
        ? "margin-diagnostics"
        : "margin-mapping",
  };
}

function teamActionTarget(href: string): OwnerReviewActionTarget {
  if (href === "#learning-progress") return "team-learning";
  if (href === "#team-actions") return "team-actions";
  if (href === "#shift-coverage") return "shift-coverage";
  if (href === "#labor-rates") return "labor-rate";
  if (href === "#iiko-shift-diagnostics") return "shift-diagnostics";
  if (href === "#shift-plan") return "shift-plan";
  return "team-actions";
}

function ownerActionFromTeam(
  input: TeamOpsReadiness,
): OwnerReviewAction | null {
  const action = input.actions.find((item) => item.id !== "ready");
  if (!action) return null;

  return {
    title: action.title,
    detail: action.detail,
    role: "manager",
    tone: ownerToneFromTeam(action.tone),
    target: teamActionTarget(action.href),
  };
}

function laborMarginHypothesis(input: {
  labor?: LaborBiSummary;
  margin?: MenuMarginReadiness;
}): OwnerReviewHypothesis | null {
  if (!input.margin) return null;

  if (input.labor) {
    const bridge = buildLaborMarginBridge({
      labor: input.labor,
      margin: input.margin,
    });
    if (bridge.tone === "good") return null;

    return {
      title: bridge.title,
      why: bridge.detail,
      check: bridge.action,
      role:
        bridge.tone === "setup" ? "chef" : bridge.employee ? "owner" : "chef",
      tone: ownerToneFromLaborBridge(bridge.tone),
      taskSourceLabel: "ФОТ и маржа",
      audienceMemberId: bridge.employee?.memberId,
      audienceMemberName: bridge.employee?.name,
    };
  }

  if (input.margin.status === "ready") return null;

  const nextAction = buildMenuMarginNextAction(input.margin);
  const topBlocker = nextAction.blocker;
  const blockerText = topBlocker
    ? `Первым закрыть «${topBlocker.dishName}» (${formatRubles(topBlocker.revenue)} выручки): ${nextAction.title}.`
    : "Начните с топ-позиций без себестоимости.";
  const marginAction = nextAction.action;

  return {
    title: "Маржа пока не доказана",
    why: `Себестоимость покрывает ${input.margin.revenueCoveragePct}% выручки периода. ${blockerText}`,
    check: marginAction,
    role: "chef",
    tone: input.margin.status === "blocked" ? "risk" : "watch",
  };
}

function ownerToneFromLaborBridge(
  tone: ReturnType<typeof buildLaborMarginBridge>["tone"],
): OwnerReviewTone {
  if (tone === "risk") return "risk";
  if (tone === "good") return "good";
  return "watch";
}

function confidenceFor(input: BuildOwnerReviewInput): {
  confidence: OwnerReviewConfidence;
  reason: string;
} {
  if (input.dataMode === "mock") {
    return {
      confidence: "low",
      reason: "показаны демо-данные, для решений нужен live iiko",
    };
  }

  if (input.dataQuality.status === "risk") {
    return {
      confidence: "low",
      reason: "период покрыт не полностью или нет продаж в выгрузке",
    };
  }

  if (input.labor?.laborReadinessStatus === "blocked") {
    return {
      confidence: "low",
      reason: "ФОТ по сменам не доказан: не закрыты сотрудники или ставки",
    };
  }

  if (!input.brief.revenue.comparisonAvailable) {
    return {
      confidence: "medium",
      reason: "есть live-данные, но пока нет честной базы сравнения",
    };
  }

  if (input.labor?.laborReadinessStatus === "partial") {
    return {
      confidence: "medium",
      reason: "ФОТ считается частично: часть сменной выручки без точных ставок",
    };
  }

  if (input.dataQuality.status === "watch") {
    return {
      confidence: "medium",
      reason: "данные рабочие, но часть метрик требует проверки",
    };
  }

  return {
    confidence: "high",
    reason: "есть live-данные, покрытие периода и база сравнения",
  };
}

function buildVerdict(input: {
  brief: DailyBrief;
  quality: RevenueDataQuality;
  dataMode: "live" | "mock";
  labor?: LaborBiSummary;
  margin?: MenuMarginReadiness;
  team?: TeamOpsReadiness;
  topCategory?: CategoryStat;
  topCategoryShare: number;
  topDish?: DishStat;
  topDishShare: number;
  volumeTrap?: DishStat | null;
}) {
  if (input.dataMode === "mock") {
    return {
      verdict:
        "Пока это демо-разбор. Подключите iiko, чтобы советы стали управленческими.",
      summary:
        "Интерфейс показывает логику работы, но не должен использоваться для решений по сменам, меню и деньгам.",
    };
  }

  if (input.quality.status === "risk") {
    return {
      verdict: "Сначала нужно проверить данные, иначе выводы будут шумными.",
      summary:
        "В периоде не хватает продаж или покрытия дней. До решений по команде и меню лучше открыть проверку iiko.",
    };
  }

  const laborIncomplete =
    Boolean(input.labor) && input.labor?.laborReadinessStatus !== "ready";
  const marginIncomplete =
    Boolean(input.margin) && input.margin?.status !== "ready";
  const laborPct = input.labor?.laborCostPct;
  const primaryMarginRisk = input.margin?.topMarginRisks[0] ?? null;
  const teamBlocked = input.team?.status === "blocked";

  if (laborIncomplete && marginIncomplete) {
    return {
      verdict: "Сначала нужно доказать экономику смены: ФОТ и маржа неполные.",
      summary:
        "Решения про прибыль, расписание и меню будут шумными, пока часть смен без точного ФОТ, а часть выручки без себестоимости.",
    };
  }

  if (
    laborPct !== null &&
    laborPct !== undefined &&
    laborPct >= 25 &&
    marginIncomplete
  ) {
    return {
      verdict: "ФОТ давит, а маржа пока не доказана.",
      summary:
        "Сначала закрыть себестоимость топ-позиций, затем решать: менять расписание, цену, порции или продажи в смене.",
    };
  }

  if (marginIncomplete) {
    return {
      verdict: "Прибыль периода пока не доказана: не хватает себестоимости.",
      summary:
        "Выручка есть, но без связки блюд с техкартами и закупочными ценами нельзя честно понять, что ресторан заработал.",
    };
  }

  if (laborIncomplete) {
    return {
      verdict: "ФОТ периода пока не доказан: часть смен без ставок.",
      summary:
        "Сначала закройте сотрудников и ставки в Team OS, иначе стоимость команды будет занижена.",
    };
  }

  if (teamBlocked) {
    return {
      verdict:
        "Смена не готова в Team OS: есть операционный блокер по команде.",
      summary:
        "Деньги можно смотреть, но смену нельзя считать управляемой, пока роли, допуски, ставки или срочные задачи не закрыты в Team OS.",
    };
  }

  if (primaryMarginRisk) {
    return {
      verdict: `У блюда «${primaryMarginRisk.dishName}» доказанная слабая маржа: ${primaryMarginRisk.grossMarginPct}%.`,
      summary:
        "Это уже не гипотеза без данных: цена продажи и себестоимость связаны. Проверьте порцию, состав техкарты, списания и цену, пока оборот не превращается в дорогую занятость кухни.",
    };
  }

  if (
    input.brief.revenue.comparisonAvailable &&
    input.brief.revenue.deltaPct <= -15
  ) {
    return {
      verdict:
        "Главная задача — найти причину просадки, а не просто смотреть график.",
      summary:
        "Сравните слабые дни, смены, стоп-лист и структуру продаж. Обычно деньги теряются в одном из этих мест.",
    };
  }

  if (input.topCategory && input.topCategoryShare >= 42) {
    return {
      verdict: `Выручка слишком сильно держится на категории «${input.topCategory.categoryName}».`,
      summary:
        "Это может быть силой, если маржа и наличие под контролем. Без проверки это риск для прибыли.",
    };
  }

  if (input.topDish && input.topDishShare >= 18) {
    return {
      verdict: `День заметно зависит от блюда «${input.topDish.dishName}».`,
      summary:
        "Проверьте заготовки, скорость отдачи и апсейл вокруг хита, чтобы не потерять вечернюю выручку.",
    };
  }

  if (input.volumeTrap) {
    return {
      verdict: `Есть позиция с большим объемом, но слабым вкладом в деньги.`,
      summary:
        "Такие блюда часто выглядят успешными по порциям, но не двигают чек. Их стоит проверить по цене, порции и апсейлу.",
    };
  }

  if (
    input.brief.revenue.comparisonAvailable &&
    input.brief.revenue.deltaPct >= 10
  ) {
    return {
      verdict:
        "Период выглядит сильнее базы. Важно зафиксировать, что сработало.",
      summary:
        "Рост надо превратить в повторяемый сценарий: смена, промо, посадка, погода, команда, меню.",
    };
  }

  return {
    verdict: "Критичного перекоса не видно. Фокус — маржа и дисциплина смен.",
    summary:
      "Даже спокойная выручка может скрывать дорогую себестоимость, слабый апсейл или лишний хвост меню.",
  };
}

export function buildOwnerReview(input: BuildOwnerReviewInput): OwnerReview {
  const categoryTotal = input.categories.reduce(
    (sum, category) => sum + category.dishSumInt,
    0,
  );
  const topCategory = [...input.categories].sort(
    (a, b) => b.dishSumInt - a.dishSumInt,
  )[0];
  const topCategoryShare = topCategory
    ? pct(topCategory.dishSumInt, categoryTotal)
    : 0;
  const topDish = input.dishes[0];
  const topDishShare = topDish
    ? pct(topDish.dishSumInt, input.summary.revenue)
    : 0;
  const weakestDay = topByRevenue(input.summary.points, "min");
  const strongestDay = topByRevenue(input.summary.points, "max");
  const weakestShift = [...input.shifts]
    .filter((shift) => shift.revenue > 0)
    .sort((a, b) => a.revenue - b.revenue)[0];
  const menu = buildMenuEngineering(input.dishes);
  const { confidence, reason } = confidenceFor(input);
  const laborInsights = input.labor ? buildLaborInsights(input.labor) : [];
  const primaryLaborInsight =
    laborInsights.find((insight) => insight.tone !== "good") ??
    laborInsights[0];
  const marginHypothesis = laborMarginHypothesis({
    labor: input.labor,
    margin: input.margin,
  });
  const operationalProof = buildOperationalProof(
    input.teamTasks,
    input.teamAuditEvents,
    input.teamStaff,
    input.teamAnnouncements,
    input.teamAnnouncementReads,
  );
  const operational = operationalPulse(operationalProof);
  const readiness = buildProfitReadiness({
    dataMode: input.dataMode,
    dataQuality: input.dataQuality,
    labor: input.labor,
    margin: input.margin,
    team: input.team,
    operationalProof,
  });
  const { verdict, summary } = buildVerdict({
    brief: input.brief,
    quality: input.dataQuality,
    dataMode: input.dataMode,
    labor: input.labor,
    margin: input.margin,
    team: input.team,
    topCategory,
    topCategoryShare,
    topDish,
    topDishShare,
    volumeTrap: menu.volumeTrap,
  });

  const evidence: OwnerReviewEvidence[] = [
    {
      label: "Деньги",
      value: formatRubles(input.summary.revenue),
      detail: `динамика: ${deltaText(input.brief)}`,
      tone:
        input.brief.revenue.comparisonAvailable &&
        input.brief.revenue.deltaPct < 0
          ? "risk"
          : "good",
    },
    ...(input.labor ? [laborEvidence(input.labor)] : []),
    ...(input.margin ? [marginEvidence(input.margin)] : []),
    ...(input.team ? [teamEvidence(input.team)] : []),
    ...(operationalProof ? [operationalProofEvidence(operationalProof)] : []),
    ...(() => {
      const evidence = operationalProof
        ? operationalCommunicationEvidence(operationalProof)
        : null;
      return evidence ? [evidence] : [];
    })(),
    ...(() => {
      const evidence = input.shiftPlanVariance
        ? shiftPlanVarianceEvidence(input.shiftPlanVariance)
        : null;
      return evidence ? [evidence] : [];
    })(),
    ...(() => {
      const evidence = unitEconomicsEvidence({
        labor: input.labor,
        margin: input.margin,
      });
      return evidence ? [evidence] : [];
    })(),
    {
      label: "Покрытие",
      value: `${input.dataQuality.activeDays}/${input.dataQuality.requestedDays}`,
      detail: input.dataQuality.summary,
      tone: input.dataQuality.status === "risk" ? "risk" : "watch",
    },
    {
      label: "Опора меню",
      value: topCategory ? `${topCategoryShare}%` : "нет данных",
      detail: topCategory
        ? `категория «${topCategory.categoryName}»`
        : "категории не пришли из BI",
      tone:
        topCategoryShare >= 42
          ? "risk"
          : topCategoryShare >= 30
            ? "watch"
            : "good",
    },
    {
      label: "Хит",
      value: topDish ? `${topDishShare}%` : "нет данных",
      detail: topDish
        ? `${topDish.dishName}, ${formatInteger(topDish.dishAmountInt)} порций`
        : "блюда не пришли из BI",
      tone: topDishShare >= 18 ? "watch" : "good",
    },
  ];
  const actions = [
    input.dataQuality.status === "risk" || input.dataMode === "mock"
      ? ({
          title: "Проверить источник данных",
          detail:
            input.dataMode === "mock"
              ? "Сейчас открыт демо-контур. Для решений нужен live iiko."
              : input.dataQuality.summary,
          role: "owner",
          tone: "risk",
          target: "iiko-settings",
        } satisfies OwnerReviewAction)
      : null,
    input.shiftPlanVariance
      ? ownerActionFromShiftPlanVariance(input.shiftPlanVariance)
      : null,
    ownerActionFromCommunication(operationalProof),
    input.labor ? ownerActionFromLabor(input.labor) : null,
    input.margin ? ownerActionFromMargin(input.margin) : null,
    input.team ? ownerActionFromTeam(input.team) : null,
  ]
    .filter((item): item is OwnerReviewAction => item !== null)
    .slice(0, 3);

  const hypotheses: OwnerReviewHypothesis[] = [];

  if (input.dataQuality.status === "risk" || input.dataMode === "mock") {
    hypotheses.push({
      title: "Данные могут подменять реальность",
      why:
        input.dataMode === "mock"
          ? "Сейчас включен демо-контур, поэтому выводы одинаковые по смыслу."
          : "В выбранном периоде не хватает продаж или дней с данными.",
      check:
        "Откройте проверку iiko и убедитесь, что ключ, организация и OLAP работают.",
      role: "owner",
      tone: "risk",
    });
  }

  if (primaryLaborInsight && primaryLaborInsight.tone !== "good") {
    hypotheses.push({
      title: primaryLaborInsight.title,
      why: primaryLaborInsight.detail,
      check: primaryLaborInsight.action,
      role: primaryLaborInsight.tone === "setup" ? "owner" : "manager",
      tone: ownerToneFromLabor(primaryLaborInsight.tone),
    });
  }

  if (marginHypothesis) {
    hypotheses.push(marginHypothesis);
  }

  const planVarianceHypothesis = input.shiftPlanVariance
    ? shiftPlanVarianceHypothesis(input.shiftPlanVariance)
    : null;
  if (planVarianceHypothesis) {
    hypotheses.push(planVarianceHypothesis);
  }

  if (
    input.brief.revenue.comparisonAvailable &&
    input.brief.revenue.deltaPct < -10
  ) {
    hypotheses.push({
      title: "Просадка могла прийти из смены, а не из меню",
      why: `Динамика к базе: ${deltaText(input.brief)}. ${
        weakestShift
          ? `Самая слабая смена: ${formatRubles(weakestShift.revenue)}.`
          : "Смены не дали явного ответа."
      }`,
      check:
        "Спросить управляющего: кто работал, какая была посадка, были ли стопы и жалобы.",
      role: "manager",
      tone: "risk",
    });
  }

  if (topCategory && topCategoryShare >= 30) {
    hypotheses.push({
      title: "Категория может держать оборот, но не прибыль",
      why: `«${topCategory.categoryName}» дает ${topCategoryShare}% выручки периода.`,
      check:
        "Проверить маржу, наличие, скорость отдачи и альтернативы для апсейла.",
      role: "chef",
      tone: topCategoryShare >= 42 ? "risk" : "watch",
    });
  }

  if (topDish && topDishShare >= 12) {
    hypotheses.push({
      title: "Хит продаж нужно защищать как операционный актив",
      why: `«${topDish.dishName}» дает ${topDishShare}% выручки и ${formatInteger(topDish.dishAmountInt)} порций.`,
      check:
        "Проверить стоп-лист, заготовки, качество отдачи и что официанты предлагают рядом.",
      role: "service",
      tone: topDishShare >= 18 ? "watch" : "good",
    });
  }

  if (menu.volumeTrap) {
    hypotheses.push({
      title: "Есть блюдо с большим объемом и слабым вкладом в чек",
      why: `«${menu.volumeTrap.dishName}» дает ${menu.volumeTrap.amountShare}% порций и ${menu.volumeTrap.revenueShare}% выручки.`,
      check: "Проверить цену, граммовку, подачу и возможность апсейла.",
      role: "chef",
      tone: "watch",
    });
  }

  if (hypotheses.length < 3 && weakestDay && strongestDay) {
    hypotheses.push({
      title: "Слабый день нужно объяснить событием",
      why: `${weakestDay.date}: ${formatRubles(weakestDay.revenue)} против ${strongestDay.date}: ${formatRubles(strongestDay.revenue)}.`,
      check:
        "Зафиксировать причину: погода, банкет, команда, промо, трафик, стоп-лист.",
      role: "manager",
      tone: "watch",
    });
  }

  const visibleHypotheses = hypotheses.slice(0, 4);
  const questions: OwnerReviewQuestion[] = visibleHypotheses.map((item) => ({
    role: item.role,
    text: item.check,
  }));
  const bridgeHypotheses = visibleHypotheses.filter((item) =>
    Boolean(item.taskSourceLabel),
  );
  const genericHypotheses = visibleHypotheses.filter(
    (item) => !item.taskSourceLabel,
  );
  const tasks = withoutAlreadyOpenTeamTasks(
    uniqueTaskDrafts([
      ...(() => {
        const task = taskFromLaborSetupProgress(input.laborSetupProgress);
        return task ? [task] : [];
      })(),
      ...actions.map(taskFromOwnerAction),
      ...bridgeHypotheses.map(taskFromHypothesis),
      ...genericHypotheses.map(taskFromHypothesis),
    ]),
    input.teamTasks,
  ).slice(0, 3);

  return {
    verdict,
    summary,
    confidence,
    confidenceReason: reason,
    readiness,
    operationalPulse: operational,
    evidence,
    actions,
    hypotheses: visibleHypotheses,
    questions,
    tasks,
  };
}
