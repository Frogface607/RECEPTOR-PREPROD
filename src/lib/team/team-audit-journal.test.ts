import { describe, expect, test } from "vitest";
import {
  auditEventJournalCategory,
  buildTeamAuditJournal,
} from "./team-audit-journal";
import type { TeamAuditEvent } from "./team-os";

function event(
  id: string,
  type: TeamAuditEvent["type"],
  summary = "Событие",
): TeamAuditEvent {
  return {
    id,
    venueId: "venue-1",
    type,
    targetType: type === "shift_plan_updated" ? "shift_plan" : "task",
    targetId: id,
    summary,
    createdAtLabel: "12:00",
  };
}

describe("team audit journal", () => {
  test("categorizes operational events for manager filters", () => {
    expect(auditEventJournalCategory("member_labor_rate_updated")).toBe(
      "labor",
    );
    expect(auditEventJournalCategory("learning_standard_updated")).toBe(
      "learning",
    );
    expect(auditEventJournalCategory("shift_plan_updated")).toBe("plan");
    expect(auditEventJournalCategory("task_status_updated")).toBe("tasks");
    expect(auditEventJournalCategory("member_password_reset")).toBe("access");
  });

  test("builds entries and filter counts", () => {
    const journal = buildTeamAuditJournal([
      event("labor-1", "member_labor_rate_updated", "Ставка ФОТ обновлена."),
      event("plan-1", "shift_plan_updated", "План смены обновлен."),
      event("task-1", "task_created", "Создана задача."),
      event("task-2", "comment_added", "Добавлен комментарий."),
      event("learning-1", "learning_standard_updated", "Допуск обновлен."),
      event("access-1", "member_invited", "Создан доступ."),
    ]);

    expect(journal.entries.map((entry) => entry.categoryId)).toEqual([
      "labor",
      "plan",
      "tasks",
      "tasks",
      "learning",
      "access",
    ]);
    expect(journal.entries[0]).toMatchObject({
      categoryLabel: "ФОТ",
      typeLabel: "ФОТ",
    });
    expect(
      Object.fromEntries(
        journal.categories.map((category) => [category.id, category.count]),
      ),
    ).toMatchObject({
      all: 6,
      labor: 1,
      plan: 1,
      tasks: 2,
      learning: 1,
      access: 1,
    });
  });
});
