import { describe, expect, test } from "vitest";
import {
  extractLearningStandardTitleFromFieldNote,
  selectIikoMemberImportTasksToClose,
  selectLearningAdoptionTasksToClose,
  selectLaborRateTasksToClose,
  selectLearningAdmissionTasksToClose,
} from "./team-task-autoresolve";
import type { TeamTask } from "./team-os";

function task(
  id: string,
  title: string,
  memberId: string,
  status: TeamTask["status"] = "new",
): Pick<TeamTask, "id" | "title" | "status" | "audience"> {
  return {
    id,
    title,
    status,
    audience: { type: "member", memberId },
  };
}

function roleTask(
  id: string,
  title: string,
  status: TeamTask["status"] = "new",
): Pick<TeamTask, "id" | "title" | "status" | "audience"> {
  return {
    id,
    title,
    status,
    audience: { type: "role", roleId: "venue_manager" },
  };
}

describe("team task autoresolve", () => {
  test("selects open member labor-rate tasks for saved FOT rates", () => {
    const tasks = [
      task("rate-1", "Заполнить ставку ФОТ: Петр", "petr"),
      task("rate-2", "Close labor rate: Maria", "maria", "in_progress"),
      task("done-rate", "Заполнить ставку ФОТ: Олег", "oleg", "done"),
      task("other", "Проверить обучение", "petr"),
    ];

    expect(selectLaborRateTasksToClose(tasks, ["petr", "maria"])).toEqual([
      tasks[0],
      tasks[1],
    ]);
  });

  test("ignores role tasks and tasks for other members", () => {
    const tasks: Array<Pick<TeamTask, "id" | "title" | "status" | "audience">> =
      [
        {
          id: "role-rate",
          title: "Заполнить ставку ФОТ",
          status: "new",
          audience: { type: "role", roleId: "service" },
        },
        task("other-member", "Заполнить ставку ФОТ: Анна", "anna"),
      ];

    expect(selectLaborRateTasksToClose(tasks, ["petr"])).toEqual([]);
  });

  test("selects open role tasks for imported iiko staff cards", () => {
    const tasks: Array<Pick<TeamTask, "id" | "title" | "status" | "audience">> =
      [
        roleTask("import", "Импортировать сотрудников из iiko в Team OS"),
        roleTask("cards", "Создать карточки сотрудников iiko", "in_progress"),
        roleTask("done", "Импортировать сотрудников из iiko", "done"),
        roleTask("other", "Проверить выгрузку смен iiko"),
        task("member", "Импортировать сотрудников из iiko", "petr"),
      ];

    expect(selectIikoMemberImportTasksToClose(tasks)).toEqual([
      tasks[0],
      tasks[1],
    ]);
  });

  test("selects only the open admission task for the passed module", () => {
    const tasks: Array<Pick<TeamTask, "id" | "title" | "status" | "audience">> =
      [
        task(
          "admission",
          "  Пройти обучение: Как рекомендовать блюдо без давления  ",
          "petr",
          "accepted",
        ),
        task("other-module", "Пройти обучение: Работа со стоп-листом", "petr"),
        task(
          "other-member",
          "Пройти обучение: Как рекомендовать блюдо без давления",
          "anna",
        ),
        task(
          "closed",
          "Пройти обучение: Как рекомендовать блюдо без давления",
          "petr",
          "verified",
        ),
      ];

    expect(
      selectLearningAdmissionTasksToClose(tasks, {
        memberId: "petr",
        moduleTitle: "Как рекомендовать блюдо без давления",
      }),
    ).toEqual([tasks[0]]);
  });

  test("extracts a learning standard title from a shift-memory note", () => {
    expect(
      extractLearningStandardTitleFromFieldNote(
        'Итог смены по стандарту "Как рекомендовать блюдо без давления": факт - гости спрашивали лимонад.',
      ),
    ).toBe("Как рекомендовать блюдо без давления");
  });

  test("selects only the open adoption task after a matching shift-memory fact", () => {
    const tasks: Array<Pick<TeamTask, "id" | "title" | "status" | "audience">> =
      [
        task(
          "adoption",
          "Вернуть факт смены: Маша — Как рекомендовать блюдо без давления",
          "petr",
          "accepted",
        ),
        task(
          "other-module",
          "Вернуть факт смены: Маша — Восьмерка продаж и апселл в сервисе",
          "petr",
        ),
        task(
          "other-member",
          "Вернуть факт смены: Маша — Как рекомендовать блюдо без давления",
          "anna",
        ),
        task(
          "closed",
          "Вернуть факт смены: Маша — Как рекомендовать блюдо без давления",
          "petr",
          "done",
        ),
      ];

    expect(
      selectLearningAdoptionTasksToClose(tasks, {
        memberId: "petr",
        fieldNoteBody:
          'Итог смены по стандарту "Как рекомендовать блюдо без давления": факт - гости спрашивали лимонад; контекст - жара; когда/сколько - вечер; что проверить - апселл десерта.',
      }),
    ).toEqual([tasks[0]]);
  });

  test("does not close adoption tasks when the note has no standard marker", () => {
    expect(
      selectLearningAdoptionTasksToClose(
        [
          task(
            "adoption",
            "Вернуть факт смены: Маша — Как рекомендовать блюдо без давления",
            "petr",
          ),
        ],
        {
          memberId: "petr",
          fieldNoteBody: "Итог смены: гости спрашивали лимонад.",
        },
      ),
    ).toEqual([]);
  });
});
