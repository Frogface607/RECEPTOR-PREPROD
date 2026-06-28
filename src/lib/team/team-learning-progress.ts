import type { TeamLearningItem } from "./team-learning";
import {
  listLearningItemsForRoleWithStandards,
  type TeamLearningStandardOverride,
} from "./team-learning-standards";
import type { StaffMember } from "./team-os";

export type TeamLearningProgress = {
  venueId: string;
  membershipId: string;
  userId: string | null;
  moduleId: string;
  bestPercentage: number;
  lastPercentage: number;
  correct: number;
  total: number;
  passed: boolean;
  answers: number[];
  completedAt: string;
  updatedAt: string;
};

export type TeamLearningProgressSnapshot = {
  bestPercentage: number;
  lastPercentage: number;
  correct: number;
  total: number;
  passed: boolean;
  answers: number[];
  completedAt: string;
};

export type TeamLearningMemberSummary = {
  member: StaffMember;
  items: TeamLearningItem[];
  totalCount: number;
  requiredCount: number;
  requiredMissing: number;
  completedCount: number;
  requiredCompleted: number;
  averageBest: number;
  status: "complete" | "attention" | "not_started";
  admissionStatus: "admitted" | "needs_training" | "not_started";
  canWorkShift: boolean;
  nextItem: TeamLearningItem | null;
  lastCompletedAt: string;
};

function keyFor(membershipId: string, moduleId: string): string {
  return `${membershipId}:${moduleId}`;
}

function latestTimestamp(values: string[]): string {
  const latest = values
    .map((value) => new Date(value).getTime())
    .filter((value) => !Number.isNaN(value))
    .sort((a, b) => b - a)[0];

  return latest ? new Date(latest).toISOString() : "";
}

export function progressToSnapshot(
  progress: TeamLearningProgress,
): TeamLearningProgressSnapshot {
  return {
    bestPercentage: progress.bestPercentage,
    lastPercentage: progress.lastPercentage,
    correct: progress.correct,
    total: progress.total,
    passed: progress.passed,
    answers: progress.answers,
    completedAt: progress.completedAt,
  };
}

export function progressToSnapshotMap(
  progress: TeamLearningProgress[],
): Record<string, TeamLearningProgressSnapshot> {
  return Object.fromEntries(
    progress.map((item) => [item.moduleId, progressToSnapshot(item)]),
  );
}

export function buildTeamLearningSummaries(
  staff: StaffMember[],
  progress: TeamLearningProgress[],
  standards: TeamLearningStandardOverride[] = [],
): TeamLearningMemberSummary[] {
  const progressByMemberAndModule = new Map(
    progress.map((item) => [keyFor(item.membershipId, item.moduleId), item]),
  );

  return staff.map((member) => {
    const items = listLearningItemsForRoleWithStandards(
      member.roleId,
      standards,
    );
    const requiredItems = items.filter((item) => item.status === "required");
    const completedItems = items.filter((item) => {
      const saved = progressByMemberAndModule.get(keyFor(member.id, item.id));
      return (saved?.bestPercentage ?? 0) >= item.passPercentage;
    });
    const requiredCompleted = requiredItems.filter((item) => {
      const saved = progressByMemberAndModule.get(keyFor(member.id, item.id));
      return (saved?.bestPercentage ?? 0) >= item.passPercentage;
    }).length;
    const requiredMissing = Math.max(
      requiredItems.length - requiredCompleted,
      0,
    );
    const averageBest =
      items.length > 0
        ? Math.round(
            items.reduce((sum, item) => {
              const saved = progressByMemberAndModule.get(
                keyFor(member.id, item.id),
              );
              return sum + (saved?.bestPercentage ?? 0);
            }, 0) / items.length,
          )
        : 0;
    const nextItem =
      requiredItems.find((item) => {
        const saved = progressByMemberAndModule.get(keyFor(member.id, item.id));
        return (saved?.bestPercentage ?? 0) < item.passPercentage;
      }) ??
      items.find((item) => {
        const saved = progressByMemberAndModule.get(keyFor(member.id, item.id));
        return (saved?.bestPercentage ?? 0) < item.passPercentage;
      }) ??
      null;
    const memberProgress = progress.filter(
      (item) => item.membershipId === member.id,
    );
    const status =
      completedItems.length === 0
        ? "not_started"
        : requiredItems.length > 0 && requiredCompleted < requiredItems.length
          ? "attention"
          : completedItems.length < items.length
            ? "attention"
            : "complete";
    const canWorkShift =
      requiredItems.length === 0 || requiredCompleted >= requiredItems.length;
    const admissionStatus = canWorkShift
      ? "admitted"
      : completedItems.length === 0
        ? "not_started"
        : "needs_training";

    return {
      member,
      items,
      totalCount: items.length,
      requiredCount: requiredItems.length,
      requiredMissing,
      completedCount: completedItems.length,
      requiredCompleted,
      averageBest,
      status,
      admissionStatus,
      canWorkShift,
      nextItem,
      lastCompletedAt: latestTimestamp(
        memberProgress.map((item) => item.completedAt),
      ),
    };
  });
}

export function summarizeTeamLearning(summaries: TeamLearningMemberSummary[]): {
  completedMembers: number;
  attentionMembers: number;
  notStartedMembers: number;
  admittedMembers: number;
  blockedMembers: number;
  admissionPct: number;
  averageBest: number;
} {
  const activeSummaries = summaries.filter(
    (summary) => summary.member.status !== "paused",
  );
  const averageBest =
    activeSummaries.length > 0
      ? Math.round(
          activeSummaries.reduce(
            (sum, summary) => sum + summary.averageBest,
            0,
          ) / activeSummaries.length,
        )
      : 0;
  const admittedMembers = activeSummaries.filter(
    (summary) => summary.canWorkShift,
  ).length;
  const blockedMembers = Math.max(activeSummaries.length - admittedMembers, 0);
  const admissionPct =
    activeSummaries.length > 0
      ? Math.round((admittedMembers / activeSummaries.length) * 100)
      : 0;

  return {
    completedMembers: activeSummaries.filter(
      (summary) => summary.status === "complete",
    ).length,
    attentionMembers: activeSummaries.filter(
      (summary) => summary.status === "attention",
    ).length,
    notStartedMembers: activeSummaries.filter(
      (summary) => summary.status === "not_started",
    ).length,
    admittedMembers,
    blockedMembers,
    admissionPct,
    averageBest,
  };
}
