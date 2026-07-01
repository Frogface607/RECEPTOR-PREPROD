import type { TeamFieldContextDigest } from "./team-field-context";
import type { TeamLearningFocusItem } from "./team-learning-role-plan";
import type { TeamManagerFollowUp } from "./team-manager-followup";
import type { TeamOpsReadiness } from "./team-ops-readiness";

export type TeamDailyWorkflowTone = "risk" | "work" | "ready";

export type TeamDailyWorkflowStep = {
  id: "before_shift" | "training" | "field_note" | "owner_decision";
  label: string;
  title: string;
  detail: string;
  reason: string;
  href: string;
  tone: TeamDailyWorkflowTone;
};

export type TeamDailyWorkflowLearningAdoptionFocus = {
  title: string;
  detail: string;
  reason: string;
  href: string;
  tone: TeamDailyWorkflowTone;
};

export function buildTeamDailyWorkflow(input: {
  opsReadiness: TeamOpsReadiness;
  managerFollowUp: TeamManagerFollowUp;
  learningFocus: TeamLearningFocusItem[];
  learningAdoptionFocus?: TeamDailyWorkflowLearningAdoptionFocus | null;
  fieldContext: TeamFieldContextDigest | null;
}): TeamDailyWorkflowStep[] {
  const primaryFollowUp = input.managerFollowUp.items[0] ?? null;
  const primaryLearning = input.learningFocus[0] ?? null;
  const primaryAdoption = input.learningAdoptionFocus ?? null;
  const primaryAction = input.opsReadiness.actions.find(
    (action) => action.id !== "ready",
  );

  return [
    {
      id: "before_shift",
      label: "Перед сменой",
      title: primaryFollowUp?.title ?? "Проверить готовность",
      detail:
        primaryFollowUp?.detail ??
        `${input.opsReadiness.score}% готовности: роли, допуск и ФОТ под контролем.`,
      reason: primaryFollowUp
        ? `Память команды показывает: ${primaryFollowUp.metric.toLocaleLowerCase("ru-RU")} нужно закрыть до смены.`
        : `Готовность ${input.opsReadiness.score}%: перед сменой достаточно сверить роли и план.`,
      href: primaryFollowUp?.href ?? "#shift-coverage",
      tone: primaryFollowUp
        ? followUpTone(primaryFollowUp.tone)
        : readinessTone(input.opsReadiness.status),
    },
    {
      id: "training",
      label: "Обучение",
      title:
        primaryAdoption?.title ??
        primaryLearning?.title ??
        "Закрыть стандарт дня",
      detail:
        primaryAdoption?.detail ??
        (primaryLearning
          ? `В смене: ${primaryLearning.practiceAction} После: ${primaryLearning.memoryPrompt}`
          : "Критичных учебных блокеров нет, можно закрепить следующий стандарт."),
      reason:
        primaryAdoption?.reason ??
        (primaryLearning
          ? `После обучения ждем факт в память: ${primaryLearning.memoryPrompt}`
          : "Допуски в норме: обучение можно вести как закрепление стандарта."),
      href:
        primaryAdoption?.href ?? primaryLearning?.href ?? "#learning-progress",
      tone:
        primaryAdoption?.tone ??
        (primaryLearning ? learningTone(primaryLearning.tone) : "ready"),
    },
    {
      id: "field_note",
      label: "После смены",
      title: input.fieldContext
        ? "Разобрать факты смены"
        : "Собрать итог смены",
      detail:
        input.fieldContext?.summary ??
        "Нужен короткий факт от команды: гости, стоп-лист, конфликт, погода, продажи или что проверить утром.",
      reason: input.fieldContext
        ? "Память смены уже дала контекст, его надо связать с утренним решением."
        : "Без короткого итога советник видит цифры, но не причину смены.",
      href: "#shift-summary",
      tone: input.fieldContext ? "work" : "risk",
    },
    {
      id: "owner_decision",
      label: "Утром",
      title: primaryAction?.title ?? "Дать один фокус",
      detail:
        primaryAction?.detail ??
        "Владелец видит готовность команды и может дать один понятный управленческий сигнал.",
      reason: primaryAction
        ? "Это действие связывает готовность команды с решением владельца на утро."
        : "Память собрана достаточно, чтобы дать один фокус без лишнего шума.",
      href: primaryAction?.href ?? "#team-actions",
      tone: primaryAction ? opsActionTone(primaryAction.tone) : "ready",
    },
  ];
}

function followUpTone(tone: TeamManagerFollowUp["items"][number]["tone"]) {
  if (tone === "risk") return "risk";
  if (tone === "watch") return "work";
  return "ready";
}

function readinessTone(status: TeamOpsReadiness["status"]) {
  if (status === "blocked") return "risk";
  if (status === "attention") return "work";
  return "ready";
}

function learningTone(tone: TeamLearningFocusItem["tone"]) {
  if (tone === "risk") return "risk";
  if (tone === "ready") return "ready";
  return "work";
}

function opsActionTone(tone: TeamOpsReadiness["actions"][number]["tone"]) {
  if (tone === "risk" || tone === "setup") return "risk";
  if (tone === "watch") return "work";
  return "ready";
}
