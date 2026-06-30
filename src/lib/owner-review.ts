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
import {
  buildTeamFieldContextDigest,
  type TeamFieldContextDigest,
  type TeamFieldSignal,
} from "@/lib/team/team-field-context";
import type {
  TeamShiftPlanVarianceIssue,
  TeamShiftPlanVarianceSummary,
  TeamShiftPlanVarianceTone,
} from "@/lib/team/team-shift-plan-variance";
import type {
  TeamOpsActionTone,
  TeamOpsReadiness,
} from "@/lib/team/team-ops-readiness";
import { buildTeamTaskQueue, isOpenTeamTask } from "@/lib/team/team-task-queue";
import type {
  StaffMember,
  TeamAnnouncement,
  TeamAnnouncementRead,
  TeamAuditEvent,
  TeamTask,
  TeamTaskComment,
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
  taskTitle?: string;
  taskSourceLabel?: string;
  impactLabel?: string;
  learningModuleId?: string;
  learningModuleTitle?: string;
  learningChecklistTitle?: string;
  briefingQuestion?: string;
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
  impactLabel?: string;
  memberId?: string;
  memberName?: string;
  sourceLabel?: string;
  taskTitle?: string;
  learningModuleId?: string;
  learningModuleTitle?: string;
  learningChecklistTitle?: string;
  briefingQuestion?: string;
  existingTaskId?: string;
  existingTaskStatus?: TeamTask["status"];
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
  openTaskContours: string[];
  closedLoops: number;
  recentEvents: OwnerOperationalPulseEvent[];
  action: OwnerProfitReadinessAction;
};

export type OwnerOperationalProof = {
  openTasks: number;
  urgentOpenTasks: number;
  openTaskContours: string[];
  nextOpenTaskTitle: string | null;
  nextOpenTaskImpactLabel: string | null;
  closedLoops: number;
  lastClosedLoop: string | null;
  lastClosedLoopLabel: string | null;
  lastClosedLoopImpactLabel: string | null;
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
  teamComments?: TeamTaskComment[];
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

function joinSentences(parts: Array<string | null | undefined>): string {
  return parts.filter(Boolean).join(" ");
}

function revenueDropGapText(brief: DailyBrief): string | null {
  if (!brief.revenue.comparisonAvailable) return null;
  const gap = brief.revenue.previous - brief.revenue.current;
  if (gap <= 0) return null;
  return `Недобор к базе: ${formatRubles(gap)}.`;
}

function revenueDropImpactLabel(brief: DailyBrief): string | undefined {
  if (!brief.revenue.comparisonAvailable) return undefined;
  const gap = brief.revenue.previous - brief.revenue.current;
  return gap > 0 ? formatRubles(gap) : undefined;
}

function revenueGrowthImpactLabel(brief: DailyBrief): string | undefined {
  if (!brief.revenue.comparisonAvailable) return undefined;
  const growth = brief.revenue.current - brief.revenue.previous;
  return growth > 0 ? formatRubles(growth) : undefined;
}

function dayRevenueGapText(
  weakestDay: RevenuePoint | null,
  strongestDay: RevenuePoint | null,
): string | null {
  if (!weakestDay || !strongestDay) return null;
  const gap = strongestDay.revenue - weakestDay.revenue;
  if (gap <= 0) return null;
  return `Разница дня: ${formatRubles(gap)}.`;
}

function dayRevenueImpactLabel(
  weakestDay: RevenuePoint | null,
  strongestDay: RevenuePoint | null,
): string | undefined {
  if (!weakestDay || !strongestDay) return undefined;
  const gap = strongestDay.revenue - weakestDay.revenue;
  return gap > 0 ? formatRubles(gap) : undefined;
}

function shiftRevenueGap(
  weakestShift: ShiftStat | undefined,
  shifts: ShiftStat[],
): number {
  if (!weakestShift) return 0;
  const positiveShifts = shifts.filter((shift) => shift.revenue > 0);
  if (positiveShifts.length < 2) return 0;
  const average =
    positiveShifts.reduce((sum, shift) => sum + shift.revenue, 0) /
    positiveShifts.length;
  return Math.max(0, Math.round(average - weakestShift.revenue));
}

function shiftRevenueGapText(
  weakestShift: ShiftStat | undefined,
  shifts: ShiftStat[],
): string | null {
  const gap = shiftRevenueGap(weakestShift, shifts);
  if (gap <= 0) return null;
  return `Недобор слабой смены к средней смене периода: ${formatRubles(gap)}.`;
}

function shiftRevenueImpactLabel(
  weakestShift: ShiftStat | undefined,
  shifts: ShiftStat[],
): string | undefined {
  const gap = shiftRevenueGap(weakestShift, shifts);
  return gap > 0 ? formatRubles(gap) : undefined;
}

function formatShiftDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value.slice(0, 10);
  return new Intl.DateTimeFormat("ru-RU", {
    day: "numeric",
    month: "short",
  }).format(date);
}

function shiftTaskTitle(prefix: string, shift: ShiftStat | undefined): string {
  return shift ? `${prefix}: ${formatShiftDate(shift.openTime)}` : prefix;
}

