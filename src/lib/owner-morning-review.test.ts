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
        learningModuleTitle: "Брифинг смены и передача контекста",
        learningChecklistTitle: "Если полевая заметка про стоп-лист",
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
        label: "Память смены",
        value: "2 сигнала · Проверить стоп-лист и потерянные продажи",
        detail: "Стоп-лист: Маша — закончилась мята",
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
          "Проверка: Сверить, какие позиции закончились",
        ),
        tone: "risk",
      }),
    ]);
    expect(rows[2].detail).not.toContain("Стандарт:");
    expect(rows[2].detail).not.toContain("Чеклист:");
    expect(rows[3].detail).not.toContain("Стандарт:");
    expect(rows[3].detail).not.toContain("Чеклист:");
  });

  test("prompts for field notes when the owner review has no field context", () => {
    const review = baseReview();
    review.evidence = review.evidence.filter((item) => item.label !== "Поле");
    review.actions[0] = {
      ...review.actions[0],
      briefingQuestion: "какая смена, человек или ставка съедает прибыль",
      learningModuleTitle: "Цифры ресторана простым языком",
      learningChecklistTitle: "Если BI показал перерасход ФОТ",
    };

    const rows = buildOwnerMorningReviewRows({ review });

    expect(rows[1]).toMatchObject({
      label: "Память смены",
      value: "нет заметок",
      tone: "watch",
    });
    expect(rows[1].detail).toContain("оставить короткий итог");
    expect(rows[2]).toMatchObject({
      label: "Действие",
      value: "Разобрать дорогую смену · 38% ФОТ",
      tone: "risk",
    });
    expect(rows[2].detail).toContain(
      "Вопрос: какая смена, человек или ставка съедает прибыль?",
    );
    expect(rows[2].detail).not.toContain("Стандарт:");
    expect(rows[2].detail).not.toContain("Чеклист:");
    expect(rows).toHaveLength(3);
  });

  test("keeps risky money field context visible even when primary BI is calm", () => {
    const review = baseReview();
    review.evidence = review.evidence.map((item) =>
      item.label === "Деньги" || item.label === "ФОТ"
        ? { ...item, tone: "good" as const }
        : item,
    );
    review.hypotheses = [
      {
        title: "Разобрать ФОТ и маржу смены",
        why: "Маржа и ФОТ смены: Саша — маржинальные закуски не предлагали",
        check:
          "Сверить ФОТ смены, средний чек, скидки и продажи маржинальных позиций.",
        role: "manager",
        tone: "risk",
        taskSourceLabel: "Полевой контекст",
        impactLabel: "1 сигнал",
        briefingQuestion:
          "что смена продавала, где потеряла валовую прибыль и какой фокус дать на следующий бриф",
        learningModuleTitle: "Брифинг смены и передача контекста",
        learningChecklistTitle: "Если полевая заметка про ФОТ или маржу",
      },
    ];

    const rows = buildOwnerMorningReviewRows({ review });

    expect(rows).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          label: "Вопрос",
          value: "Что спросить на разборе",
          detail: expect.stringContaining(
            "что смена продавала, где потеряла валовую прибыль",
          ),
          tone: "risk",
        }),
        expect.objectContaining({
          label: "Действие",
          value: "Разобрать ФОТ и маржу смены · 1 сигнал",
          detail: expect.stringContaining(
            "Проверка: Сверить ФОТ смены",
          ),
          tone: "risk",
        }),
      ]),
    );
  });

  test("turns unlinked field context into a morning briefing question", () => {
    const review = baseReview();

    const rows = buildOwnerMorningReviewRows({ review });

    expect(rows[1]).toMatchObject({
      label: "Память смены",
      value: "2 сигнала",
      tone: "risk",
    });
    expect(rows[1].detail).toContain(
      "Вопрос: какая цифра подтверждает этот факт: выручка, ФОТ, маржа, стоп-лист или отзывы гостей?",
    );
    expect(rows).toHaveLength(3);
  });

  test("keeps standard adoption visible in the owner morning rows", () => {
    const review = baseReview();
    review.evidence.push({
      label: "Стандарт",
      value: "Нужен факт",
      detail:
        "Маша: стандарт сдан, но нужен итог смены, где его применили.",
      tone: "risk",
    });

    const rows = buildOwnerMorningReviewRows({ review });

    expect(rows[2]).toMatchObject({
      label: "Стандарт",
      value: "Нужен факт",
      detail: expect.stringContaining("Маша"),
      tone: "risk",
    });
    expect(rows).toHaveLength(4);
  });
});
