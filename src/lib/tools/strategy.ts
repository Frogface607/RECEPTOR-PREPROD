import { TOOLS } from "./catalog";

export type ToolStrategicRole =
  | "core"
  | "lead"
  | "support"
  | "caution"
  | "later";

export type ToolStrategy = {
  role: ToolStrategicRole;
  label: string;
  result: string;
  note: string;
};

export type ToolWorkflow = {
  id: string;
  title: string;
  description: string;
  promise: string;
  toolIds: string[];
};

export const TOOL_STRATEGY: Record<string, ToolStrategy> = {
  "recipe-generator": {
    role: "core",
    label: "Ядро меню",
    result: "черновик блюда для дальнейшей техкарты",
    note: "Используется как вход в Tech Card Studio, а не как отдельная игрушка.",
  },
  "kbju-calculator": {
    role: "lead",
    label: "Быстрый расчет",
    result: "КБЖУ на 100 г и порцию",
    note: "Понятный бесплатный сценарий для повара, шефа и технолога.",
  },
  "allergen-check": {
    role: "support",
    label: "Меню",
    result: "список аллергенов по составу",
    note: "Полезно внутри техкарты и QR-меню, отдельно вторично.",
  },
  "food-cost": {
    role: "core",
    label: "Ядро меню",
    result: "себестоимость, процент себестоимости и цена продажи",
    note: "Денежный сценарий: дальше связывается с прайсами и iiko-номенклатурой.",
  },
  "dish-idea": {
    role: "support",
    label: "Меню",
    result: "идеи блюд под сезон, концепцию и ограничения",
    note: "Сильнее работает, когда знает профиль заведения и продажи.",
  },
  "dish-description": {
    role: "support",
    label: "Меню",
    result: "описание блюда для гостя и меню",
    note: "Лучше работает в связке с пакетной генерацией меню.",
  },
  "menu-description": {
    role: "core",
    label: "Меню",
    result: "пакет описаний блюд для меню",
    note: "Один из самых понятных сценариев для ресторатора и маркетинга.",
  },
  "seasonal-menu": {
    role: "support",
    label: "Меню",
    result: "сезонные идеи меню",
    note: "Сильнее после профиля заведения и истории продаж.",
  },
  "wine-pairing": {
    role: "later",
    label: "Ниша",
    result: "пейринги к блюдам",
    note: "Приятная функция, но не должна отвлекать от денег и операционки.",
  },
  "menu-audit": {
    role: "core",
    label: "Управление меню",
    result: "аудит структуры меню и цен",
    note: "Сильнее всего работает вместе с iiko-продажами: популярность плюс маржа.",
  },
  "stop-list": {
    role: "core",
    label: "Команда",
    result: "замены и скрипты по стоп-листу",
    note: "Сильно раскрывается при связке с остатками, меню и задачами смены.",
  },
  "inventory-checklist": {
    role: "support",
    label: "Операционка",
    result: "чеклист инвентаризации",
    note: "Операционный шаблон, который позже связывается с остатками.",
  },
  "competitor-analysis": {
    role: "caution",
    label: "Research",
    result: "SWOT и рекомендации по конкурентам",
    note: "Нужен геоконтекст и источники, иначе ответ будет слишком общим.",
  },
  "waiter-script": {
    role: "core",
    label: "Команда",
    result: "скрипт продаж для зала",
    note: "Берет блюда, стоп-лист и тон заведения из профиля ресторана.",
  },
  "guest-complaint": {
    role: "support",
    label: "Service",
    result: "скрипт отработки жалобы",
    note: "Практично для обучения, особенно внутри стандартов сервиса.",
  },
  "job-post": {
    role: "lead",
    label: "HR",
    result: "вакансия для hh.ru или Telegram",
    note: "Простой вход в командный контур, но не центр продукта.",
  },
  "onboarding-checklist": {
    role: "support",
    label: "Команда",
    result: "план стажировки на 2 недели",
    note: "Стыкуется с обучением официантов, поваров и стандартами роли.",
  },
  "review-response": {
    role: "lead",
    label: "Репутация",
    result: "ответ на отзыв без канцелярита",
    note: "Хороший вход в маркетинг и будущий модуль репутации.",
  },
  "promo-idea": {
    role: "support",
    label: "Маркетинг",
    result: "идеи акций с механикой",
    note: "Становится сильнее после подключения iiko и истории продаж.",
  },
  "social-post": {
    role: "support",
    label: "Маркетинг",
    result: "пост для соцсетей",
    note: "Нужен как часть контент-пакета, а не как главная ценность.",
  },
  "event-announce": {
    role: "support",
    label: "Маркетинг",
    result: "анонс события",
    note: "Ценно для баров и ресторанов с событиями, но не общий core.",
  },
  "ad-legal-check": {
    role: "caution",
    label: "Осторожно",
    result: "черновая проверка рекламного текста",
    note: "Нужен дисклеймер: это помощник, а не юридическое заключение.",
  },
  "haccp-generator": {
    role: "core",
    label: "Контроль",
    result: "ККТ для техкарты",
    note: "Полезно внутри профессиональной техкарты и производственного контроля.",
  },
  "sanpin-check": {
    role: "caution",
    label: "Осторожно",
    result: "черновая санитарная консультация",
    note: "Нужна актуальная база норм и аккуратная подача.",
  },
  "morning-briefing": {
    role: "core",
    label: "Команда",
    result: "брифинг смены на сегодня",
    note: "Соединяет данные продаж, стоп-лист, задачи и командный ритм.",
  },
  "expense-optimizer": {
    role: "core",
    label: "Панель владельца",
    result: "разбор расходов и точки экономии",
    note: "Сценарий для владельца, который усиливается live P&L-данными.",
  },
  "training-quiz": {
    role: "support",
    label: "Обучение",
    result: "тест для сотрудника",
    note: "Хорошо превращается в модуль обучения команды.",
  },
};

