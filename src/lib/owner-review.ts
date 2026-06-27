import { formatInteger, formatRubles } from "@/lib/format";
import { buildMenuEngineering } from "@/lib/menu-engineering";
import type { DailyBrief } from "@/lib/brief/daily-brief";
import type { RevenueDataQuality } from "@/lib/iiko/data-quality";
import {
  buildLaborInsights,
  type LaborBiSummary,
  type LaborInsightTone,
} from "@/lib/team/labor-bi";
import type {
  CategoryStat,
  DishStat,
  RevenuePoint,
  RevenueSummary,
  ShiftStat,
} from "@/lib/iiko/models";
import type { SurvivalTaskDraft } from "@/lib/survival-score";

export type OwnerReviewConfidence = "high" | "medium" | "low";
export type OwnerReviewTone = "risk" | "watch" | "good";
export type OwnerReviewRole = "owner" | "manager" | "chef" | "service";

export type OwnerReviewEvidence = {
  label: string;
  value: string;
  detail: string;
  tone: OwnerReviewTone;
};

export type OwnerReviewHypothesis = {
  title: string;
  why: string;
  check: string;
  role: OwnerReviewRole;
  tone: OwnerReviewTone;
};

export type OwnerReviewQuestion = {
  role: OwnerReviewRole;
  text: string;
};

export type OwnerReview = {
  verdict: string;
  summary: string;
  confidence: OwnerReviewConfidence;
  confidenceReason: string;
  evidence: OwnerReviewEvidence[];
  hypotheses: OwnerReviewHypothesis[];
  questions: OwnerReviewQuestion[];
  tasks: SurvivalTaskDraft[];
};

type BuildOwnerReviewInput = {
  summary: RevenueSummary;
  dishes: DishStat[];
  categories: CategoryStat[];
  shifts: ShiftStat[];
  brief: DailyBrief;
  dataQuality: RevenueDataQuality;
  dataMode: "live" | "mock";
  labor?: LaborBiSummary;
};

function pct(part: number, total: number): number {
  if (total <= 0) return 0;
  return Math.round((part / total) * 1000) / 10;
}

function deltaText(brief: DailyBrief): string {
  if (!brief.revenue.comparisonAvailable) return "нет базы";
  const value = brief.revenue.deltaPct;
  return `${value > 0 ? "+" : ""}${value}%`;
}

function topByRevenue(points: RevenuePoint[], direction: "min" | "max") {
  const positive = points.filter((point) => point.revenue > 0);
  if (!positive.length) return null;
  return [...positive].sort((a, b) =>
    direction === "min" ? a.revenue - b.revenue : b.revenue - a.revenue,
  )[0];
}

function roleTask(role: OwnerReviewRole): SurvivalTaskDraft["roleId"] {
  if (role === "manager") return "venue_manager";
  if (role === "chef") return "chef";
  if (role === "service") return "service";
  return "operations_manager";
}

function rolePriority(tone: OwnerReviewTone): SurvivalTaskDraft["priority"] {
  if (tone === "risk") return "high";
  if (tone === "watch") return "medium";
  return "low";
}

function roleDue(role: OwnerReviewRole): string {
  if (role === "service") return "до вечерней смены";
  if (role === "chef") return "до 17:00";
  return "сегодня";
}

function ownerToneFromLabor(tone: LaborInsightTone): OwnerReviewTone {
  if (tone === "risk") return "risk";
  if (tone === "good") return "good";
  return "watch";
}

function laborEvidence(input: LaborBiSummary): OwnerReviewEvidence {
  const primaryInsight = buildLaborInsights(input)[0];
  const pct =
    input.laborCostPct === null
      ? "нет данных"
      : `${input.laborCostPct.toLocaleString("ru-RU", {
          maximumFractionDigits: 1,
        })}%`;
  const detail =
    input.missingRates > 0
      ? `${input.missingRates} ставок не заведено`
      : `${formatRubles(input.laborCost)} за период`;

  return {
    label: "ФОТ",
    value: pct,
    detail,
    tone: primaryInsight ? ownerToneFromLabor(primaryInsight.tone) : "watch",
  };
}

function confidenceFor(input: BuildOwnerReviewInput): {
  confidence: OwnerReviewConfidence;
  reason: string;
} {
  if (input.dataMode === "mock") {
    return {
      confidence: "low",
      reason: "показаны демо-данные, для решений нужен live iiko",
    };
  }

  if (input.dataQuality.status === "risk") {
    return {
      confidence: "low",
      reason: "период покрыт не полностью или нет продаж в выгрузке",
    };
  }

  if (!input.brief.revenue.comparisonAvailable) {
    return {
      confidence: "medium",
      reason: "есть live-данные, но пока нет честной базы сравнения",
    };
  }

  if (input.dataQuality.status === "watch") {
    return {
      confidence: "medium",
      reason: "данные рабочие, но часть метрик требует проверки",
    };
  }

  return {
    confidence: "high",
    reason: "есть live-данные, покрытие периода и база сравнения",
  };
}

