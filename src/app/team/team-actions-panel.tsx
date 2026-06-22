"use client";

import { useMemo, useState, useTransition, type ReactNode } from "react";
import { Plus, Send, UserPlus } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  TEAM_ROLES,
  type StaffMember,
  type TeamRoleId,
  type TeamTask,
} from "@/lib/team/team-os";
import {
  createTeamTaskAction,
  inviteTeamMemberAction,
  updateTeamTaskStatusAction,
  type TeamActionResult,
} from "./actions";

type Message = {
  tone: "success" | "error";
  text: string;
};

const TASK_STATUSES: Array<{ value: TeamTask["status"]; label: string }> = [
  { value: "new", label: "новая" },
  { value: "accepted", label: "принята" },
  { value: "in_progress", label: "в работе" },
  { value: "done", label: "сделано" },
  { value: "verified", label: "проверено" },
];

const TASK_PRIORITIES: Array<{ value: TeamTask["priority"]; label: string }> = [
  { value: "high", label: "high" },
  { value: "medium", label: "medium" },
  { value: "low", label: "low" },
];

const FIELD_CLASS =
  "w-full rounded-lg border border-border/55 bg-background/45 px-3 py-2 text-sm text-foreground outline-none transition focus:border-brand/50 focus:ring-2 focus:ring-brand/15";

function resultToMessage(result: TeamActionResult): Message {
  if (!result.ok) return { tone: "error", text: result.error };
  return { tone: "success", text: result.message };
}

