"use client";

import { useMemo, useState, useTransition, type ReactNode } from "react";
import { Megaphone, MessageSquareText, Send } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  listAnnouncementsForRole,
  listCommentsForTask,
  TEAM_ROLES,
  type TeamAnnouncement,
  type TeamRoleId,
  type TeamTask,
  type TeamTaskComment,
} from "@/lib/team/team-os";
import {
  addTaskCommentAction,
  createTeamAnnouncementAction,
  type TeamActionResult,
} from "./actions";

type Message = {
  tone: "success" | "error";
  text: string;
};

const FIELD_CLASS =
  "w-full rounded-lg border border-border/55 bg-background/45 px-3 py-2 text-sm text-foreground outline-none transition focus:border-brand/50 focus:ring-2 focus:ring-brand/15";

function resultToMessage(result: TeamActionResult): Message {
  if (!result.ok) return { tone: "error", text: result.error };
  return { tone: "success", text: result.message };
}

export function TeamCommunicationPanel({
  venueId,
  roleId,
  tasks,
  comments,
  announcements,
}: {
  venueId: string;
  roleId: TeamRoleId;
  tasks: TeamTask[];
  comments: TeamTaskComment[];
  announcements: TeamAnnouncement[];
}) {
  const [pending, startTransition] = useTransition();
  const [message, setMessage] = useState<Message | null>(null);
  const [selectedTaskId, setSelectedTaskId] = useState(tasks[0]?.id ?? "");
  const [commentBody, setCommentBody] = useState("");

  const [announcementTitle, setAnnouncementTitle] = useState("");
  const [announcementBody, setAnnouncementBody] = useState("");
  const [announcementPriority, setAnnouncementPriority] =
    useState<TeamAnnouncement["priority"]>("normal");
  const [announcementAudienceType, setAnnouncementAudienceType] =
    useState<TeamAnnouncement["audience"]["type"]>("venue");
  const [announcementAudienceRole, setAnnouncementAudienceRole] =
    useState<TeamRoleId>("service");

  const visibleAnnouncements = useMemo(
    () => listAnnouncementsForRole(roleId, venueId, announcements),
    [announcements, roleId, venueId],
  );
  const taskComments = useMemo(
    () => listCommentsForTask(selectedTaskId, comments),
    [comments, selectedTaskId],
  );

  function runAction(action: () => Promise<TeamActionResult>) {
    setMessage(null);
    startTransition(async () => {
      const result = await action();
      setMessage(resultToMessage(result));
    });
  }

  return (
    <section className="border-b border-border/40">
      <div className="mx-auto max-w-7xl px-6 py-8">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-[11px] uppercase tracking-[0.18em] text-brand">
              Связь
            </p>
            <h2 className="mt-2 text-2xl font-medium">
              Объявления и комментарии
            </h2>
          </div>
          <p className="max-w-md text-sm text-muted-foreground">
            Решения по смене и контекст задач.
          </p>
        </div>

        {message ? (
          <div
            className={
              "mt-6 rounded-lg border px-4 py-3 text-sm " +
              (message.tone === "success"
                ? "border-brand/30 bg-brand/10 text-brand"
                : "border-destructive/30 bg-destructive/10 text-destructive")
            }
          >
            {message.text}
          </div>
        ) : null}

        <div className="mt-6 grid gap-4 xl:grid-cols-2">
          <div className="rounded-lg border border-border/60 bg-card/50 p-5">
            <div className="flex items-center gap-3">
              <Megaphone className="size-5 text-brand" />
              <h3 className="text-lg font-medium">Объявления</h3>
            </div>

            <form
              className="mt-5 space-y-3"
              onSubmit={(event) => {
                event.preventDefault();
                runAction(async () => {
                  const result = await createTeamAnnouncementAction({
                    venueId,
                    title: announcementTitle,
                    body: announcementBody,
                    priority: announcementPriority,
                    audienceType: announcementAudienceType,
                    audienceRole: announcementAudienceRole,
                  });
                  if (result.ok) {
                    setAnnouncementTitle("");
                    setAnnouncementBody("");
                  }
                  return result;
                });
              }}
            >
              <FieldLabel label="Заголовок">
                <input
                  value={announcementTitle}
                  onChange={(event) => setAnnouncementTitle(event.target.value)}
                  className={FIELD_CLASS}
                  placeholder="Фокус вечерней смены"
                  required
                />
              </FieldLabel>
              <FieldLabel label="Текст">
                <textarea
                  value={announcementBody}
                  onChange={(event) => setAnnouncementBody(event.target.value)}
                  className={`${FIELD_CLASS} min-h-24 resize-none`}
                  placeholder="Что команда должна знать?"
                  required
                />
              </FieldLabel>
              <div className="grid gap-3 sm:grid-cols-3">
                <FieldLabel label="Важность">
                  <select
                    value={announcementPriority}
                    onChange={(event) =>
                      setAnnouncementPriority(
                        event.target.value as TeamAnnouncement["priority"],
                      )
                    }
                    className={FIELD_CLASS}
                  >
                    <option value="normal">normal</option>
                    <option value="important">important</option>
                  </select>
                </FieldLabel>
                <FieldLabel label="Кому">
                  <select
                    value={announcementAudienceType}
                    onChange={(event) =>
                      setAnnouncementAudienceType(
                        event.target.value as TeamAnnouncement["audience"]["type"],
                      )
                    }
                    className={FIELD_CLASS}
                  >
                    <option value="venue">Всему заведению</option>
                    <option value="role">Роли</option>
                  </select>
                </FieldLabel>
                {announcementAudienceType === "role" ? (
                  <FieldLabel label="Роль">
                    <select
                      value={announcementAudienceRole}
                      onChange={(event) =>
                        setAnnouncementAudienceRole(
                          event.target.value as TeamRoleId,
                        )
                      }
                      className={FIELD_CLASS}
                    >
                      {TEAM_ROLES.map((role) => (
                        <option key={role.id} value={role.id}>
                          {role.title}
                        </option>
                      ))}
                    </select>
                  </FieldLabel>
                ) : (
                  <div className="hidden sm:block" />
                )}
              </div>
              <Button type="submit" disabled={pending}>
                <Send className="size-4" />
                Опубликовать
              </Button>
            </form>

            <div className="mt-6 space-y-3">
              {visibleAnnouncements.map((announcement) => (
                <AnnouncementRow
                  key={announcement.id}
                  announcement={announcement}
                />
              ))}
            </div>
          </div>

          <div className="rounded-lg border border-border/60 bg-card/50 p-5">
            <div className="flex items-center gap-3">
              <MessageSquareText className="size-5 text-brand" />
              <h3 className="text-lg font-medium">Комментарии к задаче</h3>
            </div>

            <div className="mt-5 space-y-3">
              <FieldLabel label="Задача">
                <select
                  value={selectedTaskId}
                  onChange={(event) => setSelectedTaskId(event.target.value)}
                  className={FIELD_CLASS}
                >
                  {tasks.map((task) => (
                    <option key={task.id} value={task.id}>
                      {task.title}
                    </option>
                  ))}
                </select>
              </FieldLabel>

              <form
                className="space-y-3"
                onSubmit={(event) => {
                  event.preventDefault();
                  runAction(async () => {
                    const result = await addTaskCommentAction({
                      venueId,
                      taskId: selectedTaskId,
                      body: commentBody,
                    });
                    if (result.ok) setCommentBody("");
                    return result;
                  });
                }}
              >
                <FieldLabel label="Комментарий">
                  <textarea
                    value={commentBody}
                    onChange={(event) => setCommentBody(event.target.value)}
                    className={`${FIELD_CLASS} min-h-24 resize-none`}
                    placeholder="Что изменилось по задаче?"
                    required
                  />
                </FieldLabel>
                <Button type="submit" disabled={pending || !selectedTaskId}>
                  <Send className="size-4" />
                  Добавить комментарий
                </Button>
              </form>
            </div>

            <div className="mt-6 space-y-3">
              {taskComments.length > 0 ? (
                taskComments.map((comment) => (
                  <CommentRow key={comment.id} comment={comment} />
                ))
              ) : (
                <p className="rounded-lg border border-border/45 bg-background/35 p-3 text-sm text-muted-foreground">
                  Комментариев по этой задаче пока нет.
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function AnnouncementRow({
  announcement,
}: {
  announcement: TeamAnnouncement;
}) {
  return (
    <article className="rounded-lg border border-border/45 bg-background/35 p-3">
      <div className="flex flex-wrap items-center gap-2">
        <Badge
          variant="outline"
          className={
            announcement.priority === "important"
              ? "border-[color:var(--pro)]/30 bg-[color:var(--pro)]/10 text-[color:var(--pro)]"
              : ""
          }
        >
          {announcement.priority}
        </Badge>
        <span className="text-[11px] uppercase tracking-[0.16em] text-muted-foreground">
          {announcement.createdAtLabel}
        </span>
      </div>
      <h4 className="mt-3 text-sm font-medium">{announcement.title}</h4>
      <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
        {announcement.body}
      </p>
    </article>
  );
}

function CommentRow({ comment }: { comment: TeamTaskComment }) {
  return (
    <article className="rounded-lg border border-border/45 bg-background/35 p-3">
      <div className="flex flex-wrap items-center gap-2">
        <p className="text-sm font-medium">{comment.authorName}</p>
        <span className="text-[11px] uppercase tracking-[0.16em] text-muted-foreground">
          {comment.createdAtLabel}
        </span>
      </div>
      <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
        {comment.body}
      </p>
    </article>
  );
}

function FieldLabel({
  label,
  children,
}: {
  label: string;
  children: ReactNode;
}) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-[11px] uppercase tracking-[0.16em] text-muted-foreground">
        {label}
      </span>
      {children}
    </label>
  );
}