function buildVerdict(input: {
  brief: DailyBrief;
  quality: RevenueDataQuality;
  dataMode: "live" | "mock";
  topCategory?: CategoryStat;
  topCategoryShare: number;
  topDish?: DishStat;
  topDishShare: number;
  volumeTrap?: DishStat | null;
}) {
  if (input.dataMode === "mock") {
    return {
      verdict: "Пока это демо-разбор. Подключите iiko, чтобы советы стали управленческими.",
      summary:
        "Интерфейс показывает логику работы, но не должен использоваться для решений по сменам, меню и деньгам.",
    };
  }

  if (input.quality.status === "risk") {
    return {
      verdict: "Сначала нужно проверить данные, иначе выводы будут шумными.",
      summary:
        "В периоде не хватает продаж или покрытия дней. До решений по команде и меню лучше открыть проверку iiko.",
    };
  }

  if (
    input.brief.revenue.comparisonAvailable &&
    input.brief.revenue.deltaPct <= -15
  ) {
    return {
      verdict: "Главная задача — найти причину просадки, а не просто смотреть график.",
      summary:
        "Сравните слабые дни, смены, стоп-лист и структуру продаж. Обычно деньги теряются в одном из этих мест.",
    };
  }

  if (input.topCategory && input.topCategoryShare >= 42) {
    return {
      verdict: `Выручка слишком сильно держится на категории «${input.topCategory.categoryName}».`,
      summary:
        "Это может быть силой, если маржа и наличие под контролем. Без проверки это риск для прибыли.",
    };
  }

  if (input.topDish && input.topDishShare >= 18) {
    return {
      verdict: `День заметно зависит от блюда «${input.topDish.dishName}».`,
      summary:
        "Проверьте заготовки, скорость отдачи и апсейл вокруг хита, чтобы не потерять вечернюю выручку.",
    };
  }

  if (input.volumeTrap) {
    return {
      verdict: `Есть позиция с большим объемом, но слабым вкладом в деньги.`,
      summary:
        "Такие блюда часто выглядят успешными по порциям, но не двигают чек. Их стоит проверить по цене, порции и апсейлу.",
    };
  }

  if (
    input.brief.revenue.comparisonAvailable &&
    input.brief.revenue.deltaPct >= 10
  ) {
    return {
      verdict: "Период выглядит сильнее базы. Важно зафиксировать, что сработало.",
      summary:
        "Рост надо превратить в повторяемый сценарий: смена, промо, посадка, погода, команда, меню.",
    };
  }

  return {
    verdict: "Критичного перекоса не видно. Фокус — маржа и дисциплина смен.",
    summary:
      "Даже спокойная выручка может скрывать дорогую себестоимость, слабый апсейл или лишний хвост меню.",
  };
}