export function TeamActionsPanel({
  venueId,
  staff,
  tasks,
}: {
  venueId: string;
  staff: StaffMember[];
  tasks: TeamTask[];
}) {
  const [pending, startTransition] = useTransition();
  const [message, setMessage] = useState<Message | null>(null);

  const [memberName, setMemberName] = useState("");
  const [memberEmail, setMemberEmail] = useState("");
  const [memberRole, setMemberRole] = useState<TeamRoleId>("service");
  const [memberShift, setMemberShift] = useState("");

  const [taskTitle, setTaskTitle] = useState("");
  const [taskPriority, setTaskPriority] =
    useState<TeamTask["priority"]>("medium");
  const [audienceType, setAudienceType] =
    useState<TeamTask["audience"]["type"]>("role");
  const [audienceRole, setAudienceRole] = useState<TeamRoleId>("service");
  const [audienceMemberId, setAudienceMemberId] = useState(staff[0]?.id ?? "");
  const [dueLabel, setDueLabel] = useState("сегодня");

  const [statusTaskId, setStatusTaskId] = useState(tasks[0]?.id ?? "");
  const [nextStatus, setNextStatus] =
    useState<TeamTask["status"]>("in_progress");

  const selectableStaff = useMemo(
    () => staff.filter((member) => member.status !== "paused"),
    [staff],
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
      <div className="mx-auto max-w-7xl px-6 py-14">
        <div className="max-w-3xl">
          <p className="text-[11px] uppercase tracking-[0.22em] text-brand">
            Team actions
          </p>
          <h2 className="mt-4 text-3xl font-medium">
            Первые операции без Telegram.
          </h2>
          <p className="mt-4 text-sm leading-relaxed text-muted-foreground">
            Добавляем людей, ставим задачи конкретному человеку, роли или всей
            точке, и двигаем статус задачи. Комментарии и объявления идут
            следующим слоем.
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

        <div className="mt-8 grid gap-5 xl:grid-cols-3">
          <form
            className="rounded-lg border border-border/60 bg-card/50 p-5"
            onSubmit={(event) => {
              event.preventDefault();
              runAction(async () => {
                const result = await inviteTeamMemberAction({
                  venueId,
                  fullName: memberName,
                  email: memberEmail,
                  role: memberRole,
                  shiftLabel: memberShift,
                });
                if (result.ok) {
                  setMemberName("");
                  setMemberEmail("");
                  setMemberShift("");
                }
                return result;
              });
            }}
          >
            <div className="flex items-center gap-3">
              <UserPlus className="size-5 text-brand" />
              <h3 className="text-lg font-medium">Добавить сотрудника</h3>
            </div>
            <div className="mt-5 space-y-3">
              <FieldLabel label="Имя">
                <input
                  value={memberName}
                  onChange={(event) => setMemberName(event.target.value)}
                  className={FIELD_CLASS}
                  placeholder="Имя сотрудника"
                  required
                />
              </FieldLabel>
              <FieldLabel label="Email">
                <input
                  value={memberEmail}
                  onChange={(event) => setMemberEmail(event.target.value)}
                  className={FIELD_CLASS}
                  placeholder="name@example.com"
                  type="email"
                />
              </FieldLabel>
              <FieldLabel label="Роль">
                <select
                  value={memberRole}
                  onChange={(event) =>
                    setMemberRole(event.target.value as TeamRoleId)
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
              <FieldLabel label="Смена">
                <input
                  value={memberShift}
                  onChange={(event) => setMemberShift(event.target.value)}
                  className={FIELD_CLASS}
                  placeholder="сегодня 16:00-00:00"
                />
              </FieldLabel>
            </div>
            <Button type="submit" className="mt-5 w-full" disabled={pending}>
              <Plus className="size-4" />
              Добавить
            </Button>
          </form>

          <form
            className="rounded-lg border border-border/60 bg-card/50 p-5"
            onSubmit={(event) => {
              event.preventDefault();
              runAction(async () => {
                const result = await createTeamTaskAction({
                  venueId,
                  title: taskTitle,
                  priority: taskPriority,
                  audienceType,
                  audienceRole,
                  audienceMemberId,
                  dueLabel,
                });
                if (result.ok) {
                  setTaskTitle("");
                }
                return result;
              });
            }}
          >
            <div className="flex items-center gap-3">
              <Send className="size-5 text-brand" />
              <h3 className="text-lg font-medium">Создать задачу</h3>
            </div>
            <div className="mt-5 space-y-3">
              <FieldLabel label="Задача">
                <textarea
                  value={taskTitle}
                  onChange={(event) => setTaskTitle(event.target.value)}
                  className={`${FIELD_CLASS} min-h-24 resize-none`}
                  placeholder="Что нужно сделать?"
                  required
                />
              </FieldLabel>
              <div className="grid gap-3 sm:grid-cols-2">
                <FieldLabel label="Приоритет">
                  <select
                    value={taskPriority}
                    onChange={(event) =>
                      setTaskPriority(event.target.value as TeamTask["priority"])
                    }
                    className={FIELD_CLASS}
                  >
                    {TASK_PRIORITIES.map((priority) => (
                      <option key={priority.value} value={priority.value}>
                        {priority.label}
                      </option>
                    ))}
                  </select>
                </FieldLabel>
                <FieldLabel label="Срок">
                  <input
                    value={dueLabel}
                    onChange={(event) => setDueLabel(event.target.value)}
                    className={FIELD_CLASS}
                    placeholder="сегодня"
                  />
                </FieldLabel>
              </div>
              <FieldLabel label="Кому">
                <select
                  value={audienceType}
                  onChange={(event) =>
                    setAudienceType(
                      event.target.value as TeamTask["audience"]["type"],
                    )
                  }
                  className={FIELD_CLASS}
                >
                  <option value="role">Роли</option>
                  <option value="member">Сотруднику</option>
                  <option value="venue">Всему заведению</option>
                </select>
              </FieldLabel>
              {audienceType === "role" ? (
                <FieldLabel label="Роль">
                  <select
                    value={audienceRole}
                    onChange={(event) =>
                      setAudienceRole(event.target.value as TeamRoleId)
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
              ) : null}
              {audienceType === "member" ? (
                <FieldLabel label="Сотрудник">
                  <select
                    value={audienceMemberId}
                    onChange={(event) => setAudienceMemberId(event.target.value)}
                    className={FIELD_CLASS}
                    required
                  >
                    {selectableStaff.map((member) => (
                      <option key={member.id} value={member.id}>
                        {member.name}
                      </option>
                    ))}
                  </select>
                </FieldLabel>
              ) : null}
            </div>
            <Button type="submit" className="mt-5 w-full" disabled={pending}>
              <Plus className="size-4" />
              Создать
            </Button>
          </form>

          <form
            className="rounded-lg border border-border/60 bg-card/50 p-5"
            onSubmit={(event) => {
              event.preventDefault();
              runAction(() =>
                updateTeamTaskStatusAction({
                  venueId,
                  taskId: statusTaskId,
                  status: nextStatus,
                }),
              );
            }}
          >
            <div className="flex items-center gap-3">
              <Send className="size-5 text-brand" />
              <h3 className="text-lg font-medium">Обновить статус</h3>
            </div>
            <div className="mt-5 space-y-3">
              <FieldLabel label="Задача">
                <select
                  value={statusTaskId}
                  onChange={(event) => setStatusTaskId(event.target.value)}
                  className={FIELD_CLASS}
                  required
                >
                  {tasks.map((task) => (
                    <option key={task.id} value={task.id}>
                      {task.title}
                    </option>
                  ))}
                </select>
              </FieldLabel>
              <FieldLabel label="Новый статус">
                <select
                  value={nextStatus}
                  onChange={(event) =>
                    setNextStatus(event.target.value as TeamTask["status"])
                  }
                  className={FIELD_CLASS}
                >
                  {TASK_STATUSES.map((status) => (
                    <option key={status.value} value={status.value}>
                      {status.label}
                    </option>
                  ))}
                </select>
              </FieldLabel>
            </div>
            <Button
              type="submit"
              className="mt-5 w-full"
              disabled={pending || tasks.length === 0}
            >
              Обновить
            </Button>
          </form>
        </div>
      </div>
    </section>
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
