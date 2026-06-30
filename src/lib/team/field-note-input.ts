export type FieldNoteTemplate = {
  label: string;
  text: string;
};

export type FieldNotePrompt = {
  label: string;
  hint: string;
  example: string;
};

export type FieldNoteReadiness = {
  hasFact: boolean;
  hasContext: boolean;
  hasScale: boolean;
  hasAction: boolean;
  score: number;
  missing: string[];
};

export type FieldNoteReadinessSummary = {
  total: number;
  complete: number;
  bestScore: number;
  bestMissing: string[];
  followUpQuestions: string[];
};

export const FIELD_NOTE_MEMORY_PROMPTS: FieldNotePrompt[] = [
  {
    label: "Факт",
    hint: "что произошло",
    example: "закончилась мята, была жалоба, просели рекомендации",
  },
  {
    label: "Контекст",
    hint: "почему это важно",
    example: "ливень, банкет, новая смена, гости спрашивали замену",
  },
  {
    label: "Масштаб",
    hint: "когда и сколько",
    example: "после 21:00, 3 стола, 6 отказов, 20 минут ожидания",
  },
  {
    label: "Действие",
    hint: "что проверить утром",
    example: "заказать мяту, дать замену залу, разобрать возврат",
  },
];

export const FIELD_NOTE_TEMPLATES: FieldNoteTemplate[] = [
  {
    label: "Итог смены",
    text: "Итог смены:\nФакт:\nКонтекст / причина:\nКогда / сколько:\nЧто команда сделала:\nЧто проверить утром:\nЧто сказать на брифе: ",
  },
  {
    label: "Гости",
    text: "Гости спрашивали:\nКонтекст / почему важно:\nСколько раз / когда:\nЧто ответили:\nЧто проверить утром: ",
  },
  {
    label: "Стоп",
    text: "Стоп-лист / закончилось:\nКогда заметили:\nЧто заменили или потеряли:\nЧто проверить утром: ",
  },
  {
    label: "Конфликт",
    text: "Конфликт или жалоба:\nПричина / время:\nЧем закрыли:\nЧто проверить утром: ",
  },
  {
    label: "Событие",
    text: "Событие / посадка:\nСколько гостей / когда:\nЧто сработало или мешало:\nЧто повторить или исправить: ",
  },
  {
    label: "Команда",
    text: "Команде мешало:\nГде потеряли время:\nЧто нужно исправить:\nКому передать утром: ",
  },
  {
    label: "Деньги",
    text: "Маржа / ФОТ:\nЧто продавали или не продавали:\nГде потеряли деньги:\nЧто проверить утром: ",
  },
  {
    label: "Продажи",
    text: "Сервис / продажи:\nЧто рекомендовали:\nЧто гости брали или не брали:\nЧто проверить утром: ",
  },
];

const FIELD_NOTE_FOLLOW_UP_QUESTIONS: Record<string, string> = {
  факт: "Что конкретно произошло в смене?",
  контекст: "Почему это повлияло на гостей, продажи или команду?",
  "контекст/причина": "Почему это повлияло на гостей, продажи или команду?",
  масштаб: "Когда это случилось и сколько гостей, столов, позиций или денег затронуло?",
  "когда/сколько": "Когда это случилось и сколько гостей, столов, позиций или денег затронуло?",
  действие: "Что команда уже сделала и что управляющему проверить утром?",
  "что сделали или проверить": "Что команда уже сделала и что управляющему проверить утром?",
};

const FIELD_NOTE_GUIDE_PREFIXES = FIELD_NOTE_TEMPLATES.flatMap((template) =>
  template.text.split(/\r?\n/).map(normalize).filter(Boolean),
);

function normalize(value: string): string {
  return value.trim().replace(/\s+/g, " ");
}

function stripTemplatePrefix(line: string): string {
  const normalized = normalize(line);
  const lower = normalized.toLocaleLowerCase("ru-RU");

  for (const rawPrefix of FIELD_NOTE_GUIDE_PREFIXES) {
    const prefix = rawPrefix.toLocaleLowerCase("ru-RU");
    if (lower === prefix) return "";
    if (lower.startsWith(`${prefix} `)) {
      return normalized.slice(prefix.length).trim();
    }
  }

  return normalized;
}

