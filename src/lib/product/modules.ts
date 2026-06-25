export type ProductModuleId =
  | "owner_cockpit"
  | "context_engine"
  | "menu_os"
  | "team_os"
  | "guest_os"
  | "delivery_os"
  | "marketing_os"
  | "integration_pack";

export type ProductModule = {
  id: ProductModuleId;
  title: string;
  shortTitle: string;
  promise: string;
  includes: string[];
  displayOrder: number;
};

export const RESTAURANT_OS_MODULES: ProductModule[] = [
  {
    id: "owner_cockpit",
    title: "Панель владельца",
    shortTitle: "Панель",
    promise: "Ежедневный бриф, BI, риски, действия и AI-помощник владельца.",
    includes: [
      "Ежедневный утренний бриф",
      "iiko BI",
      "выручка, чеки, смены и блюда",
      "риски и действия владельца",
      "недельный стратегический отчет",
    ],
    displayOrder: 1,
  },
  {
    id: "context_engine",
    title: "Память заведения",
    shortTitle: "Память",
    promise:
      "Память заведения: формат, цели, команда, системы, ограничения и правила решений.",
    includes: [
      "анкета заведения",
      "цели владельца",
      "карта команды и ролей",
      "стандарты бренда и сервиса",
      "правила AI и данных",
    ],
    displayOrder: 2,
  },
  {
    id: "menu_os",
    title: "Меню",
    shortTitle: "Меню",
    promise: "QR-меню, стоп-лист, техкарты, food cost и инженерия меню.",
    includes: [
      "QR-меню",
      "стоп-лист",
      "техкарты",
      "food cost",
      "запуск новых блюд",
      "связь с артикулами iiko",
    ],
    displayOrder: 3,
  },
  {
    id: "team_os",
    title: "Команда",
    shortTitle: "Команда",
    promise: "Роли, доступы, смены, база знаний, задачи и сообщения команды.",
    includes: [
      "роли сотрудников",
      "права доступа",
      "расписание смен",
      "база знаний",
      "задачи",
      "сообщения команды",
    ],
    displayOrder: 4,
  },
  {
    id: "integration_pack",
    title: "Интеграции",
    shortTitle: "Интеграции",
    promise: "iiko/R-Keeper, Telegram, VK и настраиваемые AI-провайдеры.",
    includes: [
      "iiko Cloud/RMS",
      "R-Keeper позже",
      "Telegram",
      "VK",
      "OpenAI/OpenRouter/YandexGPT/GigaChat/Qwen на выбор",
    ],
    displayOrder: 5,
  },
  {
    id: "guest_os",
    title: "Гости",
    shortTitle: "Гости",
    promise: "Брони, лист ожидания, кабинет гостя и история обращений с сайта.",
    includes: [
      "брони",
      "лист ожидания",
      "план зала",
      "кабинет гостя",
      "чат на сайте",
    ],
    displayOrder: 6,
  },
  {
    id: "delivery_os",
    title: "Доставка",
    shortTitle: "Доставка",
    promise: "Доставка и самовывоз со статусами и уведомлениями гостя.",
    includes: [
      "меню доставки",
      "заказы на самовывоз",
      "статусы заказов",
      "уведомления гостя",
      "рабочий контур кухни и администратора",
    ],
    displayOrder: 7,
  },
  {
    id: "marketing_os",
    title: "Маркетинг",
    shortTitle: "Маркетинг",
    promise: "Посты, события, афиши, ответы на отзывы и публикации в каналах.",
    includes: [
      "генерация контента",
      "анонсы событий",
      "афиши",
      "ответы на отзывы",
      "публикации в Telegram/VK",
    ],
    displayOrder: 8,
  },
];

export const FOUNDATION_MODULE_IDS: ProductModuleId[] = [
  "owner_cockpit",
  "context_engine",
  "menu_os",
  "integration_pack",
];

export function getProductModule(id: ProductModuleId): ProductModule {
  const productModule = RESTAURANT_OS_MODULES.find((item) => item.id === id);
  if (!productModule) throw new Error(`Unknown product module: ${id}`);
  return productModule;
}

export function listFoundationModules(): ProductModule[] {
  return FOUNDATION_MODULE_IDS.map(getProductModule);
}

export function listProductModules(): ProductModule[] {
  return [...RESTAURANT_OS_MODULES].sort(
    (a, b) => a.displayOrder - b.displayOrder,
  );
}
