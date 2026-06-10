/**
 * Mock tool runner — deterministic, presentation-safe stand-in for a real LLM call.
 *
 * While `ANTHROPIC_API_KEY` is absent, every tool in `/tools` runs through
 * this function: it validates inputs, then renders a believable,
 * category-shaped markdown draft that echoes the user's input so the
 * product feels alive while a real AI key is unavailable.
 *
 * It is honest: each result carries a small draft note. When the
 * API key arrives, the `/api/tools/run` route swaps this for a real Claude
 * call built from `tool.buildPrompt(values)` — the UI never changes.
 *
 * Determinism: no Math.random / Date.now. Same input → same output.
 */

import { getToolById, type Tool, type ToolCategoryId } from "./catalog";

export type ValidationResult =
  | { ok: true }
  | { ok: false; missing: string[] };

export function validateToolInput(
  tool: Tool,
  values: Record<string, string>,
): ValidationResult {
  const missing = tool.fields
    .filter((f) => f.required && !(values[f.id] ?? "").trim())
    .map((f) => f.id);
  return missing.length === 0 ? { ok: true } : { ok: false, missing };
}

const DEMO_NOTE =
  "> _Черновик Receptor. На подключённом AI-ключе ответ будет глубже и готов к работе._";

/** Non-empty field values in declared order, as {label, value} pairs. */
function filledInputs(tool: Tool, values: Record<string, string>) {
  return tool.fields
    .map((f) => ({ label: f.label, value: (values[f.id] ?? "").trim() }))
    .filter((x) => x.value.length > 0);
}

function inputsBlock(tool: Tool, values: Record<string, string>): string {
  const filled = filledInputs(tool, values);
  if (filled.length === 0) return "";
  return filled.map((x) => `- **${x.label}:** ${x.value}`).join("\n");
}

/** First required field's value — the "subject" of the request. */
function subject(tool: Tool, values: Record<string, string>): string {
  const req = tool.fields.find((f) => f.required);
  return req ? (values[req.id] ?? "").trim() : "";
}

type Template = (tool: Tool, values: Record<string, string>) => string;

const CATEGORY_TEMPLATE: Record<ToolCategoryId, Template> = {
  chef: (tool, values) => {
    const subj = subject(tool, values);
    return [
      `Готовлю результат по запросу: **${subj}**.`,
      "",
      "### Что войдёт в полный ответ",
      "1. Точные граммовки и список ингредиентов",
      "2. Пошаговый процесс с температурами и таймингом",
      "3. Себестоимость и рекомендованная цена",
      "4. Подача и советы шефа",
      "",
      "_Ниже — структура; полный текст откроется на боевом ключе._",
    ].join("\n");
  },
  waiter: (tool, values) => {
    const subj = subject(tool, values);
    return [
      `Скрипт под ситуацию: **${subj}**.`,
      "",
      "### Каркас",
      "1. Первая реакция — что сказать в первые 5 секунд",
      "2. Действия по шагам",
      "3. Варианты допродажи / компенсации",
      "4. Как закрыть контакт на позитиве",
      "",
      "Тон: дружелюбный, профессиональный, без шаблонов.",
    ].join("\n");
  },
  marketing: (tool, values) => {
    const subj = subject(tool, values);
    return [
      `Текст по теме: **${subj}**.`,
      "",
      "### Структура",
      "1. Цепляющий заголовок",
      "2. Основной текст 3–5 предложений",
      "3. Call to action",
      "4. 5–7 релевантных хэштегов",
      "",
      "Голос бренда: живой, тёплый, не корпоративный.",
    ].join("\n");
  },
  management: (tool, values) => {
    const subj = subject(tool, values);
    return [
      `Аналитика по вводным: **${subj}**.`,
      "",
      "### Что разберём",
      "1. Текущая картина по цифрам",
      "2. Бенчмарки рынка",
      "3. Узкие места и точки роста",
      "4. 3–5 конкретных действий с эффектом в рублях",
      "",
      "Вывод ведёт к действиям владельца, не к воде.",
    ].join("\n");
  },
  hr: (tool, values) => {
    const subj = subject(tool, values);
    return [
      `Документ под задачу: **${subj}**.`,
      "",
      "### Состав",
      "1. Чёткая структура по дням / блокам",
      "2. Конкретные задачи и критерии проверки",
      "3. Человеческий тон — чтобы захотелось включиться",
      "",
      "Готово к публикации на hh.ru / в Telegram.",
    ].join("\n");
  },
  legal: (tool, values) => {
    const subj = subject(tool, values);
    return [
      `Проверка по вопросу: **${subj}**.`,
      "",
      "### Что проверим",
      "1. Конкретные нормы и номера документов",
      "2. Требования: температура, сроки, условия",
      "3. Типичные нарушения и риски штрафов",
      "4. Рекомендации по соблюдению",
      "",
      "Структура соответствует требованиям HACCP / СанПиН.",
    ].join("\n");
  },
};

export function runToolMock(
  toolId: string,
  values: Record<string, string>,
): string {
  const tool = getToolById(toolId);
  if (!tool) {
    throw new Error(`unknown tool: ${toolId} (инструмент не найден)`);
  }

  const validation = validateToolInput(tool, values);
  if (!validation.ok) {
    throw new Error(
      `required fields missing (обязательные поля): ${validation.missing.join(", ")}`,
    );
  }

  const body = CATEGORY_TEMPLATE[tool.category](tool, values);
  const inputs = inputsBlock(tool, values);

  return [
    `# ${tool.name}`,
    "",
    DEMO_NOTE,
    "",
    body,
    inputs ? "\n### Ваши вводные\n" + inputs : "",
  ]
    .join("\n")
    .trim();
}
