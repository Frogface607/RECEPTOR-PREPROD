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
    label: "Ядро",
    result: "черновик блюда для дальнейшей техкарты",
    note: "Должен стать входом в Tech Card Studio, а не отдельной игрушкой.",
  },
  "kbju-calculator": {
    role: "lead",
    label: "Бесплатный вход",
    result: "КБЖУ на 100 г и порцию",
    note: "Хороший бесплатный калькулятор для трафика и доверия.",
  },
  "food-cost": {
    role: "core",
    label: "Ядро",
    result: "себестоимость, фудкост и цена продажи",
    note: "Деньги ресторана. Нужно связать с прайсами и iiko-номенклатурой.",
  },
  "allergen-check": {
    role: "support",
    label: "Поддержка",
    result: "список аллергенов по составу",
    note: "Полезно внутри техкарты и меню, отдельно вторично.",
  },
  "dish-idea": {
    role: "support",
    label: "Поддержка",
    result: "идеи блюд под сезон, концепцию и ограничения",
    note: "Сильнее работает, когда знает профиль заведения.",
  },
  "waiter-script": {
    role: "core",
    label: "Ядро",
    result: "скрипт продаж для зала",
    note: "Должен брать блюда, стоп-лист и тон заведения из профиля.",
  },
  "dish-description": {
    role: "support",
    label: "Поддержка",
    result: "описание блюда для гостя и меню",
    note: "Лучше объединить с батч-генерацией меню.",
  },
  "review-response": {
    role: "lead",
    label: "Бесплатный вход",
    result: "ответ на отзыв без канцелярита",
    note: "Хороший верх воронки, особенно после MyReply.",
  },
  "social-post": {
    role: "support",
    label: "Поддержка",
    result: "пост для соцсетей",
    note: "Нужен как часть контент-пакета, не как главная ценность.",
  },
  "ad-legal-check": {
    role: "caution",
    label: "Осторожно",
    result: "черновая проверка рекламного текста",
    note: "Без актуальной правовой базы нельзя обещать юридическую точность.",
  },
  "promo-idea": {
    role: "support",
    label: "Поддержка",
    result: "идеи акций с механикой",
    note: "Станет сильнее после подключения BI и истории продаж.",
  },
  "competitor-analysis": {
    role: "caution",
    label: "Нужен research",
    result: "SWOT и рекомендации по конкурентам",
    note: "Без deep research и геоконтекста выглядит слишком обобщенно.",
  },
  "menu-audit": {
    role: "core",
    label: "Ядро",
    result: "аудит структуры меню и цен",
    note: "Должен соединиться с iiko-продажами: маржинальность плюс популярность.",
  },
  "job-post": {
    role: "lead",
    label: "Бесплатный вход",
    result: "вакансия для hh.ru или Telegram",
    note: "Полезный простой инструмент, но не центр продукта.",
  },
  "onboarding-checklist": {
    role: "support",
    label: "Поддержка",
    result: "план стажировки на 2 недели",
    note: "Хорошо стыкуется с обучением официантов и стандартами.",
  },
  "haccp-generator": {
    role: "core",
    label: "Ядро",
    result: "ККТ для техкарты",
    note: "Ценная часть профессиональной техкарты, но нужна аккуратная подача.",
  },
  "sanpin-check": {
    role: "caution",
    label: "Осторожно",
    result: "черновая санитарная консультация",
    note: "Нужны дисклеймер и актуальная база норм, иначе риск доверия.",
  },
  "menu-description": {
    role: "core",
    label: "Ядро",
    result: "батч-описания блюд для меню",
    note: "Один из самых понятных демо-сценариев для ресторатора.",
  },
  "stop-list": {
    role: "core",
    label: "Ядро",
    result: "замены и скрипты по стоп-листу",
    note: "Сильно раскрывается при связке с остатками и меню.",
  },
  "wine-pairing": {
    role: "later",
    label: "Ниша",
    result: "пейринги к блюдам",
    note: "Приятная фича, но не должна отвлекать от денег и операционки.",
  },
  "inventory-checklist": {
    role: "support",
    label: "Поддержка",
    result: "чеклист инвентаризации",
    note: "Нужен как операционный шаблон, позже связать с остатками.",
  },
  "morning-briefing": {
    role: "core",
    label: "Ядро",
    result: "брифинг смены на сегодня",
    note: "Идеальный мост между BI, стоп-листом и командой.",
  },
  "expense-optimizer": {
    role: "core",
    label: "Ядро",
    result: "разбор расходов и точки экономии",
    note: "Деньги владельца. Потом кормить реальными P&L-данными.",
  },
  "guest-complaint": {
    role: "support",
    label: "Поддержка",
    result: "скрипт отработки жалобы",
    note: "Практично для обучения, но лучше внутри стандартов сервиса.",
  },
  "training-quiz": {
    role: "support",
    label: "Поддержка",
    result: "тест для сотрудника",
    note: "Хорошо превращается в модуль обучения команды.",
  },
  "event-announce": {
    role: "support",
    label: "Поддержка",
    result: "анонс события",
    note: "Ценно для баров и ресторанов с событиями, но не общий core.",
  },
  "seasonal-menu": {
    role: "support",
    label: "Поддержка",
    result: "сезонные идеи меню",
    note: "Сильнее после профиля заведения и истории продаж.",
  },
};

export const TOOL_WORKFLOWS: ToolWorkflow[] = [
  {
    id: "tech-card-menu",
    title: "Техкарты и меню",
    description:
      "Блюдо, КБЖУ, фудкост, аллергены, HACCP и описания меню в одном производственном сценарии.",
    promise:
      "Следующий уровень: ГОСТ/PDF, история версий, ингредиенты и артикулы iiko.",
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
    title: "BI и операционка",
    description:
      "Ежедневная картина для владельца: меню, расходы, стоп-лист, инвентаризация и брифинг смены.",
    promise:
      "Главная ценность растет после iiko: Copilot объясняет цифры и предлагает действия.",
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
      "Должно опираться на реальные блюда, тон заведения и слабые места сервиса.",
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
      "Не ядро SaaS, но сильный слой удержания и бесплатного привлечения.",
    toolIds: ["review-response", "promo-idea", "social-post", "event-announce", "ad-legal-check"],
  },
  {
    id: "compliance",
    title: "Санитария и контроль",
    description:
      "HACCP и санитарные вопросы как черновик для внутренней проверки.",
    promise:
      "Показывать аккуратно: это помощник, а не юридическое заключение.",
    toolIds: ["haccp-generator", "sanpin-check", "ad-legal-check"],
  },
];

export function getToolStrategy(toolId: string): ToolStrategy {
  return (
    TOOL_STRATEGY[toolId] ?? {
      role: "support",
      label: "Поддержка",
      result: "рабочий результат для ресторана",
      note: "Нужно проверить ценность на пилотах.",
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
