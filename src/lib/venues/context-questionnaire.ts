import { z } from "zod";

export const ContextQuestionTypeSchema = z.enum([
  "text",
  "textarea",
  "tags",
  "select",
  "multiselect",
]);

export const ContextQuestionSchema = z.object({
  id: z.string().min(1),
  label: z.string().min(1),
  prompt: z.string().min(1),
  type: ContextQuestionTypeSchema,
  required: z.boolean().default(false),
  placeholder: z.string().optional(),
  options: z.array(z.string().min(1)).optional(),
});

export const ContextSectionSchema = z.object({
  id: z.string().min(1),
  title: z.string().min(1),
  description: z.string().min(1),
  questions: z.array(ContextQuestionSchema).min(1),
});

const AnswerValueSchema = z.union([
  z.string(),
  z.array(z.string()),
  z.number(),
  z.boolean(),
  z.null(),
  z.undefined(),
]);

export const VenueContextAnswersSchema = z.record(z.string(), AnswerValueSchema);

export type ContextQuestionType = z.infer<typeof ContextQuestionTypeSchema>;
export type ContextQuestion = z.infer<typeof ContextQuestionSchema>;
export type ContextSection = z.infer<typeof ContextSectionSchema>;
export type VenueContextAnswers = Record<string, string | string[]>;

export type ContextCompletion = {
  answered: number;
  total: number;
  requiredAnswered: number;
  requiredTotal: number;
  percentage: number;
  requiredPercentage: number;
  missingRequired: string[];
};

export type ContextNextQuestion = {
  id: string;
  label: string;
  prompt: string;
  sectionTitle: string;
  reason: string;
};

export type ContextMemoryReadiness = {
  answeredSignals: number;
  totalSignals: number;
  percentage: number;
  status: "starter" | "usable" | "strong";
  title: string;
  summary: string;
  nextQuestion: ContextNextQuestion | null;
};

