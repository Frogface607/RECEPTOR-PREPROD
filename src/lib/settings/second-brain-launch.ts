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
      title: "Профиль ресторана",
      detail: "Формат, боли, правила и ограничения, чтобы Receptor понимал заведение.",
      status: contextReady ? "профиль готов" : `${memoryPercentage}% профиля`,
      href: venue ? `/context${venueQuery}` : onboardingHref,
      action: contextReady ? "Проверить профиль" : "Собрать профиль",
      ready: contextReady,
    },
    {
      id: "iiko",
      step: "02",
      title: "Данные iiko",
      detail: "Продажи, смены и меню становятся фактической базой для разбора.",
      status: iikoReady ? "подключено" : "нужен ключ",
      href: iikoReady ? firstVenueHref : onboardingHref,
      action: iikoReady ? "Открыть разбор" : "Подключить iiko",
      ready: iikoReady,
    },
    {
      id: "people",
      step: "03",
      title: "Команда и роли",
      detail: "Кто владелец, управляющий, кухня, зал и кому выдавать поручения.",
      status: peopleReady ? `${staffCount} человек` : "нужны роли",
      href: venue ? `/team${venueQuery}` : onboardingHref,
      action: peopleReady ? "Открыть команду" : "Добавить команду",
      ready: peopleReady,
    },
    {
      id: "field_note",
      step: "04",
      title: "Итог смены",
      detail: "Гости, погода, стоп-лист, конфликты и что нужно проверить утром.",
      status: fieldNoteReady ? `${fieldNotesCount} заметок` : "нет итогов",
      href: "/me#shift-summary",
      action: fieldNoteReady ? "Смотреть итоги" : "Оставить итог",
      ready: fieldNoteReady,
    },
    {
      id: "advisor",
      step: "05",
      title: "Первый разбор",
      detail: "Короткий ответ владельцу: что происходит, что спросить и что сделать.",
      status: advisorReady ? "можно спрашивать" : "ждет основу",
      href: `${firstVenueHref}${firstVenueHref.includes("?") ? "&" : "?"}chat=1`,
      action: advisorReady ? "Открыть советника" : "Собрать основу",
      ready: advisorReady,
    },
  ];

  const readyCount = items.filter((item) => item.ready).length;
  const focus = items.find((item) => !item.ready) ?? items[0];

  return {
    readyCount,
    totalCount: items.length,
    headline:
      readyCount === items.length
        ? "Кабинет готов к первому рабочему разбору."
        : "Пройдите короткий запуск, чтобы Receptor давал полезные действия.",
    focus,
    items,
  };
}
