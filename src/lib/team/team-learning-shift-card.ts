import type { TeamLearningItem } from "./team-learning";

export type TeamLearningShiftCard = {
  title: string;
  reason: string;
  action: string;
  fieldNote: string;
  checklistLabel: string | null;
};

type LearningShiftCardRule = {
  match: (item: TeamLearningItem) => boolean;
  reason: string;
  action: string;
  fieldNote: string;
};

const RULES: LearningShiftCardRule[] = [
  {
    match: (item) =>
      item.id === "service-recommendation" ||
      item.id === "sales-eight-upsell",
    reason:
      "Это превращает знание сервиса в деньги: официант понимает запрос гостя, рекомендует точнее и не давит.",
    action:
      "На смене выбери одну позицию или пару к заказу и предложи ее гостю в подходящей ситуации.",
    fieldNote:
      "После смены зафиксируй, что спрашивали гости, какая рекомендация сработала и где было неудобно продавать.",
  },
  {
    match: (item) => item.id === "shift-brief" || item.id === "shift-open-close",
    reason:
      "Этот стандарт убирает хаос до посадки и помогает владельцу утром видеть причину цифр, а не только результат.",
    action:
      "Перед сменой проговори один фокус, стоп-лист, ответственных и риск, который нельзя оставить на вечер.",
    fieldNote:
      "После смены оставь короткий итог: что произошло, когда, сколько гостей затронуло и что проверить утром.",
  },
  {
    match: (item) => item.id === "iiko-cash-discipline",
    reason:
      "Без дисциплины в iiko управленческие цифры становятся шумом: скидки, возвраты и чеки ломают выводы.",
    action:
      "На смене проверь, что спорные чеки, скидки и возвраты оформляются по одному правилу.",
    fieldNote:
      "После смены запиши спорные операции и причину, если из-за кассы или iiko появился риск для отчета.",
  },
  {
    match: (item) =>
      item.id === "kitchen-stop-list" || item.id === "tech-card-discipline",
    reason:
      "Кухня и зал должны видеть один и тот же факт: что можно продавать, что нельзя и чем заменить для гостя.",
    action:
      "До загрузки проверь стоп-лист, заготовки и одну понятную замену для зала.",
    fieldNote:
      "После смены зафиксируй, что закончилось, чем заменяли и потеряли ли продажу или доверие гостя.",
  },
  {
    match: (item) => item.id === "restaurant-numbers-basics",
    reason:
      "Команда начинает понимать, зачем владелец смотрит выручку, ФОТ, маржу и средний чек, а не спорит с цифрами вслепую.",
    action:
      "На разборе возьми одну цифру и сформулируй вопрос: что в смене могло на нее повлиять.",
    fieldNote:
      "После смены оставь факт, который помогает объяснить цифру: посадка, состав команды, стоп-лист, скидки или апселл.",
  },
  {
    match: (item) => item.id === "guest-feedback",
    reason:
      "Отзывы и конфликты становятся обучением, когда команда разбирает причину и меняет один стандарт.",
    action:
      "На смене поймай один повторяющийся вопрос, жалобу или момент, где гостю нужна была помощь.",
    fieldNote:
      "После смены запиши ситуацию гостя, реакцию команды и что надо изменить в сервисе или меню.",
  },
];

export function buildTeamLearningShiftCard(
  item: TeamLearningItem,
  checklistTitle?: string,
): TeamLearningShiftCard {
  const rule = RULES.find((candidate) => candidate.match(item));
  const checklistLabel = checklistTitle?.trim() || null;

  return {
    title: checklistLabel ? `Фокус смены: ${checklistLabel}` : "Карточка смены",
    reason:
      rule?.reason ??
      `Этот стандарт нужен, чтобы роль "${item.title}" была понятной в реальной смене, а не оставалась теорией.`,
    action:
      rule?.action ??
      "На смене выбери одно действие из материала и примени его в реальной ситуации.",
    fieldNote:
      rule?.fieldNote ??
      "После смены оставь короткий факт: что получилось, что мешало и что проверить утром.",
    checklistLabel,
  };
}
