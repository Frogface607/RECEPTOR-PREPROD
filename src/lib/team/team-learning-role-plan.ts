import type { TeamLearningItem } from "./team-learning";
import { buildTeamLearningShiftCard } from "./team-learning-shift-card";
import type {
  TeamFieldContextDigest,
  TeamFieldSignal,
  TeamFieldSignalKind,
} from "./team-field-context";
import {
  countCustomLearningStandards,
  listLearningItemsForRoleWithStandards,
  type TeamLearningStandardOverride,
} from "./team-learning-standards";
import {
  getTeamRole,
  TEAM_ROLES,
  type TeamRoleId,
  type TeamTask,
} from "./team-os";
import type { TeamLearningMemberSummary } from "./team-learning-progress";

export type TeamLearningRoleBlocker = {
  memberId: string;
  memberName: string;
  nextItemTitle: string;
};

export type TeamLearningRolePlan = {
  roleId: TeamRoleId;
  roleTitle: string;
  members: number;
  totalItems: number;
  requiredItems: number;
  readyItems: number;
  soonItems: number;
  customStandards: number;
  items: TeamLearningItem[];
  requiredProgressPct: number;
  admissionPct: number;
  blockedMembers: TeamLearningRoleBlocker[];
  nextItem: TeamLearningItem | null;
};

export type TeamLearningAdmissionTaskDraft = {
  title: string;
  priority: "high" | "medium";
  audienceType: "member";
  audienceMemberId: string;
  memberName: string;
  moduleTitle: string;
  roleTitle: string;
  dueLabel: string;
};

export type TeamLearningFocusTone = "risk" | "field" | "setup" | "ready";

export type TeamLearningFocusItem = {
  id: string;
  title: string;
  detail: string;
  reason: string;
  roleTitle: string;
  moduleTitle: string;
  practiceAction: string;
  memoryPrompt: string;
  href: string;
  tone: TeamLearningFocusTone;
};

export function buildTeamLearningRolePlans(
  summaries: TeamLearningMemberSummary[],
  standards: TeamLearningStandardOverride[] = [],
): TeamLearningRolePlan[] {
  const activeSummaries = summaries.filter(
    (summary) => summary.member.status !== "paused",
  );

  return TEAM_ROLES.map((role) =>
    buildRolePlan(role.id, activeSummaries, standards),
  ).filter((plan) => plan.members > 0 || plan.totalItems > 0);
}

export function buildLearningAdmissionTaskDraft(
  plan: TeamLearningRolePlan,
): TeamLearningAdmissionTaskDraft | null {
  const blocker = plan.blockedMembers[0] ?? null;
  if (!blocker) return null;

  const moduleTitle = plan.nextItem?.title ?? blocker.nextItemTitle;

  return {
    title: `Пройти обучение: ${moduleTitle}`,
    priority: plan.admissionPct < 50 ? "high" : "medium",
    audienceType: "member",
    audienceMemberId: blocker.memberId,
    memberName: blocker.memberName,
    moduleTitle,
    roleTitle: plan.roleTitle,
    dueLabel: "до смены",
  };
}

export function buildTeamLearningFocusPlan(input: {
  plans: TeamLearningRolePlan[];
  fieldContext?: TeamFieldContextDigest | null;
}): TeamLearningFocusItem[] {
  const items: TeamLearningFocusItem[] = [];

  for (const signal of input.fieldContext?.signals ?? []) {
    const focus = focusFromFieldSignal(signal, input.plans);
    if (focus) items.push(focus);
  }

  const blocked = input.plans
    .filter((plan) => plan.blockedMembers.length > 0)
    .sort(
      (a, b) =>
        a.admissionPct - b.admissionPct ||
        b.blockedMembers.length - a.blockedMembers.length,
    );

  for (const plan of blocked) {
    const item = plan.nextItem ?? plan.items[0] ?? null;
    if (!item) continue;
    const practice = learningFocusPractice(
      item,
      "Если сотрудник не прошел обязательное обучение",
    );
    items.push({
      id: `admission-${plan.roleId}-${item.id}`,
      title: `${plan.roleTitle}: закрыть допуск`,
      detail: `${plan.blockedMembers
        .slice(0, 3)
        .map((member) => member.memberName)
        .join(", ")} — не допущены к смене.`,
      reason: "Обязательный стандарт блокирует уверенную работу в смене.",
      roleTitle: plan.roleTitle,
      moduleTitle: item.title,
      practiceAction: practice.practiceAction,
      memoryPrompt: practice.memoryPrompt,
      href: "#learning-progress",
      tone: "risk",
    });
  }

  if (items.length === 0) {
    const readyPlan = input.plans.find((plan) => plan.nextItem) ?? input.plans[0];
    const item = readyPlan?.nextItem ?? readyPlan?.items[0] ?? null;
    if (readyPlan && item) {
      const practice = learningFocusPractice(item);
      items.push({
        id: `ready-${readyPlan.roleId}-${item.id}`,
        title: `${readyPlan.roleTitle}: развитие команды`,
        detail: "Критичных блокеров нет. Можно усилить следующий стандарт.",
        reason: "План обучения готов к развитию без срочного блокера.",
        roleTitle: readyPlan.roleTitle,
        moduleTitle: item.title,
        practiceAction: practice.practiceAction,
        memoryPrompt: practice.memoryPrompt,
        href: "#learning-progress",
        tone: "ready",
      });
    }
  }

  return uniqueLearningFocus(items).slice(0, 4);
}

