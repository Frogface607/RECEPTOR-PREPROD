export type FieldNoteTemplate = {
  label: string;
  text: string;
};

export const FIELD_NOTE_TEMPLATES: FieldNoteTemplate[] = [
  { label: "Гости", text: "Гости спрашивали: " },
  { label: "Стоп", text: "Стоп-лист / закончилось: " },
  { label: "Конфликт", text: "Конфликт или жалоба: " },
  { label: "Событие", text: "Событие / посадка: " },
  { label: "Команда", text: "Команде мешало: " },
  { label: "Продажи", text: "Сервис / продажи: " },
];

function normalize(value: string): string {
  return value.trim().replace(/\s+/g, " ");
}

function stripTemplatePrefix(line: string): string {
  const normalized = normalize(line);
  const lower = normalized.toLocaleLowerCase("ru-RU");

  for (const template of FIELD_NOTE_TEMPLATES) {
    const prefix = normalize(template.text).toLocaleLowerCase("ru-RU");
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
