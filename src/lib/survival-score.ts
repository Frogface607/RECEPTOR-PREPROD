import type { DailyBrief } from "./brief/daily-brief";
import type { RevenueDataQuality } from "./iiko/data-quality";
import type { CategoryStat, DishStat } from "./iiko/models";
import type { TeamRoleId, TeamTask } from "./team/team-os";
import {
  buildMenuEngineering,
  type MenuEngineeringReport,
} from "./menu-engineering";

export type SurvivalStatus = "critical" | "serious" | "watch" | "stable";
export type SurvivalRole = "owner" | "manager" | "chef" | "service";

export type SurvivalFactor = {
  id:
    | "revenue-drop"
    | "category-concentration"
    | "hit-dependency"
    | "volume-trap"
    | "tail-risk"
    | "margin-unknown"
    | "revenue-momentum"
    | "data-coverage"
    | "comparison-missing";
  level: "critical" | "serious" | "watch" | "info";
  title: string;
  metric: string;
  detail: string;
  action: string;
};

export type SurvivalQuestion = {
  role: SurvivalRole;
  text: string;
};

export type SurvivalTaskDraft = {
  title: string;
  priority: TeamTask["priority"];
  roleId: TeamRoleId;
  dueLabel: string;
  impactLabel?: string;
  sourceLabel?: string;
  audienceMemberId?: string;
  audienceMemberName?: string;
};

export type SurvivalBrief = {
  score: number;
  status: SurvivalStatus;
  title: string;
  summary: string;
  factors: SurvivalFactor[];
  actions: string[];
  taskDrafts: SurvivalTaskDraft[];
  questions: SurvivalQuestion[];
  missingData: string[];
  menu: MenuEngineeringReport;
};

type BuildSurvivalBriefInput = {
  dailyBrief: DailyBrief;
  dishes: DishStat[];
  categories: CategoryStat[];
  dataQuality?: RevenueDataQuality;
};

function pct(value: number): string {
  return `${value > 0 ? "+" : ""}${value.toFixed(1)}%`;
}

function share(part: number, total: number): number {
  if (total <= 0) return 0;
  return Math.round((part / total) * 1000) / 10;
}

function statusFromScore(score: number): SurvivalStatus {
  if (score >= 70) return "critical";
  if (score >= 45) return "serious";
  if (score > 0) return "watch";
  return "stable";
}

function titleFromStatus(status: SurvivalStatus): string {
  if (status === "critical") return "Прибыль под давлением";
  if (status === "serious") return "Нужен управленческий разбор";
  if (status === "watch") return "Есть зоны внимания";
  return "Операционная картина спокойная";
}

function pushFactor(
  factors: SurvivalFactor[],
  factor: SurvivalFactor,
): number {
  factors.push(factor);
  if (factor.level === "critical") return 30;
  if (factor.level === "serious") return 20;
  if (factor.level === "watch") return 10;
  return 4;
}

