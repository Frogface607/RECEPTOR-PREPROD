"use client";

import { useMemo, useState, useTransition, type ReactNode } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  AlertTriangle,
  ArrowRight,
  BookOpenCheck,
  CheckCircle2,
  Copy,
  History,
  HelpCircle,
  KeyRound,
  Lightbulb,
  ListChecks,
  MessageSquareText,
  PauseCircle,
  PlayCircle,
  Plus,
  Save,
  Send,
  UserPlus,
  WandSparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { formatInteger, formatRubles } from "@/lib/format";
import type { LaborBiSummary } from "@/lib/team/labor-bi";
import {
  getLearningItem,
  getLearningItemByTitle,
  learningModuleHref,
} from "@/lib/team/team-learning";
import {
  buildTeamAuditJournal,
  type TeamAuditJournalCategoryId,
} from "@/lib/team/team-audit-journal";
import { buildIikoStaffImportCandidates } from "@/lib/team/team-iiko-staff-import";
import {
  TEAM_ROLES,
  listCommentsForTask,
  taskChecklistHintFromContext,
  taskContextBriefFromContext,
  taskContextWithoutLearningHint,
  taskLearningHintFromContext,
  type StaffMember,
  type TeamAuditEvent,
  type TeamRoleId,
  type TeamTask,
  type TeamTaskComment,
} from "@/lib/team/team-os";
import { buildTeamTaskQueue } from "@/lib/team/team-task-queue";
import {
  buildBulkLaborRateTargets,
  buildTeamLaborReadiness,
  hasLaborRate,
  type TeamLaborIikoBlocker,
  type TeamLaborReadinessStatus,
} from "@/lib/team/team-labor-readiness";
import {
  bulkUpdateTeamMemberLaborRatesAction,
  createTeamTaskAction,
  importIikoTeamMembersAction,
  inviteTeamMemberAction,
  resetTeamMemberPasswordAction,
  updateTeamMemberLaborRateAction,
  updateTeamMemberStatusAction,
  updateTeamTaskStatusAction,
  type TeamActionResult,
} from "./actions";

type Message = {
  tone: "success" | "error";
  text: string;
};
type RateDraft = {
  hourlyRate: string;
  shiftPay: string;
  revenueBonusPct: string;
};
type LaborSourceStatus = "live" | "demo" | "unavailable";

type LaborSource = {
  status: LaborSourceStatus;
  periodLabel: string;
  error: string | null;
};

const TASK_STATUSES: Array<{ value: TeamTask["status"]; label: string }> = [
  { value: "new", label: "новая" },
  { value: "accepted", label: "принята" },
  { value: "in_progress", label: "в работе" },
  { value: "done", label: "сделано" },
  { value: "verified", label: "проверено" },
];

const TASK_PRIORITIES: Array<{ value: TeamTask["priority"]; label: string }> = [
  { value: "high", label: "срочно" },
  { value: "medium", label: "обычно" },
  { value: "low", label: "низкий" },
];

const FIELD_CLASS =
  "w-full rounded-lg border border-border/55 bg-background/45 px-3 py-2 text-sm text-foreground outline-none transition focus:border-brand/50 focus:ring-2 focus:ring-brand/15";

function generateTemporaryPassword(): string {
  const alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789";
  const bytes = new Uint32Array(10);
  window.crypto.getRandomValues(bytes);
  const chars = Array.from(bytes, (value) => alphabet[value % alphabet.length]);
  return `Rcp-${chars.slice(0, 4).join("")}-${chars.slice(4, 8).join("")}-${chars.slice(8).join("")}`;
}

function formatHours(value: number): string {
  return `${value.toLocaleString("ru-RU", { maximumFractionDigits: 1 })} ч`;
}

function iikoBlockerActionLabel(blocker: TeamLaborIikoBlocker): string {
  return blocker.action === "add-member"
    ? "Создать карточку"
    : "Открыть ставку";
}

function iikoBlockerReasonLabel(blocker: TeamLaborIikoBlocker): string {
  return blocker.action === "add-member"
    ? "нет карточки Team OS"
    : "нет ставки";
}

function laborSourceCopy(source: LaborSource): {
  label: string;
  detail: string;
  className: string;
} {
  if (source.status === "live") {
    return {
      label: "реальные данные",
      detail: `Смены загружены за период: ${source.periodLabel}.`,
      className: "border-brand/30 bg-brand/10 text-brand",
    };
  }
  if (source.status === "demo") {
    return {
      label: "тестовые данные",
      detail: `Показываем пример смен за период: ${source.periodLabel}. После подключения iiko расчет перейдет на реальные смены.`,
      className: "border-border/60 bg-background/45 text-muted-foreground",
    };
  }
  return {
    label: "iiko недоступна",
    detail:
      source.error ??
      `Смены за период ${source.periodLabel} не загрузились. Показываем ставки Team OS.`,
    className: "border-amber-400/35 bg-amber-400/10 text-amber-200",
  };
}

function resultToMessage(result: TeamActionResult): Message {
  if (!result.ok) return { tone: "error", text: result.error };
  return { tone: "success", text: result.message };
}

function taskStatusLabel(status: TeamTask["status"]): string {
  return TASK_STATUSES.find((item) => item.value === status)?.label ?? status;
}

function taskPriorityLabel(priority: TeamTask["priority"]): string {
  return (
    TASK_PRIORITIES.find((item) => item.value === priority)?.label ?? priority
  );
}

