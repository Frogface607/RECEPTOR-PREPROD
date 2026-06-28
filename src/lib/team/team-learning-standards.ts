import {
  listLearningItemsForRole,
  type TeamLearningItem,
} from "./team-learning";
import type { TeamRoleId } from "./team-os";

export type TeamLearningStandardStatus = "required" | "ready" | "hidden";

export type TeamLearningStandardOverride = {
  venueId: string;
  roleId: TeamRoleId;
  moduleId: string;
  status: TeamLearningStandardStatus;
  updatedAt: string;
};

export function listLearningItemsForRoleWithStandards(
  roleId: TeamRoleId,
  standards: readonly TeamLearningStandardOverride[] = [],
): TeamLearningItem[] {
  const overrides = new Map(
    standards
      .filter((standard) => standard.roleId === roleId)
      .map((standard) => [standard.moduleId, standard.status]),
  );

  return listLearningItemsForRole(roleId).flatMap((item) => {
    const status = overrides.get(item.id);
    if (status === "hidden") return [];
    if (!status) return [item];

    return [{ ...item, status }];
  });
}

export function countCustomLearningStandards(
  roleId: TeamRoleId,
  standards: readonly TeamLearningStandardOverride[] = [],
): number {
  const baseStatuses = new Map(
    listLearningItemsForRole(roleId).map((item) => [item.id, item.status]),
  );

  return standards.filter((standard) => {
    if (standard.roleId !== roleId) return false;
    return baseStatuses.get(standard.moduleId) !== standard.status;
  }).length;
}

export function normalizeLearningStandardStatus(
  value: string | null | undefined,
): TeamLearningStandardStatus {
  if (value === "required" || value === "hidden") return value;
  return "ready";
}
