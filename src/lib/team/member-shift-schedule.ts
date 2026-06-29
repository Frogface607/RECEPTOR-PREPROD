import type {
  LaborBiSummary,
  LaborShiftInput,
  LaborShiftWorker,
} from "./labor-bi";
import type { TeamLearningMemberSummary } from "./team-learning-progress";
import type {
  StaffMember,
  TeamAnnouncement,
  TeamAnnouncementRead,
  TeamTask,
} from "./team-os";

export type MemberShiftScheduleItem = {
  shiftId: string;
  dateKey: string;
  dayLabel: string;
  timeLabel: string;
  revenue: number;
  items: number;
  hours: number;
};

export type MemberLaborProfileStatus = "ready" | "missing_rate" | "no_shifts";

export type MemberLaborProfile = {
  status: MemberLaborProfileStatus;
  shifts: number;
  hours: number;
  sales: number;
  laborCost: number;
  revenuePerHour: number | null;
  laborCostPct: number | null;
  missingRate: boolean;
};

export type MemberOperationPlanTone = "risk" | "setup" | "work" | "ready";

export type MemberOperationPlanItem = {
  id: string;
  title: string;
  detail: string;
  href: string;
  tone: MemberOperationPlanTone;
  badge: string;
  taskId?: string;
  announcementId?: string;
};

export function buildMemberShiftSchedule(input: {
  member: StaffMember;
  shifts: LaborShiftInput[];
}): MemberShiftScheduleItem[] {
  return input.shifts
    .map((shift) => {
      const worker = matchShiftWorker(shift, input.member);
      if (!worker) return null;

      const workerCount = Math.max(shift.workers?.length ?? 1, 1);
      return {
        shiftId: shift.shiftId,
        dateKey: shift.openTime.slice(0, 10),
        dayLabel: formatScheduleDay(shift.openTime),
        timeLabel: formatShiftTime(
          worker.startedAt ?? shift.openTime,
          worker.endedAt ?? shift.closeTime,
        ),
        revenue: Math.round(worker.sales ?? shift.revenue / workerCount),
        items: shift.items,
        hours: roundHours(resolveWorkerHours(worker, shift)),
      } satisfies MemberShiftScheduleItem;
    })
    .filter((item): item is MemberShiftScheduleItem => item !== null)
    .sort((a, b) => a.dateKey.localeCompare(b.dateKey));
}

export function buildMemberLaborProfile(input: {
  member: StaffMember;
  labor: LaborBiSummary | null;
}): MemberLaborProfile {
  const employee = input.labor?.employees.find(
    (item) =>
      item.memberId === input.member.id ||
      normalizeName(item.name) === normalizeName(input.member.name),
  );

  if (!employee) {
    return {
      status: "no_shifts",
      shifts: 0,
      hours: 0,
      sales: 0,
      laborCost: 0,
      revenuePerHour: null,
      laborCostPct: null,
      missingRate: false,
    };
  }

  return {
    status: employee.missingRate ? "missing_rate" : "ready",
    shifts: employee.shifts,
    hours: employee.hours,
    sales: employee.sales,
    laborCost: employee.laborCost,
    revenuePerHour: employee.revenuePerHour,
    laborCostPct: employee.laborCostPct,
    missingRate: employee.missingRate,
  };
}

export function buildMemberOperationPlan(input: {
  member: StaffMember;
  tasks: TeamTask[];
  schedule: MemberShiftScheduleItem[];
  laborProfile: MemberLaborProfile | null;
  learning: TeamLearningMemberSummary | null;
  announcements?: TeamAnnouncement[];
  announcementReads?: TeamAnnouncementRead[];
  nextLearning?: { title: string; timeLabel: string } | null;
}): MemberOperationPlanItem[] {
  const items: MemberOperationPlanItem[] = [];

  if (input.laborProfile?.status === "missing_rate") {
    items.push({
      id: "labor-rate",
      title: "Заполнить ставку ФОТ",
      detail: `${formatCount(input.laborProfile.shifts, "смена", "смены", "смен")} есть, но стоимость сотрудника не участвует в экономике.`,
      href: `#labor-member-${encodeURIComponent(input.member.id)}`,
      tone: "risk",
      badge: "ФОТ",
    });
  } else if (
    input.laborProfile?.status === "no_shifts" &&
    input.schedule.length === 0
  ) {
    items.push({
      id: "shift-match",
      title: "Проверить смены в iiko",
      detail:
        "В выбранном периоде система не нашла смен этого сотрудника. Проверьте период или совпадение имени.",
      href: "#iiko-shift-diagnostics",
      tone: "setup",
      badge: "смены",
    });
  }

  if (input.learning && !input.learning.canWorkShift) {
    const next = input.nextLearning ?? input.learning.nextItem;
    items.push({
      id: "learning-admission",
      title: "Закрыть допуск к смене",
      detail: next
        ? `${next.title} · ${next.timeLabel}`
        : `Осталось обязательных модулей: ${input.learning.requiredMissing}.`,
      href: "#learning-progress",
      tone: input.learning.admissionStatus === "not_started" ? "risk" : "setup",
      badge: "допуск",
    });
  }

  const openTasks = input.tasks.filter(isOpenTask);
  const urgentTask = openTasks.find((task) => task.priority === "high");
  if (urgentTask) {
    items.push({
      id: `task-${urgentTask.id}`,
      title: "Закрыть срочную задачу",
      detail: urgentTask.title,
      href: "#team-actions",
      tone: "risk",
      badge: urgentTask.dueLabel || "задача",
      taskId: urgentTask.id,
    });
  }

  const unreadAnnouncement = findUnreadImportantAnnouncement({
    member: input.member,
    announcements: input.announcements,
    reads: input.announcementReads,
  });
  if (unreadAnnouncement) {
    items.push({
      id: `announcement-${unreadAnnouncement.id}`,
      title: "Подтвердить важное объявление",
      detail: unreadAnnouncement.title,
      href: `#team-announcement-${encodeURIComponent(unreadAnnouncement.id)}`,
      tone: "work",
      badge: "связь",
      announcementId: unreadAnnouncement.id,
    });
  }

  const nextTask = urgentTask ? null : (openTasks[0] ?? null);
  if (nextTask) {
    items.push({
      id: `task-${nextTask.id}`,
      title: "Продвинуть задачу",
      detail: nextTask.title,
      href: "#team-actions",
      tone: "work",
      badge: nextTask.dueLabel || "задача",
      taskId: nextTask.id,
    });
  }

  const nextShift = input.schedule[0] ?? null;
  if (items.length < 3 && nextShift) {
    items.push({
      id: `shift-${nextShift.shiftId}`,
      title: "Проверить смену периода",
      detail: `${nextShift.dayLabel} · ${nextShift.timeLabel} · ${formatMoney(nextShift.revenue)}`,
      href: "#shift-coverage",
      tone: "ready",
      badge: "смена",
    });
  }

  if (items.length === 0 && input.nextLearning) {
    items.push({
      id: "next-learning",
      title: "Продолжить обучение",
      detail: `${input.nextLearning.title} · ${input.nextLearning.timeLabel}`,
      href: "#learning-progress",
      tone: "work",
      badge: "урок",
    });
  }

  if (items.length === 0) {
    items.push({
      id: "ready",
      title: "Смена без блокеров",
      detail: "ФОТ, допуск и очередь задач не требуют срочного действия.",
      href: "#shift-coverage",
      tone: "ready",
      badge: "готово",
    });
  }

  return items.slice(0, 4);
}

