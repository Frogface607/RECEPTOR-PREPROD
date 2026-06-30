import { describe, expect, test } from "vitest";
import { buildOwnerMorningReviewRows } from "./owner-morning-review";
import type { OwnerReview } from "./owner-review";

function baseReview(): OwnerReview {
  return {
    verdict: "Выручка требует внимания",
    summary: "Период нужно разобрать через смены и команду.",
    confidence: "medium",
    confidenceReason: "Есть продажи и часть операционного контекста.",
    readiness: {
      status: "partial",
      score: 72,
      title: "частично готово",
      detail: "Не хватает полевого контекста и закрытых задач.",
      missing: [],
      action: { label: "Открыть Team OS", target: "team-actions" },
      tone: "watch",
    },
    operationalPulse: null,
    evidence: [
      {
        label: "Деньги",
        value: "120 000 ₽",
        detail: "динамика: -8%",
        tone: "good",
      },
      {
        label: "ФОТ",
        value: "38%",
        detail: "смена дорогая относительно выручки",
        tone: "risk",
      },
      {
        label: "Поле",
        value: "2 сигнала",
        detail: "Стоп-лист: Маша — закончилась мята",
        tone: "risk",
      },
    ],
    actions: [
      {
        title: "Разобрать дорогую смену",
        detail: "Проверить состав смены и выручку по часам.",
        role: "manager",
        tone: "risk",
        target: "shift-diagnostics",
        impactLabel: "38% ФОТ",
      },
    ],
    hypotheses: [],
    questions: [],
    tasks: [],
  };
}

describe("buildOwnerMorningReviewRows", () => {
  test("builds a compact owner morning review from BI, field context and action", () => {
    const rows = buildOwnerMorningReviewRows({ review: baseReview() });

    expect(rows).toEqual([
      expect.objectContaining({
        label: "Цифры",
        value: "ФОТ: 38%",
        detail: expect.stringContaining("смена дорогая"),
        tone: "risk",
      }),
      expect.objectContaining({
        label: "Поле",
        value: "2 сигнала",
        detail: expect.stringContaining("закончилась мята"),
        tone: "risk",
      }),
      expect.objectContaining({
        label: "Действие",
        value: "Разобрать дорогую смену · 38% ФОТ",
        detail: expect.stringContaining("состав смены"),
        tone: "risk",
      }),
    ]);
  });

  test("prompts for field notes when the owner review has no field context", () => {
    const review = baseReview();
    review.evidence = review.evidence.filter((item) => item.label !== "Поле");

    const rows = buildOwnerMorningReviewRows({ review });

    expect(rows[1]).toMatchObject({
      label: "Поле",
      value: "нет заметок",
      tone: "watch",
    });
    expect(rows[1].detail).toContain("собрать короткий факт смены");
  });
});