function shiftCheckWithFieldContext(
  check: string,
  fieldHypothesis: OwnerReviewHypothesis | null,
): string {
  if (!fieldHypothesis) return check;
  return `${check} Сверить с полевым фактом: ${fieldHypothesis.title}.`;
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

function trimContextNote(value: string, limit = 420): string {
  const normalized = value.replace(/\s+/g, " ").trim();
  if (normalized.length <= limit) return normalized;
  return `${normalized.slice(0, Math.max(0, limit - 3)).trim()}...`;
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
  if (action.taskTitle) return trimTaskTitle(action.taskTitle);
  return trimTaskTitle(`${action.title}: ${action.detail}`);
}

function appendSentence(base: string, sentence: string): string {
  const trimmedBase = base.trim();
  const trimmedSentence = sentence.trim();
  if (!trimmedBase) return trimmedSentence;
  if (!trimmedSentence) return trimmedBase;
  const separator = /[.!?]$/.test(trimmedBase) ? " " : ". ";
  return `${trimmedBase}${separator}${trimmedSentence}`;
}

function withLearningContext({
  context,
  question,
  learningModuleTitle,
  checklistTitle,
  reason,
  limit = 420,
}: {
  context: string;
  question?: string | null;
  learningModuleTitle?: string;
  checklistTitle?: string | null;
  reason?: string | null;
  limit?: number;
}): string {
  const base = context.trim();
  const suffixParts = [
    question && !base.includes("Вопрос:") ? `Вопрос: ${question}.` : null,
    reason ? `Зачем: ${reason}.` : null,
    learningModuleTitle ? `Стандарт: ${learningModuleTitle}.` : null,
    checklistTitle ? `Чеклист: ${checklistTitle}.` : null,
  ].filter((item): item is string => Boolean(item));

  if (suffixParts.length === 0) return trimContextNote(base, limit);

  const suffix = suffixParts.join(" ");
  const fullContext = appendSentence(base, suffix);

  if (fullContext.length <= limit) return trimContextNote(fullContext, limit);

  const baseLimit = Math.max(0, limit - suffix.length - 5);
  return trimContextNote(
    appendSentence(`${base.slice(0, baseLimit).trim()}...`, suffix),
    limit,
  );
}

function taskReasonForSource(
  sourceLabel: string | undefined,
  impactLabel: string | undefined,
): string | null {
  if (sourceLabel === "Маржа и техкарты") {
    return impactLabel
      ? `закрыть ${impactLabel} выручки без понятной себестоимости`
      : "понять, где меню зарабатывает деньги, а где только делает оборот";
  }
  if (sourceLabel === "ФОТ и смены" || sourceLabel === "ФОТ и маржа") {
    return impactLabel
      ? `понять, сколько ${impactLabel} стоит смене и прибыли`
      : "связать выручку смены с реальной стоимостью команды";
  }
  if (sourceLabel === "Выручка и смены") {
    return impactLabel
      ? `найти причину недобора ${impactLabel}`
      : "понять, в какой смене теряется выручка";
  }
  if (sourceLabel === "Продажи и сервис") {
    return impactLabel
      ? `защитить ${impactLabel} выручки через сервис и апселл`
      : "превратить продажи в повторяемый стандарт сервиса";
  }
  if (sourceLabel === "Данные iiko") {
    return "не принимать управленческие решения на неполных данных";
  }
  if (sourceLabel === "Полевой контекст") {
    return "связать факты смены с BI, назначить ответственного и убрать повторяемую причину";
  }
  if (sourceLabel?.startsWith("ФОТ")) {
    return "доказать стоимость смен до выводов о прибыли";
  }
  if (sourceLabel === "Команда") {
    return "довести BI-решение до людей, иначе оно останется отчетом";
  }
  return null;
}

function taskQuestionForSource(sourceLabel: string | undefined): string | null {
  if (sourceLabel === "Маржа и техкарты") {
    return "какая цена, порция, списание или себестоимость объясняет провал маржи";
  }
  if (sourceLabel === "ФОТ и смены" || sourceLabel === "ФОТ и маржа") {
    return "какая смена, человек или ставка съедает прибыль";
  }
  if (sourceLabel === "Выручка и смены") {
    return "какая причина внутри смены объясняет просадку выручки";
  }
  if (sourceLabel === "Продажи и сервис") {
    return "что команда должна предложить гостю, чтобы поднять чек без давления";
  }
  if (sourceLabel === "Данные iiko") {
    return "каких данных не хватает, чтобы решать по фактам, а не по ощущению";
  }
  if (sourceLabel?.startsWith("ФОТ")) {
    return "какие ставки, смены или сотрудники мешают доверять расчету ФОТ";
  }
  if (sourceLabel === "Команда") {
    return "какое действие должен выполнить конкретный человек или роль";
  }
  return null;
}

function taskChecklistForSource(
  sourceLabel: string | undefined,
  learningModuleId: string | undefined,
): string | null {
  if (learningModuleId === "shift-open-close") {
    return "Если BI показал слабую смену";
  }
  if (
    learningModuleId === "shift-brief" &&
    sourceLabel === "Полевой контекст"
  ) {
    return "Разбор: факт, вопрос, проверка, действие";
  }
  if (
    learningModuleId === "iiko-cash-discipline" &&
    sourceLabel === "Данные iiko"
  ) {
    return "Если Receptor не видит смены iiko";
  }
  if (learningModuleId === "restaurant-numbers-basics") {
    return "Если BI показал перерасход ФОТ";
  }
  if (
    learningModuleId === "sales-eight-upsell" &&
    sourceLabel === "Продажи и сервис"
  ) {
    return "Если BI показал точку для апселла";
  }
  if (learningModuleId === "tech-card-discipline") {
    if (sourceLabel === "Маржа и техкарты" || sourceLabel === "ФОТ и маржа") {
      return "Если BI показал недобор валовой прибыли";
    }
  }
  return null;
}

function actionChecklistTitle(action: OwnerReviewAction): string | null {
  if (
    action.learningModuleId === "shift-open-close" &&
    action.target === "shift-plan-variance"
  ) {
    return "Если план и факт смен не совпали";
  }

  if (
    action.learningModuleId === "tech-card-discipline" &&
    action.target === "margin-diagnostics" &&
    action.detail.includes("ингредиент")
  ) {
    return "Если в техкарте нет цен ингредиентов";
  }

  return (
    action.learningChecklistTitle ??
    taskChecklistForSource(
      action.sourceLabel ?? actionSourceLabel(action),
      action.learningModuleId,
    )
  );
}

function hypothesisChecklistTitle(item: OwnerReviewHypothesis): string | null {
  if (
    item.learningModuleId === "tech-card-discipline" &&
    item.check.includes("ингредиент")
  ) {
    return "Если в техкарте нет цен ингредиентов";
  }

  return (
    item.learningChecklistTitle ??
    taskChecklistForSource(item.taskSourceLabel, item.learningModuleId)
  );
}

function withActionChecklist(action: OwnerReviewAction): OwnerReviewAction {
  const learningChecklistTitle = actionChecklistTitle(action);
  const briefingQuestion =
    action.briefingQuestion ??
    taskQuestionForSource(action.sourceLabel ?? actionSourceLabel(action));

  if (!learningChecklistTitle && !briefingQuestion) return action;

  return {
    ...action,
    ...(learningChecklistTitle ? { learningChecklistTitle } : {}),
    ...(briefingQuestion ? { briefingQuestion } : {}),
  };
}

function withHypothesisChecklist(
  item: OwnerReviewHypothesis,
): OwnerReviewHypothesis {
  const learningChecklistTitle = hypothesisChecklistTitle(item);
  const briefingQuestion =
    item.briefingQuestion ?? taskQuestionForSource(item.taskSourceLabel);

  if (!learningChecklistTitle && !briefingQuestion) return item;

  return {
    ...item,
    ...(learningChecklistTitle ? { learningChecklistTitle } : {}),
    ...(briefingQuestion ? { briefingQuestion } : {}),
  };
}

function actionContextNote(action: OwnerReviewAction): string {
  const sourceLabel = action.sourceLabel ?? actionSourceLabel(action);
  const context =
    sourceLabel === "Полевой контекст"
      ? fieldBriefingContext(action.detail, action.briefingQuestion)
      : action.detail.startsWith("Проверка:")
        ? action.detail
        : `Проверка: ${action.detail}`;
  return withLearningContext({
    context,
    learningModuleTitle: action.learningModuleTitle,
    checklistTitle:
      action.learningChecklistTitle ??
      taskChecklistForSource(sourceLabel, action.learningModuleId),
    question: action.briefingQuestion ?? taskQuestionForSource(sourceLabel),
    reason: taskReasonForSource(sourceLabel, action.impactLabel),
    limit: sourceLabel === "Полевой контекст" ? 900 : undefined,
  });
}

function taskFromOwnerAction(action: OwnerReviewAction): SurvivalTaskDraft {
  return {
    title: actionTaskTitle(action),
    priority: rolePriority(action.tone),
    roleId: roleTask(action.role),
    dueLabel: roleDue(action.role),
    impactLabel: action.impactLabel,
    contextNote: actionContextNote(action),
    sourceLabel: action.sourceLabel ?? actionSourceLabel(action),
    learningModuleId: action.learningModuleId,
    learningModuleTitle: action.learningModuleTitle,
    learningChecklistTitle: actionChecklistTitle(action) ?? undefined,
    audienceMemberId: action.memberId,
    audienceMemberName: action.memberName,
  };
}

function fieldBriefingContext(
  detail: string,
  question?: string | null,
): string {
  const checkMarker = " Проверка: ";
  const checkIndex = detail.indexOf(checkMarker);
  const rawFact =
    checkIndex >= 0 ? detail.slice(0, checkIndex).trim() : detail.trim();
  const rawCheck =
    checkIndex >= 0 ? detail.slice(checkIndex + checkMarker.length).trim() : "";
  const fact = rawFact.startsWith("Полевой факт:")
    ? rawFact
    : `Полевой факт: ${rawFact}`;

  if (!rawCheck) return fact;

  return `${fact} Вопрос: ${
    question ?? "что в смене объясняет эту цифру"
  }? Проверка: ${rawCheck}`;
}

function taskFromHypothesis(item: OwnerReviewHypothesis): SurvivalTaskDraft {
  const shouldLeadWithCheck =
    item.taskSourceLabel === "Выручка и смены" &&
    item.check.includes("Сверить с полевым фактом");
  const context =
    item.taskSourceLabel === "Полевой контекст"
      ? fieldBriefingContext(
          `${item.why} Проверка: ${item.check}`,
          item.briefingQuestion,
        )
      : shouldLeadWithCheck
        ? `Проверка: ${item.check} ${item.why}`
        : `${item.why} Проверка: ${item.check}`;

  return {
    title: item.taskTitle
      ? trimTaskTitle(item.taskTitle)
      : trimTaskTitle(item.check),
    priority: rolePriority(item.tone),
    roleId: roleTask(item.role),
    dueLabel: roleDue(item.role),
    impactLabel: item.impactLabel,
    contextNote: withLearningContext({
      context,
      learningModuleTitle: item.learningModuleTitle,
      checklistTitle: hypothesisChecklistTitle(item),
      question: item.briefingQuestion ?? taskQuestionForSource(item.taskSourceLabel),
      reason: taskReasonForSource(item.taskSourceLabel, item.impactLabel),
      limit: item.taskSourceLabel === "Полевой контекст" ? 900 : undefined,
    }),
    sourceLabel: item.taskSourceLabel ?? "Гипотеза",
    learningModuleId: item.learningModuleId,
    learningModuleTitle: item.learningModuleTitle,
    learningChecklistTitle: hypothesisChecklistTitle(item) ?? undefined,
    audienceMemberId: item.audienceMemberId,
    audienceMemberName: item.audienceMemberName,
  };
}

function taskFromLaborSetupProgress(
  progress: TeamLaborSetupProgress | undefined,
): SurvivalTaskDraft | null {
  if (!progress || progress.status === "ready") return null;

  if (progress.status === "needs-shifts") {
    const learningModuleTitle = "iiko и кассовая дисциплина на смене";
    const learningChecklistTitle = "Если Receptor не видит смены iiko";
    return {
      title:
        "Проверить выгрузку смен iiko для расчета ФОТ: без смен Receptor не видит сотрудников, часы и стоимость периода.",
      priority: "high",
      roleId: "operations_manager",
      dueLabel: "сегодня",
      sourceLabel: "ФОТ setup",
      learningModuleId: "iiko-cash-discipline",
      learningModuleTitle,
      learningChecklistTitle,
      contextNote: withLearningContext({
        context:
          "Проверка: смены iiko не пришли в ФОТ-контур, поэтому Receptor не может связать выручку с людьми, часами и стоимостью команды.",
        question:
          "каких прав, смен или фильтров iiko не хватает для расчета ФОТ",
        reason:
          "не принимать решения по сменам и прибыли без фактических смен iiko",
        learningModuleTitle,
        checklistTitle: learningChecklistTitle,
      }),
    };
  }

  const learningModuleTitle = "Цифры ресторана простым языком";
  const learningChecklistTitle = "Если ФОТ не считается полностью";

  if (progress.status === "needs-members") {
    return {
      title: trimTaskTitle(
        `Импортировать сотрудников из iiko в Team OS: ${progress.missingStaffCards} карточек не связано, ${formatRubles(progress.unpricedRevenue)} выручки без точного ФОТ.`,
      ),
      priority: "medium",
      roleId: "venue_manager",
      dueLabel: "сегодня",
      sourceLabel: "ФОТ setup",
      learningModuleId: "restaurant-numbers-basics",
      learningModuleTitle,
      learningChecklistTitle,
      contextNote: withLearningContext({
        context: `Проверка: ${progress.missingStaffCards} карточек сотрудников не связано с iiko, ${formatRubles(progress.unpricedRevenue)} выручки без точного ФОТ.`,
        question:
          "какие сотрудники iiko должны быть связаны с Team OS, чтобы ФОТ стал доказанным",
        reason:
          "видеть реальную стоимость команды в сменах, а не только выручку",
        learningModuleTitle,
        checklistTitle: learningChecklistTitle,
      }),
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
      learningModuleId: "restaurant-numbers-basics",
      learningModuleTitle,
      learningChecklistTitle,
      contextNote: withLearningContext({
        context: `Проверка: у ${firstRateTarget.name}${extraTargets > 0 ? ` и еще ${extraTargets}` : ""} нет ставки ФОТ, ${formatRubles(progress.unpricedRevenue)} выручки под вопросом.`,
        question:
          "какая ставка или роль нужна, чтобы корректно посчитать ФОТ смены",
        reason:
          "не завышать прибыль из-за незаполненной стоимости сотрудника",
        learningModuleTitle,
        checklistTitle: learningChecklistTitle,
      }),
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
    learningModuleId: "restaurant-numbers-basics",
    learningModuleTitle,
    learningChecklistTitle,
    contextNote: withLearningContext({
      context: `Проверка: ${progress.missingRateCards} сотрудников без ставки, ${formatRubles(progress.unpricedRevenue)} выручки под вопросом.`,
      question: "какие ставки нужно заполнить, чтобы ФОТ стал доказанным",
      reason: "не завышать прибыль из-за незаполненной стоимости команды",
      learningModuleTitle,
      checklistTitle: learningChecklistTitle,
    }),
  };
}

function openTaskContourLabels(tasks: TeamTask[]): string[] {
  return buildTeamTaskQueue(tasks)
    .openContours.slice(0, 3)
    .map(({ label, count }) => (count > 1 ? `${label} x${count}` : label));
}

function openTaskContourText(contours: string[]): string {
  if (contours.length === 0) return "";
  return ` Контуры: ${contours.join(", ")}.`;
}

function nextOpenTaskText(
  title: string | null,
  impactLabel?: string | null,
): string {
  if (!title) return "";
  const impactText = impactLabel
    ? ` Вес: ${trimEvidenceDetail(impactLabel)}.`
    : "";
  return ` Следующая задача: ${trimEvidenceDetail(title)}.${impactText}`;
}

function closedLoopResultText(proof: OwnerOperationalProof): string {
  if (proof.closedLoops <= 0) return "";
  const labelText = proof.lastClosedLoopLabel
    ? ` Контур: ${trimEvidenceDetail(proof.lastClosedLoopLabel)}.`
    : "";
  const impactText = proof.lastClosedLoopImpactLabel
    ? ` Вес: ${trimEvidenceDetail(proof.lastClosedLoopImpactLabel)}.`
    : "";
  const summaryText = proof.lastClosedLoop
    ? ` Последнее: ${trimEvidenceDetail(proof.lastClosedLoop)}.`
    : "";

  return `${proof.closedLoops} закрыто недавно.${labelText}${impactText}${summaryText}`;
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
  if (event.type === "task_created") return event.sourceLabel ?? "Задача";
  if (event.type === "comment_added") return "Комментарий";
  if (event.type === "announcement_created") return "Объявление";
  if (event.type === "task_status_updated") {
    if (event.sourceLabel) return event.sourceLabel;
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

function auditEventSummary(event: TeamAuditEvent): string {
  const summary = trimEvidenceDetail(event.summary);
  if (!event.impactLabel) return summary;
  return `${summary} Вес: ${trimEvidenceDetail(event.impactLabel)}.`;
}

function operationalPulseEvent(
  event: TeamAuditEvent,
): OwnerOperationalPulseEvent {
  return {
    label: auditEventLabel(event),
    summary: auditEventSummary(event),
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

  const taskQueue = buildTeamTaskQueue(tasks ?? []);
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
    openTasks: taskQueue.openCount,
    urgentOpenTasks: taskQueue.urgentOpenCount,
    openTaskContours: openTaskContourLabels(
      taskQueue.openTasks.map((item) => item.task),
    ),
    nextOpenTaskTitle: taskQueue.openTasks[0]?.task.title ?? null,
    nextOpenTaskImpactLabel: taskQueue.openTasks[0]?.task.impactLabel ?? null,
    closedLoops: closedLoopEvents.length,
    lastClosedLoop: closedLoopEvents[0]?.summary ?? null,
    lastClosedLoopLabel: closedLoopEvents[0]?.sourceLabel ?? null,
    lastClosedLoopImpactLabel: closedLoopEvents[0]?.impactLabel ?? null,
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
      detail: `${urgentTasksLabel(proof.urgentOpenTasks)} держат контур открытым.${openTaskContourText(proof.openTaskContours)}${nextOpenTaskText(proof.nextOpenTaskTitle, proof.nextOpenTaskImpactLabel)} Закройте их в Team OS, чтобы выводы владельца стали доказанными.`,
      tone: "risk",
      openTasks: proof.openTasks,
      urgentOpenTasks: proof.urgentOpenTasks,
      openTaskContours: proof.openTaskContours,
      closedLoops: proof.closedLoops,
      recentEvents: proof.recentEvents,
      action: { label: "Открыть Team OS", target: "team-actions" },
    };
  }

  if (proof.openTasks > 0) {
    return {
      title: "Контур в работе",
      detail: `${openTasksLabel(proof.openTasks)} еще ждут исполнения.${openTaskContourText(proof.openTaskContours)}${nextOpenTaskText(proof.nextOpenTaskTitle, proof.nextOpenTaskImpactLabel)} После закрытия задач владелец увидит это как управленческий результат.`,
      tone: "watch",
      openTasks: proof.openTasks,
      urgentOpenTasks: proof.urgentOpenTasks,
      openTaskContours: proof.openTaskContours,
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
      openTaskContours: proof.openTaskContours,
      closedLoops: proof.closedLoops,
      recentEvents: proof.recentEvents,
      action: { label: "Открыть связь", target: "team-journal" },
    };
  }

  if (proof.closedLoops > 0) {
    return {
      title: "Команда закрывает действия",
      detail: `${closedLoopResultText(
        proof,
      )} Экран владельца учитывает эти действия в готовности прибыли и операционном контуре.`,
      tone: "good",
      openTasks: proof.openTasks,
      urgentOpenTasks: proof.urgentOpenTasks,
      openTaskContours: proof.openTaskContours,
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
      openTaskContours: proof.openTaskContours,
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
    openTaskContours: proof.openTaskContours,
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
      ? `${closedLoopResultText(proof)}${nextOpenTaskText(
          proof.nextOpenTaskTitle,
          proof.nextOpenTaskImpactLabel,
        )}`
      : proof.openTasks > 0
        ? `${proof.urgentOpenTasks} срочных${proof.openTaskContours.length ? `: ${proof.openTaskContours.join(", ")}` : ""}.${nextOpenTaskText(proof.nextOpenTaskTitle, proof.nextOpenTaskImpactLabel)} Закрытые контуры появятся после выполнения задач в Team OS.`
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

function readinessCoverageLine(input: {
  dataMode: "live" | "mock";
  dataQuality: RevenueDataQuality;
  labor?: LaborBiSummary;
  margin?: MenuMarginReadiness;
}): string {
  const sales =
    input.dataMode === "mock"
      ? "продажи в демо"
      : `продажи ${formatCoverage(input.dataQuality.coveragePct)}`;
  const labor =
    input.labor?.revenueCoveragePct !== null &&
    input.labor?.revenueCoveragePct !== undefined
      ? `ФОТ ${formatCoverage(input.labor.revenueCoveragePct)} выручки`
      : "ФОТ без покрытия";
  const margin = input.margin
    ? `себестоимость ${formatCoverage(input.margin.revenueCoveragePct)} выручки`
    : "себестоимость без покрытия";

  return `Покрытие: ${sales}, ${labor}, ${margin}.`;
}

function announcementCountLabel(count: number): string {
  return `${count} ${taskWord(count, "объявление", "объявления", "объявлений")}`;
}

function announcementReadLabel(count: number): string {
  return `${count} ${taskWord(count, "прочтение", "прочтения", "прочтений")}`;
}

function laborMissingReadinessLabel(labor: LaborBiSummary): string {
  if (labor.staffShifts === 0) return "смены iiko для ФОТ";
  const blocker = labor.topBlockers[0];
  if (blocker?.reason === "missing-member") return "карточки сотрудников из iiko";
  if (blocker?.reason === "missing-rate") return "точные ставки ФОТ";
  return "сотрудники и ставки ФОТ";
}

function laborReadinessAction(labor: LaborBiSummary): OwnerProfitReadinessAction {
  if (labor.staffShifts === 0) {
    return { label: "Проверить смены", target: "shift-coverage" };
  }

  const blocker = labor.topBlockers[0];
  if (blocker?.reason === "missing-member") {
    return { label: "Добавить сотрудника", target: "labor-member" };
  }

  if (blocker?.reason === "missing-rate") {
    return { label: "Заполнить ставку", target: "labor-rate" };
  }

  return { label: "Заполнить ФОТ", target: "labor-rate" };
}

function marginMissingReadinessLabel(margin: MenuMarginReadiness): string {
  const strongestBlocker = Math.max(
    margin.missingLinkRevenue,
    margin.missingProductCostRevenue,
    margin.missingTechCardPriceRevenue,
  );

  if (
    margin.missingTechCardPriceRevenue > 0 &&
    margin.missingTechCardPriceRevenue === strongestBlocker
  ) {
    return "цены ингредиентов техкарт";
  }

  if (
    margin.missingProductCostRevenue > 0 &&
    margin.missingProductCostRevenue === strongestBlocker
  ) {
    return "закупочные цены товаров";
  }

  if (margin.missingLinkRevenue > 0) {
    return "связи блюд с iiko";
  }

  return "закупочные цены и техкарты";
}

function marginReadinessAction(
  margin: MenuMarginReadiness,
): OwnerProfitReadinessAction {
  const strongestBlocker = Math.max(
    margin.missingLinkRevenue,
    margin.missingProductCostRevenue,
    margin.missingTechCardPriceRevenue,
  );

  if (
    margin.missingTechCardPriceRevenue > 0 &&
    margin.missingTechCardPriceRevenue === strongestBlocker
  ) {
    return { label: "Закрыть цены техкарт", target: "margin-diagnostics" };
  }

  if (
    margin.missingProductCostRevenue > 0 &&
    margin.missingProductCostRevenue === strongestBlocker
  ) {
    return { label: "Проверить цены RMS", target: "margin-diagnostics" };
  }

  return { label: "Связать блюда", target: "margin-mapping" };
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
    missing.push("реальные данные iiko");
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
    missing.push(laborMissingReadinessLabel(input.labor));
    setAction(laborReadinessAction(input.labor));
  } else {
    missing.push(laborMissingReadinessLabel(input.labor));
    setAction(laborReadinessAction(input.labor));
  }

  if (!input.margin) {
    missing.push("себестоимость блюд");
    setAction({ label: "Связать блюда", target: "margin-mapping" });
  } else if (input.margin.status === "ready") {
    score += 35;
  } else if (input.margin.status === "partial") {
    score += 18;
    missing.push(marginMissingReadinessLabel(input.margin));
    setAction(marginReadinessAction(input.margin));
  } else {
    missing.push(marginMissingReadinessLabel(input.margin));
    setAction(marginReadinessAction(input.margin));
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
      detail:
        "Реальные данные iiko, ФОТ, себестоимость и Team OS контуры закрыты.",
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
      detail: `${readinessCoverageLine(input)} Проверить: ${compactMissing(missing)}. После закрытия контуров выводы можно превращать в задачи.`,
      missing,
      action,
      tone: "watch",
    };
  }

  return {
    status,
    score: roundedScore,
    title: "Прибыль не доказана",
    detail: `${readinessCoverageLine(input)} Не хватает: ${compactMissing(missing)}. До этого решения по прибыли лучше держать как гипотезы.`,
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
  const titleMatches =
    normalizeTaskTitle(task.title) === normalizeTaskTitle(draft.title);
  const contourMatches =
    draft.sourceLabel !== "Выручка и смены" &&
    Boolean(draft.sourceLabel) &&
    draft.sourceLabel === task.sourceLabel;

  if (draft.audienceMemberId) {
    return (
      task.audience.type === "member" &&
      task.audience.memberId === draft.audienceMemberId &&
      (titleMatches || contourMatches)
    );
  }

  return (
    task.audience.type === "role" &&
    task.audience.roleId === draft.roleId &&
    (titleMatches || contourMatches)
  );
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

function taskDraftForAction(action: OwnerReviewAction): SurvivalTaskDraft {
  return taskFromOwnerAction(action);
}

function openTaskForDraft(
  draft: SurvivalTaskDraft,
  tasks: TeamTask[] | undefined,
): TeamTask | null {
  if (!tasks?.length) return null;
  return tasks.find((task) => draftMatchesOpenTeamTask(draft, task)) ?? null;
}

function markActionsWithOpenTasks(
  actions: OwnerReviewAction[],
  tasks: TeamTask[] | undefined,
): OwnerReviewAction[] {
  if (!tasks?.length) return actions;

  return actions.map((action) => {
    const existingTask = openTaskForDraft(taskDraftForAction(action), tasks);
    return existingTask
      ? {
          ...action,
          existingTaskId: existingTask.id,
          existingTaskStatus: existingTask.status,
        }
      : action;
  });
}

function impactScore(label: string | undefined): number {
  if (!label) return 0;
  const match = label
    .replace(/\s/g, "")
    .replace(",", ".")
    .match(/\d+(?:\.\d+)?/);
  if (!match) return 0;
  const value = Number(match[0]);
  if (!Number.isFinite(value)) return 0;
  return label.includes("%") ? value * 1_000 : value;
}

function targetScore(target: OwnerReviewActionTarget): number {
  if (target === "iiko-settings") return 900_000;
  if (
    target === "margin-diagnostics" ||
    target === "margin-mapping" ||
    target === "margin-risk"
  ) {
    return 70_000;
  }
  if (
    target === "labor-member" ||
    target === "labor-rate" ||
    target === "shift-coverage" ||
    target === "shift-diagnostics" ||
    target === "shift-plan-variance"
  ) {
    return 65_000;
  }
  if (target === "shift-plan") return 55_000;
  if (target === "team-actions") return 45_000;
  if (target === "team-learning") return 35_000;
  if (target === "team-journal") return 30_000;
  return 0;
}

function toneScore(tone: OwnerReviewTone): number {
  if (tone === "risk") return 1_000_000;
  if (tone === "watch") return 500_000;
  return 0;
}

function actionPriorityScore(action: OwnerReviewAction): number {
  return (
    toneScore(action.tone) +
    targetScore(action.target) +
    impactScore(action.impactLabel)
  );
}

function sortOwnerActions(actions: OwnerReviewAction[]): OwnerReviewAction[] {
  return actions
    .map((action, index) => ({ action, index }))
    .sort((a, b) => {
      const scoreDelta =
        actionPriorityScore(b.action) - actionPriorityScore(a.action);
      return scoreDelta || a.index - b.index;
    })
    .map(({ action }) => action);
}

function hypothesisSourceScore(sourceLabel: string | undefined): number {
  if (sourceLabel === "Данные iiko") return 900_000;
  if (sourceLabel === "Маржа и техкарты") return 70_000;
  if (sourceLabel === "ФОТ и смены") return 65_000;
  if (sourceLabel === "Полевой контекст") return 62_000;
  if (sourceLabel === "Выручка и смены") return 60_000;
  if (sourceLabel === "Продажи и сервис") return 50_000;
  return 0;
}

function hypothesisPriorityScore(item: OwnerReviewHypothesis): number {
  return (
    toneScore(item.tone) +
    hypothesisSourceScore(item.taskSourceLabel) +
    impactScore(item.impactLabel)
  );
}

function sortOwnerHypotheses(
  hypotheses: OwnerReviewHypothesis[],
): OwnerReviewHypothesis[] {
  return hypotheses
    .map((item, index) => ({ item, index }))
    .sort((a, b) => {
      const scoreDelta =
        hypothesisPriorityScore(b.item) - hypothesisPriorityScore(a.item);
      return scoreDelta || a.index - b.index;
    })
    .map(({ item }) => item);
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

function isRevenueShiftTask(draft: SurvivalTaskDraft): boolean {
  return draft.sourceLabel === "Выручка и смены";
}

function isFieldContextTask(draft: SurvivalTaskDraft): boolean {
  return draft.sourceLabel === "Полевой контекст";
}

function keepOperationalTaskDraftsVisible(
  drafts: SurvivalTaskDraft[],
): SurvivalTaskDraft[] {
  const firstDraft = drafts[0];
  if (!firstDraft) return drafts;

  const promotedIndexes = new Set<number>();
  const promoted: SurvivalTaskDraft[] = [];
  const promote = (predicate: (draft: SurvivalTaskDraft) => boolean) => {
    const index = drafts.findIndex(predicate);
    if (index === -1 || index === 0 || promotedIndexes.has(index)) return;

    promotedIndexes.add(index);
    promoted.push(drafts[index]);
  };

  promote(isFieldContextTask);
  promote(isRevenueShiftTask);

  if (promoted.length === 0) return drafts;

  return [
    firstDraft,
    ...promoted,
    ...drafts.filter((_, index) => index !== 0 && !promotedIndexes.has(index)),
  ];
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
  const bridge =
    labor && margin
      ? buildLaborMarginBridge({
          labor,
          margin,
        })
      : null;
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
      detail: bridge
        ? `${bridge.title}: ФОТ покрыт на ${laborCoverage}, маржа на ${marginCoverage} выручки.`
        : `ФОТ покрыт на ${laborCoverage}, маржа на ${marginCoverage} выручки.`,
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
      detail: bridge
        ? bridge.detail
        : `${formatRubles(margin.blockedRevenue)} выручки без себестоимости.`,
      tone: margin.status === "blocked" ? "risk" : "watch",
    };
  }

  if (laborPct !== null && laborPct >= 25) {
    return {
      label: "Экономика",
      value: "ФОТ давит",
      detail:
        bridge && bridge.tone !== "good"
          ? bridge.detail
          : `ФОТ ${formatCoverage(laborPct)} от выручки, маржа покрыта на ${marginCoverage}.`,
      tone: "risk",
    };
  }

  return {
    label: "Экономика",
    value: bridge?.tone === "good" ? "связана" : "можно считать",
    detail:
      bridge?.tone === "good"
        ? bridge.detail
        : `ФОТ ${formatCoverage(laborPct)}, маржа покрыта на ${marginCoverage}.`,
    tone: bridge ? ownerToneFromLaborBridge(bridge.tone) : "good",
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

function fieldCountLabel(
  count: number,
  single: string,
  plural: string,
): string {
  return count === 1 ? `1 ${single}` : `${count} ${plural}`;
}

function fieldContextEvidence(
  digest: TeamFieldContextDigest,
): OwnerReviewEvidence {
  const hasHardSignal = digest.signals.some(
    (signal) =>
      signal.kind === "conflict" ||
      signal.kind === "stock" ||
      signal.kind === "team",
  );

  return {
    label: "Поле",
    value:
      digest.signalCount > 0
        ? fieldCountLabel(digest.signalCount, "сигнал", "сигналов")
        : fieldCountLabel(digest.totalNotes, "заметка", "заметок"),
    detail: digest.summary,
    tone: hasHardSignal ? "risk" : "watch",
  };
}

function fieldContextHypothesis(
  digest: TeamFieldContextDigest | null,
): OwnerReviewHypothesis | null {
  if (!digest) return null;
  const signal = digest.signals[0];
  if (!signal) {
    return {
      title: "Связать полевую заметку с цифрами",
      why: digest.summary,
      check:
        "На утреннем брифинге выбрать одну цифру, которая подтверждает или опровергает заметку: выручка, ФОТ, маржа, стоп-лист или отзывы гостей.",
      role: "manager",
      tone: "watch",
      taskSourceLabel: "Полевой контекст",
      taskTitle: "Связать полевую заметку с цифрами",
      briefingQuestion:
        "какая цифра подтверждает этот факт: выручка, ФОТ, маржа, стоп-лист или отзывы гостей",
      impactLabel:
        digest.totalNotes > 1 ? `${digest.totalNotes} заметки` : "1 заметка",
      learningModuleId: "shift-brief",
      learningModuleTitle: "Брифинг смены и передача контекста",
      learningChecklistTitle: "Разбор: факт, вопрос, проверка, действие",
    };
  }
  const task = fieldContextTaskFor(signal.kind);
  const relatedSignals = digest.signals.slice(1);
  const relatedLine =
    relatedSignals.length > 0
      ? ` Связанные факты: ${relatedSignals
          .map((item) => `${item.title} (${item.sourceCount})`)
          .join(", ")}.`
      : "";

  return {
    title: task.title,
    why: `${signal.detail}${relatedLine}`,
    check: task.check,
    role: "manager",
    tone:
      signal.kind === "conflict" ||
      signal.kind === "stock" ||
      signal.kind === "team"
        ? "risk"
        : "watch",
    taskSourceLabel: "Полевой контекст",
    taskTitle: task.title,
    briefingQuestion: task.question,
    impactLabel:
      digest.signalCount > 1 ? `${digest.signalCount} сигнала` : "1 сигнал",
    learningModuleId: task.learningModuleId,
    learningModuleTitle: task.learningModuleTitle,
    learningChecklistTitle: task.checklistTitle,
  };
}

function fieldContextTaskFor(kind: TeamFieldSignal["kind"]): {
  title: string;
  question: string;
  checklistTitle: string;
  check: string;
  learningModuleId: string;
  learningModuleTitle: string;
} {
  if (kind === "conflict") {
    return {
      title: "Разобрать конфликт смены с цифрами",
      question: "что стало причиной конфликта и повторяется ли это в сменах",
      checklistTitle: "Если полевая заметка про конфликт",
      check:
        "На брифинге уточнить причину конфликта, стол/блюдо/время ожидания и проверить, повлияло ли это на возвраты, скидки или повторные жалобы.",
      learningModuleId: "shift-brief",
      learningModuleTitle: "Брифинг смены и передача контекста",
    };
  }
  if (kind === "stock") {
    return {
      title: "Проверить стоп-лист и потерянные продажи",
      question:
        "что закончилось, сколько продаж потеряли и кто отвечает за запас",
      checklistTitle: "Если полевая заметка про стоп-лист",
      check:
        "Сверить, какие позиции закончились, сколько они давали выручки в периоде и кто отвечает за заказ, заготовки и вечерний стоп-лист.",
      learningModuleId: "shift-brief",
      learningModuleTitle: "Брифинг смены и передача контекста",
    };
  }
  if (kind === "team") {
    return {
      title: "Снять трение команды перед сменой",
      question: "где команда теряет время и какой один стандарт снимет трение",
      checklistTitle: "Разбор: факт, вопрос, проверка, действие",
      check:
        "Спросить, где команда теряет время или путается, и превратить ответ в один чеклист, задачу или короткое обучение по роли.",
      learningModuleId: "shift-brief",
      learningModuleTitle: "Брифинг смены и передача контекста",
    };
  }
  if (kind === "event") {
    return {
      title: "Связать событие с выручкой смены",
      question: "что в событии надо повторить или исправить перед похожим днем",
      checklistTitle: "Разбор: факт, вопрос, проверка, действие",
      check:
        "Уточнить посадку, событие, состав смены и средний чек, чтобы понять, что повторить или исправить перед похожим днем.",
      learningModuleId: "shift-brief",
      learningModuleTitle: "Брифинг смены и передача контекста",
    };
  }
  if (kind === "guest") {
    return {
      title: "Проверить частый вопрос гостей",
      question:
        "какой запрос гостей стоит превратить в меню, скрипт или обучение",
      checklistTitle: "Если BI показал точку для апселла",
      check:
        "Посчитать, повторяется ли запрос гостей, и решить: добавить позицию, подготовить скрипт официантам или вынести ответ в меню.",
      learningModuleId: "sales-eight-upsell",
      learningModuleTitle: "Восьмерка продаж и апселл в сервисе",
    };
  }
  return {
    title: "Проверить сервис и допродажи",
    question:
      "что команда реально рекомендовала гостям и где нужен простой скрипт",
    checklistTitle: "Если BI показал точку для апселла",
    check:
      "На брифинге разобрать, что команда рекомендовала гостям, какие позиции продавались лучше и где нужен простой скрипт допродажи.",
    learningModuleId: "sales-eight-upsell",
    learningModuleTitle: "Восьмерка продаж и апселл в сервисе",
  };
}

function ownerActionFromFieldContext(
  digest: TeamFieldContextDigest | null,
): OwnerReviewAction | null {
  const hypothesis = fieldContextHypothesis(digest);
  if (!hypothesis) return null;

  return {
    title: hypothesis.taskTitle ?? hypothesis.title,
    detail: `${hypothesis.why} Проверка: ${hypothesis.check}`,
    role: hypothesis.role,
    tone: hypothesis.tone,
    target: "team-actions",
    impactLabel: hypothesis.impactLabel,
    sourceLabel: hypothesis.taskSourceLabel,
    taskTitle: hypothesis.taskTitle,
    learningModuleId: hypothesis.learningModuleId,
    learningModuleTitle: hypothesis.learningModuleTitle,
    learningChecklistTitle: hypothesis.learningChecklistTitle,
    briefingQuestion: hypothesis.briefingQuestion,
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
    taskTitle: shiftPlanVarianceActionTitle(primaryIssue),
    impactLabel:
      primaryIssue.laborDelta !== 0
        ? formatRubles(Math.abs(primaryIssue.laborDelta))
        : primaryIssue.dateLabel,
    learningModuleId: "shift-open-close",
    learningModuleTitle: "Открытие и закрытие смены без хаоса",
    learningChecklistTitle: "Если план и факт смен не совпали",
    briefingQuestion:
      "какое отклонение графика изменило ФОТ или нагрузку смены",
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
    taskSourceLabel: "ФОТ и смены",
    taskTitle: shiftPlanVarianceActionTitle(primaryIssue),
    impactLabel:
      primaryIssue.laborDelta !== 0
        ? formatRubles(Math.abs(primaryIssue.laborDelta))
        : primaryIssue.dateLabel,
    learningModuleId: "shift-open-close",
    learningModuleTitle: "Открытие и закрытие смены без хаоса",
    learningChecklistTitle: "Если план и факт смен не совпали",
    briefingQuestion:
      "какое отклонение графика изменило ФОТ или нагрузку смены",
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

function laborEmployeeImpact(
  issue: ReturnType<typeof buildLaborEmployeeDiagnostics>[number],
): string {
  if (issue.laborOverTarget && issue.laborOverTarget > 0) {
    return formatRubles(issue.laborOverTarget);
  }
  if (issue.laborCostPct !== null) {
    return `ФОТ ${formatCoverage(issue.laborCostPct)}`;
  }
  if (issue.sales > 0) return formatRubles(issue.sales);
  return `${issue.shifts} смен`;
}

function laborShiftImpact(shift: {
  laborCostPct: number | null;
  laborOverTarget?: number | null;
  revenue: number;
  staffCount: number;
}): string {
  if (shift.laborOverTarget && shift.laborOverTarget > 0) {
    return formatRubles(shift.laborOverTarget);
  }
  if (shift.laborCostPct !== null) {
    return `ФОТ ${formatCoverage(shift.laborCostPct)}`;
  }
  if (shift.revenue > 0) return formatRubles(shift.revenue);
  return `${shift.staffCount} сотрудников`;
}

function laborNumbersLearningHint(): Pick<
  OwnerReviewAction,
  "learningModuleId" | "learningModuleTitle"
> {
  return {
    learningModuleId: "restaurant-numbers-basics",
    learningModuleTitle: "Цифры ресторана простым языком",
  };
}

function iikoCashLearningHint(): Pick<
  OwnerReviewAction,
  "learningModuleId" | "learningModuleTitle"
> {
  return {
    learningModuleId: "iiko-cash-discipline",
    learningModuleTitle: "iiko и кассовая дисциплина на смене",
  };
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
        impactLabel: laborEmployeeImpact(firstLinkedEmployeeIssue),
        memberId: firstLinkedEmployeeIssue.memberId,
        memberName: firstLinkedEmployeeIssue.name,
        ...laborNumbersLearningHint(),
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
      impactLabel: laborShiftImpact(firstShiftIssue),
      ...laborNumbersLearningHint(),
    };
  }

  if (nextAction.kind === "missing-shifts") {
    return {
      title: nextAction.title,
      detail: nextAction.detail,
      role: "owner",
      tone: "watch",
      target: "iiko-settings",
      impactLabel: `${input.shifts} смен`,
      ...iikoCashLearningHint(),
    };
  }

  if (nextAction.kind === "missing-member" && nextAction.blocker) {
    return {
      title: nextAction.title,
      detail: nextAction.detail,
      role: "manager",
      tone: "watch",
      target: "labor-member",
      impactLabel: formatRubles(nextAction.blocker.sales),
      memberName: nextAction.blocker.name,
      ...laborNumbersLearningHint(),
    };
  }

  if (nextAction.kind === "missing-rate" && nextAction.blocker) {
    return {
      title: nextAction.title,
      detail: nextAction.detail,
      role: "manager",
      tone: "watch",
      target: "labor-rate",
      impactLabel: formatRubles(nextAction.blocker.sales),
      memberId: nextAction.blocker.memberId,
      memberName: nextAction.blocker.name,
      ...laborNumbersLearningHint(),
    };
  }

  if (nextAction.kind === "expensive-labor" && firstLinkedEmployeeIssue) {
    return {
      title: firstLinkedEmployeeIssue.title,
      detail: firstLinkedEmployeeIssue.detail,
      role: "manager",
      tone: ownerToneFromLabor(firstLinkedEmployeeIssue.tone),
      target: "labor-member",
      impactLabel: laborEmployeeImpact(firstLinkedEmployeeIssue),
      memberId: firstLinkedEmployeeIssue.memberId,
      memberName: firstLinkedEmployeeIssue.name,
      ...laborNumbersLearningHint(),
    };
  }

  if (nextAction.kind === "expensive-labor") {
    return {
      title: nextAction.title,
      detail: nextAction.detail,
      role: "manager",
      tone: "risk",
      target: "shift-diagnostics",
      impactLabel: nextAction.impactLabel,
      ...laborNumbersLearningHint(),
    };
  }

  if (nextAction.kind === "low-productivity") {
    return {
      title: nextAction.title,
      detail: nextAction.detail,
      role: "manager",
      tone: "watch",
      target: "shift-diagnostics",
      impactLabel: nextAction.shift
        ? laborShiftImpact(nextAction.shift)
        : undefined,
      sourceLabel: "ФОТ и смены",
      taskTitle: nextAction.title,
      ...laborNumbersLearningHint(),
    };
  }

  return null;
}

function ownerActionFromMargin(
  input: MenuMarginReadiness,
): OwnerReviewAction | null {
  const nextAction = buildMenuMarginNextAction(input);
  const primaryRisk = input.topMarginRisks[0] ?? null;
  const learning = marginLearningHint();

  if (nextAction.kind === "ready") {
    if (!primaryRisk) return null;
    const source =
      primaryRisk.costSource === "tech-card" ? "по техкарте" : "по товару iiko";
    const profitGapText =
      primaryRisk.grossProfitGapToTarget > 0
        ? ` Недобор валовой прибыли к цели: ${formatRubles(primaryRisk.grossProfitGapToTarget)}.`
        : "";

    return {
      title: `Разобрать маржу: ${primaryRisk.dishName}`,
      detail: `Валовая маржа ${primaryRisk.grossMarginPct}%: цена ${formatRubles(primaryRisk.salePrice)}, себестоимость ${formatRubles(primaryRisk.costReference)} ${source}.${profitGapText} Проверьте цену, порцию, списания и состав техкарты.`,
      role: "chef",
      tone: primaryRisk.grossMarginPct < 45 ? "risk" : "watch",
      target: "margin-risk",
      sourceLabel: "Маржа и техкарты",
      taskTitle: `Разобрать маржу: ${primaryRisk.dishName}`,
      learningChecklistTitle: "Если BI показал недобор валовой прибыли",
      briefingQuestion:
        "какая цена, порция, списание или себестоимость объясняет провал маржи",
      impactLabel:
        primaryRisk.grossProfitGapToTarget > 0
          ? formatRubles(primaryRisk.grossProfitGapToTarget)
          : `маржа ${primaryRisk.grossMarginPct}%`,
      ...learning,
    };
  }

  const missingTechCardPrices =
    nextAction.kind === "missing-cost" && Boolean(nextAction.blocker?.hasTechCard);
  const learningChecklistTitle = missingTechCardPrices
    ? "Если в техкарте нет цен ингредиентов"
    : "Если BI показал недобор валовой прибыли";
  const briefingQuestion = missingTechCardPrices
    ? "каким ингредиентам не хватает закупочной цены и почему RMS не доказывает food cost"
    : "каких связей, техкарт или закупочных цен не хватает, чтобы доверять марже";

  return {
    title: nextAction.title,
    detail: nextAction.detail,
    role: nextAction.kind === "missing-cost" ? "owner" : "chef",
    tone: input.status === "blocked" ? "risk" : "watch",
    impactLabel: nextAction.blocker
      ? formatRubles(nextAction.blocker.revenue)
      : `${input.revenueCoveragePct}%`,
    target:
      nextAction.kind === "missing-cost"
        ? "margin-diagnostics"
        : "margin-mapping",
    sourceLabel: "Маржа и техкарты",
    taskTitle: nextAction.title,
    learningChecklistTitle,
    briefingQuestion,
    ...learning,
  };
}

function marginLearningHint(): Pick<
  OwnerReviewAction,
  "learningModuleId" | "learningModuleTitle"
> {
  return {
    learningModuleId: "tech-card-discipline",
    learningModuleTitle: "Техкарта как договор внутри команды",
  };
}

function ownerActionFromLaborMargin(input: {
  labor?: LaborBiSummary;
  margin?: MenuMarginReadiness;
}): OwnerReviewAction | null {
  if (!input.labor || !input.margin) return null;

  const bridge = buildLaborMarginBridge({
    labor: input.labor,
    margin: input.margin,
  });
  if (bridge.tone === "good") return null;

  const marginAction = buildMenuMarginNextAction(input.margin);
  const target: OwnerReviewActionTarget = bridge.employee?.memberId
    ? "labor-member"
    : bridge.employee
      ? "shift-diagnostics"
      : marginAction.kind === "missing-cost"
        ? "margin-diagnostics"
        : marginAction.kind === "ready"
          ? "margin-risk"
          : "margin-mapping";

  return {
    title: bridge.title,
    detail: bridge.detail,
    role: bridge.employee
      ? "manager"
      : bridge.tone === "setup"
        ? "chef"
        : "owner",
    tone: ownerToneFromLaborBridge(bridge.tone),
    target,
    impactLabel:
      bridge.employee?.laborCostPct !== null &&
      bridge.employee?.laborCostPct !== undefined
        ? `ФОТ ${formatCoverage(bridge.employee.laborCostPct)}`
        : bridge.employee
          ? formatRubles(bridge.employee.sales)
          : marginAction.blocker
            ? formatRubles(marginAction.blocker.revenue)
            : `${bridge.marginCoveragePct}% маржа`,
    memberId: bridge.employee?.memberId,
    memberName: bridge.employee?.name,
    sourceLabel: "ФОТ и маржа",
    learningModuleId: "tech-card-discipline",
    learningModuleTitle: "Техкарта как договор внутри команды",
    learningChecklistTitle: "Если BI показал недобор валовой прибыли",
    briefingQuestion:
      "какая цена, порция, списание, ставка или состав смены объясняет разрыв прибыли",
    taskTitle: bridge.employee
      ? `Разобрать ФОТ и маржу: ${bridge.employee.name}`
      : bridge.marginRiskDish
        ? `Разобрать ФОТ и маржу: ${bridge.marginRiskDish}`
        : "Доказать ФОТ и маржу периода",
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
  const isLearningAction = action.id === "learning";

  return {
    title: action.title,
    detail: action.detail,
    role: "manager",
    tone: ownerToneFromTeam(action.tone),
    target: teamActionTarget(action.href),
    impactLabel: `${input.score}% готово`,
    learningModuleId: action.learningModuleId,
    learningModuleTitle: action.learningModuleTitle,
    briefingQuestion: isLearningAction
      ? "какой обязательный модуль мешает сотруднику выйти в смену"
      : undefined,
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
      taskTitle: bridge.employee
        ? `Разобрать ФОТ и маржу: ${bridge.employee.name}`
        : bridge.marginRiskDish
          ? `Разобрать ФОТ и маржу: ${bridge.marginRiskDish}`
          : "Доказать ФОТ и маржу периода",
      learningModuleId: "tech-card-discipline",
      learningModuleTitle: "Техкарта как договор внутри команды",
      learningChecklistTitle: "Если BI показал недобор валовой прибыли",
      briefingQuestion:
        "какая цена, порция, списание, ставка или состав смены объясняет разрыв прибыли",
      audienceMemberId: bridge.employee?.memberId,
      audienceMemberName: bridge.employee?.name,
    };
  }

  if (input.margin.status === "ready") return null;

  const nextAction = buildMenuMarginNextAction(input.margin);
  const topBlocker = nextAction.blocker;
  const missingTechCardPrices =
    nextAction.kind === "missing-cost" && Boolean(topBlocker?.hasTechCard);
  const learningChecklistTitle = missingTechCardPrices
    ? "Если в техкарте нет цен ингредиентов"
    : "Если BI показал недобор валовой прибыли";
  const briefingQuestion = missingTechCardPrices
    ? "каким ингредиентам не хватает закупочной цены и почему RMS не доказывает food cost"
    : "каких связей, техкарт или закупочных цен не хватает, чтобы доверять марже";
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
    taskSourceLabel: "Маржа и техкарты",
    taskTitle: nextAction.title,
    impactLabel: topBlocker
      ? formatRubles(topBlocker.revenue)
      : `${input.margin.revenueCoveragePct}% маржа`,
    learningChecklistTitle,
    briefingQuestion,
    ...marginLearningHint(),
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
      reason:
        "показаны тестовые данные, для решений нужны реальные данные iiko",
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
  const fieldContext = buildTeamFieldContextDigest({
    comments: input.teamComments ?? [],
    tasks: input.teamTasks ?? [],
  });
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
    ...(() => {
      const evidence = unitEconomicsEvidence({
        labor: input.labor,
        margin: input.margin,
      });
      return evidence ? [evidence] : [];
    })(),
    ...(input.team ? [teamEvidence(input.team)] : []),
    ...(fieldContext ? [fieldContextEvidence(fieldContext)] : []),
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
  const actions = sortOwnerActions(
    markActionsWithOpenTasks(
      [
        input.dataQuality.status === "risk" || input.dataMode === "mock"
          ? ({
              title: "Проверить источник данных",
              detail:
                input.dataMode === "mock"
                  ? "Сейчас открыт тестовый контур. Для решений нужны реальные данные iiko."
                  : input.dataQuality.summary,
              role: "owner",
              tone: "risk",
              target: "iiko-settings",
              learningModuleId: "iiko-cash-discipline",
              learningModuleTitle: "iiko и кассовая дисциплина на смене",
            } satisfies OwnerReviewAction)
          : null,
        input.shiftPlanVariance
          ? ownerActionFromShiftPlanVariance(input.shiftPlanVariance)
          : null,
        ownerActionFromCommunication(operationalProof),
        ownerActionFromFieldContext(fieldContext),
        ownerActionFromLaborMargin({
          labor: input.labor,
          margin: input.margin,
        }),
        input.labor ? ownerActionFromLabor(input.labor) : null,
        input.margin ? ownerActionFromMargin(input.margin) : null,
        input.team ? ownerActionFromTeam(input.team) : null,
      ]
        .filter((item): item is OwnerReviewAction => item !== null)
        .map(withActionChecklist),
      input.teamTasks,
    ),
  ).slice(0, 3);

  const hypotheses: OwnerReviewHypothesis[] = [];

  if (input.dataQuality.status === "risk" || input.dataMode === "mock") {
    hypotheses.push({
      title: "Данные могут подменять реальность",
      why:
        input.dataMode === "mock"
          ? "Сейчас включены тестовые данные, поэтому выводы одинаковые по смыслу."
          : "В выбранном периоде не хватает продаж или дней с данными.",
      check:
        "Откройте проверку iiko и убедитесь, что ключ, организация и OLAP работают.",
      role: "owner",
      tone: "risk",
      taskSourceLabel: "Данные iiko",
    });
  }

  if (primaryLaborInsight && primaryLaborInsight.tone !== "good") {
    const missingIikoShifts = input.labor?.staffShifts === 0;
    const learning = missingIikoShifts
      ? iikoCashLearningHint()
      : laborNumbersLearningHint();

    hypotheses.push({
      title: primaryLaborInsight.title,
      why: primaryLaborInsight.detail,
      check: primaryLaborInsight.action,
      role: primaryLaborInsight.tone === "setup" ? "owner" : "manager",
      tone: ownerToneFromLabor(primaryLaborInsight.tone),
      taskSourceLabel: missingIikoShifts ? "Данные iiko" : "ФОТ и смены",
      ...learning,
    });
  }

  if (marginHypothesis) {
    hypotheses.push(marginHypothesis);
  }

  const fieldHypothesis = fieldContextHypothesis(fieldContext);
  if (fieldHypothesis) {
    hypotheses.push(fieldHypothesis);
  }

  const planVarianceHypothesis = input.shiftPlanVariance
    ? shiftPlanVarianceHypothesis(input.shiftPlanVariance)
    : null;
  if (planVarianceHypothesis) {
    hypotheses.push(planVarianceHypothesis);
  }

  if (
    input.brief.revenue.comparisonAvailable &&
    input.brief.revenue.deltaPct >= 10
  ) {
    hypotheses.push({
      title: "Рост нужно превратить в повторяемый сценарий",
      why: joinSentences([
        `Динамика к базе: ${deltaText(input.brief)}.`,
        revenueGrowthImpactLabel(input.brief)
          ? `Прирост к базе: ${revenueGrowthImpactLabel(input.brief)}.`
          : null,
        strongestDay
          ? `Самый сильный день: ${strongestDay.date}, ${formatRubles(strongestDay.revenue)}.`
          : "Сильный день нужно уточнить по сменам.",
      ]),
      check:
        "Зафиксировать, что сработало: смена, промо, посадка, команда, хит меню, погода или апсейл.",
      role: "manager",
      tone: "good",
      taskTitle: "Зафиксировать, что сработало в росте выручки",
      taskSourceLabel: "Выручка и смены",
      impactLabel: revenueGrowthImpactLabel(input.brief),
      learningModuleId: "shift-open-close",
      learningModuleTitle: "Открытие и закрытие смены без хаоса",
      learningChecklistTitle: "Если период вырос к базе",
      briefingQuestion:
        "что именно сработало и как повторить это в следующей похожей смене",
    });
  }

  if (
    input.brief.revenue.comparisonAvailable &&
    input.brief.revenue.deltaPct < -10
  ) {
    hypotheses.push({
      title: "Просадка могла прийти из смены, а не из меню",
      why: joinSentences([
        `Динамика к базе: ${deltaText(input.brief)}.`,
        revenueDropGapText(input.brief),
        weakestShift
          ? `Самая слабая смена: ${formatRubles(weakestShift.revenue)}.`
          : "Смены не дали явного ответа.",
        shiftRevenueGapText(weakestShift, input.shifts),
      ]),
      check: shiftCheckWithFieldContext(
        "Спросить управляющего: кто работал, какая была посадка, были ли стопы и жалобы.",
        fieldHypothesis,
      ),
      role: "manager",
      tone: "risk",
      taskTitle: shiftTaskTitle("Разобрать просадку смены", weakestShift),
      taskSourceLabel: "Выручка и смены",
      impactLabel: revenueDropImpactLabel(input.brief),
      learningModuleId: "shift-open-close",
      learningModuleTitle: "Открытие и закрытие смены без хаоса",
    });
  }

  if (
    hypotheses.length < 4 &&
    (!input.brief.revenue.comparisonAvailable ||
      input.brief.revenue.deltaPct >= -10) &&
    weakestShift &&
    shiftRevenueGap(weakestShift, input.shifts) > 0
  ) {
    hypotheses.push({
      title: "Слабую смену нужно объяснить событием",
      why: joinSentences([
        `Смена ${formatShiftDate(weakestShift.openTime)} дала ${formatRubles(weakestShift.revenue)}.`,
        shiftRevenueGapText(weakestShift, input.shifts),
      ]),
      check: shiftCheckWithFieldContext(
        "Спросить управляющего: посадка, команда, стоп-лист, погода, жалобы и апсейл в этой смене.",
        fieldHypothesis,
      ),
      role: "manager",
      tone: "watch",
      taskTitle: shiftTaskTitle("Разобрать слабую смену", weakestShift),
      taskSourceLabel: "Выручка и смены",
      impactLabel: shiftRevenueImpactLabel(weakestShift, input.shifts),
      learningModuleId: "shift-open-close",
      learningModuleTitle: "Открытие и закрытие смены без хаоса",
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
      taskSourceLabel: "Маржа и техкарты",
      impactLabel: formatRubles(topCategory.dishSumInt),
      learningModuleId: "tech-card-discipline",
      learningModuleTitle: "Техкарта как договор внутри команды",
      learningChecklistTitle: "Если категория держит оборот",
      briefingQuestion:
        "какие позиции категории дают деньги, маржу и риск стоп-листа",
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
      taskSourceLabel: "Продажи и сервис",
      impactLabel: formatRubles(topDish.dishSumInt),
      learningModuleId: "sales-eight-upsell",
      learningModuleTitle: "Восьмерка продаж и апселл в сервисе",
    });
  }

  if (menu.volumeTrap) {
    hypotheses.push({
      title: "Есть блюдо с большим объемом и слабым вкладом в чек",
      why: `«${menu.volumeTrap.dishName}» дает ${menu.volumeTrap.amountShare}% порций и ${menu.volumeTrap.revenueShare}% выручки.`,
      check: "Проверить цену, граммовку, подачу и возможность апсейла.",
      role: "chef",
      tone: "watch",
      taskSourceLabel: "Маржа и техкарты",
      learningModuleId: "tech-card-discipline",
      learningModuleTitle: "Техкарта как договор внутри команды",
      learningChecklistTitle: "Если блюдо дает объем без денег",
      briefingQuestion:
        "какая цена, порция или себестоимость делает объем слабым для чека",
    });
  }

  if (hypotheses.length < 3 && weakestDay && strongestDay) {
    hypotheses.push({
      title: "Слабый день нужно объяснить событием",
      why: joinSentences([
        `${weakestDay.date}: ${formatRubles(weakestDay.revenue)} против ${strongestDay.date}: ${formatRubles(strongestDay.revenue)}.`,
        dayRevenueGapText(weakestDay, strongestDay),
      ]),
      check:
        "Зафиксировать причину: погода, банкет, команда, промо, трафик, стоп-лист.",
      role: "manager",
      tone: "watch",
      taskSourceLabel: "Выручка и смены",
      impactLabel: dayRevenueImpactLabel(weakestDay, strongestDay),
      learningModuleId: "shift-open-close",
      learningModuleTitle: "Открытие и закрытие смены без хаоса",
    });
  }

  const visibleHypotheses = sortOwnerHypotheses(
    hypotheses.map(withHypothesisChecklist),
  ).slice(0, 4);
  const questions: OwnerReviewQuestion[] = visibleHypotheses.map((item) => ({
    role: item.role,
    text: item.briefingQuestion ?? item.check,
  }));
  const bridgeHypotheses = visibleHypotheses.filter((item) =>
    Boolean(item.taskSourceLabel),
  );
  const genericHypotheses = visibleHypotheses.filter(
    (item) => !item.taskSourceLabel,
  );
  const tasks = keepOperationalTaskDraftsVisible(
    withoutAlreadyOpenTeamTasks(
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
    ),
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
