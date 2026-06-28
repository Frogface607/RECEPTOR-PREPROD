import {
  listLearningItemsForRole,
  type TeamLearningItem,
} from "./team-learning";
import { getTeamRole, TEAM_ROLES, type TeamRoleId } from "./team-os";
import type { TeamLearningMemberSummary } from "./team-learning-progress";

export type TeamLearningRoleBlocker = {
  memberId: string;
  memberName: string;
  nextItemTitle: string;
};

export type TeamLearningRolePlan = {
  roleId: TeamRoleId;
  roleTitle: string;
  members: number;
  totalItems: number;
  requiredItems: number;
  readyItems: number;
  soonItems: number;
  requiredProgressPct: number;
  admissionPct: number;
  blockedMembers: TeamLearningRoleBlocker[];
  nextItem: TeamLearningItem | null;
};

export type TeamLearningAdmissionTaskDraft = {
  title: string;
  priority: "high" | "medium";
  audienceType: "member";
  audienceMemberId: string;
  memberName: string;
  moduleTitle: string;
  roleTitle: string;
  dueLabel: string;
};

export function buildTeamLearningRolePlans(
  summaries: TeamLearningMemberSummary[],
): TeamLearningRolePlan[] {
  const activeSummaries = summaries.filter(
    (summary) => summary.member.status !== "paused",
  );

  return TEAM_ROLES.map((role) =>
    buildRolePlan(role.id, activeSummaries),
  ).filter((plan) => plan.members > 0 || plan.totalItems > 0);
}

export function buildLearningAdmissionTaskDraft(
  plan: TeamLearningRolePlan,
): TeamLearningAdmissionTaskDraft | null {
  const blocker = plan.blockedMembers[0] ?? null;
  if (!blocker) return null;

  const moduleTitle = plan.nextItem?.title ?? blocker.nextItemTitle;

  return {
    title: `Пройти обучение: ${moduleTitle}`,
    priority: plan.admissionPct < 50 ? "high" : "medium",
    audienceType: "member",
    audienceMemberId: blocker.memberId,
    memberName: blocker.memberName,
    moduleTitle,
    roleTitle: plan.roleTitle,
    dueLabel: "до смены",
  };
}

function buildRolePlan(
  roleId: TeamRoleId,
  summaries: TeamLearningMemberSummary[],
): TeamLearningRolePlan {
  const roleSummaries = summaries.filter(
    (summary) => summary.member.roleId === roleId,
  );
  const items = listLearningItemsForRole(roleId);
  const requiredItems = items.filter((item) => item.status === "required");
  const requiredSlots = requiredItems.length * roleSummaries.length;
  const requiredCompleted = roleSummaries.reduce(
    (sum, summary) => sum + summary.requiredCompleted,
    0,
  );
  const admittedMembers = roleSummaries.filter(
    (summary) => summary.canWorkShift,
  ).length;
  const blockedMembers = roleSummaries
    .filter((summary) => !summary.canWorkShift)
    .map((summary) => ({
      memberId: summary.member.id,
      memberName: summary.member.name,
      nextItemTitle: summary.nextItem?.title ?? "обязательный материал",
    }));

  return {
    roleId,
    roleTitle: getTeamRole(roleId).title,
    members: roleSummaries.length,
    totalItems: items.length,
    requiredItems: requiredItems.length,
    readyItems: items.filter((item) => item.status === "ready").length,
    soonItems: items.filter((item) => item.status === "soon").length,
    requiredProgressPct:
      requiredSlots > 0
        ? Math.round((requiredCompleted / requiredSlots) * 100)
        : 100,
    admissionPct:
      roleSummaries.length > 0
        ? Math.round((admittedMembers / roleSummaries.length) * 100)
        : 100,
    blockedMembers,
    nextItem: mostCommonNextItem(roleSummaries),
  };
}

function mostCommonNextItem(
  summaries: TeamLearningMemberSummary[],
): TeamLearningItem | null {
  const counts = new Map<string, { item: TeamLearningItem; count: number }>();

  summaries.forEach((summary) => {
    if (!summary.nextItem) return;
    const existing = counts.get(summary.nextItem.id);
    counts.set(summary.nextItem.id, {
      item: summary.nextItem,
      count: (existing?.count ?? 0) + 1,
    });
  });

  return (
    [...counts.values()].sort(
      (a, b) =>
        b.count - a.count ||
        learningStatusWeight(b.item.status) -
          learningStatusWeight(a.item.status) ||
        a.item.title.localeCompare(b.item.title, "ru"),
    )[0]?.item ?? null
  );
}

function learningStatusWeight(status: TeamLearningItem["status"]): number {
  if (status === "required") return 3;
  if (status === "ready") return 2;
  return 1;
}
