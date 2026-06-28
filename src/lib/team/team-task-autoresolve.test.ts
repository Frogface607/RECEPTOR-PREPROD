import { describe, expect, test } from "vitest";
import {
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
});
