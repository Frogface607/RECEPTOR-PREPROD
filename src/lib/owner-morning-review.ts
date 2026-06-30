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

function fieldHypothesis(review: OwnerReview) {
  return (
    review.hypotheses.find(
      (item) => item.taskSourceLabel === "Полевой контекст",
    ) ?? null
  );
}

function questionSentence(question: string | null | undefined): string | null {
  const trimmed = question?.trim();
  if (!trimmed) return null;
  return `Вопрос: ${trimmed}${/[?!.]$/.test(trimmed) ? "" : "?"}`;
}

function appendBriefingQuestion(
  detail: string,
  question: string | null | undefined,
): string {
  const questionText = questionSentence(question);
  if (!questionText || detail.includes("Вопрос:")) return detail;
  return `${detail} ${questionText}`;
}

const UNTIED_FIELD_CONTEXT_QUESTION =
  "какая цифра подтверждает этот факт: выручка, ФОТ, маржа, стоп-лист или отзывы гостей";

function fieldRow(review: OwnerReview): OwnerMorningReviewRow {
  const field = review.evidence.find((item) => item.label === "Поле");
  const hypothesis = fieldHypothesis(review);

  if (field) {
    const detail = hypothesis
      ? `${field.detail} Проверка: ${hypothesis.check}`
      : appendBriefingQuestion(field.detail, UNTIED_FIELD_CONTEXT_QUESTION);

    return {
      label: "Поле",
      value: hypothesis ? `${field.value} · ${hypothesis.title}` : field.value,
      detail,
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

function bridgeRow(
  review: OwnerReview,
  bi: OwnerMorningReviewRow,
): OwnerMorningReviewRow | null {
  const field = review.evidence.find((item) => item.label === "Поле");
  const hypothesis = fieldHypothesis(review);
  if (!field || !hypothesis || bi.tone === "good") return null;

  return {
    label: "Вопрос",
    value: "Что спросить на разборе",
    detail: [
      `Объясняет ли полевой факт цифру «${bi.value}»?`,
      questionSentence(hypothesis.briefingQuestion),
      `Проверка: ${hypothesis.check}`,
    ]
      .filter((part): part is string => Boolean(part))
      .join(" "),
    tone: bi.tone === "risk" || field.tone === "risk" ? "risk" : "watch",
  };
}

function fieldActionRow(
  review: OwnerReview,
  bi: OwnerMorningReviewRow,
): OwnerMorningReviewRow | null {
  const field = review.evidence.find((item) => item.label === "Поле");
  const hypothesis = fieldHypothesis(review);
  if (!field || !hypothesis || bi.tone === "good") return null;

  const title = hypothesis.taskTitle ?? hypothesis.title;
  return {
    label: "Действие",
    value: hypothesis.impactLabel
      ? `${title} · ${hypothesis.impactLabel}`
      : title,
    detail: appendBriefingQuestion(
      `${hypothesis.why} Проверка: ${hypothesis.check}`,
      hypothesis.briefingQuestion,
    ),
    tone:
      hypothesis.tone === "risk" || field.tone === "risk" ? "risk" : "watch",
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
      detail: appendBriefingQuestion(
        mainAction.detail,
        mainAction.briefingQuestion,
      ),
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
  const bi = primaryBiRow(review);
  const bridge = bridgeRow(review, bi);
  const action = fieldActionRow(review, bi) ?? actionRow(review, mainAction);

  return [bi, fieldRow(review), ...(bridge ? [bridge] : []), action];
}
