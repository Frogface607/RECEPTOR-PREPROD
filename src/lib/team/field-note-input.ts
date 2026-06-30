export type FieldNoteTemplate = {
  label: string;
  text: string;
};

export const FIELD_NOTE_TEMPLATES: FieldNoteTemplate[] = [
  {
    label: "Гости",
    text: "Гости спрашивали:\nСколько раз / когда:\nЧто ответили: ",
  },
  {
    label: "Стоп",
    text: "Стоп-лист / закончилось:\nКогда заметили:\nЧто заменили или потеряли: ",
  },
  {
    label: "Конфликт",
    text: "Конфликт или жалоба:\nПричина / время:\nЧем закрыли: ",
  },
  {
    label: "Событие",
    text: "Событие / посадка:\nСколько гостей / когда:\nЧто сработало или мешало: ",
  },
  {
    label: "Команда",
    text: "Команде мешало:\nГде потеряли время:\nЧто нужно исправить: ",
  },
  {
    label: "Продажи",
    text: "Сервис / продажи:\nЧто рекомендовали:\nЧто гости брали или не брали: ",
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

export function hasMeaningfulFieldNoteBody(value: string): boolean {
  return value
    .split(/\r?\n/)
    .map(stripTemplatePrefix)
    .map((line) => line.replace(/^[\s:;.,/\\|—-]+|[\s:;.,/\\|—-]+$/g, ""))
    .some((line) => line.length >= 3 && /[\p{L}\p{N}]/u.test(line));
}
