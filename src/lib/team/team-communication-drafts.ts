import type { TeamLaborReadiness } from "./team-labor-readiness";
import type { TeamLearningRolePlan } from "./team-learning-role-plan";
import type { TeamShiftPlanVarianceSummary } from "./team-shift-plan-variance";
import type { TeamAnnouncement, TeamRoleId } from "./team-os";

export type TeamCommunicationDraft = {
  id: string;
  label: string;
  reason: string;
  title: string;
  body: string;
  priority: TeamAnnouncement["priority"];
  audience:
    | { type: "venue" }
    | {
        type: "role";
        roleId: TeamRoleId;
      };
};

function namesList(names: string[], limit = 3): string {
  const visible = names.slice(0, limit);
  const rest = names.length - visible.length;
  return `${visible.join(", ")}${rest > 0 ? ` и еще ${rest}` : ""}`;
}

function buildLearningDraft(
  plans: TeamLearningRolePlan[],
): TeamCommunicationDraft | null {
  const plan =
    plans
      .filter((item) => item.blockedMembers.length > 0)
      .sort(
        (a, b) =>
          a.admissionPct - b.admissionPct ||
          b.blockedMembers.length - a.blockedMembers.length ||
          a.roleTitle.localeCompare(b.roleTitle, "ru-RU"),
      )[0] ?? null;

  if (!plan) return null;

  const moduleTitle =
    plan.nextItem?.title ?? plan.blockedMembers[0]?.nextItemTitle ?? "допуск";
  const blockedNames = namesList(
    plan.blockedMembers.map((member) => member.memberName),
  );

  return {
    id: "learning-admission",
    label: "Обучение",
    reason: `${plan.blockedMembers.length} без допуска`,
    title: `Допуск к смене: ${plan.roleTitle}`,
    body: `Команда, до смены закрываем обязательное обучение: ${moduleTitle}. Сейчас без допуска: ${blockedNames}. После прохождения теста задача закроется в Receptor.`,
    priority: plan.admissionPct < 70 ? "important" : "normal",
    audience: { type: "role", roleId: plan.roleId },
  };
}

function buildLaborDraft(
  readiness: TeamLaborReadiness,
): TeamCommunicationDraft | null {
  if (readiness.status === "ready") return null;

  const blocker = readiness.iikoBlockers[0];
  const names =
    readiness.iikoBlockers.length > 0
      ? readiness.iikoBlockers.map((item) => item.name)
      : readiness.missingStaff.map((member) => member.name);
  const focus = names.length > 0 ? namesList(names) : "проверить ставки";
  const missing =
    readiness.iikoUnpricedStaffShifts > 0
      ? `${readiness.iikoUnpricedStaffShifts} смен без точного ФОТ`
      : `${readiness.readyStaff}/${readiness.activeStaff} ставок заполнено`;

  return {
    id: "labor-rates",
    label: "ФОТ",
    reason: `${readiness.coveragePct}% покрытия`,
    title: "ФОТ перед отчетом",
    body: `Нужно закрыть ставки ФОТ в Team OS: ${missing}. Первый фокус: ${focus}. Без этого владелец видит выручку, но не видит реальную экономику смены.`,
    priority:
      readiness.status === "blocked" || blocker?.action === "add-member"
        ? "important"
        : "normal",
    audience: { type: "role", roleId: "venue_manager" },
  };
}

function buildPlanFactDraft(
  variance: TeamShiftPlanVarianceSummary,
): TeamCommunicationDraft | null {
  const issue = variance.issues[0] ?? null;
  if (!issue) return null;

  const title =
    issue.tone === "risk" ? "План смен требует внимания" : "Сверка плана смен";
  const body =
    issue.status === "missed_plan"
      ? `${issue.member.name} не вышел по плану ${issue.dateLabel}. Зафиксируйте причину и обновите план смен, чтобы ФОТ и расписание не расходились.`
      : issue.status === "day_off_worked"
        ? `${issue.member.name} вышел в запланированный выходной ${issue.dateLabel}. Проверьте замену, часы и ставку.`
        : issue.status === "missing_rate"
          ? `${issue.member.name}: смена ${issue.dateLabel} без ставки ФОТ. Заполните ставку, чтобы план/факт стал управленческим, а не просто календарем.`
          : `${issue.member.name}: расхождение плана и факта ${issue.dateLabel}. Проверьте часы, роль на смене и причину изменения.`;

  return {
    id: "plan-fact",
    label: "План/факт",
    reason: `${variance.planCoveragePct}% покрытия`,
    title,
    body,
    priority: issue.tone === "risk" ? "important" : "normal",
    audience: { type: "role", roleId: "venue_manager" },
  };
}

export function buildTeamCommunicationDrafts(input: {
  learningRolePlans: TeamLearningRolePlan[];
  laborReadiness: TeamLaborReadiness;
  shiftPlanVariance: TeamShiftPlanVarianceSummary;
  limit?: number;
}): TeamCommunicationDraft[] {
  const limit = Math.max(input.limit ?? 3, 1);
  return [
    buildLearningDraft(input.learningRolePlans),
    buildLaborDraft(input.laborReadiness),
    buildPlanFactDraft(input.shiftPlanVariance),
  ]
    .filter((draft): draft is TeamCommunicationDraft => Boolean(draft))
    .slice(0, limit);
}
