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

const BI_EVIDENCE_PRIORITY: Record<string, number> = {
  "Юнит-экономика": 100,
  ФОТ: 90,
  Маржа: 85,
  "План/факт": 80,
  Покрытие: 70,
  "Опора меню": 60,
  Хит: 50,
  Деньги: 40,
};

function tonePriority(tone: OwnerReviewTone): number {
  if (tone === "risk") return 300;
  if (tone === "watch") return 200;
  return 100;
}

function biPriority(label: string): number {
  return BI_EVIDENCE_PRIORITY[label] ?? 0;
}

function primaryBiRow(review: OwnerReview): OwnerMorningReviewRow {
  const riskyBi = review.evidence
    .filter((item) => BI_EVIDENCE_LABELS.has(item.label))
    .toSorted((a, b) => {
      const toneDelta = tonePriority(b.tone) - tonePriority(a.tone);
      if (toneDelta !== 0) return toneDelta;
      return biPriority(b.label) - biPriority(a.label);
    })[0];

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
  const fieldHypothesis =
    review.hypotheses.find(
      (item) => item.taskSourceLabel === "Полевой контекст",
    ) ?? null;

  if (field) {
    return {
      label: "Поле",
      value: fieldHypothesis
        ? `${field.value} · ${fieldHypothesis.title}`
        : field.value,
      detail: fieldHypothesis
        ? `${field.detail} Проверка: ${fieldHypothesis.check}`
        : field.detail,
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
