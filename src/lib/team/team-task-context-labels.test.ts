import { describe, expect, test } from "vitest";
import {
  EMPTY_TEAM_TASK_CONTEXT_LABELS,
  taskContextLabelsFromAuditMetadata,
} from "./team-task-context-labels";

describe("team task context labels", () => {
  test("uses the newest audit metadata with useful labels", () => {
    const labels = taskContextLabelsFromAuditMetadata([
      {
        metadata: {
          status: "done",
        },
      },
      {
        metadata: {
          sourceLabel: "  Полевой   контекст ",
          impactLabel: " 1 сигнал ",
          learningModuleId: "shift-brief",
          learningModuleTitle: "Брифинг смены и передача контекста",
          learningChecklistTitle: "Если полевая заметка про ФОТ или маржу",
        },
      },
      {
        metadata: {
          sourceLabel: "старое",
          learningModuleId: "old",
        },
      },
    ]);

    expect(labels).toEqual({
      sourceLabel: "Полевой контекст",
      impactLabel: "1 сигнал",
      learningModuleId: "shift-brief",
      learningModuleTitle: "Брифинг смены и передача контекста",
      learningChecklistTitle: "Если полевая заметка про ФОТ или маржу",
    });
  });

  test("returns empty labels when audit metadata has no task context", () => {
    expect(
      taskContextLabelsFromAuditMetadata([
        { metadata: { status: "in_progress" } },
        { metadata: null },
      ]),
    ).toBe(EMPTY_TEAM_TASK_CONTEXT_LABELS);
  });
});
