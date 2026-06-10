import { z } from "zod";

export const VenueIntelligenceSchema = z.object({
  format: z.string().min(1),
  positioning: z.string().min(1),
  audience: z.array(z.string().min(1)).default([]),
  strengths: z.array(z.string().min(1)).default([]),
  guestPains: z.array(z.string().min(1)).default([]),
  ownerGoals: z.array(z.string().min(1)).default([]),
  operatingRisks: z.array(z.string().min(1)).default([]),
  decisionRules: z.array(z.string().min(1)).default([]),
  recommendedFocus: z.array(z.string().min(1)).default([]),
  researchStatus: z.enum(["template", "manual", "researched"]).default("template"),
});

export type VenueIntelligenceProfile = {
  format: string;
  positioning: string;
  audience: string[];
  strengths: string[];
  guestPains: string[];
  ownerGoals: string[];
  operatingRisks: string[];
  decisionRules: string[];
  recommendedFocus: string[];
  researchStatus: "template" | "manual" | "researched";
};

export const DEFAULT_VENUE_INTELLIGENCE: VenueIntelligenceProfile = {
  format: "Городское заведение с кухней, баром и регулярной вечерней посадкой",
  positioning:
    "Место, где важны не только продажи, но и управляемость: меню, смены, сервис, отзывы и повторные визиты.",
  audience: [
    "Гости, которые приходят за понятным качеством и атмосферой",
    "Компании вечером и в выходные",
    "Постоянные гости, чувствительные к сервису и стабильности",
  ],
  strengths: [
    "Можно быстро видеть деньги, блюда, категории и смены в одном месте",
    "Меню удобно анализировать по выручке и количеству продаж",
    "Copilot может объяснять цифры человеческим языком",
  ],
  guestPains: [
    "Долгое ожидание",
    "Нестабильный сервис между сменами",
    "Ощущение, что цена не совпадает с ценностью",
  ],
  ownerGoals: [
    "Понимать, где ресторан зарабатывает и где теряет деньги",
    "Сократить ручные отчёты и утренний разбор в таблицах",
    "Быстрее находить действия на сегодня, а не просто смотреть графики",
  ],
  operatingRisks: [
    "Рост выручки может скрывать падение маржинальности",
    "Топ по выручке не всегда равен топу по прибыли",
    "Продажи по сотрудникам могут быть неточными, если чек закрывает не тот, кто обслуживал гостя",
    "Слабые категории часто теряются внутри общей выручки",
  ],
  decisionRules: [
    "Всегда отделять факт от вывода и действия",
    "Не делать кадровые выводы без понимания качества данных по сотрудникам",
    "Сравнивать периоды и дни недели, а не смотреть одну цифру в вакууме",
    "Проверять не только выручку, но и вклад меню, смен и гостевого опыта",
  ],
  recommendedFocus: [
    "Найти просадки по периодам и категориям",
    "Понять, какие блюда тянут деньги и какие продаются часто",
    "Выделить смены, которые стоит разобрать управляющему",
    "Сформулировать 2-3 действия на сегодняшний день",
  ],
  researchStatus: "template",
};

export function normalizeVenueProfile(
  value: unknown,
): VenueIntelligenceProfile {
  const parsed = VenueIntelligenceSchema.safeParse(value);
  if (!parsed.success) return DEFAULT_VENUE_INTELLIGENCE;

  return {
    ...DEFAULT_VENUE_INTELLIGENCE,
    ...parsed.data,
    audience: parsed.data.audience.length
      ? parsed.data.audience
      : DEFAULT_VENUE_INTELLIGENCE.audience,
    strengths: parsed.data.strengths.length
      ? parsed.data.strengths
      : DEFAULT_VENUE_INTELLIGENCE.strengths,
    guestPains: parsed.data.guestPains.length
      ? parsed.data.guestPains
      : DEFAULT_VENUE_INTELLIGENCE.guestPains,
    ownerGoals: parsed.data.ownerGoals.length
      ? parsed.data.ownerGoals
      : DEFAULT_VENUE_INTELLIGENCE.ownerGoals,
    operatingRisks: parsed.data.operatingRisks.length
      ? parsed.data.operatingRisks
      : DEFAULT_VENUE_INTELLIGENCE.operatingRisks,
    decisionRules: parsed.data.decisionRules.length
      ? parsed.data.decisionRules
      : DEFAULT_VENUE_INTELLIGENCE.decisionRules,
    recommendedFocus: parsed.data.recommendedFocus.length
      ? parsed.data.recommendedFocus
      : DEFAULT_VENUE_INTELLIGENCE.recommendedFocus,
  };
}

export function formatVenueProfileForPrompt(
  profile: VenueIntelligenceProfile,
): string {
  return [
    `Формат: ${profile.format}`,
    `Позиционирование: ${profile.positioning}`,
    `Аудитория: ${profile.audience.join("; ")}`,
    `Сильные стороны: ${profile.strengths.join("; ")}`,
    `Боли гостей: ${profile.guestPains.join("; ")}`,
    `Цели владельца: ${profile.ownerGoals.join("; ")}`,
    `Операционные риски: ${profile.operatingRisks.join("; ")}`,
    `Правила выводов: ${profile.decisionRules.join("; ")}`,
    `Фокус анализа: ${profile.recommendedFocus.join("; ")}`,
  ].join("\n");
}
