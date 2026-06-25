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
  pos_system: "iiko",
  channels: ["Telegram", "сайт", "iiko", "ручные таблицы"],
  integration_pains: ["ручные отчеты", "разрозненные чаты", "нет единого контекста по задачам"],
  ai_provider_policy: "пока не важно",
  copilot_tone: "Коротко, по делу, как операционный директор: факт, вывод, действие, недостающие данные.",
  red_lines: ["не увольнять сотрудников по данным без проверки", "не менять цены автоматически", "не публиковать контент без подтверждения"],
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