function taskAudienceLabel(task: TeamTask, staff: StaffMember[]): string {
  const audience = task.audience;
  if (audience.type === "venue") return "всему заведению";
  if (audience.type === "role") {
    return (
      TEAM_ROLES.find((role) => role.id === audience.roleId)?.title ?? "роли"
    );
  }
  return (
    staff.find((member) => member.id === audience.memberId)?.name ??
    "сотруднику"
  );
}

function laborReadinessCopy(status: TeamLaborReadinessStatus): {
  title: string;
  detail: string;
  className: string;
} {
  if (status === "ready") {
    return {
      title: "ФОТ готов к расчету",
      detail:
        "У активной команды заведены ставки. Owner Dashboard может считать ФОТ точнее.",
      className: "border-brand/35 bg-brand/10 text-brand",
    };
  }
  if (status === "partial") {
    return {
      title: "ФОТ считается частично",
      detail:
        "Часть активной команды без ставки. Их смены будут занижать ФОТ в BI.",
      className: "border-amber-400/35 bg-amber-400/10 text-amber-200",
    };
  }
  return {
    title: "ФОТ заблокирован",
    detail:
      "Нет активных ставок. Смены видны, но стоимость команды пока не считается.",
    className: "border-destructive/35 bg-destructive/10 text-destructive",
  };
}

