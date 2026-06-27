import { formatInteger, formatRubles } from "@/lib/format";
import { buildMenuEngineering } from "@/lib/menu-engineering";
import type { DailyBrief } from "@/lib/brief/daily-brief";
import type { RevenueDataQuality } from "@/lib/iiko/data-quality";
import {
  buildMenuMarginNextAction,
  type MenuMarginReadiness,
} from "@/lib/menu-margin-readiness";
import {
  buildLaborInsights,
  buildLaborNextAction,
  buildLaborShiftDiagnostics,
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

export type OwnerReviewActionTarget =
  | "iiko-settings"
  | "labor-member"
  | "labor-rate"
  | "shift-coverage"
  | "shift-diagnostics"
  | "margin-diagnostics"
  | "margin-mapping";

export type OwnerReviewAction = {
  title: string;
  detail: string;
  role: OwnerReviewRole;
  tone: OwnerReviewTone;
  target: OwnerReviewActionTarget;
  memberId?: string;
  memberName?: string;
};

export type OwnerReview = {
  verdict: string;
  summary: string;
  confidence: OwnerReviewConfidence;
  confidenceReason: string;
  evidence: OwnerReviewEvidence[];
  actions: OwnerReviewAction[];
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
  margin?: MenuMarginReadiness;
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

function trimTaskTitle(value: string): string {
  const normalized = value.replace(/\s+/g, " ").trim();
  if (normalized.length <= 220) return normalized;
  return `${normalized.slice(0, 217).trim()}...`;
}

function actionSourceLabel(action: OwnerReviewAction): string {
  if (
    action.target === "labor-member" ||
    action.target === "labor-rate" ||
    action.target === "shift-coverage" ||
    action.target === "shift-diagnostics"
  ) {
    return "ФОТ и смены";
  }
  if (
    action.target === "margin-diagnostics" ||
    action.target === "margin-mapping"
  ) {
    return "Маржа и техкарты";
  }
  return "Данные iiko";
}

function actionTaskTitle(action: OwnerReviewAction): string {
  return trimTaskTitle(`${action.title}: ${action.detail}`);
}

function taskFromOwnerAction(action: OwnerReviewAction): SurvivalTaskDraft {
  return {
    title: actionTaskTitle(action),
    priority: rolePriority(action.tone),
    roleId: roleTask(action.role),
    dueLabel: roleDue(action.role),
    sourceLabel: actionSourceLabel(action),
  };
}

function taskFromHypothesis(item: OwnerReviewHypothesis): SurvivalTaskDraft {
  return {
    title: trimTaskTitle(item.check),
    priority: rolePriority(item.tone),
    roleId: roleTask(item.role),
    dueLabel: roleDue(item.role),
    sourceLabel: "Гипотеза",
  };
}

function uniqueTaskDrafts(drafts: SurvivalTaskDraft[]): SurvivalTaskDraft[] {
  const seen = new Set<string>();
  return drafts.filter((draft) => {
    const key = `${draft.roleId}:${draft.title.toLowerCase()}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function ownerToneFromLabor(tone: LaborInsightTone): OwnerReviewTone {
  if (tone === "risk") return "risk";
  if (tone === "good") return "good";
  return "watch";
}

function laborEvidence(input: LaborBiSummary): OwnerReviewEvidence {
  const primaryInsight = buildLaborInsights(input)[0];
  const blocker = input.topBlockers[0];
  const pct =
    input.laborCostPct === null
      ? "нет данных"
      : `${input.laborCostPct.toLocaleString("ru-RU", {
          maximumFractionDigits: 1,
        })}%`;
  const coverage =
    input.revenueCoveragePct === null
      ? "покрытие неизвестно"
      : `${input.revenueCoveragePct.toLocaleString("ru-RU", {
          maximumFractionDigits: 1,
        })}% выручки с точным ФОТ`;
  const detail =
    blocker
      ? `${blocker.name}: ${formatRubles(blocker.sales)} без точного ФОТ, ${coverage}`
      : input.missingRates > 0
      ? `${input.missingRates} ставок не заведено, ${coverage}`
      : `${formatRubles(input.laborCost)} за период`;

  return {
    label: "ФОТ",
    value: pct,
    detail,
    tone: primaryInsight ? ownerToneFromLabor(primaryInsight.tone) : "watch",
  };
}

function marginEvidence(input: MenuMarginReadiness): OwnerReviewEvidence {
  const nextAction = buildMenuMarginNextAction(input);
  const blocker = nextAction.blocker;
  const detail = blocker
    ? blocker.reason === "missing-cost"
      ? `${blocker.dishName}: ${formatRubles(blocker.revenue)} без закупочной цены`
      : `${blocker.dishName}: ${formatRubles(blocker.revenue)} без связи с iiko`
    : `${input.costedDishes}/${input.totalDishes} блюд с себестоимостью`;

  return {
    label: "Маржа",
    value: `${input.revenueCoveragePct}%`,
    detail,
    tone:
      input.status === "ready"
        ? "good"
        : input.status === "blocked"
          ? "risk"
          : "watch",
  };
}

function formatCoverage(value: number | null): string {
  if (value === null) return "нет данных";
  return `${value.toLocaleString("ru-RU", { maximumFractionDigits: 1 })}%`;
}

function unitEconomicsEvidence(input: {
  labor?: LaborBiSummary;
  margin?: MenuMarginReadiness;
}): OwnerReviewEvidence | null {
  if (!input.labor && !input.margin) return null;

  const labor = input.labor;
  const margin = input.margin;
  const laborIncomplete =
    Boolean(labor) && labor?.laborReadinessStatus !== "ready";
  const marginIncomplete = Boolean(margin) && margin?.status !== "ready";
  const laborPct = labor?.laborCostPct ?? null;
  const laborCoverage = formatCoverage(labor?.revenueCoveragePct ?? null);
  const marginCoverage =
    margin ? `${margin.revenueCoveragePct}%` : "нет данных";

  if (laborIncomplete && marginIncomplete) {
    return {
      label: "Экономика",
      value: "не доказана",
      detail: `ФОТ покрыт на ${laborCoverage}, маржа на ${marginCoverage} выручки.`,
      tone: "risk",
    };
  }

  if (laborIncomplete && labor) {
    return {
      label: "Экономика",
      value: "ФОТ не доказан",
      detail: `${formatRubles(labor.unpricedRevenue)} сменной выручки без точного ФОТ.`,
      tone: labor.laborReadinessStatus === "blocked" ? "risk" : "watch",
    };
  }

  if (marginIncomplete && margin) {
    return {
      label: "Экономика",
      value: "маржа не доказана",
      detail: `${formatRubles(margin.blockedRevenue)} выручки без себестоимости.`,
      tone: margin.status === "blocked" ? "risk" : "watch",
    };
  }

  if (laborPct !== null && laborPct >= 25) {
    return {
      label: "Экономика",
      value: "ФОТ давит",
      detail: `ФОТ ${formatCoverage(laborPct)} от выручки, маржа покрыта на ${marginCoverage}.`,
      tone: "risk",
    };
  }

  return {
    label: "Экономика",
    value: "можно считать",
    detail: `ФОТ ${formatCoverage(laborPct)}, маржа покрыта на ${marginCoverage}.`,
    tone: "good",
  };
}

function ownerActionFromLabor(input: LaborBiSummary): OwnerReviewAction | null {
  const nextAction = buildLaborNextAction(input);

  if (nextAction.kind === "ready") {
    const firstShiftIssue = buildLaborShiftDiagnostics(input).find(
      (shift) => shift.kind !== "healthy",
    );

    if (!firstShiftIssue) return null;

    return {
      title: firstShiftIssue.title,
      detail: firstShiftIssue.detail,
      role: "manager",
      tone: ownerToneFromLabor(firstShiftIssue.tone),
      target: "shift-diagnostics",
    };
  }

  if (nextAction.kind === "missing-shifts") {
    return {
      title: nextAction.title,
      detail: nextAction.detail,
      role: "owner",
      tone: "watch",
      target: "iiko-settings",
    };
  }

  if (nextAction.kind === "missing-member" && nextAction.blocker) {
    return {
      title: nextAction.title,
      detail: nextAction.detail,
      role: "manager",
      tone: "watch",
      target: "labor-member",
      memberName: nextAction.blocker.name,
    };
  }

  if (nextAction.kind === "missing-rate" && nextAction.blocker) {
    return {
      title: nextAction.title,
      detail: nextAction.detail,
      role: "manager",
      tone: "watch",
      target: "labor-rate",
      memberId: nextAction.blocker.memberId,
      memberName: nextAction.blocker.name,
    };
  }

  if (nextAction.kind === "expensive-labor") {
    return {
      title: nextAction.title,
      detail: nextAction.detail,
      role: "manager",
      tone: "risk",
      target: "shift-diagnostics",
    };
  }

  return null;
}

function ownerActionFromMargin(input: MenuMarginReadiness): OwnerReviewAction | null {
  const nextAction = buildMenuMarginNextAction(input);

  if (nextAction.kind === "ready") return null;

  return {
    title: nextAction.title,
    detail: nextAction.detail,
    role: nextAction.kind === "missing-cost" ? "owner" : "chef",
    tone: input.status === "blocked" ? "risk" : "watch",
    target:
      nextAction.kind === "missing-cost"
        ? "margin-diagnostics"
        : "margin-mapping",
  };
}

function laborMarginHypothesis(input: {
  labor?: LaborBiSummary;
  margin?: MenuMarginReadiness;
}): OwnerReviewHypothesis | null {
  if (!input.margin || input.margin.status === "ready") return null;
  const nextAction = buildMenuMarginNextAction(input.margin);
  const laborPct = input.labor?.laborCostPct;
  const laborIsHigh = laborPct !== null && laborPct !== undefined && laborPct >= 25;
  const topBlocker = nextAction.blocker;
  const blockerText = topBlocker
    ? `Первым закрыть «${topBlocker.dishName}» (${formatRubles(topBlocker.revenue)} выручки): ${nextAction.title}.`
    : "Начните с топ-позиций без себестоимости.";
  const marginAction = nextAction.action;

  if (!laborIsHigh) {
    return {
      title: "Маржа пока не доказана",
      why: `Себестоимость покрывает ${input.margin.revenueCoveragePct}% выручки периода. ${blockerText}`,
      check: marginAction,
      role: "chef",
      tone: input.margin.status === "blocked" ? "risk" : "watch",
    };
  }

  return {
    title: "ФОТ давит, а маржа не доказана",
    why: `ФОТ ${laborPct}% от выручки, при этом себестоимость покрывает только ${input.margin.revenueCoveragePct}% выручки. ${blockerText}`,
    check: `${marginAction} После этого решать: резать часы, менять расписание или править меню.`,
    role: "owner",
    tone: "risk",
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

  if (input.labor?.laborReadinessStatus === "blocked") {
    return {
      confidence: "low",
      reason: "ФОТ по сменам не доказан: не закрыты сотрудники или ставки",
    };
  }

  if (!input.brief.revenue.comparisonAvailable) {
    return {
      confidence: "medium",
      reason: "есть live-данные, но пока нет честной базы сравнения",
    };
  }

  if (input.labor?.laborReadinessStatus === "partial") {
    return {
      confidence: "medium",
      reason: "ФОТ считается частично: часть сменной выручки без точных ставок",
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
  labor?: LaborBiSummary;
  margin?: MenuMarginReadiness;
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

  const laborIncomplete =
    Boolean(input.labor) && input.labor?.laborReadinessStatus !== "ready";
  const marginIncomplete =
    Boolean(input.margin) && input.margin?.status !== "ready";
  const laborPct = input.labor?.laborCostPct;

  if (laborIncomplete && marginIncomplete) {
    return {
      verdict: "Сначала нужно доказать экономику смены: ФОТ и маржа неполные.",
      summary:
        "Решения про прибыль, расписание и меню будут шумными, пока часть смен без точного ФОТ, а часть выручки без себестоимости.",
    };
  }

  if (
    laborPct !== null &&
    laborPct !== undefined &&
    laborPct >= 25 &&
    marginIncomplete
  ) {
    return {
      verdict: "ФОТ давит, а маржа пока не доказана.",
      summary:
        "Сначала закрыть себестоимость топ-позиций, затем решать: менять расписание, цену, порции или продажи в смене.",
    };
  }

  if (marginIncomplete) {
    return {
      verdict: "Прибыль периода пока не доказана: не хватает себестоимости.",
      summary:
        "Выручка есть, но без связки блюд с техкартами и закупочными ценами нельзя честно понять, что ресторан заработал.",
    };
  }

  if (laborIncomplete) {
    return {
      verdict: "ФОТ периода пока не доказан: часть смен без ставок.",
      summary:
        "Сначала закройте сотрудников и ставки в Team OS, иначе стоимость команды будет занижена.",
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
  const marginHypothesis = laborMarginHypothesis({
    labor: input.labor,
    margin: input.margin,
  });
  const { verdict, summary } = buildVerdict({
    brief: input.brief,
    quality: input.dataQuality,
    dataMode: input.dataMode,
    labor: input.labor,
    margin: input.margin,
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
    ...(input.margin ? [marginEvidence(input.margin)] : []),
    ...(() => {
      const evidence = unitEconomicsEvidence({
        labor: input.labor,
        margin: input.margin,
      });
      return evidence ? [evidence] : [];
    })(),
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
  const actions = [
    input.dataQuality.status === "risk" || input.dataMode === "mock"
      ? ({
          title: "Проверить источник данных",
          detail:
            input.dataMode === "mock"
              ? "Сейчас открыт демо-контур. Для решений нужен live iiko."
              : input.dataQuality.summary,
          role: "owner",
          tone: "risk",
          target: "iiko-settings",
        } satisfies OwnerReviewAction)
      : null,
    input.labor ? ownerActionFromLabor(input.labor) : null,
    input.margin ? ownerActionFromMargin(input.margin) : null,
  ]
    .filter((item): item is OwnerReviewAction => item !== null)
    .slice(0, 3);

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

  if (marginHypothesis) {
    hypotheses.push(marginHypothesis);
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
  const tasks = uniqueTaskDrafts([
    ...actions.map(taskFromOwnerAction),
    ...visibleHypotheses.map(taskFromHypothesis),
  ]).slice(0, 3);

  return {
    verdict,
    summary,
    confidence,
    confidenceReason: reason,
    evidence,
    actions,
    hypotheses: visibleHypotheses,
    questions,
    tasks,
  };
}
