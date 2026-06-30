import { describe, expect, test } from "vitest";
import {
  buildRestaurantAdvisorMemory,
  formatRestaurantAdvisorMemoryForAnswer,
  formatRestaurantAdvisorMemoryForPrompt,
} from "./restaurant-memory";
import type { StaffMember, TeamTask, TeamTaskComment } from "@/lib/team/team-os";

const staff: StaffMember[] = [
  {
    id: "manager",
    name: "Маша",
    roleId: "venue_manager",
    venueId: "venue",
    status: "active",
    shiftLabel: "зал",
  },
  {
    id: "service",
    name: "Алина",
    roleId: "service",
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
    id: "stock",
    title: "Проверить стоп-лист",
    source: "manager",
    sourceLabel: "Кухня",
    impactLabel: "вечерняя выручка",
    priority: "high",
    status: "new",
    venueId: "venue",
    audience: { type: "role", roleId: "chef" },
    dueLabel: "до 17:00",
  },
];

const comments: TeamTaskComment[] = [
  {
    id: "note",
    venueId: "venue",
    taskId: "field",
    authorName: "Маша",
    body:
      "Итог смены: ливень, отменили 3 брони после 19:00. Гости спрашивали безалкогольные коктейли. Утром проверить стоп-лист.",
    createdAtLabel: "22:30",
  },
];

describe("restaurant advisor memory", () => {
  test("builds compact restaurant memory from team workspace", () => {
    const memory = buildRestaurantAdvisorMemory({
      staff,
      tasks,
      comments,
      learningProgress: [],
      learningStandards: [],
    });

    expect(memory.teamSummary).toContain("2 активных сотрудников");
    expect(memory.teamSummary).toContain("Управляющий: 1");
    expect(memory.teamSummary).toContain("Официант: 1");
    expect(memory.fieldSummary).toContain("Итог смены");
    expect(memory.fieldSignals.join("\n")).toContain("Погода");
    expect(memory.openTasks[0]).toContain("Проверить стоп-лист");
    expect(memory.learningGaps[0]).toContain("Маша");
  });

  test("formats memory for advisor prompt", () => {
    const text = formatRestaurantAdvisorMemoryForPrompt({
      teamSummary: "2 активных сотрудников",
      fieldSummary: "Память смены: ливень и стоп-лист",
      fieldSignals: ["Погода: ливень"],
      openTasks: ["Проверить стоп-лист — до 17:00"],
      learningGaps: ["Алина: Как рекомендовать блюдо без давления"],
    });

    expect(text).toContain("Память ресторана");
    expect(text).toContain("Сигналы с поля");
    expect(text).toContain("Учебные пробелы");
  });

  test("formats a compact memory summary for user-facing answers", () => {
    const text = formatRestaurantAdvisorMemoryForAnswer({
      teamSummary: "2 активных сотрудников",
      fieldSummary: "Итог смены: ливень и стоп-лист",
      fieldSignals: ["Погода: ливень", "Стоп-лист: мята"],
      openTasks: ["Проверить стоп-лист — до 17:00"],
      learningGaps: ["Алина: Как рекомендовать блюдо без давления"],
    });

    expect(text).toContain("Что уже знаю");
    expect(text).toContain("Последняя память смены");
    expect(text).toContain("Первый учебный пробел");
    expect(text).not.toContain("Сигналы с поля");
    expect(text).not.toContain("Открытые действия:");
  });
});
