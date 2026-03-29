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

  // ═══════════ ДОПОЛНИТЕЛЬНЫЕ ИНСТРУМЕНТЫ ═══════════

  {
    id: 'menu-description',
    category: 'chef',
    name: 'Описание для меню',
    description: 'Создаёт аппетитные описания блюд для печатного или электронного меню',
    icon: 'FileText',
    fields: [
      { id: 'dishes', label: 'Список блюд (каждое с новой строки)', placeholder: 'Цезарь с креветками\nТом Ям\nТирамису', required: true, multiline: true },
    ],
    buildPrompt: (f) =>
      `Напиши аппетитные описания для меню ресторана. Каждое описание — 1-2 предложения, изысканно, вкусно. Не перегружай.\n\nБлюда:\n${f.dishes}\n\nФормат: название → описание. Markdown.`,
    free: true,
  },
  {
    id: 'stop-list',
    category: 'chef',
    name: 'Стоп-лист менеджер',
    description: 'Формирует стоп-лист и предлагает замены для гостей',
    icon: 'XCircle',
    fields: [
      { id: 'items', label: 'Блюда в стоп-листе', placeholder: 'Стейк Рибай\nТунец татаки', required: true, multiline: true },
      { id: 'menu_context', label: 'Какое у вас меню (кратко)', placeholder: 'Европейская кухня, мясо, рыба, паста', required: false },
    ],
    buildPrompt: (f) =>
      `Блюда в стоп-листе:\n${f.items}\n\n${f.menu_context ? `Контекст меню: ${f.menu_context}` : ''}\n\nДля каждого блюда предложи:\n1. Причину (типичную) почему может быть в стопе\n2. 2-3 альтернативы из того же ценового сегмента\n3. Скрипт для официанта: как красиво предложить замену\n\nФормат: markdown.`,
    free: false,
  },
  {
    id: 'wine-pairing',
    category: 'chef',
    name: 'Подбор вина к блюду',
    description: 'Рекомендует вина и напитки к блюдам для винной карты или официантов',
    icon: 'Wine',
    fields: [
      { id: 'dishes', label: 'Блюда', placeholder: 'Стейк из мраморной говядины\nПаста карбонара\nТирамису', required: true, multiline: true },
    ],
    buildPrompt: (f) =>
      `Подбери вино и напитки к каждому блюду:\n${f.dishes}\n\nДля каждого укажи:\n1. Тип вина (красное/белое/розе/игристое)\n2. Сорт винограда\n3. Регион (Италия, Франция, Чили и т.д.)\n4. Ценовой сегмент (бюджет/средний/премиум)\n5. Почему подходит (1 предложение)\n6. Безалкогольная альтернатива\n\nФормат: markdown.`,
    free: false,
  },
  {
    id: 'inventory-checklist',
    category: 'management',
    name: 'Чеклист инвентаризации',
    description: 'Генерирует чеклист для инвентаризации по категориям',
    icon: 'ClipboardCheck',
    fields: [
      { id: 'venue_type', label: 'Тип заведения', placeholder: 'Ресторан итальянской кухни на 80 посадок', required: true },
    ],
    buildPrompt: (f) =>
      `Создай полный чеклист инвентаризации для: ${f.venue_type}\n\nРазбей по зонам:\n1. Кухня (холодильники, морозильники, сухой склад)\n2. Бар\n3. Зал\n4. Хозяйственные товары\n\nДля каждой зоны: список категорий товаров, на что обратить внимание, типичные потери.\n\nФормат: markdown чеклист с чекбоксами.`,
    free: false,
  },
  {
    id: 'morning-briefing',
    category: 'management',
    name: 'Утренний брифинг',
    description: 'Генерирует план утреннего собрания для команды ресторана',
    icon: 'Sun',
    fields: [
      { id: 'context', label: 'Что важно сегодня', placeholder: 'Банкет на 20 человек в 19:00, новое блюдо в меню, день рождения постоянного гостя', required: true },
    ],
    buildPrompt: (f) =>
      `Составь план утреннего брифинга для команды ресторана.\n\nВажное сегодня: ${f.context}\n\nСтруктура:\n1. Приветствие и настрой (1 мин)\n2. Стоп-лист / новинки (2 мин)\n3. Бронирования и особые события (3 мин)\n4. Цель дня (выручка, upsell, фокус)\n5. Мотивация / фишка дня\n\nФормат: markdown, кратко, по делу.`,
    free: true,
  },
  {
    id: 'expense-optimizer',
    category: 'management',
    name: 'Оптимизация расходов',
    description: 'Анализирует расходы ресторана и предлагает конкретные способы экономии',
    icon: 'TrendingDown',
    fields: [
      { id: 'expenses', label: 'Основные расходы (категория — сумма/мес)', placeholder: 'Продукты — 800 000₽\nЗарплаты — 500 000₽\nАренда — 300 000₽\nМаркетинг — 50 000₽', required: true, multiline: true },
      { id: 'revenue', label: 'Выручка в месяц', placeholder: '2 000 000₽', required: false },
    ],
    buildPrompt: (f) =>
      `Проанализируй расходы ресторана и предложи оптимизацию:\n\n${f.expenses}\n${f.revenue ? `\nВыручка: ${f.revenue}` : ''}\n\nДля каждой категории:\n1. Нормальный % от выручки (бенчмарк)\n2. Твой текущий %\n3. 3-5 конкретных способов оптимизации\n4. Потенциальная экономия в рублях\n\nФормат: markdown с таблицей.`,
    free: false,
  },
  {
    id: 'guest-complaint',
    category: 'waiter',
    name: 'Работа с жалобой гостя',
    description: 'Скрипт для официанта: как правильно отработать жалобу на месте',
    icon: 'AlertCircle',
    fields: [
      { id: 'complaint', label: 'Суть жалобы', placeholder: 'Блюдо холодное / Долго ждали / Волос в еде / Неправильный заказ', required: true },
    ],
    buildPrompt: (f) =>
      `Создай скрипт для официанта по отработке жалобы гостя:\n\nЖалоба: "${f.complaint}"\n\nВключи:\n1. Первая реакция (что сказать сразу, 5 секунд)\n2. Действия (что делать физически — забрать, позвать менеджера и т.д.)\n3. Компенсация (варианты: комплимент, скидка, замена)\n4. Закрытие (как завершить ситуацию позитивно)\n5. Чего НЕЛЬЗЯ делать (типичные ошибки)\n\nТон: спокойный, эмпатичный, решительный. Формат: markdown.`,
    free: true,
  },
  {
    id: 'training-quiz',
    category: 'hr',
    name: 'Тест для сотрудника',
    description: 'Создаёт тест на знание меню, стандартов или сервиса',
    icon: 'GraduationCap',
    fields: [
      { id: 'topic', label: 'Тема теста', placeholder: 'Знание коктейльной карты / Стандарты сервиса / Пожарная безопасность', required: true },
      { id: 'role', label: 'Для какой роли', placeholder: 'Бармен / Официант / Повар', required: false },
    ],
    buildPrompt: (f) =>
      `Создай тест из 10 вопросов для сотрудника ресторана.\n\nТема: ${f.topic}\n${f.role ? `Роль: ${f.role}` : ''}\n\nФормат:\n- 10 вопросов с 4 вариантами ответа (A, B, C, D)\n- Правильный ответ отмечен\n- Краткое пояснение к правильному ответу\n\nУровень: практический, не теоретический. Вопросы из реальной работы.\nФормат: markdown.`,
    free: false,
  },
  {
    id: 'event-announce',
    category: 'marketing',
    name: 'Анонс мероприятия',
    description: 'Создаёт текст анонса для мероприятия в ресторане/баре',
    icon: 'PartyPopper',
    fields: [
      { id: 'event', label: 'Что за мероприятие', placeholder: 'Живая музыка, джаз-квартет, пятница 20:00, вход свободный', required: true },
      { id: 'venue', label: 'Название заведения', placeholder: 'Бар Edison', required: false },
    ],
    buildPrompt: (f) =>
      `Напиши анонс мероприятия для соцсетей и Telegram-канала:\n\nМероприятие: ${f.event}\n${f.venue ? `Заведение: ${f.venue}` : ''}\n\nСоздай 2 варианта:\n1. Telegram-пост (короткий, с эмодзи, call to action — "бронируй стол")\n2. Instagram-пост (более развёрнутый, с хэштегами)\n\nТон: энергичный, создающий предвкушение. Формат: markdown.`,
    free: true,
  },
  {
    id: 'seasonal-menu',
    category: 'chef',
    name: 'Сезонное меню',
    description: 'Предлагает идеи сезонных блюд на основе текущего месяца и доступных продуктов',
    icon: 'Leaf',
    fields: [
      { id: 'season', label: 'Сезон или месяц', placeholder: 'Весна / Апрель / Новый год', required: true },
      { id: 'cuisine', label: 'Кухня', placeholder: 'Русская, европейская', required: false },
    ],
    buildPrompt: (f) =>
      `Предложи сезонное меню для ресторана.\n\nСезон: ${f.season}\n${f.cuisine ? `Кухня: ${f.cuisine}` : ''}\n\nСоздай:\n1. 3-4 закуски\n2. 2-3 супа\n3. 4-5 горячих блюд\n4. 2-3 десерта\n5. 2 сезонных напитка/коктейля\n\nДля каждого: название, ключевые ингредиенты, почему подходит для этого сезона.\nФормат: markdown.`,
    free: false,
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