export function buildSurvivalBrief({
  dailyBrief,
  dishes,
  categories,
  dataQuality,
}: BuildSurvivalBriefInput): SurvivalBrief {
  const factors: SurvivalFactor[] = [];
  const menu = buildMenuEngineering(dishes);
  const categoryTotal = categories.reduce(
    (sum, category) => sum + category.dishSumInt,
    0,
  );
  const topCategory = [...categories].sort(
    (a, b) => b.dishSumInt - a.dishSumInt,
  )[0];
  const topCategoryShare = topCategory
    ? share(topCategory.dishSumInt, categoryTotal)
    : 0;
  const topDish = dishes[0];
  const topDishShare = topDish
    ? share(topDish.dishSumInt, dailyBrief.revenue.current)
    : 0;

  let score = 0;

  if (dataQuality && dataQuality.status !== "ok") {
    score += pushFactor(factors, {
      id: "data-coverage",
      level: dataQuality.status === "risk" ? "serious" : "watch",
      title: "Данные требуют проверки",
      metric: `${dataQuality.activeDays}/${dataQuality.requestedDays}`,
      detail:
        dataQuality.status === "risk"
          ? "Период покрыт не полностью. Сначала проверь дату подключения, смену iiko или выбранный диапазон, иначе выводы будут слишком уверенными."
          : "Источник выглядит рабочим, но часть периода или метрик требует внимания перед жесткими решениями.",
      action:
        "Проверить период, дату подключения iiko и покрытие дней перед тем, как ставить план по выручке.",
    });
  }

  if (!dailyBrief.revenue.comparisonAvailable) {
    score += pushFactor(factors, {
      id: "comparison-missing",
      level: "info",
      title: "Нет базы сравнения",
      metric: "—",
      detail:
        "Рост или просадку нельзя честно посчитать без предыдущего периода с продажами. Этот диапазон лучше считать стартовой базой.",
      action:
        "Зафиксировать этот период как базу и не оценивать динамику, пока не появится сопоставимый период.",
    });
  }

  if (dailyBrief.revenue.comparisonAvailable && dailyBrief.revenue.deltaPct <= -25) {
    score += pushFactor(factors, {
      id: "revenue-drop",
      level: "critical",
      title: "Выручка резко просела",
      metric: pct(dailyBrief.revenue.deltaPct),
      detail:
        "Это уже не шум периода. Нужно искать конкретную причину: дни, смены, стоп-лист, спрос, команда, промо.",
      action:
        "Уже сегодня сравнить слабые дни и смены с нормальными: кто работал, что было в стопе, какие категории просели.",
    });
  } else if (dailyBrief.revenue.comparisonAvailable && dailyBrief.revenue.deltaPct < -10) {
    score += pushFactor(factors, {
      id: "revenue-drop",
      level: "serious",
      title: "Выручка ниже нормы",
      metric: pct(dailyBrief.revenue.deltaPct),
      detail:
        "Падение ещё можно быстро отловить, если разобрать категории и смены до конца дня.",
      action:
        "Поставить управляющему задачу найти 2 причины просадки и 1 действие на вечер.",
    });
  } else if (dailyBrief.revenue.comparisonAvailable) {
    score += pushFactor(factors, {
      id: "revenue-momentum",
      level: dailyBrief.revenue.deltaPct >= 0 ? "info" : "watch",
      title: dailyBrief.revenue.deltaPct >= 0 ? "Выручка держится" : "Лёгкая просадка",
      metric: pct(dailyBrief.revenue.deltaPct),
      detail:
        "Даже при плюсе важно проверять, не куплен ли рост дорогой себестоимостью, скидками или перегрузкой команды.",
      action:
        "Зафиксировать, что сработало, и проверить маржу лидеров меню.",
    });
  }

  if (topCategory && topCategoryShare >= 55) {
    score += pushFactor(factors, {
      id: "category-concentration",
      level: "critical",
      title: "Выручка зависит от одной категории",
      metric: `${topCategoryShare}%`,
      detail: `Категория «${topCategory.categoryName}» забирает больше половины выручки. Это рабочая зависимость, но её нужно держать под контролем: наличие, качество и себестоимость могут заметно изменить итог периода.`,
      action:
        "Сегодня проверить наличие, маржу и скорость отдачи этой категории, а залу дать альтернативы для апсейла.",
    });
  } else if (topCategory && topCategoryShare >= 42) {
    score += pushFactor(factors, {
      id: "category-concentration",
      level: "serious",
      title: "Слишком большая опора на одну категорию",
      metric: `${topCategoryShare}%`,
      detail: `Категория «${topCategory.categoryName}» держит непропорционально большую долю выручки. Это опасно без контроля маржи и наличия.`,
      action:
        "Проверить себестоимость, стоп-лист и скорость отдачи этой категории перед вечерней посадкой.",
    });
  } else if (topCategory && topCategoryShare >= 30) {
    score += pushFactor(factors, {
      id: "category-concentration",
      level: "watch",
      title: "Есть категория-локомотив",
      metric: `${topCategoryShare}%`,
      detail: `«${topCategory.categoryName}» сильно влияет на итог периода. Это может быть силой, если маржа и наличие под контролем.`,
      action:
        "Дать команде понятный фокус продаж, но не забыть проверить маржинальность.",
    });
  }

  if (topDish && topDishShare >= 18) {
    score += pushFactor(factors, {
      id: "hit-dependency",
      level: "watch",
      title: "Зависимость от хита",
      metric: `${topDishShare}%`,
      detail: `«${topDish.dishName}» заметно влияет на выручку. Если оно уйдёт в стоп или потеряет качество, день может просесть.`,
      action:
        "Проверить заготовки, скорость отдачи и апсейл вокруг этого блюда.",
    });
  }

  if (menu.volumeTrap) {
    score += pushFactor(factors, {
      id: "volume-trap",
      level: "watch",
      title: "Много порций, мало денег",
      metric: `${menu.volumeTrap.amountShare.toFixed(1)}% порций`,
      detail: `«${menu.volumeTrap.dishName}» продаётся часто, но вклад в выручку ниже объёма. Это кандидат на пересборку цены, порции или апсейла.`,
      action:
        "Попросить шефа и зал проверить: почему берут часто, но чек растёт слабо.",
    });
  }

  const tailShare = menu.cItems.length / Math.max(menu.aItems.length + menu.bItems.length + menu.cItems.length, 1);
  if (tailShare >= 0.35) {
    score += pushFactor(factors, {
      id: "tail-risk",
      level: "watch",
      title: "Раздутый хвост меню",
      metric: `${menu.cItems.length} C-поз.`,
      detail:
        "Слабые позиции занимают внимание кухни, закупки и место в меню. Хорошее меню должно быть легче, понятнее и прибыльнее.",
      action:
        "Отметить C-позиции: оставить, переименовать, заменить или убрать.",
    });
  }

  score += pushFactor(factors, {
    id: "margin-unknown",
    level: "info",
    title: "Маржа пока не доказана",
    metric: "нет себестоимости",
    detail:
      "Сейчас Receptor видит выручку и продажи, но точная прибыль появится после связи с техкартами, закупками и iiko-номенклатурой.",
    action:
      "Начать с техкарт A-позиций: сначала проверяем блюда, которые двигают деньги.",
  });

  score = Math.min(100, Math.max(0, score));
  const status = statusFromScore(score);
  const priorityFactors = factors.filter((factor) => factor.level !== "info");
  const actions = [
    priorityFactors[0]?.action ??
      "Сегодня проверить маржу A-позиций и слабые смены.",
    priorityFactors[1]?.action ??
      "Дать залу один понятный фокус продаж на вечер.",
    "Выбрать 3 блюда из A/B и проверить по ним себестоимость, наличие и скорость отдачи.",
  ];
  const taskDrafts = buildTaskDrafts(priorityFactors, factors, actions, status);

  return {
    score,
    status,
    title: titleFromStatus(status),
    summary:
      status === "critical"
        ? "Есть признаки, которые могут съедать прибыль: падение денег, концентрация меню или слепая зона по марже."
        : "Система не видит грубых перекосов, но прибыль всё равно нужно проверять через маржу, меню и дисциплину смен.",
    factors,
    actions,
    taskDrafts,
    questions: [
      {
        role: "owner",
        text: "Какая одна причина сильнее всего объясняет деньги этого периода: трафик, меню, команда или наличие?",
      },
      {
        role: "manager",
        text: "Какая смена просела и чем она отличалась от нормальной?",
      },
      {
        role: "chef",
        text: "У каких A-позиций маржа может быть хуже, чем кажется по выручке?",
      },
      {
        role: "service",
        text: "Что официанты должны продавать сегодня осознанно, а не по привычке?",
      },
    ],
    missingData: [
      "себестоимость",
      "закупочные цены и списания",
      "наличие/стоп-лист по ключевым позициям",
    ],
    menu,
  };
}