export const VENUE_CONTEXT_QUESTIONNAIRE: ContextSection[] = [
  {
    id: "identity",
    title: "Идентичность заведения",
    description: "Формат, позиционирование, аудитория и причина, по которой гости выбирают место.",
    questions: [
      {
        id: "format",
        label: "Формат",
        prompt: "Что это за заведение: ресторан, бар, кафе, сеть, доставка, гибрид?",
        type: "textarea",
        required: true,
        placeholder: "Городской ресторан с кухней, баром и вечерней посадкой",
      },
      {
        id: "positioning",
        label: "Позиционирование",
        prompt: "Как заведение должно звучать для гостя и чем отличается от соседей?",
        type: "textarea",
        required: true,
      },
      {
        id: "audience",
        label: "Аудитория",
        prompt: "Кто основные гости и в какие сценарии они приходят?",
        type: "tags",
        required: true,
      },
    ],
  },
  {
    id: "economics",
    title: "Экономика и фокус владельца",
    description: "Что считаем главным: выручка, маржа, средний чек, загрузка, доставка или команда.",
    questions: [
      {
        id: "owner_goals",
        label: "Цели владельца",
        prompt: "Какие 3-5 бизнес-задач Receptor должен помогать решать?",
        type: "tags",
        required: true,
      },
      {
        id: "revenue_model",
        label: "Модель выручки",
        prompt: "Откуда приходит выручка: зал, доставка, банкет, бар, события, завтраки?",
        type: "multiselect",
        required: true,
        options: ["зал", "бар", "доставка", "самовывоз", "банкеты", "события", "завтраки", "кейтеринг"],
      },
      {
        id: "decision_metrics",
        label: "Ключевые метрики",
        prompt: "Какие цифры владелец реально смотрит или должен смотреть утром?",
        type: "tags",
        required: true,
      },
    ],
  },
  {
    id: "team",
    title: "Команда и роли",
    description: "Кто принимает решения, кто исполняет действия и кому нужны отдельные права.",
    questions: [
      {
        id: "team_roles",
        label: "Роли команды",
        prompt: "Какие роли есть в заведении или холдинге?",
        type: "multiselect",
        required: true,
        options: ["владелец", "управляющий", "шеф", "су-шеф", "бар-менеджер", "маркетолог", "администратор", "официант", "хостес", "бухгалтер"],
      },
      {
        id: "responsible_people",
        label: "Ответственные",
        prompt: "Кто должен получать задачи по кухне, залу, меню, маркетингу и финансам?",
        type: "textarea",
        required: false,
      },
      {
        id: "service_standards",
        label: "Стандарты сервиса",
        prompt: "Что команда обязана делать одинаково каждый день?",
        type: "tags",
        required: false,
      },
    ],
  },
  {
    id: "operating_reality",
    title: "Как ресторан живет на самом деле",
    description:
      "Неидеальная операционка: где хаос, чему не обучены люди, что нужно спрашивать после смены и какие решения нельзя принимать вслепую.",
    questions: [
      {
        id: "daily_pains",
        label: "Главные боли",
        prompt: "Где сейчас больше всего хаоса: люди, сервис, кухня, iiko, закупки, касса, маркетинг, обучение?",
        type: "tags",
        required: false,
        placeholder: "новые сотрудники долго входят в работу; стоп-лист живет в чате; никто не понимает маржу",
      },
      {
        id: "knowledge_gaps",
        label: "Пробелы в знаниях",
        prompt: "Чего команда не знает или делает каждый по-своему?",
        type: "tags",
        required: false,
        placeholder: "кассовая дисциплина; работа с конфликтом; апселл; техкарты; закрытие смены",
      },
      {
        id: "shift_summary_rules",
        label: "Итог смены",
        prompt: "Что сотрудники должны фиксировать после смены, чтобы советник понимал реальность?",
        type: "textarea",
        required: false,
        placeholder: "посадка, гости, погода, стоп-лист, конфликты, что продавали, что мешало и что проверить утром",
      },
      {
        id: "owner_decision_style",
        label: "Как владелец принимает решения",
        prompt: "Как владелец обычно решает: по цифрам, по ощущениям, через управляющего, через бриф, через чат?",
        type: "textarea",
        required: false,
      },
    ],
  },
  {
    id: "systems",
    title: "Системы и интеграции",
    description: "Какие источники данных и каналы уже есть, а какие надо заменить или подключить.",
    questions: [
      {
        id: "pos_system",
        label: "POS/back-office",
        prompt: "Какая учетная система используется?",
        type: "select",
        required: true,
        options: ["iiko", "R-Keeper", "Poster", "1C", "другое", "пока нет"],
      },
      {
        id: "channels",
        label: "Каналы работы",
        prompt: "Где сейчас живут брони, доставка, сообщения и контент?",
        type: "tags",
        required: false,
      },
      {
        id: "integration_pains",
        label: "Боли интеграций",
        prompt: "Что сейчас не работает, дублируется или требует ручной работы?",
        type: "tags",
        required: false,
      },
    ],
  },
  {
    id: "ai_policy",
    title: "AI и данные",
    description: "Ограничения по данным, модели и тону ответа AI-помощника.",
    questions: [
      {
        id: "ai_provider_policy",
        label: "Политика AI",
        prompt: "Можно ли использовать внешние модели или нужен локальный/российский провайдер?",
        type: "select",
        required: true,
        options: ["можно внешние модели", "нужен российский провайдер", "нужен локальный/частный режим", "пока не важно"],
      },
      {
        id: "copilot_tone",
        label: "Тон AI-помощника",
        prompt: "Как AI-помощник должен говорить с владельцем и командой?",
        type: "textarea",
        required: false,
      },
      {
        id: "red_lines",
        label: "Красные линии",
        prompt: "Какие советы, действия или автоматизации нельзя делать без человека?",
        type: "tags",
        required: false,
      },
    ],
  },
];

