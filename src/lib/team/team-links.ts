export type TeamPeriodParams = Record<string, string>;

export function buildTeamHref({
  venueId,
  hash,
  periodParams,
  params: extraParams = {},
}: {
  venueId: string;
  hash: string;
  periodParams?: TeamPeriodParams;
  params?: Record<string, string | undefined>;
}): string {
  const params = new URLSearchParams({
    role: "venue_manager",
    venueId,
    ...(periodParams ?? {}),
  });

  for (const [key, value] of Object.entries(extraParams)) {
    if (value) params.set(key, value);
  }

  return `/team?${params.toString()}${hash}`;
}

export function buildFocusedTeamTaskHref({
  venueId,
  taskId,
  pathname = "/team",
  currentSearch = "",
}: {
  venueId: string;
  taskId: string;
  pathname?: string;
  currentSearch?: string;
}): string {
  const params = new URLSearchParams(currentSearch);
  if (!params.get("role")) params.set("role", "venue_manager");
  params.set("venueId", venueId);
  params.set("focusTaskId", taskId);

  return `${pathname}?${params.toString()}#team-actions`;
}