function meaningfulFieldNoteLines(value: string): string[] {
  return value
    .split(/\r?\n/)
    .map(stripTemplatePrefix)
    .map((line) => line.replace(/^[\s:;.,/\\|—-]+|[\s:;.,/\\|—-]+$/g, ""))
    .filter((line) => line.length >= 3 && /[\p{L}\p{N}]/u.test(line));
}

function hasScaleSignal(line: string): boolean {
  return /(\d|раз|гост|стол|посад|брон|порц|руб|₽|чек|минут|час|после|(^|\s)до\s|к \d|утром|вечером|днем|ночью|погода|дожд|ливн|снег|жар|мороз|ветер|отмен)/iu.test(
    line,
  );
}

function hasContextSignal(line: string): boolean {
  return /(почему|причин|контекст|из-за|из за|потому|повлия|мешал|сработал|важн|гост|погод|дожд|ливн|снег|жар|мороз|ветер|банкет|мероприят|посад|брон|конфликт|жалоб|стоп|закончил|команд|кухн|зал|сервис|апсел|рекоменд)/iu.test(
    line,
  );
}

function hasActionSignal(line: string): boolean {
  return /(ответ|замен|предлож|закры|сдела|провер|исправ|заказ|переда|разобра|нужно|надо|повтор|убра|добав|бриф|обуч|рассказ|назнач|реши)/iu.test(
    line,
  );
}

export function getFieldNoteReadiness(value: string): FieldNoteReadiness {
  const lines = meaningfulFieldNoteLines(value);
  const hasFact = lines.length > 0;
  const hasContext = lines.some(hasContextSignal);
  const hasScale = lines.some(hasScaleSignal);
  const hasAction = lines.some(hasActionSignal);
  const missing = [
    hasFact ? null : "факт",
    hasContext ? null : "контекст/причина",
    hasScale ? null : "когда/сколько",
    hasAction ? null : "что сделали или проверить",
  ].filter((item): item is string => Boolean(item));

  return {
    hasFact,
    hasContext,
    hasScale,
    hasAction,
    score: [hasFact, hasContext, hasScale, hasAction].filter(Boolean).length,
    missing,
  };
}

export function hasMeaningfulFieldNoteBody(value: string): boolean {
  return getFieldNoteReadiness(value).hasFact;
}

export function fieldNoteReadinessHint(readiness: FieldNoteReadiness): string {
  if (readiness.score === 4) {
    return "Готово: итог попадет в память смены и утренний разбор владельца.";
  }

  if (!readiness.hasFact) {
    return "Начните с одного факта смены: что случилось с гостями, продажами, стоп-листом, командой или сервисом.";
  }

  return `Чтобы советник понял контекст, добавьте: ${readiness.missing.join(", ")}.`;
}

export function buildFieldNoteFollowUpQuestions(
  missing: readonly string[],
): string[] {
  const questions = missing
    .map((item) => FIELD_NOTE_FOLLOW_UP_QUESTIONS[item])
    .filter((item): item is string => Boolean(item));

  return questions.length > 0
    ? questions
    : ["Что важно запомнить из смены для утреннего разбора?"];
}

export function summarizeFieldNoteReadiness(
  values: readonly string[],
): FieldNoteReadinessSummary {
  const readiness = values
    .map(getFieldNoteReadiness)
    .filter((item) => item.hasFact);
  const best = readiness.toSorted((left, right) => right.score - left.score)[0];

  return {
    total: readiness.length,
    complete: readiness.filter((item) => item.score === 4).length,
    bestScore: best?.score ?? 0,
    bestMissing: best?.missing ?? FIELD_NOTE_MEMORY_PROMPTS.map((item) =>
      item.label.toLocaleLowerCase("ru-RU"),
    ),
    followUpQuestions: buildFieldNoteFollowUpQuestions(
      best?.missing ??
        FIELD_NOTE_MEMORY_PROMPTS.map((item) =>
          item.label.toLocaleLowerCase("ru-RU"),
        ),
    ),
  };
}
