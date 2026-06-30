import type {
  OwnerReview,
  OwnerReviewAction,
  OwnerReviewTone,
} from "@/lib/owner-review";

export type OwnerMorningReviewRow = {
  label: string;
  value: string;
  detail: string;
  tone: OwnerReviewTone;
};

const BI_EVIDENCE_LABELS = new Set([
  "Деньги",
  "ФОТ",
  "Маржа",
  "Юнит-экономика",
  "План/факт",
  "Покрытие",
  "Опора меню",
  "Хит",
]);

function primaryBiRow(review: OwnerReview): OwnerMorningReviewRow {
  const riskyBi =
    review.evidence.find(
      (item) => BI_EVIDENCE_LABELS.has(item.label) && item.tone !== "good",
    ) ?? review.evidence.find((item) => item.label === "Деньги");

  if (riskyBi) {
    return {
      label: "Цифры",
      value: `${riskyBi.label}: ${riskyBi.value}`,
      detail: riskyBi.detail,
      tone: riskyBi.tone,
    };
  }

  return {
    label: "Цифры",
    value: review.readiness.title,
    detail: review.summary,
    tone: review.readiness.tone,
  };
}

function fieldRow(review: OwnerReview): OwnerMorningReviewRow {
  const field = review.evidence.find((item) => item.label === "Поле");
  if (field) {
    return {
      label: "Поле",
      value: field.value,
      detail: field.detail,
      tone: field.tone,
    };
  }

  return {
    label: "Поле",
    value: "нет заметок",
    detail:
      "Попросите управляющего собрать короткий факт смены: гости, стоп-лист, конфликт, событие или трение команды.",
    tone: "watch",
  };
}

function actionRow(
  review: OwnerReview,
  mainAction: OwnerReviewAction | null,
): OwnerMorningReviewRow {
  if (mainAction) {
    return {
      label: "Действие",
      value: mainAction.impactLabel
        ? `${mainAction.title} · ${mainAction.impactLabel}`
        : mainAction.title,
      detail: mainAction.detail,
      tone: mainAction.tone,
    };
  }

  if (review.readiness.action) {
    return {
      label: "Действие",
      value: review.readiness.action.label,
      detail: review.readiness.detail,
      tone: review.readiness.tone,
    };
  }

  return {
    label: "Действие",
    value: "контур спокойный",
    detail: "Критичных действий нет. Можно смотреть детали ниже.",
    tone: "good",
  };
}

export function buildOwnerMorningReviewRows({
  review,
  mainAction = review.actions[0] ?? null,
}: {
  review: OwnerReview;
  mainAction?: OwnerReviewAction | null;
}): OwnerMorningReviewRow[] {
  return [
    primaryBiRow(review),
    fieldRow(review),
    actionRow(review, mainAction),
  ];
}
