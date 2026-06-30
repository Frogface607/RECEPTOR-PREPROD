import { describe, expect, test } from "vitest";
import type { StaffMember, TeamTask } from "./team-os";
import {
  buildTeamLearningSummaries,
  type TeamLearningProgress,
} from "./team-learning-progress";
import {
  buildLearningAdmissionTaskDraft,
  buildTeamLearningFocusPlan,
  buildTeamLearningRolePlans,
  findOpenLearningAdmissionTask,
} from "./team-learning-role-plan";

const staff: StaffMember[] = [
  {
    id: "service-1",
    name: "Маша",
    roleId: "service",
    venueId: "venue-1",
    status: "active",
    shiftLabel: "зал",
  },
  {
    id: "service-2",
    name: "Петр",
    roleId: "service",
    venueId: "venue-1",
    status: "active",
    shiftLabel: "зал",
  },
  {
    id: "chef-1",
    name: "Роман",
    roleId: "chef",
    venueId: "venue-1",
    status: "paused",
    shiftLabel: "кухня",
  },
];

const progress: TeamLearningProgress[] = [
  {
    venueId: "venue-1",
    membershipId: "service-1",
    userId: null,
    moduleId: "service-recommendation",
    bestPercentage: 100,
    lastPercentage: 100,
    correct: 3,
    total: 3,
    passed: true,
    answers: [1, 0, 2],
    completedAt: "2026-06-27T10:00:00.000Z",
    updatedAt: "2026-06-27T10:00:00.000Z",
  },
];

describe("buildTeamLearningRolePlans", () => {
  test("summarizes admission and next role lesson from member progress", () => {
    const summaries = buildTeamLearningSummaries(staff, progress);
    const plans = buildTeamLearningRolePlans(summaries);
    const service = plans.find((plan) => plan.roleId === "service");

    expect(service).toMatchObject({
      roleTitle: "Официант",
      members: 2,
      totalItems: 6,
      requiredItems: 1,
      requiredProgressPct: 50,
      admissionPct: 50,
    });
    expect(service?.blockedMembers).toEqual([
      {
        memberId: "service-2",
        memberName: "Петр",
        nextItemTitle: "Как рекомендовать блюдо без давления",
      },
    ]);
    expect(service?.nextItem?.id).toBe("service-recommendation");
  });

  test("creates a task draft for the first blocked admission", () => {
    const summaries = buildTeamLearningSummaries(staff, progress);
    const service = buildTeamLearningRolePlans(summaries).find(
      (plan) => plan.roleId === "service",
    );

    expect(service).toBeDefined();
    const draft = buildLearningAdmissionTaskDraft(service!);

    expect(draft).toEqual({
      title: "Пройти обучение: Как рекомендовать блюдо без давления",
      priority: "medium",
      audienceType: "member",
      audienceMemberId: "service-2",
      memberName: "Петр",
      moduleTitle: "Как рекомендовать блюдо без давления",
      roleTitle: "Официант",
      dueLabel: "до смены",
    });
  });

  test("finds an existing open task for the same blocked admission", () => {
    const summaries = buildTeamLearningSummaries(staff, progress);
    const service = buildTeamLearningRolePlans(summaries).find(
      (plan) => plan.roleId === "service",
    );
    const draft = buildLearningAdmissionTaskDraft(service!);
    expect(draft).toBeDefined();

    const tasks: TeamTask[] = [
      {
        id: "task-other",
        venueId: "venue-1",
        title: draft!.title,
        source: "manager",
        priority: "medium",
        status: "new",
        audience: { type: "member", memberId: "service-1" },
        dueLabel: "today",
      },
      {
        id: "task-existing",
        venueId: "venue-1",
        title: `  ${draft!.title}  `,
        source: "manager",
        priority: "medium",
        status: "accepted",
        audience: { type: "member", memberId: "service-2" },
        dueLabel: "today",
      },
    ];

    expect(findOpenLearningAdmissionTask(tasks, draft!)?.id).toBe(
      "task-existing",
    );
  });

  test("ignores completed learning admission tasks", () => {
    const summaries = buildTeamLearningSummaries(staff, progress);
    const service = buildTeamLearningRolePlans(summaries).find(
      (plan) => plan.roleId === "service",
    );
    const draft = buildLearningAdmissionTaskDraft(service!);
    expect(draft).toBeDefined();

    const tasks: TeamTask[] = [
      {
        id: "task-closed",
        venueId: "venue-1",
        title: draft!.title,
        source: "manager",
        priority: "medium",
        status: "verified",
        audience: { type: "member", memberId: "service-2" },
        dueLabel: "today",
      },
    ];

    expect(findOpenLearningAdmissionTask(tasks, draft!)).toBeNull();
  });

  test("keeps role lesson catalog visible even before staff is created", () => {
    const plans = buildTeamLearningRolePlans([]);
    const owner = plans.find((plan) => plan.roleId === "owner");

    expect(owner).toMatchObject({
      roleTitle: "Владелец",
      members: 0,
      totalItems: 5,
      admissionPct: 100,
      requiredProgressPct: 100,
    });
  });

  test("turns field service signals into a concrete learning focus", () => {
    const summaries = buildTeamLearningSummaries(staff, progress);
    const plans = buildTeamLearningRolePlans(summaries);
    const focus = buildTeamLearningFocusPlan({
      plans,
      fieldContext: {
        totalNotes: 1,
        signalCount: 1,
        summary: "Вопросы гостей: Маша — гости просили безалкогольный коктейль.",
        signals: [
          {
            kind: "service",
            title: "Сервис и продажи",
            detail:
              "Маша — гости просили безалкогольный коктейль, официанты не знали что предложить.",
            sourceCount: 1,
            latestAtLabel: "23:10",
          },
        ],
      },
    });

    expect(focus[0]).toMatchObject({
      title: "Усилить сервис и продажи: Официант",
      roleTitle: "Официант",
      moduleTitle: "Как рекомендовать блюдо без давления",
      tone: "field",
    });
  });

  test("falls back to admission blockers when field context is empty", () => {
    const summaries = buildTeamLearningSummaries(staff, progress);
    const plans = buildTeamLearningRolePlans(summaries);
    const focus = buildTeamLearningFocusPlan({ plans });

    expect(focus[0]).toMatchObject({
      title: "Официант: закрыть допуск",
      moduleTitle: "Как рекомендовать блюдо без давления",
      tone: "risk",
    });
  });
});