export function buildOwnerReview(input: BuildOwnerReviewInput): OwnerReview {
  const categoryTotal = input.categories.reduce(
    (sum, category) => sum + category.dishSumInt,
    0,
  );
  const topCategory = [...input.categories].sort(
    (a, b) => b.dishSumInt - a.dishSumInt,
  )[0];
  const topCategoryShare = topCategory
    ? pct(topCategory.dishSumInt, categoryTotal)
    : 0;
  const topDish = input.dishes[0];
  const topDishShare = topDish ? pct(topDish.dishSumInt, input.summary.revenue) : 0;
  const weakestDay = topByRevenue(input.summary.points, "min");
  const strongestDay = topByRevenue(input.summary.points, "max");
  const weakestShift = [...input.shifts]
    .filter((shift) => shift.revenue > 0)
    .sort((a, b) => a.revenue - b.revenue)[0];
  const menu = buildMenuEngineering(input.dishes);
  const { confidence, reason } = confidenceFor(input);
  const laborInsights = input.labor ? buildLaborInsights(input.labor) : [];
  const primaryLaborInsight =
    laborInsights.find((insight) => insight.tone !== "good") ?? laborInsights[0];
  const { verdict, summary } = buildVerdict({
    brief: input.brief,
    quality: input.dataQuality,
    dataMode: input.dataMode,
    topCategory,
    topCategoryShare,
    topDish,
    topDishShare,
    volumeTrap: menu.volumeTrap,
  });

  const evidence: OwnerReviewEvidence[] = [
    {
      label: "Деньги",
      value: formatRubles(input.summary.revenue),
      detail: `динамика: ${deltaText(input.brief)}`,
      tone:
        input.brief.revenue.comparisonAvailable && input.brief.revenue.deltaPct < 0
          ? "risk"
          : "good",
    },
    ...(input.labor ? [laborEvidence(input.labor)] : []),
    {
      label: "Покрытие",
      value: `${input.dataQuality.activeDays}/${input.dataQuality.requestedDays}`,
      detail: input.dataQuality.summary,
      tone: input.dataQuality.status === "risk" ? "risk" : "watch",
    },
    {
      label: "Опора меню",
      value: topCategory ? `${topCategoryShare}%` : "нет данных",
      detail: topCategory
        ? `категория «${topCategory.categoryName}»`
        : "категории не пришли из BI",
      tone: topCategoryShare >= 42 ? "risk" : topCategoryShare >= 30 ? "watch" : "good",
    },
    {
      label: "Хит",
      value: topDish ? `${topDishShare}%` : "нет данных",
      detail: topDish
        ? `${topDish.dishName}, ${formatInteger(topDish.dishAmountInt)} порций`
        : "блюда не пришли из BI",
      tone: topDishShare >= 18 ? "watch" : "good",
    },
  ];

  const hypotheses: OwnerReviewHypothesis[] = [];

  if (input.dataQuality.status === "risk" || input.dataMode === "mock") {
    hypotheses.push({
      title: "Данные могут подменять реальность",
      why:
        input.dataMode === "mock"
          ? "Сейчас включен демо-контур, поэтому выводы одинаковые по смыслу."
          : "В выбранном периоде не хватает продаж или дней с данными.",
      check: "Откройте проверку iiko и убедитесь, что ключ, организация и OLAP работают.",
      role: "owner",
      tone: "risk",
    });
  }

  if (primaryLaborInsight && primaryLaborInsight.tone !== "good") {
    hypotheses.push({
      title: primaryLaborInsight.title,
      why: primaryLaborInsight.detail,
      check: primaryLaborInsight.action,
      role: primaryLaborInsight.tone === "setup" ? "owner" : "manager",
      tone: ownerToneFromLabor(primaryLaborInsight.tone),
    });
  }

  if (
    input.brief.revenue.comparisonAvailable &&
    input.brief.revenue.deltaPct < -10
  ) {
    hypotheses.push({
      title: "Просадка могла прийти из смены, а не из меню",
      why: `Динамика к базе: ${deltaText(input.brief)}. ${
        weakestShift
          ? `Самая слабая смена: ${formatRubles(weakestShift.revenue)}.`
          : "Смены не дали явного ответа."
      }`,
      check: "Спросить управляющего: кто работал, какая была посадка, были ли стопы и жалобы.",
      role: "manager",
      tone: "risk",
    });
  }

  if (topCategory && topCategoryShare >= 30) {
    hypotheses.push({
      title: "Категория может держать оборот, но не прибыль",
      why: `«${topCategory.categoryName}» дает ${topCategoryShare}% выручки периода.`,
      check: "Проверить маржу, наличие, скорость отдачи и альтернативы для апсейла.",
      role: "chef",
      tone: topCategoryShare >= 42 ? "risk" : "watch",
    });
  }

  if (topDish && topDishShare >= 12) {
    hypotheses.push({
      title: "Хит продаж нужно защищать как операционный актив",
      why: `«${topDish.dishName}» дает ${topDishShare}% выручки и ${formatInteger(topDish.dishAmountInt)} порций.`,
      check: "Проверить стоп-лист, заготовки, качество отдачи и что официанты предлагают рядом.",
      role: "service",
      tone: topDishShare >= 18 ? "watch" : "good",
    });
  }

  if (menu.volumeTrap) {
    hypotheses.push({
      title: "Есть блюдо с большим объемом и слабым вкладом в чек",
      why: `«${menu.volumeTrap.dishName}» дает ${menu.volumeTrap.amountShare}% порций и ${menu.volumeTrap.revenueShare}% выручки.`,
      check: "Проверить цену, граммовку, подачу и возможность апсейла.",
      role: "chef",
      tone: "watch",
    });
  }

  if (hypotheses.length < 3 && weakestDay && strongestDay) {
    hypotheses.push({
      title: "Слабый день нужно объяснить событием",
      why: `${weakestDay.date}: ${formatRubles(weakestDay.revenue)} против ${strongestDay.date}: ${formatRubles(strongestDay.revenue)}.`,
      check: "Зафиксировать причину: погода, банкет, команда, промо, трафик, стоп-лист.",
      role: "manager",
      tone: "watch",
    });
  }

  const visibleHypotheses = hypotheses.slice(0, 4);
  const questions: OwnerReviewQuestion[] = visibleHypotheses.map((item) => ({
    role: item.role,
    text: item.check,
  }));
  const tasks = visibleHypotheses.slice(0, 3).map((item) => ({
    title: item.check,
    priority: rolePriority(item.tone),
    roleId: roleTask(item.role),
    dueLabel: roleDue(item.role),
  }));

  return {
    verdict,
    summary,
    confidence,
    confidenceReason: reason,
    evidence,
    hypotheses: visibleHypotheses,
    questions,
    tasks,
  };
}
