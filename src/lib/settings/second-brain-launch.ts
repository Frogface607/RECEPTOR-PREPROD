export type SecondBrainLaunchVenue = {
  id: string;
  iikoConnected: boolean;
  contextRequiredPercentage: number;
  teamMembersCount: number;
  fieldNotesCount: number;
};

export type SecondBrainLaunchItemId =
  | "context"
  | "people"
  | "field_note"
  | "advisor"
  | "iiko";

export type SecondBrainLaunchItem = {
  id: SecondBrainLaunchItemId;
  step: string;
  title: string;
  detail: string;
  status: string;
  href: string;
  action: string;
  ready: boolean;
};

export type SecondBrainLaunchPath = {
  readyCount: number;
  totalCount: number;
  headline: string;
  focus: SecondBrainLaunchItem;
  items: SecondBrainLaunchItem[];
};

export function buildSecondBrainLaunchPath({
  venue,
  firstVenueHref,
}: {
  venue: SecondBrainLaunchVenue | null | undefined;
  firstVenueHref: string;
}): SecondBrainLaunchPath {
  const onboardingHref = "/onboarding?new=1";
  const venueQuery = venue ? `?venueId=${encodeURIComponent(venue.id)}` : "";
  const memoryPercentage = venue?.contextRequiredPercentage ?? 0;
  const contextReady = memoryPercentage >= 100;
  const staffCount = venue?.teamMembersCount ?? 0;
  const peopleReady = staffCount > 1;
  const fieldNotesCount = venue?.fieldNotesCount ?? 0;
  const fieldNoteReady = fieldNotesCount > 0;
  const advisorReady = contextReady && peopleReady && fieldNoteReady;
  const iikoReady = Boolean(venue?.iikoConnected);

  const items: SecondBrainLaunchItem[] = [
    {
      id: "context",
      step: "01",
      title: "Память ресторана",
      detail: "Формат, боли, правила, стандарты и красные линии для советника.",
      status: contextReady ? "контекст готов" : `${memoryPercentage}% памяти`,
      href: venue ? `/context${venueQuery}` : onboardingHref,
      action: contextReady ? "Проверить память" : "Ответить на вопросы",
      ready: contextReady,
    },
    {
      id: "people",
      step: "02",
      title: "Люди и роли",
      detail: "Кто владелец, управляющий, кухня, зал и кто отвечает за решения.",
      status: peopleReady ? `${staffCount} человек` : "нужны роли",
      href: venue ? `/team${venueQuery}` : onboardingHref,
      action: peopleReady ? "Открыть команду" : "Добавить людей",
      ready: peopleReady,
    },
    {
      id: "field_note",
      step: "03",
      title: "Итог смены",
      detail: "Живые факты: гости, погода, стоп-лист, конфликты и что проверить утром.",
      status: fieldNoteReady ? `${fieldNotesCount} заметок` : "память пустая",
      href: "/me#shift-summary",
      action: fieldNoteReady ? "Смотреть память" : "Оставить итог",
      ready: fieldNoteReady,
    },
    {
      id: "advisor",
      step: "04",
      title: "Советник владельца",
      detail: "Утренний разбор объединяет контекст, команду, смену и факты iiko.",
      status: advisorReady ? "можно спрашивать" : "ждет память",
      href: `${firstVenueHref}${firstVenueHref.includes("?") ? "&" : "?"}chat=1`,
      action: advisorReady ? "Открыть советника" : "Собрать основу",
      ready: advisorReady,
    },
    {
      id: "iiko",
      step: "05",
      title: "Факты iiko",
      detail: "Продажи, смены и меню становятся доказательным слоем поверх памяти.",
      status: iikoReady ? "подключено" : "нужен ключ",
      href: iikoReady ? firstVenueHref : onboardingHref,
      action: iikoReady ? "Открыть BI" : "Подключить",
      ready: iikoReady,
    },
  ];

  const readyCount = items.filter((item) => item.ready).length;
  const focus = items.find((item) => !item.ready) ?? items[0];

  return {
    readyCount,
    totalCount: items.length,
    headline:
      readyCount === items.length
        ? "Второй мозг ресторана готов к рабочему дню."
        : "Соберите основу, чтобы советник стал полезным.",
    focus,
    items,
  };
}
