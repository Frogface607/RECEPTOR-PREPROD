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
  targetType: TeamAuditEvent["targetType"] = "task",
): TeamAuditEvent {
  return {
    id,
    venueId: "venue-1",
    type,
    targetType,
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
      event(
        "member-1",
        "member_labor_rate_updated",
        "Ставка ФОТ обновлена.",
        "member",
      ),
      event(
        "plan-1",
        "shift_plan_updated",
        "План смены обновлен.",
        "shift_plan",
      ),
      event("task-1", "task_created", "Создана задача."),
      event("task-2", "comment_added", "Добавлен комментарий."),
      event(
        "announcement-1",
        "announcement_created",
        "Опубликовано объявление.",
        "announcement",
      ),
      event(
        "learning-1",
        "learning_standard_updated",
        "Допуск обновлен.",
        "learning_standard",
      ),
      event("access-1", "member_invited", "Создан доступ.", "member"),
    ]);

    expect(journal.entries.map((entry) => entry.categoryId)).toEqual([
      "labor",
      "plan",
      "tasks",
      "tasks",
      "tasks",
      "learning",
      "access",
    ]);
    expect(journal.entries[0]).toMatchObject({
      categoryLabel: "ФОТ",
      typeLabel: "ФОТ",
      contextHref: "#labor-member-member-1",
      contextLabel: "К сотруднику",
    });
    expect(journal.entries[1]).toMatchObject({
      contextHref: "#shift-plan",
      contextLabel: "К плану",
    });
    expect(journal.entries[2]).toMatchObject({
      contextHref: "#team-task-task-1",
      contextLabel: "К задаче",
    });
    expect(journal.entries[4]).toMatchObject({
      contextHref: "#team-announcement-announcement-1",
      contextLabel: "К объявлению",
    });
    expect(journal.entries[5]).toMatchObject({
      contextHref: "#learning-progress",
      contextLabel: "К обучению",
    });
    expect(
      Object.fromEntries(
        journal.categories.map((category) => [category.id, category.count]),
      ),
    ).toMatchObject({
      all: 7,
      labor: 1,
      plan: 1,
      tasks: 3,
      learning: 1,
      access: 1,
    });
  });
});
