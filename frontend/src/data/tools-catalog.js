/**
 * RECEPTOR Tools — Catalog of AI instruments for restaurant professionals.
 *
 * Each tool: id, name, description, icon, category, fields[], prompt builder, free tier.
 * Tools are prompt-based (1-2 fields → AI result) or calculator-based (instant compute).
 */

export const CATEGORIES = [
  { id: 'chef',       name: 'Шеф-повар',    icon: 'ChefHat',    color: 'emerald' },
  { id: 'waiter',     name: 'Официанты',     icon: 'Users',      color: 'blue' },
  { id: 'marketing',  name: 'Маркетинг',     icon: 'Megaphone',  color: 'pink' },
  { id: 'management', name: 'Управление',    icon: 'BarChart3',  color: 'purple' },
  { id: 'hr',         name: 'HR & Персонал', icon: 'UserPlus',   color: 'amber' },
  { id: 'legal',      name: 'Юрист & HACCP', icon: 'Shield',     color: 'cyan' },
];

export const TOOLS = [
  // ═══════════ ШЕФ-ПОВАР ═══════════
  {
    id: 'recipe-generator',
    category: 'chef',
    name: 'Генератор рецептов',
    description: 'Создаёт полный рецепт с ингредиентами, шагами приготовления и подачей',
    icon: 'Utensils',
    fields: [
      { id: 'dish', label: 'Название блюда или идея', placeholder: 'Том Ям с креветками', required: true },
      { id: 'style', label: 'Стиль / ограничения', placeholder: 'Без лактозы, азиатская кухня', required: false },
    ],
    buildPrompt: (f) =>
      `Создай подробный рецепт блюда "${f.dish}"${f.style ? `. Стиль: ${f.style}` : ''}.
Включи: список ингредиентов с граммовками, пошаговое приготовление, время, подачу, советы шефа.
Формат: markdown.`,
    free: true,
  },
  {
    id: 'kbju-calculator',
    category: 'chef',
    name: 'Калькулятор КБЖУ',
    description: 'Рассчитывает белки, жиры, углеводы и калории на 100г и на порцию',
    icon: 'Calculator',
    fields: [
      { id: 'ingredients', label: 'Ингредиенты (каждый с новой строки)', placeholder: 'Куриная грудка 200г\nРис 150г\nОливковое масло 15мл', required: true, multiline: true },
    ],
    buildPrompt: (f) =>
      `Рассчитай КБЖУ (калории, белки, жиры, углеводы) для блюда с ингредиентами:
${f.ingredients}

Выведи таблицу: каждый ингредиент + итого на 100г и на полную порцию.
Формат: markdown таблица.`,
    free: true,
  },
  {
    id: 'food-cost',
    category: 'chef',
    name: 'Расчёт себестоимости',
    description: 'Считает себестоимость блюда и рекомендует цену продажи',
    icon: 'DollarSign',
    fields: [
      { id: 'ingredients', label: 'Ингредиенты с ценами', placeholder: 'Лосось 200г — 350₽/кг\nРис 150г — 80₽/кг\nСоевый соус 30мл — 250₽/л', required: true, multiline: true },
      { id: 'target_margin', label: 'Целевая наценка (%)', placeholder: '300', required: false },
    ],
    buildPrompt: (f) =>
      `Рассчитай себестоимость блюда:
${f.ingredients}

${f.target_margin ? `Целевая наценка: ${f.target_margin}%` : 'Рекомендуй наценку для ресторана (обычно 250-350%)'}

Выведи: себестоимость каждого ингредиента, итого, рекомендуемую цену продажи, фудкост %.
Формат: markdown.`,
    free: true,
  },
  {
    id: 'allergen-check',
    category: 'chef',
    name: 'Проверка аллергенов',
    description: 'Определяет все аллергены в блюде по составу ингредиентов',
    icon: 'AlertTriangle',
    fields: [
      { id: 'ingredients', label: 'Состав блюда', placeholder: 'Мука, яйца, молоко, сливочное масло, сахар, ваниль', required: true },
    ],
    buildPrompt: (f) =>
      `Проанализируй состав блюда на аллергены:
${f.ingredients}

Определи ВСЕ аллергены из списка: глютен, молоко, яйца, арахис, орехи, рыба, морепродукты, соя, сельдерей, горчица, кунжут, люпин, моллюски, диоксид серы.
Для каждого найденного аллергена укажи в каком ингредиенте он содержится.
Формат: markdown.`,
    free: true,
  },
  {
    id: 'dish-idea',
    category: 'chef',
    name: 'Идея нового блюда',
    description: 'Генерирует креативные идеи блюд на основе кухни, сезона или тренда',
    icon: 'Lightbulb',
    fields: [
      { id: 'context', label: 'Тип кухни / сезон / тренд', placeholder: 'Итальянская кухня, осеннее меню', required: true },
      { id: 'constraints', label: 'Ограничения', placeholder: 'Без мяса, бюджет до 200₽ себестоимость', required: false },
    ],
    buildPrompt: (f) =>
      `Предложи 5 креативных идей блюд для ресторана.
Контекст: ${f.context}
${f.constraints ? `Ограничения: ${f.constraints}` : ''}

Для каждого блюда: название, краткое описание, ключевые ингредиенты, примерная себестоимость.
Формат: markdown.`,
    free: true,
  },

  // ═══════════ ОФИЦИАНТЫ ═══════════
  {
    id: 'waiter-script',
    category: 'waiter',
    name: 'Скрипт продаж',
    description: 'Создаёт скрипт для официанта: приветствие, допродажи, работа с возражениями',
    icon: 'MessageSquare',
    fields: [
      { id: 'venue_type', label: 'Тип заведения', placeholder: 'Итальянский ресторан среднего сегмента', required: true },
      { id: 'upsell', label: 'Что допродавать', placeholder: 'Вино, десерты, сезонные блюда', required: false },
    ],
    buildPrompt: (f) =>
      `Создай скрипт продаж для официанта в "${f.venue_type}".

Включи:
1. Приветствие и посадка (2-3 варианта)
2. Рекомендации блюд (как предложить красиво)
3. Допродажи: ${f.upsell || 'напитки, десерты, закуски'}
4. Работа с возражениями ("дорого", "не голодный", "не знаю что выбрать")
5. Прощание и расчёт

Стиль: дружелюбный, но профессиональный. Формат: markdown.`,
    free: true,
  },
  {
    id: 'dish-description',
    category: 'waiter',
    name: 'Описание блюда для гостя',
    description: 'Красивое описание блюда для меню или устной рекомендации гостю',
    icon: 'FileText',
    fields: [
      { id: 'dish', label: 'Блюдо и состав', placeholder: 'Стейк Рибай, мраморная говядина, гриль, овощи, соус демиглас', required: true },
    ],
    buildPrompt: (f) =>
      `Напиши красивое, аппетитное описание блюда для меню ресторана:
${f.dish}

Создай 3 варианта:
1. Для печатного меню (2-3 строки, изысканно)
2. Для устной рекомендации официанта (живая речь, 2 предложения)
3. Для Instagram/соцсетей (с эмодзи, вкусно, продающе)

Формат: markdown.`,
    free: false,
  },

  // ═══════════ МАРКЕТИНГ ═══════════
  {
    id: 'review-response',
    category: 'marketing',
    name: 'Ответ на отзыв',
    description: 'Генерирует профессиональный ответ на отзыв гостя (позитивный или негативный)',
    icon: 'MessageCircle',
    fields: [
      { id: 'review', label: 'Текст отзыва', placeholder: 'Ждали еду 40 минут, стейк пережарен, официант грубый...', required: true, multiline: true },
    ],
    buildPrompt: (f) =>
      `Напиши профессиональный ответ от лица ресторана на отзыв гостя:

"${f.review}"

Правила:
- Если негативный: извинись, прими ответственность, предложи решение (скидка/приглашение)
- Если позитивный: поблагодари, выдели конкретику, пригласи снова
- Тон: тёплый, профессиональный, без шаблонности
- 3-5 предложений

Формат: готовый текст для публикации.`,
    free: true,
  },
  {
    id: 'social-post',
    category: 'marketing',
    name: 'Пост для соцсетей',
    description: 'Создаёт пост для Instagram, VK или Telegram канала ресторана',
    icon: 'Share2',
    fields: [
      { id: 'topic', label: 'Тема поста', placeholder: 'Новое сезонное меню, бранч по выходным, скидка 20%', required: true },
      { id: 'platform', label: 'Площадка', placeholder: 'Instagram / VK / Telegram', required: false },
    ],
    buildPrompt: (f) =>
      `Напиши пост для ресторана в ${f.platform || 'Instagram'}.
Тема: ${f.topic}

Включи: цепляющий заголовок, текст (3-5 предложений), call to action, 5-7 хэштегов.
Тон: живой, тёплый, не корпоративный.
Формат: готовый к публикации текст.`,
    free: false,
  },
  {
    id: 'ad-legal-check',
    category: 'marketing',
    name: 'Проверка рекламы по закону',
    description: 'Проверяет рекламный текст на соответствие ФЗ "О рекламе"',
    icon: 'Scale',
    fields: [
      { id: 'ad_text', label: 'Текст рекламы', placeholder: 'Лучшие бургеры в городе! Скидка 50% только сегодня!', required: true, multiline: true },
    ],
    buildPrompt: (f) =>
      `Проверь рекламный текст ресторана на соответствие российскому ФЗ "О рекламе":

"${f.ad_text}"

Проверь на:
1. Некорректные сравнения ("лучший", "номер 1")
2. Недостоверные обещания
3. Обязательную маркировку (если нужна)
4. Соответствие правилам рекламы алкоголя (если есть)

Для каждого нарушения: объясни проблему и предложи исправление.
Формат: markdown.`,
    free: false,
  },
  {
    id: 'promo-idea',
    category: 'marketing',
    name: 'Идея акции',
    description: 'Генерирует идеи акций, спецпредложений и маркетинговых активностей',
    icon: 'Sparkles',
    fields: [
      { id: 'venue', label: 'Тип заведения и цель', placeholder: 'Кофейня, увеличить утренний трафик', required: true },
    ],
    buildPrompt: (f) =>
      `Предложи 5 идей акций/спецпредложений для: ${f.venue}

Для каждой идеи:
1. Название акции
2. Механика (что получает гость)
3. Как продвигать (каналы)
4. Примерная стоимость для бизнеса
5. Ожидаемый эффект

Формат: markdown.`,
    free: true,
  },

  // ═══════════ УПРАВЛЕНИЕ ═══════════
  {
    id: 'competitor-analysis',
    category: 'management',
    name: 'Анализ конкурентов',
    description: 'SWOT-анализ вашего заведения с разбором конкурентов',
    icon: 'Target',
    fields: [
      { id: 'venue', label: 'Ваше заведение', placeholder: 'Кофейня "Бариста" на Невском, Санкт-Петербург', required: true },
      { id: 'competitors', label: 'Конкуренты (если знаете)', placeholder: 'Starbucks, Surf Coffee, локальные кофейни рядом', required: false },
    ],
    buildPrompt: (f) =>
      `Проведи конкурентный анализ для: ${f.venue}
${f.competitors ? `Основные конкуренты: ${f.competitors}` : ''}

Создай:
1. SWOT-анализ (сильные стороны, слабые, возможности, угрозы)
2. Позиционирование на рынке
3. 3-5 конкретных рекомендаций по усилению позиции
4. Идеи отстройки от конкурентов

Формат: markdown.`,
    free: false,
  },
  {
    id: 'menu-audit',
    category: 'management',
    name: 'Аудит меню',
    description: 'Анализирует структуру меню и даёт рекомендации по оптимизации',
    icon: 'ClipboardList',
    fields: [
      { id: 'menu', label: 'Ваше меню (названия + цены)', placeholder: 'Цезарь — 490₽\nТом Ям — 590₽\nСтейк Рибай — 1890₽\n...', required: true, multiline: true },
    ],
    buildPrompt: (f) =>
      `Проведи аудит меню ресторана:

${f.menu}

Проанализируй:
1. Структура (баланс категорий, количество позиций)
2. Ценообразование (разброс, якорные цены, психология)
3. Потенциальные "мёртвые" позиции
4. Рекомендации по оптимизации (что убрать, добавить, переоценить)
5. Сезонные рекомендации

Формат: markdown.`,
    free: false,
  },

  // ═══════════ HR & ПЕРСОНАЛ ═══════════
  {
    id: 'job-post',
    category: 'hr',
    name: 'Вакансия для ресторана',
    description: 'Создаёт привлекательное описание вакансии для повара, бармена, официанта',
    icon: 'Briefcase',
    fields: [
      { id: 'position', label: 'Должность', placeholder: 'Повар горячего цеха', required: true },
      { id: 'details', label: 'Детали (зарплата, график, бонусы)', placeholder: '60-80К, 2/2, питание, метро рядом', required: false },
    ],
    buildPrompt: (f) =>
      `Напиши привлекательную вакансию для ресторана:
Должность: ${f.position}
${f.details ? `Условия: ${f.details}` : ''}

Включи: цепляющий заголовок, обязанности (5-7), требования (4-5), условия, бонусы.
Стиль: живой, человечный, не "канцелярский". Должен захотеть откликнуться.
Формат: готовый текст для hh.ru / Telegram.`,
    free: true,
  },
  {
    id: 'onboarding-checklist',
    category: 'hr',
    name: 'Чеклист стажировки',
    description: 'Создаёт программу стажировки для нового сотрудника',
    icon: 'ListChecks',
    fields: [
      { id: 'position', label: 'Должность', placeholder: 'Официант / Бармен / Повар', required: true },
    ],
    buildPrompt: (f) =>
      `Создай чеклист стажировки (первые 2 недели) для новичка на позицию: ${f.position}

Разбей по дням:
День 1-3: знакомство и базовые навыки
День 4-7: основные обязанности под наблюдением
День 8-14: самостоятельная работа + аттестация

Для каждого дня: конкретные задачи, навыки, критерии проверки.
Формат: markdown чеклист.`,
    free: false,
  },

  // ═══════════ ЮРИСТ & HACCP ═══════════
  {
    id: 'haccp-generator',
    category: 'legal',
    name: 'HACCP контрольные точки',
    description: 'Генерирует критические контрольные точки для блюда по HACCP',
    icon: 'ShieldCheck',
    fields: [
      { id: 'dish', label: 'Блюдо и способ приготовления', placeholder: 'Стейк из говядины, гриль, подача с соусом', required: true },
    ],
    buildPrompt: (f) =>
      `Сгенерируй HACCP-анализ критических контрольных точек (ККТ) для блюда:
${f.dish}

Для каждой ККТ укажи:
1. Этап процесса
2. Опасный фактор (биологический, химический, физический)
3. Критический предел (температура, время, pH)
4. Метод мониторинга
5. Корректирующее действие

Формат: markdown таблица.`,
    free: false,
  },
  {
    id: 'sanpin-check',
    category: 'legal',
    name: 'Проверка по СанПиН',
    description: 'Проверяет процесс на соответствие санитарным нормам',
    icon: 'FileCheck',
    fields: [
      { id: 'process', label: 'Опишите процесс или вопрос', placeholder: 'Хранение готовых салатов, сроки годности суши, температура подачи', required: true },
    ],
    buildPrompt: (f) =>
      `Дай консультацию по СанПиН для общепита по вопросу:
${f.process}

Укажи:
1. Конкретные нормы СанПиН (номера документов)
2. Требования (температура, сроки, условия)
3. Типичные нарушения
4. Рекомендации по соблюдению
5. Штрафы за нарушения

Формат: markdown.`,
    free: true,
  },
];

// Helper: get tools by category
export const getToolsByCategory = (categoryId) =>
  TOOLS.filter(t => t.category === categoryId);

// Helper: get free tools
export const getFreeTools = () =>
  TOOLS.filter(t => t.free);

// Helper: get tool by id
export const getToolById = (toolId) =>
  TOOLS.find(t => t.id === toolId);
