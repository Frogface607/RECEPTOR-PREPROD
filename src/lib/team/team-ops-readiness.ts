import type { TeamLaborReadiness } from "./team-labor-readiness";
import type { TeamLearningMemberSummary } from "./team-learning-progress";
import type { ShiftOverview, ShiftRoleCoverage } from "./team-shift-planner";
import type { TeamRoleId, TeamTask } from "./team-os";

export type TeamOpsReadinessStatus = "ready" | "attention" | "blocked";

export type TeamOpsActionTone = "risk" | "setup" | "watch" | "good";

export type TeamOpsAction = {
  id: string;
  tone: TeamOpsActionTone;
  title: string;
  detail: string;
  href: string;
};

export type TeamOpsReadiness = {
  score: number;
  status: TeamOpsReadinessStatus;
  roleCoveragePct: number;
  laborCoveragePct: number;
  learningAveragePct: number;
  actions: TeamOpsAction[];
};

const OPERATIONAL_ROLES = new Set<TeamRoleId>([
  "venue_manager",
  "chef",
  "line_cook",
  "service",
]);

function isOpenTask(task: TeamTask): boolean {
  return task.status !== "done" && task.status !== "verified";
}

function criticalRoleBlocker(
  uncoveredRoles: ShiftRoleCoverage[],
): ShiftRoleCoverage | undefined {
  return (
    uncoveredRoles.find((role) => OPERATIONAL_ROLES.has(role.roleId)) ??
    uncoveredRoles[0]
  );
}

function activeLearningBlocker(
  summaries: TeamLearningMemberSummary[],
): TeamLearningMemberSummary | undefined {
  return summaries
    .filter(
      (summary) =>
        summary.member.status !== "paused" && summary.status !== "complete",
    )
    .sort((a, b) => {
      if (a.status !== b.status) {
        return a.status === "not_started" ? -1 : 1;
      }
      return a.averageBest - b.averageBest;
    })[0];
}

function actionDetail(value: string, fallback: string): string {
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : fallback;
}

export function buildTeamOpsReadiness(input: {
  shiftOverview: ShiftOverview;
  laborReadiness: TeamLaborReadiness;
  learningSummaries: TeamLearningMemberSummary[];
  tasks: TeamTask[];
}): TeamOpsReadiness {
  const { shiftOverview, laborReadiness, learningSummaries, tasks } = input;
  const roleCoveragePct =
    shiftOverview.coverage.length > 0
      ? Math.round(
          (shiftOverview.coveredRoles / shiftOverview.coverage.length) * 100,
        )
      : 0;
  const activeLearning = learningSummaries.filter(
    (summary) => summary.member.status !== "paused",
  );
  const learningAveragePct =
    activeLearning.length > 0
      ? Math.round(
          activeLearning.reduce(
            (total, summary) => total + summary.averageBest,
            0,
          ) / activeLearning.length,
        )
      : 0;
  const laborCoveragePct = laborReadiness.coveragePct;
  const score = Math.round(
    laborCoveragePct * 0.4 + roleCoveragePct * 0.35 + learningAveragePct * 0.25,
  );
  const actions: TeamOpsAction[] = [];
  const firstMissingRate = laborReadiness.missingStaff[0];

  if (firstMissingRate) {
    const extraMissing = laborReadiness.missingStaff.length - 1;
    actions.push({
      id: "labor-rate",
      tone: laborReadiness.status === "blocked" ? "risk" : "setup",
      title: "Закрыть ставку ФОТ",
      detail: `${firstMissingRate.name}${extraMissing > 0 ? ` и еще ${extraMissing}` : ""}: BI считает смены без точной стоимости.`,
      href: "#labor-rates",
    });
  }

  const roleBlocker = criticalRoleBlocker(shiftOverview.uncoveredRoles);
  if (roleBlocker) {
    actions.push({
      id: "role-coverage",
      tone: roleBlocker.status === "empty" ? "risk" : "watch",
      title: "Закрыть роль на смене",
      detail: `${roleBlocker.title}: ${roleBlocker.status === "invited" ? "сотрудник приглашен, но еще не активен" : "нет активного сотрудника"}.`,
      href: "#shift-coverage",
    });
  }

  const learningBlocker = activeLearningBlocker(learningSummaries);
  if (learningBlocker) {
    actions.push({
      id: "learning",
      tone: learningBlocker.status === "not_started" ? "setup" : "watch",
      title: "Дожать обучение",
      detail: `${learningBlocker.member.name}: ${actionDetail(
        learningBlocker.nextItem?.title ?? "",
        "закрыть материалы роли",
      )}.`,
      href: "#learning-progress",
    });
  }

  const importantTask = tasks.find(
    (task) => task.priority === "high" && isOpenTask(task),
  );
  if (importantTask) {
    actions.push({
      id: "task",
      tone: "watch",
      title: "Разобрать важную задачу",
      detail: importantTask.title,
      href: "#team-actions",
    });
  }

  const finalActions =
    actions.length > 0
      ? actions.slice(0, 4)
      : [
          {
            id: "ready",
            tone: "good" as const,
            title: "Команда готова",
            detail: "Роли, ставки и обучение выглядят закрытыми для текущей смены.",
            href: "#team-actions",
          },
        ];
  const status: TeamOpsReadinessStatus =
    laborReadiness.status === "blocked" || roleCoveragePct < 50
      ? "blocked"
      : score >= 80 && actions.length === 0
        ? "ready"
        : "attention";

  return {
    score,
    status,
    roleCoveragePct,
    laborCoveragePct,
    learningAveragePct,
    actions: finalActions,
  };
}
