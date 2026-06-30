import { describe, expect, test } from "vitest";
import {
  buildRestaurantMemoryGraph,
  buildRestaurantMemoryGraphModel,
  formatRestaurantMemoryGraph,
  formatRestaurantMemoryGraphMarkdown,
  summarizeRestaurantMemoryGraph,
} from "./restaurant-memory-graph";
import type { StaffMember, TeamTask, TeamTaskComment } from "@/lib/team/team-os";

const staff: StaffMember[] = [
  {
    id: "manager",
    name: "Маша",
    roleId: "venue_manager",
    venueId: "venue",
    status: "active",
    shiftLabel: "вечер",
  },
];

const tasks: TeamTask[] = [
  {
    id: "field",
    title: "Полевой контекст смены",
    source: "manager",
    sourceLabel: "Поле",
    priority: "medium",
    status: "in_progress",
    venueId: "venue",
    audience: { type: "venue", venueId: "venue" },
    dueLabel: "после смены",
  },
  {
    id: "shift-memory",
    title: "Уточнить итог смены: контекст/причина",
    source: "copilot",
    sourceLabel: "Память смены",
    learningChecklistTitle: "Если итог смены неполный",
    priority: "medium",
    status: "new",
    venueId: "venue",
    audience: { type: "role", roleId: "venue_manager" },
    dueLabel: "до утреннего разбора",
  },
];

const comments: TeamTaskComment[] = [
  {
    id: "note",
    venueId: "venue",
    taskId: "field",
    authorName: "Маша",
    body:
      "Итог смены: из-за ливня после 19:00 отменили 3 брони, утром проверить стоп-лист.",
    createdAtLabel: "22:30",
  },
  {
    id: "system",
    venueId: "venue",
    taskId: "shift-memory",
    authorName: "Receptor",
    body: "Проверка: советнику не хватает контекста. Зачем: связать факты.",
    createdAtLabel: "22:31",
  },
];

describe("restaurant memory graph", () => {
  test("builds graph-ready relations from team, shift memory and tasks", () => {
    const relations = buildRestaurantMemoryGraph({ staff, tasks, comments });
    const lines = formatRestaurantMemoryGraph(relations);

    expect(lines).toContain("Маша -> роль -> Управляющий");
    expect(lines.join("\n")).toContain("Маша -> оставил(а) итог смены -> Поле");
    expect(lines.join("\n")).toContain(
      "Память смены -> добирает контекст -> Уточнить итог смены",
    );
    expect(lines.join("\n")).toContain("Погода и внешний контекст");
    expect(lines.join("\n")).not.toContain("Receptor -> сообщил");
  });

  test("keeps a lightweight node-edge model with a markdown snapshot", () => {
    const model = buildRestaurantMemoryGraphModel({ staff, tasks, comments });

    expect(model.relations.length).toBeGreaterThan(0);
    expect(model.nodes).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          id: "person:маша",
          kind: "person",
          label: "Маша",
        }),
        expect.objectContaining({
          kind: "role",
          label: "Управляющий",
        }),
      ]),
    );
    expect(model.edges[0]).toMatchObject({
      from: "person:маша",
      predicate: "роль",
      source: "team",
    });
    expect(model.markdownSnapshot).toContain("# Карта памяти ресторана");
    expect(model.markdownSnapshot).toContain("## Узлы");
    expect(model.markdownSnapshot).toContain("## Связи");
    expect(formatRestaurantMemoryGraphMarkdown(model)).toContain(
      "person:маша -> роль -> role:управляющий",
    );
  });

  test("summarizes graph coverage without exposing raw edges to the UI", () => {
    const brief = summarizeRestaurantMemoryGraph(
      buildRestaurantMemoryGraph({ staff, tasks, comments }),
    );

    expect(brief).toMatchObject({
      status: "ready",
      sourceLabels: ["люди", "смена", "задачи"],
      missingLabels: [],
      nextAction: "можно спрашивать советника о причинах и действиях",
    });
    expect(brief.summary).toContain("связей");
    expect(brief.summary).not.toContain("->");
  });
});
