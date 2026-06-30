import type { TeamTask, TeamTaskComment } from "./team-os";

export type TeamFieldSignalKind =
  "conflict" | "stock" | "event" | "guest" | "team" | "service";

export type TeamFieldSignal = {
  kind: TeamFieldSignalKind;
  title: string;
  detail: string;
  sourceCount: number;
  latestAtLabel: string;
};

export type TeamFieldContextDigest = {
  totalNotes: number;
  signalCount: number;
  signals: TeamFieldSignal[];
  summary: string;
};

const SYSTEM_MARKERS = [
  "урок для команды:",
  "стандарт:",
  "стандарт задачи:",
  "чеклист:",
  "зачем:",
  "receptor",
];
const FIELD_CONTEXT_TASK_TITLE = "Полевой контекст смены";
const FIELD_CONTEXT_SOURCE_LABELS = new Set(["Поле", "Полевой контекст"]);

const SIGNAL_RULES: Array<{
  kind: TeamFieldSignalKind;
  title: string;
  keywords: string[];
}> = [
  {
    kind: "conflict",
    title: "Конфликты и жалобы",
    keywords: ["конфликт", "жалоб", "недовол", "возврат", "спор"],
  },
  {
    kind: "stock",
    title: "Стоп-лист и заготовки",
    keywords: ["стоп", "закончил", "не было", "нет в наличии", "заготов"],
  },
  {
    kind: "event",
    title: "События и посадка",
    keywords: ["банкет", "мероприят", "событи", "посадк", "гостей", "очеред"],
  },
  {
    kind: "guest",
    title: "Вопросы гостей",
    keywords: [
      "спрашивал",
      "спросили",
      "просили",
      "гость спрос",
      "часто спраш",
    ],
  },
  {
    kind: "team",
    title: "Трение в команде",
    keywords: ["неудоб", "не успев", "хаос", "долго", "меша", "устал"],
  },
  {
    kind: "service",
    title: "Сервис и продажи",
    keywords: ["апсел", "допрод", "рекоменд", "продаж", "сервис", "задерж"],
  },
];

function normalize(value: string): string {
  return value.trim().replace(/\s+/g, " ");
}

function searchText(value: string): string {
  return normalize(value).toLocaleLowerCase("ru-RU");
}

function isSystemComment(comment: TeamTaskComment): boolean {
  const body = searchText(comment.body);
  return SYSTEM_MARKERS.some((marker) => body.includes(marker));
}

function commentTaskLabel(
  comment: TeamTaskComment,
  tasksById: Map<string, TeamTask>,
): string {
  const task = tasksById.get(comment.taskId);
  if (!task) return comment.authorName;
  return `${comment.authorName}: ${task.sourceLabel ?? task.title}`;
}

function isFieldContextTask(task: TeamTask | undefined): boolean {
  if (!task) return false;
  return (
    task.title === FIELD_CONTEXT_TASK_TITLE ||
    FIELD_CONTEXT_SOURCE_LABELS.has(task.sourceLabel ?? "")
  );
}

function signalWeight(kind: TeamFieldSignalKind): number {
  if (kind === "conflict" || kind === "stock") return 500;
  if (kind === "team") return 400;
  if (kind === "event") return 300;
  if (kind === "guest") return 200;
  return 100;
}

function relatedSignalsLine(signals: TeamFieldSignal[]): string {
  const related = signals.slice(1);
  if (related.length === 0) return "";

  return ` Связанные факты: ${related
    .map((signal) => `${signal.title} (${signal.sourceCount})`)
    .join(", ")}.`;
}

function fieldSummary(signals: TeamFieldSignal[]): string {
  if (signals.length === 0) return "";
  return `${signals[0].title}: ${signals[0].detail}${relatedSignalsLine(
    signals,
  )}`;
}

function untaggedFieldSummary(
  notes: TeamTaskComment[],
  tasksById: Map<string, TeamTask>,
): string {
  const latest = notes[notes.length - 1];
  if (!latest) return "";

  const prefix =
    notes.length === 1
      ? "Команда оставила заметку без явного BI-тега"
      : `Команда оставила ${notes.length} заметок без явного BI-тега`;

  return `${prefix}: ${commentTaskLabel(latest, tasksById)} — ${normalize(latest.body)}`;
}

export function buildTeamFieldContextDigest({
  comments,
  tasks = [],
}: {
  comments: TeamTaskComment[];
  tasks?: TeamTask[];
}): TeamFieldContextDigest | null {
  const tasksById = new Map(tasks.map((task) => [task.id, task]));
  const candidateComments = comments.filter(
    (comment) =>
      normalize(comment.body).length > 0 && !isSystemComment(comment),
  );

  if (candidateComments.length === 0) return null;

  const matchedCommentIds = new Set<string>();

  const signals = SIGNAL_RULES.flatMap((rule) => {
    const matched = candidateComments.filter((comment) => {
      const body = searchText(comment.body);
      return rule.keywords.some((keyword) => body.includes(keyword));
    });

    if (matched.length === 0) return [];
    for (const comment of matched) matchedCommentIds.add(comment.id);

    const latest = matched[matched.length - 1];
    return [
      {
        kind: rule.kind,
        title: rule.title,
        detail: `${commentTaskLabel(latest, tasksById)} — ${normalize(latest.body)}`,
        sourceCount: matched.length,
        latestAtLabel: latest.createdAtLabel,
      },
    ];
  }).sort((a, b) => {
    const weightDelta = signalWeight(b.kind) - signalWeight(a.kind);
    return weightDelta || b.sourceCount - a.sourceCount;
  });

  const fieldContextNotes = candidateComments.filter(
    (comment) =>
      isFieldContextTask(tasksById.get(comment.taskId)) &&
      !matchedCommentIds.has(comment.id),
  );

  if (signals.length === 0 && fieldContextNotes.length === 0) return null;

  const totalNotes = new Set([
    ...matchedCommentIds,
    ...fieldContextNotes.map((comment) => comment.id),
  ]).size;

  const signalCount = signals.reduce(
    (sum, signal) => sum + signal.sourceCount,
    0,
  );
  const summary =
    signals.length > 0
      ? fieldSummary(signals)
      : untaggedFieldSummary(fieldContextNotes, tasksById);

  return {
    totalNotes,
    signalCount,
    signals: signals.slice(0, 3),
    summary,
  };
}
