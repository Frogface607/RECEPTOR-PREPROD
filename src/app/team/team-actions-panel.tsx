"use client";

import { useMemo, useState, useTransition, type ReactNode } from "react";
import {
  Copy,
  KeyRound,
  PauseCircle,
  PlayCircle,
  Plus,
  Send,
  UserPlus,
} from "lucide-react";
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
  resetTeamMemberPasswordAction,
  updateTeamMemberStatusAction,
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
  const [memberLogin, setMemberLogin] = useState("");
  const [memberPassword, setMemberPassword] = useState("");
  const [memberRole, setMemberRole] = useState<TeamRoleId>("service");
  const [memberShift, setMemberShift] = useState("");
  const [resetPasswords, setResetPasswords] = useState<
    Record<string, string>
  >({});
  const [copiedMemberId, setCopiedMemberId] = useState<string | null>(null);

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

  async function copyLogin(member: StaffMember) {
    if (!member.email) return;
    await navigator.clipboard.writeText(member.email);
    setCopiedMemberId(member.id);
    window.setTimeout(() => setCopiedMemberId(null), 1600);
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
                  login: memberLogin,
                  password: memberPassword,
                  role: memberRole,
                  shiftLabel: memberShift,
                });
                if (result.ok) {
                  setMemberName("");
                  setMemberEmail("");
                  setMemberLogin("");
                  setMemberPassword("");
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
              <div className="grid gap-3 sm:grid-cols-2">
                <FieldLabel label="Логин">
                  <input
                    value={memberLogin}
                    onChange={(event) => setMemberLogin(event.target.value)}
                    className={FIELD_CLASS}
                    placeholder="masha"
                    autoComplete="off"
                  />
                </FieldLabel>
                <FieldLabel label="Пароль">
                  <input
                    value={memberPassword}
                    onChange={(event) => setMemberPassword(event.target.value)}
                    className={FIELD_CLASS}
                    placeholder="временный пароль"
                    type="password"
                    autoComplete="new-password"
                  />
                </FieldLabel>
              </div>
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
            <p className="mt-3 text-[12px] leading-relaxed text-muted-foreground">
              Если задать логин и пароль, Receptor создаст личный вход
              сотрудника. Короткий логин станет адресом вида
              login@staff.receptorai.pro.
            </p>
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

        <div className="mt-8 rounded-lg border border-border/60 bg-card/50 p-5">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="text-[11px] uppercase tracking-[0.22em] text-brand">
                Доступы
              </p>
              <h3 className="mt-2 text-xl font-medium">
                Логины, статусы и сброс пароля
              </h3>
            </div>
            <p className="max-w-md text-xs leading-relaxed text-muted-foreground">
              Активный сотрудник может войти в личный кабинет. Пауза скрывает
              его кабинет без удаления истории задач.
            </p>
          </div>

          <div className="mt-5 overflow-x-auto">
            <table className="w-full min-w-[860px] text-left text-sm">
              <thead>
                <tr className="border-b border-border/50 text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
                  <th className="px-3 py-3 font-normal">Сотрудник</th>
                  <th className="px-3 py-3 font-normal">Роль</th>
                  <th className="px-3 py-3 font-normal">Логин</th>
                  <th className="px-3 py-3 font-normal">Статус</th>
                  <th className="px-3 py-3 font-normal">Пароль</th>
                  <th className="px-3 py-3 font-normal">Действия</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/35">
                {staff.map((member) => {
                  const role = TEAM_ROLES.find(
                    (item) => item.id === member.roleId,
                  );
                  const resetPassword = resetPasswords[member.id] ?? "";
                  const canReset = Boolean(member.userId);
                  return (
                    <tr key={member.id} className="align-top">
                      <td className="px-3 py-4">
                        <p className="font-medium text-foreground">{member.name}</p>
                        <p className="mt-1 text-xs text-muted-foreground">
                          {member.shiftLabel || "смена не указана"}
                        </p>
                      </td>
                      <td className="px-3 py-4 text-muted-foreground">
                        {role?.title ?? member.roleId}
                      </td>
                      <td className="px-3 py-4">
                        {member.email ? (
                          <button
                            type="button"
                            onClick={() => copyLogin(member)}
                            className="inline-flex items-center gap-2 rounded-md border border-border/55 bg-background/45 px-2.5 py-1.5 font-mono text-xs text-foreground transition-colors hover:border-brand/40"
                          >
                            <Copy className="size-3.5 text-brand" />
                            {copiedMemberId === member.id
                              ? "скопировано"
                              : member.email}
                          </button>
                        ) : (
                          <span className="text-xs text-muted-foreground">
                            нет логина
                          </span>
                        )}
                      </td>
                      <td className="px-3 py-4">
                        <span
                          className={
                            "rounded-md border px-2 py-1 text-[11px] uppercase tracking-[0.14em] " +
                            (member.status === "active"
                              ? "border-brand/35 bg-brand/10 text-brand"
                              : member.status === "paused"
                                ? "border-destructive/30 bg-destructive/10 text-destructive"
                                : "border-border/60 bg-background/40 text-muted-foreground")
                          }
                        >
                          {member.status === "active"
                            ? "активен"
                            : member.status === "paused"
                              ? "пауза"
                              : "приглашен"}
                        </span>
                      </td>
                      <td className="px-3 py-4">
                        <div className="flex max-w-[250px] gap-2">
                          <input
                            value={resetPassword}
                            onChange={(event) =>
                              setResetPasswords((current) => ({
                                ...current,
                                [member.id]: event.target.value,
                              }))
                            }
                            className={FIELD_CLASS}
                            placeholder="новый пароль"
                            type="password"
                            autoComplete="new-password"
                            disabled={!canReset}
                          />
                          <button
                            type="button"
                            disabled={!canReset || pending || resetPassword.length < 6}
                            onClick={() =>
                              runAction(async () => {
                                const result = await resetTeamMemberPasswordAction({
                                  venueId,
                                  memberId: member.id,
                                  password: resetPassword,
                                });
                                if (result.ok) {
                                  setResetPasswords((current) => ({
                                    ...current,
                                    [member.id]: "",
                                  }));
                                }
                                return result;
                              })
                            }
                            className="inline-flex size-10 shrink-0 items-center justify-center rounded-lg border border-border/60 bg-background/60 text-foreground transition-colors hover:border-brand/40 disabled:opacity-40"
                            title="Сбросить пароль"
                          >
                            <KeyRound className="size-4 text-brand" />
                          </button>
                        </div>
                      </td>
                      <td className="px-3 py-4">
                        <button
                          type="button"
                          disabled={pending}
                          onClick={() =>
                            runAction(() =>
                              updateTeamMemberStatusAction({
                                venueId,
                                memberId: member.id,
                                status:
                                  member.status === "paused" ? "active" : "paused",
                              }),
                            )
                          }
                          className="inline-flex h-9 items-center gap-2 rounded-lg border border-border/60 bg-background/60 px-3 text-xs font-medium text-foreground transition-colors hover:border-brand/40 disabled:opacity-50"
                        >
                          {member.status === "paused" ? (
                            <>
                              <PlayCircle className="size-3.5 text-brand" />
                              Активировать
                            </>
                          ) : (
                            <>
                              <PauseCircle className="size-3.5 text-destructive" />
                              Пауза
                            </>
                          )}
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
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