function findUnreadImportantAnnouncement(input: {
  member: StaffMember;
  announcements?: TeamAnnouncement[];
  reads?: TeamAnnouncementRead[];
}): TeamAnnouncement | null {
  return (
    input.announcements?.find(
      (announcement) =>
        announcement.priority === "important" &&
        isAnnouncementVisibleToMember(announcement, input.member) &&
        !input.reads?.some(
          (read) =>
            read.announcementId === announcement.id &&
            read.memberId === input.member.id,
        ),
    ) ?? null
  );
}

function isAnnouncementVisibleToMember(
  announcement: TeamAnnouncement,
  member: StaffMember,
): boolean {
  if (announcement.venueId !== member.venueId) return false;
  if (announcement.audience.type === "venue") return true;
  return announcement.audience.roleId === member.roleId;
}

function matchShiftWorker(
  shift: LaborShiftInput,
  member: StaffMember,
): LaborShiftWorker | null {
  if (shift.workers?.length) {
    return (
      shift.workers.find((worker) => worker.memberId === member.id) ??
      shift.workers.find(
        (worker) => normalizeName(worker.name) === normalizeName(member.name),
      ) ??
      null
    );
  }

  if (normalizeName(shift.employee) !== normalizeName(member.name)) {
    return null;
  }

  return {
    memberId: member.id,
    name: shift.employee,
    roleId: member.roleId,
    startedAt: shift.openTime,
    endedAt: shift.closeTime,
    hourlyRate: member.hourlyRate,
    shiftPay: member.shiftPay,
    revenueBonusPct: member.revenueBonusPct,
    sales: shift.revenue,
  };
}

function resolveWorkerHours(
  worker: LaborShiftWorker,
  shift: LaborShiftInput,
): number {
  if (typeof worker.hours === "number" && Number.isFinite(worker.hours)) {
    return Math.max(worker.hours, 0);
  }

  const startedAt = worker.startedAt ?? shift.openTime;
  const endedAt = worker.endedAt ?? shift.closeTime;
  if (!endedAt) return 0;

  const started = Date.parse(startedAt);
  const ended = Date.parse(endedAt);
  if (
    !Number.isFinite(started) ||
    !Number.isFinite(ended) ||
    ended <= started
  ) {
    return 0;
  }

  return (ended - started) / 3_600_000;
}

function formatScheduleDay(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value.slice(0, 10);
  return new Intl.DateTimeFormat("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    weekday: "short",
  }).format(date);
}

function formatShiftTime(start: string, end?: string): string {
  return `${formatTime(start)} - ${end ? formatTime(end) : "..."}`;
}

function formatTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value.slice(11, 16) || value;
  return new Intl.DateTimeFormat("ru-RU", {
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function normalizeName(value: string): string {
  return value.trim().toLowerCase().replace(/\s+/g, " ");
}

function roundHours(value: number): number {
  return Math.round(value * 10) / 10;
}

function isOpenTask(task: TeamTask): boolean {
  return task.status !== "done" && task.status !== "verified";
}

function formatCount(
  value: number,
  one: string,
  few: string,
  many: string,
): string {
  const rounded = Math.abs(Math.trunc(value));
  const mod10 = rounded % 10;
  const mod100 = rounded % 100;
  const word =
    mod10 === 1 && mod100 !== 11
      ? one
      : mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)
        ? few
        : many;

  return `${value.toLocaleString("ru-RU")} ${word}`;
}

function formatMoney(value: number): string {
  return `${Math.round(value).toLocaleString("ru-RU")} ₽`;
}