export const TOOL_WORKFLOWS: ToolWorkflow[] = [
  {
    id: "tech-card-menu",
    title: "Техкарты и меню",
    description:
      "Блюдо, КБЖУ, себестоимость, аллергены, HACCP и описания меню в одном производственном сценарии.",
    promise:
      "Следующий уровень: PDF, история версий, ингредиенты и артикулы iiko.",
    toolIds: [
      "recipe-generator",
      "food-cost",
      "kbju-calculator",
      "allergen-check",
      "haccp-generator",
      "menu-description",
      "dish-description",
      "dish-idea",
      "seasonal-menu",
      "wine-pairing",
    ],
  },
  {
    id: "owner-operations",
    title: "Разбор и операционка",
    description:
      "Ежедневная картина для владельца: меню, расходы, стоп-лист, инвентаризация и брифинг смены.",
    promise:
      "После подключения iiko AI объясняет цифры и превращает их в действия.",
    toolIds: [
      "menu-audit",
      "expense-optimizer",
      "morning-briefing",
      "stop-list",
      "inventory-checklist",
      "competitor-analysis",
    ],
  },
  {
    id: "sales-service",
    title: "Зал и продажи",
    description:
      "Скрипты продаж, работа с жалобами, обучение и стажировка команды.",
    promise:
      "Сценарии опираются на реальные блюда, тон заведения и слабые места сервиса.",
    toolIds: [
      "waiter-script",
      "guest-complaint",
      "training-quiz",
      "onboarding-checklist",
      "job-post",
    ],
  },
  {
    id: "marketing-reputation",
    title: "Маркетинг и репутация",
    description:
      "Отзывы, акции, посты и анонсы как продолжение профиля заведения.",
    promise:
      "Маркетинг не отрывается от кухни, меню, событий и реального голоса бренда.",
    toolIds: ["review-response", "promo-idea", "social-post", "event-announce", "ad-legal-check"],
  },
  {
    id: "compliance",
    title: "Санитария и контроль",
    description:
      "HACCP и санитарные вопросы как черновик для проверки управляющим.",
    promise:
      "Помощник подсвечивает риски и чеклисты, но не заменяет юридическую или санитарную экспертизу.",
    toolIds: ["haccp-generator", "sanpin-check", "ad-legal-check"],
  },
];

export function getToolStrategy(toolId: string): ToolStrategy {
  return (
    TOOL_STRATEGY[toolId] ?? {
      role: "support",
      label: "Поддержка",
      result: "рабочий результат для ресторана",
      note: "Сценарий стоит проверять на live-данных и реальных задачах команды.",
    }
  );
}

export function getWorkflowTools(workflow: ToolWorkflow) {
  const byId = new Map(TOOLS.map((tool) => [tool.id, tool]));
  return workflow.toolIds.flatMap((id) => {
    const tool = byId.get(id);
    return tool ? [tool] : [];
  });
}