export function TeamActionsPanel({
  venueId,
  staff,
  tasks,
  comments = [],
  auditEvents,
  focusMemberId = "",
  focusTaskId = "",
  prefillMemberName = "",
  laborBi = null,
  laborSource,
}: {
  venueId: string;
  staff: StaffMember[];
  tasks: TeamTask[];
  comments?: TeamTaskComment[];
  auditEvents: TeamAuditEvent[];
  focusMemberId?: string;
  focusTaskId?: string;
  prefillMemberName?: string;
  laborBi?: LaborBiSummary | null;
  laborSource: LaborSource;
}) {
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const [message, setMessage] = useState<Message | null>(null);
  const taskQueue = useMemo(
    () => buildTeamTaskQueue(tasks, focusTaskId),
    [tasks, focusTaskId],
  );
  const focusedTask = taskQueue.focusedTask?.task;
  const latestTaskContext = useMemo(() => {
    return Object.fromEntries(
      taskQueue.openTasks.map(({ task }) => [
        task.id,
        listCommentsForTask(task.id, comments)[0] ?? null,
      ]),
    ) as Record<string, TeamTaskComment | null>;
  }, [comments, taskQueue.openTasks]);

  const [memberName, setMemberName] = useState(prefillMemberName);
  const [memberEmail, setMemberEmail] = useState("");
  const [memberLogin, setMemberLogin] = useState("");
  const [memberPassword, setMemberPassword] = useState("");
  const [memberRole, setMemberRole] = useState<TeamRoleId>("service");
  const [memberShift, setMemberShift] = useState("");
  const [memberHourlyRate, setMemberHourlyRate] = useState("");
  const [memberShiftPay, setMemberShiftPay] = useState("");
  const [memberRevenueBonusPct, setMemberRevenueBonusPct] = useState("");
  const [resetPasswords, setResetPasswords] = useState<Record<string, string>>(
    {},
  );
  const [rateDrafts, setRateDrafts] = useState<Record<string, RateDraft>>(() =>
    Object.fromEntries(staff.map((member) => [member.id, rateDraft(member)])),
  );
  const [bulkHourlyRate, setBulkHourlyRate] = useState("");
  const [bulkShiftPay, setBulkShiftPay] = useState("");
  const [bulkRevenueBonusPct, setBulkRevenueBonusPct] = useState("");
  const [copiedMemberId, setCopiedMemberId] = useState<string | null>(null);

  const [taskTitle, setTaskTitle] = useState("");
  const [taskPriority, setTaskPriority] =
    useState<TeamTask["priority"]>("medium");
  const [audienceType, setAudienceType] =
    useState<TeamTask["audience"]["type"]>("role");
  const [audienceRole, setAudienceRole] = useState<TeamRoleId>("service");
  const [audienceMemberId, setAudienceMemberId] = useState(staff[0]?.id ?? "");
  const [dueLabel, setDueLabel] = useState("сегодня");

  const [statusTaskId, setStatusTaskId] = useState(
    focusedTask?.id ?? tasks[0]?.id ?? "",
  );
  const [nextStatus, setNextStatus] =
    useState<TeamTask["status"]>("in_progress");
  const [journalFilter, setJournalFilter] =
    useState<TeamAuditJournalCategoryId>("all");

  const selectableStaff = useMemo(
    () => staff.filter((member) => member.status !== "paused"),
    [staff],
  );
  const laborReadiness = useMemo(
    () => buildTeamLaborReadiness(staff, laborBi),
    [staff, laborBi],
  );
  const bulkRateTargets = useMemo(
    () => buildBulkLaborRateTargets(staff),
    [staff],
  );
  const iikoImportCandidates = useMemo(
    () => buildIikoStaffImportCandidates(laborReadiness.iikoBlockers),
    [laborReadiness.iikoBlockers],
  );
  const journal = useMemo(
    () => buildTeamAuditJournal(auditEvents),
    [auditEvents],
  );
  const visibleJournalEntries = useMemo(
    () =>
      journalFilter === "all"
        ? journal.entries
        : journal.entries.filter((entry) => entry.categoryId === journalFilter),
    [journal.entries, journalFilter],
  );
  const hasBulkRateValue = Boolean(
    bulkHourlyRate.trim() || bulkShiftPay.trim() || bulkRevenueBonusPct.trim(),
  );
  const laborCopy = laborReadinessCopy(laborReadiness.status);
  const sourceCopy = laborSourceCopy(laborSource);
  const iikoBlockers = laborReadiness.iikoBlockers.slice(0, 4);
  const focusedMember = focusMemberId
    ? staff.find((member) => member.id === focusMemberId)
    : undefined;
  const missingRateNames = laborReadiness.missingStaff
    .slice(0, 4)
    .map((member) => member.name)
    .join(", ");
  const laborCoverageLabel =
    laborReadiness.source === "iiko" ? "точность ФОТ" : "ставок";
  const laborCoverageDetail =
    laborReadiness.source === "iiko"
      ? laborReadiness.iikoUnpricedStaffShifts > 0
        ? `${formatInteger(laborReadiness.iikoUnpricedStaffShifts)} записей · ${formatRubles(laborReadiness.iikoUnpricedRevenue)} под вопросом`
        : "вся сменная выручка покрыта"
      : missingRateNames
        ? missingRateNames
        : "ставки заведены";

  function runAction(action: () => Promise<TeamActionResult>) {
    setMessage(null);
    startTransition(async () => {
      const result = await action();
      setMessage(resultToMessage(result));
      if (result.ok) router.refresh();
    });
  }

  function updateTaskStatus(taskId: string, status: TeamTask["status"]): void {
    setStatusTaskId(taskId);
    setNextStatus(status);
    runAction(() =>
      updateTeamTaskStatusAction({
        venueId,
        taskId,
        status,
      }),
    );
  }

  async function copyLogin(member: StaffMember) {
    if (!member.email) return;
    await navigator.clipboard.writeText(member.email);
    setCopiedMemberId(member.id);
    window.setTimeout(() => setCopiedMemberId(null), 1600);
  }

  function updateRateDraft(
    memberId: string,
    field: keyof RateDraft,
    value: string,
  ) {
    setRateDrafts((current) => ({
      ...current,
      [memberId]: {
        ...(current[memberId] ?? {
          hourlyRate: "",
          shiftPay: "",
          revenueBonusPct: "",
        }),
        [field]: value,
      },
    }));
  }

  function prefillMemberFromIiko(blocker: TeamLaborIikoBlocker) {
    setMemberName(blocker.name);
    if (blocker.roleId) setMemberRole(blocker.roleId);
    setMemberShift(
      `${formatInteger(blocker.shifts)} смен · ${formatHours(blocker.hours)}`,
    );
    document
      .getElementById("add-team-member")
      ?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function importIikoMembersFromShifts() {
    if (iikoImportCandidates.length === 0) return;
    runAction(() =>
      importIikoTeamMembersAction({
        venueId,
        members: iikoImportCandidates.map((candidate) => ({
          fullName: candidate.name,
          role: candidate.roleId,
          shiftLabel: candidate.shiftLabel,
        })),
      }),
    );
  }

  function applyBulkLaborRate() {
    if (bulkRateTargets.length === 0) return;
    runAction(async () => {
      const result = await bulkUpdateTeamMemberLaborRatesAction({
        venueId,
        memberIds: bulkRateTargets.map((target) => target.id),
        hourlyRate: bulkHourlyRate,
        shiftPay: bulkShiftPay,
        revenueBonusPct: bulkRevenueBonusPct,
      });

      if (result.ok) {
        setBulkHourlyRate("");
        setBulkShiftPay("");
        setBulkRevenueBonusPct("");
      }

      return result;
    });
  }

  return (
    <section
      id="team-actions"
      className="scroll-mt-24 border-b border-border/40"
    >
      <div className="mx-auto max-w-7xl px-6 py-8">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-[11px] uppercase tracking-[0.18em] text-brand">
              Операции
            </p>
            <h2 className="mt-2 text-2xl font-medium">Доступы и задачи</h2>
            <div className="mt-3 flex flex-wrap items-center gap-2">
              <span className="rounded-full border border-border/55 bg-background/45 px-3 py-1 text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
                период: {laborSource.periodLabel}
              </span>
              <span
                className={
                  "rounded-full border px-3 py-1 text-[11px] uppercase tracking-[0.14em] " +
                  sourceCopy.className
                }
              >
                {sourceCopy.label}
              </span>
            </div>
          </div>
          <p className="max-w-md text-sm text-muted-foreground">
            Быстрые действия управляющего в том же периоде, который открыт в BI.
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

        <div className="mt-6 grid gap-4 xl:grid-cols-3">
          <form
            id="add-team-member"
            className={
              "rounded-lg border bg-card/50 p-5 " +
              (prefillMemberName
                ? "border-brand/45 ring-1 ring-brand/25"
                : "border-border/60")
            }
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
                  hourlyRate: memberHourlyRate,
                  shiftPay: memberShiftPay,
                  revenueBonusPct: memberRevenueBonusPct,
                });
                if (result.ok) {
                  setMemberName("");
                  setMemberEmail("");
                  setMemberLogin("");
                  setMemberPassword("");
                  setMemberShift("");
                  setMemberHourlyRate("");
                  setMemberShiftPay("");
                  setMemberRevenueBonusPct("");
                }
                return result;
              });
            }}
          >
            <div className="flex items-center gap-3">
              <UserPlus className="size-5 text-brand" />
              <h3 className="text-lg font-medium">Добавить сотрудника</h3>
            </div>
            {prefillMemberName ? (
              <p className="mt-3 rounded-lg border border-brand/25 bg-brand/10 px-3 py-2 text-[12px] leading-relaxed text-brand">
                Из BI: добавьте «{prefillMemberName}», чтобы смены считались с
                точным ФОТ.
              </p>
            ) : null}
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
                  <div className="flex gap-2">
                    <input
                      value={memberPassword}
                      onChange={(event) =>
                        setMemberPassword(event.target.value)
                      }
                      className={FIELD_CLASS}
                      placeholder="временный пароль"
                      autoComplete="new-password"
                    />
                    <button
                      type="button"
                      onClick={() =>
                        setMemberPassword(generateTemporaryPassword())
                      }
                      className="inline-flex size-10 shrink-0 items-center justify-center rounded-lg border border-border/60 bg-background/60 text-foreground transition-colors hover:border-brand/40"
                      title="Сгенерировать пароль"
                    >
                      <WandSparkles className="size-4 text-brand" />
                    </button>
                  </div>
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
              <div className="grid gap-3 sm:grid-cols-3">
                <FieldLabel label="₽ / час">
                  <input
                    value={memberHourlyRate}
                    onChange={(event) =>
                      setMemberHourlyRate(event.target.value)
                    }
                    className={FIELD_CLASS}
                    inputMode="decimal"
                    placeholder="350"
                  />
                </FieldLabel>
                <FieldLabel label="₽ / смена">
                  <input
                    value={memberShiftPay}
                    onChange={(event) => setMemberShiftPay(event.target.value)}
                    className={FIELD_CLASS}
                    inputMode="decimal"
                    placeholder="4000"
                  />
                </FieldLabel>
                <FieldLabel label="% продаж">
                  <input
                    value={memberRevenueBonusPct}
                    onChange={(event) =>
                      setMemberRevenueBonusPct(event.target.value)
                    }
                    className={FIELD_CLASS}
                    inputMode="decimal"
                    placeholder="1"
                  />
                </FieldLabel>
              </div>
            </div>
            <p className="mt-3 text-[12px] leading-relaxed text-muted-foreground">
              Формат входа: login@staff.receptorai.pro.
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
                      setTaskPriority(
                        event.target.value as TeamTask["priority"],
                      )
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
                    onChange={(event) =>
                      setAudienceMemberId(event.target.value)
                    }
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
            className={
              "rounded-lg border bg-card/50 p-5 " +
              (focusedTask
                ? "border-brand/45 ring-1 ring-brand/25"
                : "border-border/60")
            }
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
            {focusedTask ? (
              <p className="mt-3 rounded-lg border border-brand/25 bg-brand/10 px-3 py-2 text-[12px] leading-relaxed text-brand">
                Открыта задача из экрана владельца: «{focusedTask.title}».
              </p>
            ) : null}

            <div className="mt-4 grid grid-cols-3 gap-2">
              <TeamMetric
                label="Открыто"
                value={`${taskQueue.openCount}`}
                detail="в работе"
              />
              <TeamMetric
                label="Сейчас"
                value={`${taskQueue.inProgressCount}`}
                detail="исполняется"
              />
              <TeamMetric
                label="Срочно"
                value={`${taskQueue.urgentOpenCount}`}
                detail="в очереди"
              />
            </div>

            {taskQueue.openContours.length > 0 ? (
              <div className="mt-3 flex flex-wrap gap-2">
                {taskQueue.openContours.slice(0, 4).map((contour) => (
                  <span
                    key={contour.label}
                    className="rounded-md border border-border/45 bg-background/35 px-2 py-1 text-[10px] uppercase tracking-[0.12em] text-muted-foreground"
                  >
                    {contour.label}: {contour.count}
                  </span>
                ))}
              </div>
            ) : null}

            <div className="mt-4 space-y-2">
              {taskQueue.openTasks.length > 0 ? (
                taskQueue.openTasks.slice(0, 6).map(({ task, focused }) => {
                  const context = latestTaskContext[task.id];
                  const contextLearningHint = taskLearningHintFromContext(
                    context?.body,
                  );
                  const contextChecklistHint = taskChecklistHintFromContext(
                    context?.body,
                  );
                  const checklistHint =
                    task.learningChecklistTitle ?? contextChecklistHint;
                  const learningItem =
                    (task.learningModuleId
                      ? getLearningItem(task.learningModuleId)
                      : undefined) ??
                    getLearningItemByTitle(
                      task.learningModuleTitle ?? contextLearningHint,
                    );
                  const learningHint =
                    task.learningModuleTitle ??
                    learningItem?.title ??
                    contextLearningHint;
                  const contextBody = taskContextWithoutLearningHint(
                    context?.body,
                  );
                  const contextBrief = taskContextBriefFromContext(
                    context?.body,
                  );
                  const hasContextBrief = Boolean(
                    contextBrief.fieldFact ||
                    contextBrief.question ||
                    contextBrief.check ||
                    contextBrief.reason,
                  );

                  return (
                    <div
                      key={task.id}
                      className={
                        "rounded-lg border p-3 " +
                        (focused
                          ? "border-brand/45 bg-brand/10"
                          : "border-border/45 bg-background/35")
                      }
                    >
                      <button
                        type="button"
                        onClick={() => setStatusTaskId(task.id)}
                        className="block w-full text-left"
                      >
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="rounded-md border border-border/55 bg-card/60 px-2 py-1 text-[10px] uppercase tracking-[0.12em] text-muted-foreground">
                            {taskPriorityLabel(task.priority)}
                          </span>
                          <span className="rounded-md border border-brand/25 bg-brand/10 px-2 py-1 text-[10px] uppercase tracking-[0.12em] text-brand">
                            {taskStatusLabel(task.status)}
                          </span>
                          {task.sourceLabel ? (
                            <span className="rounded-md border border-border/55 bg-background/50 px-2 py-1 text-[10px] uppercase tracking-[0.12em] text-muted-foreground">
                              {task.sourceLabel}
                            </span>
                          ) : null}
                          {task.impactLabel ? (
                            <span className="rounded-md border border-amber-500/30 bg-amber-500/10 px-2 py-1 text-[10px] uppercase tracking-[0.12em] text-amber-200">
                              {task.impactLabel}
                            </span>
                          ) : null}
                          {learningHint ? (
                            <span className="inline-flex items-center gap-1 rounded-md border border-sky-400/25 bg-sky-400/10 px-2 py-1 text-[10px] uppercase tracking-[0.12em] text-sky-200">
                              <BookOpenCheck className="size-3" />
                              стандарт
                            </span>
                          ) : null}
                        </div>
                        <p className="mt-2 text-sm font-medium leading-relaxed text-foreground">
                          {task.title}
                        </p>
                        <p className="mt-1 text-[11px] text-muted-foreground">
                          {taskAudienceLabel(task, staff)} · {task.dueLabel}
                        </p>
                        {hasContextBrief ? (
                          <div className="mt-2 space-y-1 rounded-md border border-border/40 bg-card/35 px-3 py-2 text-[12px] leading-relaxed">
                            {contextBrief.fieldFact ? (
                              <p className="flex items-start gap-2 text-foreground/80">
                                <MessageSquareText className="mt-0.5 size-3.5 shrink-0 text-brand" />
                                <span>{contextBrief.fieldFact}</span>
                              </p>
                            ) : null}
                            {contextBrief.question ? (
                              <p className="flex items-start gap-2 text-foreground/80">
                                <HelpCircle className="mt-0.5 size-3.5 shrink-0 text-brand" />
                                <span>{contextBrief.question}</span>
                              </p>
                            ) : null}
                            {contextBrief.check ? (
                              <p className="flex items-start gap-2 text-muted-foreground">
                                <ListChecks className="mt-0.5 size-3.5 shrink-0 text-brand" />
                                <span>{contextBrief.check}</span>
                              </p>
                            ) : null}
                            {contextBrief.reason ? (
                              <p className="flex items-start gap-2 text-amber-100/85">
                                <Lightbulb className="mt-0.5 size-3.5 shrink-0 text-amber-200" />
                                <span>{contextBrief.reason}</span>
                              </p>
                            ) : null}
                          </div>
                        ) : context && contextBody ? (
                          <p className="mt-2 line-clamp-2 rounded-md border border-border/40 bg-card/35 px-3 py-2 text-[12px] leading-relaxed text-muted-foreground">
                            <span className="font-medium text-foreground/80">
                              {context.authorName}:
                            </span>{" "}
                            {contextBody}
                          </p>
                        ) : null}
                        {learningHint ? (
                          <div className="mt-2 flex items-start gap-2 rounded-md border border-sky-400/20 bg-sky-400/5 px-3 py-2 text-[12px] leading-relaxed text-sky-100/90">
                            <BookOpenCheck className="mt-0.5 size-3.5 shrink-0 text-sky-200" />
                            <div className="min-w-0">
                              <p>Стандарт задачи: {learningHint}</p>
                              {checklistHint ? (
                                <p className="mt-1 text-sky-100">
                                  Чеклист: {checklistHint}
                                </p>
                              ) : null}
                            </div>
                          </div>
                        ) : null}
                      </button>
                      <div className="mt-3 flex flex-wrap gap-2">
                        {learningItem ? (
                          <Link
                            href={learningModuleHref(
                              learningItem.id,
                              checklistHint,
                            )}
                            className="inline-flex h-8 items-center justify-center gap-1.5 rounded-lg border border-sky-400/25 bg-sky-400/10 px-3 text-xs font-medium text-sky-100 transition-colors hover:bg-sky-400/15"
                          >
                            <BookOpenCheck className="size-3.5" />
                            {checklistHint
                              ? "Открыть чеклист"
                              : "Открыть стандарт"}
                          </Link>
                        ) : null}
                        {task.status !== "in_progress" ? (
                          <button
                            type="button"
                            disabled={pending}
                            onClick={() =>
                              updateTaskStatus(task.id, "in_progress")
                            }
                            className="inline-flex h-8 items-center justify-center rounded-lg border border-border/60 bg-background/50 px-3 text-xs font-medium text-foreground transition-colors hover:border-brand/35 hover:text-brand disabled:opacity-45"
                          >
                            В работу
                          </button>
                        ) : null}
                        <button
                          type="button"
                          disabled={pending}
                          onClick={() => updateTaskStatus(task.id, "done")}
                          className="inline-flex h-8 items-center justify-center rounded-lg border border-brand/35 bg-brand/10 px-3 text-xs font-medium text-brand transition-colors hover:bg-brand/15 disabled:opacity-45"
                        >
                          Сделано
                        </button>
                      </div>
                    </div>
                  );
                })
              ) : (
                <p className="rounded-lg border border-border/45 bg-background/35 p-3 text-sm leading-relaxed text-muted-foreground">
                  Открытых задач нет. Новые задачи из Owner Dashboard появятся
                  здесь, чтобы управляющий сразу вел их до результата.
                </p>
              )}
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

        <div
          id="labor-rates"
          className="mt-6 scroll-mt-24 rounded-lg border border-border/60 bg-card/50 p-5"
        >
          <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="text-[11px] uppercase tracking-[0.22em] text-brand">
                Доступы
              </p>
              <h3 className="mt-2 text-xl font-medium">Команда</h3>
            </div>
            <p className="max-w-md text-xs leading-relaxed text-muted-foreground">
              Логины, роли, статусы, пароли и ставки для ФОТ.
            </p>
          </div>
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <span
              className={
                "inline-flex items-center rounded-full border px-3 py-1 text-[10px] uppercase tracking-[0.14em] " +
                sourceCopy.className
              }
            >
              {sourceCopy.label}
            </span>
            <p className="text-xs leading-relaxed text-muted-foreground">
              {sourceCopy.detail}
            </p>
          </div>
          {focusedMember ? (
            <p className="mt-3 rounded-lg border border-brand/25 bg-brand/10 px-3 py-2 text-[12px] leading-relaxed text-brand">
              Фокус из BI: заполните ставку для «{focusedMember.name}».
            </p>
          ) : null}

          <div className="mt-5 border-y border-border/45 py-4">
            <div className="grid gap-4 lg:grid-cols-[0.85fr_1.15fr] lg:items-center">
              <div>
                <span
                  className={
                    "inline-flex items-center gap-2 rounded-full border px-3 py-1 text-[11px] uppercase tracking-[0.14em] " +
                    laborCopy.className
                  }
                >
                  {laborReadiness.status === "ready" ? (
                    <CheckCircle2 className="size-3.5" />
                  ) : (
                    <AlertTriangle className="size-3.5" />
                  )}
                  {laborReadiness.coveragePct}% {laborCoverageLabel}
                </span>
                <h4 className="mt-3 text-base font-medium text-foreground">
                  {laborCopy.title}
                </h4>
                <p className="mt-1 max-w-xl text-xs leading-relaxed text-muted-foreground">
                  {laborCopy.detail}
                </p>
              </div>

              <div className="grid gap-3 sm:grid-cols-3">
                <TeamMetric
                  label="Активная команда"
                  value={`${laborReadiness.activeStaff}`}
                  detail={`всего: ${laborReadiness.totalStaff}`}
                />
                <TeamMetric
                  label="Со ставкой"
                  value={`${laborReadiness.readyStaff}`}
                  detail="участвуют в ФОТ"
                />
                <TeamMetric
                  label={
                    laborReadiness.source === "iiko"
                      ? "В iiko без ФОТ"
                      : "Без ставки"
                  }
                  value={`${
                    laborReadiness.source === "iiko"
                      ? laborReadiness.iikoUnpricedStaffShifts
                      : laborReadiness.missingStaff.length
                  }`}
                  detail={laborCoverageDetail}
                />
              </div>
            </div>
          </div>

          {bulkRateTargets.length > 0 ? (
            <div className="mt-5 rounded-lg border border-amber-400/25 bg-amber-400/10 p-4">
              <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
                <div className="min-w-0">
                  <p className="text-[10px] uppercase tracking-[0.18em] text-amber-200">
                    быстро закрыть ФОТ
                  </p>
                  <h4 className="mt-1 text-base font-medium text-foreground">
                    Применить ставку к {bulkRateTargets.length} без ФОТ
                  </h4>
                  <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
                    Только сотрудники без ставки. Заполненные ставки не
                    перезаписываем.
                  </p>
                </div>
                <div className="grid w-full gap-2 sm:grid-cols-[1fr_1fr_0.8fr_auto] lg:max-w-2xl">
                  <input
                    value={bulkHourlyRate}
                    onChange={(event) => setBulkHourlyRate(event.target.value)}
                    className={`${FIELD_CLASS} px-2 py-1.5 text-xs`}
                    inputMode="decimal"
                    placeholder="руб/час"
                    aria-label="Массовая почасовая ставка"
                  />
                  <input
                    value={bulkShiftPay}
                    onChange={(event) => setBulkShiftPay(event.target.value)}
                    className={`${FIELD_CLASS} px-2 py-1.5 text-xs`}
                    inputMode="decimal"
                    placeholder="руб/смена"
                    aria-label="Массовый фикс за смену"
                  />
                  <input
                    value={bulkRevenueBonusPct}
                    onChange={(event) =>
                      setBulkRevenueBonusPct(event.target.value)
                    }
                    className={`${FIELD_CLASS} px-2 py-1.5 text-xs`}
                    inputMode="decimal"
                    placeholder="% продаж"
                    aria-label="Массовый процент от продаж"
                  />
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={applyBulkLaborRate}
                    disabled={pending || !hasBulkRateValue}
                  >
                    Применить
                  </Button>
                </div>
              </div>
              <p className="mt-2 truncate text-[11px] text-muted-foreground">
                В очереди:{" "}
                {bulkRateTargets
                  .slice(0, 4)
                  .map((target) => target.name)
                  .join(", ")}
                {bulkRateTargets.length > 4
                  ? ` и еще ${bulkRateTargets.length - 4}`
                  : ""}
              </p>
            </div>
          ) : null}

          {iikoBlockers.length > 0 ? (
            <div className="mt-5 rounded-lg border border-brand/25 bg-background/30 p-4">
              <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
                <div>
                  <p className="text-[10px] uppercase tracking-[0.18em] text-brand">
                    Из смен iiko
                  </p>
                  <h4 className="mt-1 text-base font-medium text-foreground">
                    Закрыть реальных сотрудников в ФОТ
                  </h4>
                </div>
                <p className="max-w-md text-xs leading-relaxed text-muted-foreground">
                  Очередь собрана из смен выбранного периода: сначала те, кто
                  сильнее всего искажает стоимость команды.
                </p>
                {iikoImportCandidates.length > 0 ? (
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={importIikoMembersFromShifts}
                    disabled={pending}
                    className="self-start sm:self-auto"
                  >
                    <UserPlus className="size-3.5" />
                    Импортировать {iikoImportCandidates.length}
                  </Button>
                ) : null}
              </div>

              <div className="mt-3 grid gap-2 lg:grid-cols-2">
                {iikoBlockers.map((blocker) => (
                  <div
                    key={`${blocker.name}-${blocker.reason}`}
                    className="rounded-lg border border-border/45 bg-card/45 p-3"
                  >
                    <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                      <div className="min-w-0">
                        <p className="truncate text-sm font-medium text-foreground">
                          {blocker.name}
                        </p>
                        <p className="mt-1 text-[11px] text-muted-foreground">
                          {formatInteger(blocker.shifts)} смен ·{" "}
                          {formatHours(blocker.hours)}
                        </p>
                      </div>
                      <span className="shrink-0 rounded-md border border-amber-400/35 bg-amber-400/10 px-2 py-1 text-[10px] uppercase tracking-[0.12em] text-amber-200">
                        {iikoBlockerReasonLabel(blocker)}
                      </span>
                    </div>

                    <div className="mt-3 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
                      <div>
                        <p className="numeric text-lg font-medium text-foreground">
                          {formatRubles(blocker.sales)}
                        </p>
                        <p className="mt-1 text-[11px] text-muted-foreground">
                          выручки без точного ФОТ
                        </p>
                      </div>

                      {blocker.action === "add-member" ? (
                        <button
                          type="button"
                          onClick={() => prefillMemberFromIiko(blocker)}
                          className="inline-flex items-center justify-center rounded-lg border border-brand/35 bg-brand/10 px-3 py-2 text-xs font-medium text-brand transition-colors hover:bg-brand/15"
                        >
                          {iikoBlockerActionLabel(blocker)}
                        </button>
                      ) : blocker.memberId ? (
                        <a
                          href={`#labor-member-${encodeURIComponent(blocker.memberId)}`}
                          className="inline-flex items-center justify-center rounded-lg border border-brand/35 bg-brand/10 px-3 py-2 text-xs font-medium text-brand transition-colors hover:bg-brand/15"
                        >
                          {iikoBlockerActionLabel(blocker)}
                        </a>
                      ) : null}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : null}

          <div className="mt-5 overflow-x-auto">
            <table className="w-full min-w-[1080px] text-left text-sm">
              <thead>
                <tr className="border-b border-border/50 text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
                  <th className="px-3 py-3 font-normal">Сотрудник</th>
                  <th className="px-3 py-3 font-normal">Роль</th>
                  <th className="px-3 py-3 font-normal">ФОТ</th>
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
                  const draft = rateDrafts[member.id] ?? rateDraft(member);
                  const canReset = Boolean(member.userId);
                  const memberHasLaborRate = hasLaborRate(member);
                  const isFocused = focusMemberId === member.id;
                  return (
                    <tr
                      id={`labor-member-${member.id}`}
                      key={member.id}
                      className={
                        "operational-target scroll-mt-24 align-top " +
                        (isFocused ? "bg-brand/10" : "")
                      }
                    >
                      <td className="px-3 py-4">
                        <p className="font-medium text-foreground">
                          {member.name}
                        </p>
                        <p className="mt-1 text-xs text-muted-foreground">
                          {member.shiftLabel || "смена не указана"}
                        </p>
                        {isFocused ? (
                          <p className="mt-2 text-[11px] text-brand">
                            Фокус из BI: заполнить ставку
                          </p>
                        ) : null}
                        <p
                          className={
                            "mt-2 text-[11px] " +
                            (memberHasLaborRate
                              ? "text-brand"
                              : "text-amber-200")
                          }
                        >
                          {memberHasLaborRate
                            ? "ставка заведена"
                            : "ставка не заведена"}
                        </p>
                      </td>
                      <td className="px-3 py-4 text-muted-foreground">
                        {role?.title ?? member.roleId}
                      </td>
                      <td className="px-3 py-4">
                        <div className="grid min-w-[280px] gap-2 sm:grid-cols-[1fr_1fr_0.85fr_auto]">
                          <input
                            value={draft.hourlyRate}
                            onChange={(event) =>
                              updateRateDraft(
                                member.id,
                                "hourlyRate",
                                event.target.value,
                              )
                            }
                            className={`${FIELD_CLASS} px-2 py-1.5 text-xs`}
                            inputMode="decimal"
                            placeholder="₽/час"
                            aria-label="Почасовая ставка"
                          />
                          <input
                            value={draft.shiftPay}
                            onChange={(event) =>
                              updateRateDraft(
                                member.id,
                                "shiftPay",
                                event.target.value,
                              )
                            }
                            className={`${FIELD_CLASS} px-2 py-1.5 text-xs`}
                            inputMode="decimal"
                            placeholder="₽/смена"
                            aria-label="Фикс за смену"
                          />
                          <input
                            value={draft.revenueBonusPct}
                            onChange={(event) =>
                              updateRateDraft(
                                member.id,
                                "revenueBonusPct",
                                event.target.value,
                              )
                            }
                            className={`${FIELD_CLASS} px-2 py-1.5 text-xs`}
                            inputMode="decimal"
                            placeholder="%"
                            aria-label="Процент от продаж"
                          />
                          <button
                            type="button"
                            disabled={pending}
                            onClick={() =>
                              runAction(() =>
                                updateTeamMemberLaborRateAction({
                                  venueId,
                                  memberId: member.id,
                                  hourlyRate: draft.hourlyRate,
                                  shiftPay: draft.shiftPay,
                                  revenueBonusPct: draft.revenueBonusPct,
                                }),
                              )
                            }
                            className="inline-flex size-9 shrink-0 items-center justify-center rounded-lg border border-border/60 bg-background/60 text-foreground transition-colors hover:border-brand/40 disabled:opacity-50"
                            title="Сохранить ставки"
                          >
                            <Save className="size-4 text-brand" />
                          </button>
                        </div>
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
                        <div className="flex max-w-[300px] gap-2">
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
                            autoComplete="new-password"
                            disabled={!canReset}
                          />
                          <button
                            type="button"
                            disabled={!canReset}
                            onClick={() =>
                              setResetPasswords((current) => ({
                                ...current,
                                [member.id]: generateTemporaryPassword(),
                              }))
                            }
                            className="inline-flex size-10 shrink-0 items-center justify-center rounded-lg border border-border/60 bg-background/60 text-foreground transition-colors hover:border-brand/40 disabled:opacity-40"
                            title="Сгенерировать пароль"
                          >
                            <WandSparkles className="size-4 text-brand" />
                          </button>
                          <button
                            type="button"
                            disabled={
                              !canReset || pending || resetPassword.length < 6
                            }
                            onClick={() =>
                              runAction(async () => {
                                const result =
                                  await resetTeamMemberPasswordAction({
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
                                  member.status === "paused"
                                    ? "active"
                                    : "paused",
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

        <div
          id="team-journal"
          className="mt-6 scroll-mt-24 rounded-lg border border-border/60 bg-card/50 p-5"
        >
          <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="text-[11px] uppercase tracking-[0.22em] text-brand">
                Журнал
              </p>
              <h3 className="mt-2 text-xl font-medium">Последние действия</h3>
              <p className="mt-2 max-w-xl text-sm leading-relaxed text-muted-foreground">
                Фильтруйте события по контуру, чтобы быстро понять, что
                изменилось в ФОТ, обучении, плане смен и задачах.
              </p>
            </div>
            <History className="size-5 text-brand" />
          </div>

          <div className="mt-5 flex flex-wrap gap-2">
            {journal.categories.map((category) => {
              const active = journalFilter === category.id;
              return (
                <button
                  key={category.id}
                  type="button"
                  onClick={() => setJournalFilter(category.id)}
                  className={
                    "inline-flex h-8 items-center gap-2 rounded-lg border px-3 text-xs font-medium transition-colors " +
                    (active
                      ? "border-brand/45 bg-brand/10 text-brand"
                      : "border-border/55 bg-background/35 text-muted-foreground hover:border-brand/30 hover:text-foreground")
                  }
                  aria-pressed={active}
                  title={category.description}
                >
                  <span>{category.label}</span>
                  <span className="numeric rounded-md bg-card/70 px-1.5 py-0.5 text-[10px]">
                    {formatInteger(category.count)}
                  </span>
                </button>
              );
            })}
          </div>

          <div className="mt-5 grid gap-3">
            {visibleJournalEntries.length > 0 ? (
              visibleJournalEntries.map((event) => (
                <Link
                  key={event.id}
                  href={event.contextHref}
                  className="grid gap-3 rounded-lg border border-border/45 bg-background/35 p-3 transition-colors hover:border-brand/35 hover:bg-background/55 sm:grid-cols-[auto_1fr_auto_auto] sm:items-center"
                >
                  <div className="flex flex-wrap gap-2">
                    <span className="rounded-md border border-brand/25 bg-brand/10 px-2 py-1 text-[11px] uppercase tracking-[0.14em] text-brand">
                      {event.categoryLabel}
                    </span>
                    <span className="rounded-md border border-border/60 bg-card/60 px-2 py-1 text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
                      {event.typeLabel}
                    </span>
                    {event.impactLabel ? (
                      <span className="rounded-md border border-amber-500/30 bg-amber-500/10 px-2 py-1 text-[11px] uppercase tracking-[0.14em] text-amber-200">
                        {event.impactLabel}
                      </span>
                    ) : null}
                  </div>
                  <p className="text-sm leading-relaxed text-foreground/90">
                    {event.summary}
                  </p>
                  <span className="text-xs text-muted-foreground">
                    {event.createdAtLabel || "только что"}
                  </span>
                  <span className="inline-flex items-center gap-1 text-xs font-medium text-brand">
                    {event.contextLabel}
                    <ArrowRight className="size-3.5" />
                  </span>
                </Link>
              ))
            ) : (
              <p className="rounded-lg border border-border/45 bg-background/35 p-4 text-sm text-muted-foreground">
                {auditEvents.length > 0
                  ? "В этом фильтре пока нет событий."
                  : "Журнал появится после первого изменения доступа, задачи или объявления."}
              </p>
            )}
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

function TeamMetric({
  label,
  value,
  detail,
}: {
  label: string;
  value: string;
  detail: string;
}) {
  return (
    <div>
      <p className="text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
        {label}
      </p>
      <p className="mt-1 font-mono text-2xl text-foreground">{value}</p>
      <p className="mt-1 truncate text-xs text-muted-foreground">{detail}</p>
    </div>
  );
}

function rateDraft(member: StaffMember): RateDraft {
  return {
    hourlyRate: member.hourlyRate ? String(member.hourlyRate) : "",
    shiftPay: member.shiftPay ? String(member.shiftPay) : "",
    revenueBonusPct: member.revenueBonusPct
      ? String(member.revenueBonusPct)
      : "",
  };
}