const OPEN_TASK_STATUSES = new Set<TeamTask["status"]>([
  "new",
  "accepted",
  "in_progress",
]);

export function findOpenLearningAdmissionTask(
  tasks: TeamTask[],
  draft: TeamLearningAdmissionTaskDraft,
): TeamTask | null {
  const draftTitle = normalizeLearningTaskTitle(draft.title);

  return (
    tasks.find(
      (task) =>
        OPEN_TASK_STATUSES.has(task.status) &&
        task.audience.type === "member" &&
        task.audience.memberId === draft.audienceMemberId &&
        normalizeLearningTaskTitle(task.title) === draftTitle,
    ) ?? null
  );
}

function normalizeLearningTaskTitle(value: string): string {
  return value.trim().replace(/\s+/g, " ").toLocaleLowerCase("ru-RU");
}

function buildRolePlan(
  roleId: TeamRoleId,
  summaries: TeamLearningMemberSummary[],
  standards: TeamLearningStandardOverride[],
): TeamLearningRolePlan {
  const roleSummaries = summaries.filter(
    (summary) => summary.member.roleId === roleId,
  );
  const items =
    roleSummaries[0]?.items ??
    listLearningItemsForRoleWithStandards(roleId, standards);
  const requiredItems = items.filter((item) => item.status === "required");
  const requiredSlots = requiredItems.length * roleSummaries.length;
  const requiredCompleted = roleSummaries.reduce(
    (sum, summary) => sum + summary.requiredCompleted,
    0,
  );
  const admittedMembers = roleSummaries.filter(
    (summary) => summary.canWorkShift,
  ).length;
  const blockedMembers = roleSummaries
    .filter((summary) => !summary.canWorkShift)
    .map((summary) => ({
      memberId: summary.member.id,
      memberName: summary.member.name,
      nextItemTitle: summary.nextItem?.title ?? "обязательный материал",
    }));

  return {
    roleId,
    roleTitle: getTeamRole(roleId).title,
    members: roleSummaries.length,
    totalItems: items.length,
    requiredItems: requiredItems.length,
    readyItems: items.filter((item) => item.status === "ready").length,
    soonItems: items.filter((item) => item.status === "soon").length,
    customStandards: countCustomLearningStandards(roleId, standards),
    items,
    requiredProgressPct:
      requiredSlots > 0
        ? Math.round((requiredCompleted / requiredSlots) * 100)
        : 100,
    admissionPct:
      roleSummaries.length > 0
        ? Math.round((admittedMembers / roleSummaries.length) * 100)
        : 100,
    blockedMembers,
    nextItem: mostCommonNextItem(roleSummaries),
  };
}

function mostCommonNextItem(
  summaries: TeamLearningMemberSummary[],
): TeamLearningItem | null {
  const counts = new Map<string, { item: TeamLearningItem; count: number }>();

  summaries.forEach((summary) => {
    if (!summary.nextItem) return;
    const existing = counts.get(summary.nextItem.id);
    counts.set(summary.nextItem.id, {
      item: summary.nextItem,
      count: (existing?.count ?? 0) + 1,
    });
  });

  return (
    [...counts.values()].sort(
      (a, b) =>
        b.count - a.count ||
        learningStatusWeight(b.item.status) -
          learningStatusWeight(a.item.status) ||
        a.item.title.localeCompare(b.item.title, "ru"),
    )[0]?.item ?? null
  );
}

