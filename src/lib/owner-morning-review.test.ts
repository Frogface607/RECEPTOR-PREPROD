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
        tone: "risk",
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
    const review = baseReview();
    review.hypotheses = [
      {
        title: "Проверить стоп-лист и потерянные продажи",
        why: "Стоп-лист: Маша — закончилась мята",
        check:
          "Сверить, какие позиции закончились и сколько выручки они давали.",
        role: "manager",
        tone: "risk",
        taskSourceLabel: "Полевой контекст",
        impactLabel: "2 сигнала",
        briefingQuestion:
          "что закончилось, сколько продаж потеряли и кто отвечает за запас",
      },
    ];

    const rows = buildOwnerMorningReviewRows({ review });

    expect(rows).toEqual([
      expect.objectContaining({
        label: "Цифры",
        value: "ФОТ: 38%",
        detail: expect.stringContaining("смена дорогая"),
        tone: "risk",
      }),
      expect.objectContaining({
        label: "Поле",
        value: "2 сигнала · Проверить стоп-лист и потерянные продажи",
        detail: expect.stringContaining("сколько выручки"),
        tone: "risk",
      }),
      expect.objectContaining({
        label: "Вопрос",
        value: "Что спросить на разборе",
        detail: expect.stringContaining(
          "Вопрос: что закончилось, сколько продаж потеряли и кто отвечает за запас?",
        ),
        tone: "risk",
      }),
      expect.objectContaining({
        label: "Действие",
        value: "Проверить стоп-лист и потерянные продажи · 2 сигнала",
        detail: expect.stringContaining(
          "Вопрос: что закончилось, сколько продаж потеряли и кто отвечает за запас?",
        ),
        tone: "risk",
      }),
    ]);
  });

  test("prompts for field notes when the owner review has no field context", () => {
    const review = baseReview();
    review.evidence = review.evidence.filter((item) => item.label !== "Поле");
    review.actions[0] = {
      ...review.actions[0],
      briefingQuestion: "какая смена, человек или ставка съедает прибыль",
    };

    const rows = buildOwnerMorningReviewRows({ review });

    expect(rows[1]).toMatchObject({
      label: "Поле",
      value: "нет заметок",
      tone: "watch",
    });
    expect(rows[1].detail).toContain("собрать короткий факт смены");
    expect(rows[2]).toMatchObject({
      label: "Действие",
      value: "Разобрать дорогую смену · 38% ФОТ",
      tone: "risk",
    });
    expect(rows[2].detail).toContain(
      "Вопрос: какая смена, человек или ставка съедает прибыль?",
    );
    expect(rows).toHaveLength(3);
  });

  test("turns unlinked field context into a morning briefing question", () => {
    const review = baseReview();

    const rows = buildOwnerMorningReviewRows({ review });

    expect(rows[1]).toMatchObject({
      label: "Поле",
      value: "2 сигнала",
      tone: "risk",
    });
    expect(rows[1].detail).toContain(
      "Вопрос: какая цифра подтверждает этот факт: выручка, ФОТ, маржа, стоп-лист или отзывы гостей?",
    );
    expect(rows).toHaveLength(3);
  });
});
