export type FieldNoteTemplate = {
  label: string;
  text: string;
};

export type FieldNoteReadiness = {
  hasFact: boolean;
  hasScale: boolean;
  hasAction: boolean;
  score: number;
  missing: string[];
};

export const FIELD_NOTE_TEMPLATES: FieldNoteTemplate[] = [
  {
    label: "Гости",
    text: "Гости спрашивали:\nСколько раз / когда:\nЧто ответили:\nЧто проверить утром: ",
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
    label: "Продажи",
    text: "Сервис / продажи:\nЧто рекомендовали:\nЧто гости брали или не брали:\nЧто проверить утром: ",
  },
];

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
  return /(\d|раз|гост|стол|порц|руб|₽|чек|минут|час|после|до |к \d|утром|вечером|днем|ночью)/iu.test(
    line,
  );
}

function hasActionSignal(line: string): boolean {
  return /(ответ|замен|предлож|закры|сдела|провер|исправ|заказ|переда|разобра|нужно|надо|повтор|убра|добав)/iu.test(
    line,
  );
}

export function getFieldNoteReadiness(value: string): FieldNoteReadiness {
  const lines = meaningfulFieldNoteLines(value);
  const hasFact = lines.length > 0;
  const hasScale = lines.some(hasScaleSignal);
  const hasAction = lines.some(hasActionSignal);
  const missing = [
    hasFact ? null : "факт",
    hasScale ? null : "когда/сколько",
    hasAction ? null : "что сделали или проверить",
  ].filter((item): item is string => Boolean(item));

  return {
    hasFact,
    hasScale,
    hasAction,
    score: [hasFact, hasScale, hasAction].filter(Boolean).length,
    missing,
  };
}

export function hasMeaningfulFieldNoteBody(value: string): boolean {
  return getFieldNoteReadiness(value).hasFact;
}