export const DEMO_CONTEXT_ANSWERS: VenueContextAnswers = {
  format: "Городской ресторан на 80 посадочных мест с кухней, баром, вечерней посадкой и доставкой на пиковые дни.",
  positioning: "Место для понятного ужина, стабильного сервиса и управляемого меню без хаоса в ручных отчетах.",
  audience: ["гости на ужин после работы", "компании друзей", "постоянные гости", "семейные визиты"],
  owner_goals: ["видеть действия на сегодня", "сократить ручные отчеты", "контролировать меню и маржу"],
  revenue_model: ["зал", "бар", "доставка", "события"],
  decision_metrics: ["выручка", "средний чек", "топ блюд", "категории", "смены", "маржинальность"],
  team_roles: ["владелец", "управляющий", "шеф", "маркетолог", "администратор", "официант"],
  responsible_people: "Управляющий отвечает за смену и зал, шеф за кухню и техкарты, маркетолог за акции и контент.",
  service_standards: ["скорость подачи", "рекомендации официантов", "стоп-лист до смены", "обратная связь гостя"],
  daily_pains: ["нет единой картины смены", "сотрудники учатся устно", "часть решений живет в чатах"],
  knowledge_gaps: ["кассовая дисциплина", "работа с конфликтом", "апселл без давления", "понимание маржи"],
  shift_summary_rules:
    "После смены команда фиксирует посадку, гостей, погоду, стоп-лист, конфликты, что продавали или не продавали, что мешало и что проверить утром.",
  owner_decision_style:
    "Владелец хочет короткий утренний разбор: факт, причина, вопрос к команде и одно действие на день.",
  pos_system: "iiko",
  channels: ["Telegram", "сайт", "iiko", "ручные таблицы"],
  integration_pains: ["ручные отчеты", "разрозненные чаты", "нет единого контекста по задачам"],
  ai_provider_policy: "пока не важно",
  copilot_tone: "Коротко, по делу, как операционный директор: факт, вывод, действие, недостающие данные.",
  red_lines: ["не увольнять сотрудников по данным без проверки", "не менять цены автоматически", "не публиковать контент без подтверждения"],
};

const MEMORY_SIGNAL_IDS = [
  "format",
  "positioning",
  "audience",
  "owner_goals",
  "decision_metrics",
  "daily_pains",
  "knowledge_gaps",
  "shift_summary_rules",
  "team_roles",
  "service_standards",
  "pos_system",
  "integration_pains",
] as const;

const NEXT_QUESTION_REASONS: Record<string, string> = {
  format: "сначала нужно понять, что за место мы разбираем",
  positioning: "советник должен отличать ресторан от соседей и сетевых шаблонов",
  audience: "без сценариев гостей советы по сервису и меню будут общими",
  owner_goals: "утренние выводы должны вести к целям владельца",
  daily_pains: "здесь появляется реальность, которую не видно в отчетах",
  knowledge_gaps: "это основа будущего обучения и чеклистов команды",
  shift_summary_rules: "так команда будет каждый день пополнять память ресторана",
  team_roles: "задачи и обучение должны попадать нужным людям",
  service_standards: "общие стандарты убирают работу по наитию",
  responsible_people: "система должна знать, кто отвечает за кухню, зал, кассу и маркетинг",
  decision_metrics: "цифры становятся полезными, когда понятно, какие из них важны",
  pos_system: "факты из учетной системы привязывают память к реальным данным",
  integration_pains: "это показывает, где ресторан теряет время на ручную работу",
  ai_provider_policy: "нужно заранее понимать ограничения по данным и моделям",
  red_lines: "советник должен знать, где решение остается за человеком",
};

function normalizeAnswerValue(value: z.infer<typeof AnswerValueSchema>): string | string[] | null {
  if (Array.isArray(value)) {
    const items = value.map((item) => String(item).trim()).filter(Boolean);
    return items.length ? items : null;
  }

  if (value === null || value === undefined) return null;

  const text = String(value).trim();
  return text ? text : null;
}

export function normalizeContextAnswers(value: unknown): VenueContextAnswers {
  const parsed = VenueContextAnswersSchema.safeParse(value);
  if (!parsed.success) return {};

  return Object.fromEntries(
    Object.entries(parsed.data).flatMap(([key, raw]) => {
      const normalized = normalizeAnswerValue(raw);
      return normalized === null ? [] : [[key, normalized]];
    }),
  );
}

function hasContextAnswer(answers: VenueContextAnswers, id: string): boolean {
  const answer = answers[id];
  return Array.isArray(answer) ? answer.length > 0 : Boolean(answer?.trim());
}

export function listRequiredContextQuestionIds(
  sections: ContextSection[] = VENUE_CONTEXT_QUESTIONNAIRE,
): string[] {
  return sections.flatMap((section) =>
    section.questions.filter((question) => question.required).map((question) => question.id),
  );
}