function learningStatusWeight(status: TeamLearningItem["status"]): number {
  if (status === "required") return 3;
  if (status === "ready") return 2;
  return 1;
}

function focusFromFieldSignal(
  signal: TeamFieldSignal,
  plans: TeamLearningRolePlan[],
): TeamLearningFocusItem | null {
  const target = fieldSignalLearningTarget(signal.kind);
  const plan =
    target.roleIds
      .map((roleId) => plans.find((candidate) => candidate.roleId === roleId))
      .find(Boolean) ?? null;
  if (!plan) return null;

  const item =
    target.moduleIds
      .map((moduleId) => plan.items.find((candidate) => candidate.id === moduleId))
      .find(Boolean) ??
    plan.nextItem ??
    plan.items[0] ??
    null;
  if (!item) return null;
  const practice = learningFocusPractice(item, target.checklistTitle);

  return {
    id: `field-${signal.kind}-${plan.roleId}-${item.id}`,
    title: `${target.title}: ${plan.roleTitle}`,
    detail: signal.detail,
    reason: target.reason,
    roleTitle: plan.roleTitle,
    moduleTitle: item.title,
    practiceAction: practice.practiceAction,
    memoryPrompt: practice.memoryPrompt,
    href: "#learning-progress",
    tone: signal.kind === "training" ? "setup" : "field",
  };
}

function fieldSignalLearningTarget(kind: TeamFieldSignalKind): {
  title: string;
  reason: string;
  roleIds: TeamRoleId[];
  moduleIds: string[];
  checklistTitle?: string;
} {
  if (kind === "conflict") {
    return {
      title: "Разобрать конфликт",
      reason: "Полевой факт говорит, что команде нужен единый сценарий общения с гостем.",
      roleIds: ["service", "venue_manager"],
      moduleIds: ["guest-conflict-service", "shift-brief"],
      checklistTitle: "Если полевая заметка про конфликт",
    };
  }
  if (kind === "stock") {
    return {
      title: "Закрыть стоп-лист",
      reason: "Кухня и зал должны одинаково понимать замену, заготовки и стоп до посадки.",
      roleIds: ["chef", "line_cook", "venue_manager"],
      moduleIds: ["kitchen-stop-list", "shift-open-close"],
      checklistTitle: "Если полевая заметка про стоп-лист",
    };
  }
  if (kind === "guest" || kind === "service") {
    return {
      title: "Усилить сервис и продажи",
      reason: "Запросы гостей превращаются в деньги только когда команда знает, что рекомендовать.",
      roleIds: ["service", "venue_manager"],
      moduleIds: [
        "service-recommendation",
        "sales-eight-upsell",
        "guest-feedback",
      ],
      checklistTitle: "Если гости спрашивают и команда не знает, что предложить",
    };
  }
  if (kind === "money") {
    return {
      title: "Объяснить цифры",
      reason: "Команда должна понимать, как выручка, ФОТ и маржа связаны с действиями смены.",
      roleIds: ["owner", "operations_manager", "venue_manager"],
      moduleIds: ["restaurant-numbers-basics", "iiko-cash-discipline"],
      checklistTitle: "Если смена не понимает цифры",
    };
  }
  if (kind === "training" || kind === "team") {
    return {
      title: "Убрать хаос в стандартах",
      reason: "В заметках есть сигнал, что люди не понимают правило или работают по-разному.",
      roleIds: ["venue_manager", "operations_manager", "service"],
      moduleIds: ["shift-brief", "shift-open-close"],
      checklistTitle: "Если команда работает по-разному",
    };
  }

  return {
    title: "Подготовить бриф",
    reason: "Событие, погода или итог смены должны стать коротким фокусом для команды.",
    roleIds: ["venue_manager", "operations_manager", "owner"],
    moduleIds: ["shift-brief", "shift-open-close"],
    checklistTitle: "Если событие повлияло на смену",
  };
}

function learningFocusPractice(
  item: TeamLearningItem,
  checklistTitle?: string,
): Pick<TeamLearningFocusItem, "practiceAction" | "memoryPrompt"> {
  const card = buildTeamLearningShiftCard(item, checklistTitle);

  return {
    practiceAction: card.action,
    memoryPrompt: card.fieldNote,
  };
}

function uniqueLearningFocus(
  items: TeamLearningFocusItem[],
): TeamLearningFocusItem[] {
  const seen = new Set<string>();

  return items.filter((item) => {
    const key = `${item.roleTitle}:${item.moduleTitle}:${item.tone}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}