function buildTaskDrafts(
  priorityFactors: SurvivalFactor[],
  allFactors: SurvivalFactor[],
  fallbackActions: string[],
  status: SurvivalStatus,
): SurvivalTaskDraft[] {
  const sourceFactors =
    priorityFactors.length > 0 ? priorityFactors : allFactors.slice(0, 2);
  const drafts = sourceFactors.slice(0, 3).map((factor) => ({
    title: trimTaskTitle(factor.action),
    priority: priorityForFactor(factor, status),
    roleId: roleForFactor(factor),
    dueLabel: dueForFactor(factor),
  }));

  for (const action of fallbackActions) {
    if (drafts.length >= 3) break;
    drafts.push({
      title: trimTaskTitle(action),
      priority: status === "critical" ? "high" : "medium",
      roleId: "venue_manager",
      dueLabel: "сегодня",
    });
  }

  return drafts;
}

function trimTaskTitle(value: string): string {
  const normalized = value.replace(/\s+/g, " ").trim();
  if (normalized.length <= 220) return normalized;
  return `${normalized.slice(0, 217).trim()}...`;
}

function priorityForFactor(
  factor: SurvivalFactor,
  status: SurvivalStatus,
): TeamTask["priority"] {
  if (factor.level === "critical" || status === "critical") return "high";
  if (factor.level === "serious") return "high";
  if (factor.level === "info") return "low";
  return "medium";
}

function roleForFactor(factor: SurvivalFactor): TeamRoleId {
  if (factor.id === "revenue-drop" || factor.id === "data-coverage") {
    return "venue_manager";
  }
  if (factor.id === "comparison-missing" || factor.id === "revenue-momentum") {
    return "operations_manager";
  }
  if (factor.id === "hit-dependency") return "service";
  return "chef";
}

function dueForFactor(factor: SurvivalFactor): string {
  if (factor.id === "hit-dependency") return "до вечерней смены";
  if (factor.id === "data-coverage" || factor.id === "comparison-missing") {
    return "сегодня";
  }
  if (factor.id === "category-concentration" || factor.id === "revenue-drop") {
    return "до 17:00";
  }
  return "до вечерней посадки";
}