export function calculateContextCompletion(
  value: unknown,
  sections: ContextSection[] = VENUE_CONTEXT_QUESTIONNAIRE,
): ContextCompletion {
  const answers = normalizeContextAnswers(value);
  const questions = sections.flatMap((section) => section.questions);
  const requiredIds = new Set(listRequiredContextQuestionIds(sections));
  const answeredIds = new Set(
    Object.entries(answers)
      .filter(([, answer]) => (Array.isArray(answer) ? answer.length > 0 : answer.length > 0))
      .map(([id]) => id),
  );
  const requiredAnswered = [...requiredIds].filter((id) => answeredIds.has(id));
  const missingRequired = [...requiredIds].filter((id) => !answeredIds.has(id));

  return {
    answered: answeredIds.size,
    total: questions.length,
    requiredAnswered: requiredAnswered.length,
    requiredTotal: requiredIds.size,
    percentage: questions.length ? Math.round((answeredIds.size / questions.length) * 100) : 0,
    requiredPercentage: requiredIds.size
      ? Math.round((requiredAnswered.length / requiredIds.size) * 100)
      : 100,
    missingRequired,
  };
}

export function formatContextAnswersForPrompt(value: unknown): string {
  const answers = normalizeContextAnswers(value);

  return VENUE_CONTEXT_QUESTIONNAIRE.map((section) => {
    const lines = section.questions.flatMap((question) => {
      const answer = answers[question.id];
      if (!answer || (Array.isArray(answer) && answer.length === 0)) return [];
      const formatted = Array.isArray(answer) ? answer.join("; ") : answer;
      return [`- ${question.label}: ${formatted}`];
    });

    if (!lines.length) return null;
    return [`${section.title}:`, ...lines].join("\n");
  })
    .filter(Boolean)
    .join("\n\n");
}

export function buildContextMemoryReadiness(value: unknown): ContextMemoryReadiness {
  const answers = normalizeContextAnswers(value);
  const questions = VENUE_CONTEXT_QUESTIONNAIRE.flatMap((section) =>
    section.questions.map((question) => ({ ...question, sectionTitle: section.title })),
  );
  const questionsById = new Map(questions.map((question) => [question.id, question]));
  const answeredSignals = MEMORY_SIGNAL_IDS.filter((id) => hasContextAnswer(answers, id)).length;
  const percentage = Math.round((answeredSignals / MEMORY_SIGNAL_IDS.length) * 100);
  const nextQuestionId = [
    "format",
    "positioning",
    "audience",
    "owner_goals",
    "daily_pains",
    "knowledge_gaps",
    "shift_summary_rules",
    "team_roles",
    "service_standards",
    "responsible_people",
    "decision_metrics",
    "pos_system",
    "integration_pains",
    "ai_provider_policy",
    "red_lines",
  ].find((id) => !hasContextAnswer(answers, id));
  const nextQuestionBase = nextQuestionId ? questionsById.get(nextQuestionId) : undefined;

  const status =
    percentage >= 85 ? "strong" : percentage >= 50 ? "usable" : "starter";

  return {
    answeredSignals,
    totalSignals: MEMORY_SIGNAL_IDS.length,
    percentage,
    status,
    title:
      status === "strong"
        ? "Память уже можно использовать"
        : status === "usable"
          ? "Память собирает реальность ресторана"
          : "Память пока знает только основу",
    summary:
      status === "strong"
        ? "Советник видит формат, цели, команду и операционные боли. Дальше важно регулярно добавлять итоги смен."
        : status === "usable"
          ? "Уже можно задавать рабочие вопросы, но не хватает деталей о людях, стандартах или ежедневной реальности."
          : "Заполните несколько ключевых ответов: кто вы, что болит, чему учить команду и что фиксировать после смены.",
    nextQuestion:
      nextQuestionBase && nextQuestionId
        ? {
            id: nextQuestionBase.id,
            label: nextQuestionBase.label,
            prompt: nextQuestionBase.prompt,
            sectionTitle: nextQuestionBase.sectionTitle,
            reason:
              NEXT_QUESTION_REASONS[nextQuestionId] ??
              "этот ответ сделает советника точнее",
          }
        : null,
  };
}

