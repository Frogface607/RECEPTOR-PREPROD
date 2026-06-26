import type { TeamRoleId } from "./team-os";

export type RoleDayFocus = {
  title: string;
  summary: string;
};

export type TeamLearningItem = {
  id: string;
  title: string;
  description: string;
  timeLabel: string;
  status: "required" | "ready" | "soon";
  roles?: readonly TeamRoleId[];
};

const ROLE_DAY_FOCUS: Record<TeamRoleId, RoleDayFocus> = {
  owner: {
    title: "Деньги, риски, команда",
    summary:
      "Проверь выручку, просевшие зоны, важные задачи и то, где команде нужен быстрый управленческий сигнал.",
  },
  operations_manager: {
    title: "Контроль точек и стандартов",
    summary:
      "Собери статус по сменам, задачам, стоп-листу и проблемам, которые нельзя оставлять до завтра.",
  },
  venue_manager: {
    title: "Смена без потерь",
    summary:
      "Раздай фокус команде, проверь готовность зала и кухни, закрой зависшие задачи до пикового времени.",
  },
  chef: {
    title: "Кухня, стоп-лист, техкарты",
    summary:
      "Проверь заготовки, проблемные позиции, себестоимость и то, что зал сегодня должен продавать аккуратно.",
  },
  line_cook: {
    title: "Отдача по стандарту",
    summary:
      "Сверь заготовки, техкарты и задачи шефа. В смене важно не держать вопросы в голове.",
  },
  service: {
    title: "Гость, сервис, рекомендации",
    summary:
      "Посмотри фокус продаж, объявления по смене и задачи, которые влияют на сервис прямо сегодня.",
  },
  marketing: {
    title: "Спрос, события, отзывы",
    summary:
      "Проверь контент, события, отзывы и задачи, которые помогают ресторану получить гостей в ближайшие дни.",
  },
};

const SHIFT_CHECKLIST: Record<TeamRoleId, string[]> = {
  owner: [
    "Открыть панель владельца и проверить выручку периода.",
    "Посмотреть важные задачи управляющего и шефа.",
    "Дать один понятный фокус команде на день.",
  ],
  operations_manager: [
    "Сверить статусы задач по точкам.",
    "Проверить роли, доступы и ответственных на смене.",
    "Зафиксировать один риск, который требует решения сегодня.",
  ],
  venue_manager: [
    "Проверить состав смены и зоны ответственности.",
    "Раздать задачи залу и кухне до пикового времени.",
    "Опубликовать короткое объявление по фокусу смены.",
  ],
  chef: [
    "Проверить стоп-лист и заготовки.",
    "Разобрать позиции с риском по себестоимости.",
    "Передать залу, что сегодня продавать осторожно или активно.",
  ],
  line_cook: [
    "Открыть свои задачи и принять новые.",
    "Сверить техкарты по позициям в фокусе.",
    "Сообщить шефу о недостающих заготовках до загрузки.",
  ],
  service: [
    "Прочитать объявления перед сменой.",
    "Принять задачи управляющего.",
    "Выучить фокус продаж и одну рекомендацию гостю.",
  ],
  marketing: [
    "Проверить события и промо на ближайшие дни.",
    "Собрать отзывы, на которые нужен ответ.",
    "Подготовить один пост или сторис по фокусу ресторана.",
  ],
};

const LEARNING_CATALOG: TeamLearningItem[] = [
  {
    id: "service-recommendation",
    title: "Как рекомендовать блюдо без давления",
    description:
      "Короткий стандарт для официанта: вопрос гостю, одна уверенная рекомендация, напиток и десерт в конце.",
    timeLabel: "7 минут",
    status: "required",
    roles: ["service", "venue_manager"],
  },
  {
    id: "shift-brief",
    title: "Бриф смены: что сказать команде",
    description:
      "Шаблон короткой планерки: цель дня, стоп-лист, роли, риск и одно действие для каждого участка.",
    timeLabel: "5 минут",
    status: "ready",
    roles: ["venue_manager", "operations_manager", "owner"],
  },
  {
    id: "kitchen-stop-list",
    title: "Стоп-лист и заготовки до посадки",
    description:
      "Как быстро проверить готовность кухни и не узнать о проблеме уже на пике.",
    timeLabel: "6 минут",
    status: "required",
    roles: ["chef", "line_cook", "venue_manager"],
  },
  {
    id: "tech-card-discipline",
    title: "Техкарта как договор внутри команды",
    description:
      "Что должно совпадать между отдачей, списанием, себестоимостью и ожиданием гостя.",
    timeLabel: "9 минут",
    status: "ready",
    roles: ["chef", "line_cook", "owner", "operations_manager"],
  },
  {
    id: "owner-morning",
    title: "Утренний контроль владельца",
    description:
      "Четыре вопроса: деньги, маржа, команда, гости. Без длинного отчета, только решение на сегодня.",
    timeLabel: "4 минуты",
    status: "ready",
    roles: ["owner", "operations_manager"],
  },
  {
    id: "guest-feedback",
    title: "Отзывы и повторные визиты",
    description:
      "Как собрать обратную связь и превратить ее в задачу для зала, кухни или маркетинга.",
    timeLabel: "8 минут",
    status: "soon",
    roles: ["marketing", "venue_manager", "service"],
  },
];

export function getRoleDayFocus(roleId: TeamRoleId): RoleDayFocus {
  return ROLE_DAY_FOCUS[roleId];
}

export function listShiftChecklistForRole(roleId: TeamRoleId): string[] {
  return SHIFT_CHECKLIST[roleId];
}

export function listLearningItemsForRole(roleId: TeamRoleId): TeamLearningItem[] {
  return LEARNING_CATALOG.filter(
    (item) => !item.roles || item.roles.includes(roleId),
  );
}
