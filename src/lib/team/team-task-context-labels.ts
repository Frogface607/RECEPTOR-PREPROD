import {
  normalizeTaskImpactLabel,
  normalizeTaskLabel,
  normalizeTaskSourceLabel,
} from "./team-task-labels";

export type TeamTaskContextLabels = {
  sourceLabel: string | null;
  impactLabel: string | null;
  learningModuleId: string | null;
  learningModuleTitle: string | null;
  learningChecklistTitle: string | null;
};

export type TeamTaskContextMetadataEvent = {
  metadata: Record<string, unknown> | null;
};

export const EMPTY_TEAM_TASK_CONTEXT_LABELS: TeamTaskContextLabels = {
  sourceLabel: null,
  impactLabel: null,
  learningModuleId: null,
  learningModuleTitle: null,
  learningChecklistTitle: null,
};

function contextLabelsFromMetadata(
  metadata: Record<string, unknown> | null | undefined,
): TeamTaskContextLabels {
  return {
    sourceLabel: normalizeTaskSourceLabel(metadata?.sourceLabel),
    impactLabel: normalizeTaskImpactLabel(metadata?.impactLabel),
    learningModuleId: normalizeTaskLabel(metadata?.learningModuleId),
    learningModuleTitle: normalizeTaskLabel(metadata?.learningModuleTitle),
    learningChecklistTitle: normalizeTaskLabel(metadata?.learningChecklistTitle),
  };
}

function hasContextLabels(labels: TeamTaskContextLabels): boolean {
  return Boolean(
    labels.sourceLabel ||
      labels.impactLabel ||
      labels.learningModuleId ||
      labels.learningModuleTitle ||
      labels.learningChecklistTitle,
  );
}

export function taskContextLabelsFromAuditMetadata(
  events: TeamTaskContextMetadataEvent[],
): TeamTaskContextLabels {
  for (const event of events) {
    const labels = contextLabelsFromMetadata(event.metadata);
    if (hasContextLabels(labels)) return labels;
  }

  return EMPTY_TEAM_TASK_CONTEXT_LABELS;
}
