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
  TeamTaskComment,
  TeamTask,
} from "./team-os";
import { getTeamRole } from "./team-os";
import {
  isLikelySameTeamMemberName,
  normalizeTeamMemberName,
} from "./team-member-match";
import {
  summarizeFieldNoteReadiness,
  type FieldNoteReadinessSummary,
} from "./field-note-input";

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

export type MemberDailyRouteItemId =
  | "briefing"
  | "learning"
  | "task"
  | "shift_memory";

export type MemberDailyRouteItem = {
  id: MemberDailyRouteItemId;
  step: string;
  title: string;
  detail: string;
  href: string;
  status: string;
  action: string;
  ready: boolean;
  tone: MemberOperationPlanTone;
};

export type MemberDailyRoute = {
  readyCount: number;
  totalCount: number;
  headline: string;
  focus: MemberDailyRouteItem;
  items: MemberDailyRouteItem[];
};

export type MemberSecondBrainTone = "risk" | "setup" | "work" | "ready";

export type MemberSecondBrainFact = {
  label: string;
  value: string;
  detail: string;
  tone: MemberSecondBrainTone;
};

export type MemberSecondBrainMemoryLink = {
  label: string;
  detail: string;
  href: string;
  action: string;
  tone: MemberSecondBrainTone;
};

export type MemberSecondBrainProfile = {
  title: string;
  summary: string;
  tags: string[];
  facts: MemberSecondBrainFact[];
  nextQuestion: string;
  memoryLink: MemberSecondBrainMemoryLink;
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

export function buildMemberDailyRoute(input: {
  member: StaffMember;
  tasks: TeamTask[];
  comments?: TeamTaskComment[];
  learning: TeamLearningMemberSummary | null;
  announcements?: TeamAnnouncement[];
  announcementReads?: TeamAnnouncementRead[];
  nextLearning?: { title: string; timeLabel: string } | null;
}): MemberDailyRoute {
  const unreadAnnouncement = findUnreadImportantAnnouncement({
    member: input.member,
    announcements: input.announcements,
    reads: input.announcementReads,
  });
  const openTasks = input.tasks.filter(isOpenTask);
  const urgentTask = openTasks.find((task) => task.priority === "high");
  const nextTask = urgentTask ?? openTasks[0] ?? null;
  const ownNotes = (input.comments ?? []).filter((comment) =>
    isLikelySameTeamMemberName(comment.authorName, input.member.name),
  );
  const latestNote = ownNotes[ownNotes.length - 1] ?? null;
  const learningReady = Boolean(input.learning?.canWorkShift);
  const nextLearning = input.nextLearning ?? input.learning?.nextItem ?? null;

  const items: MemberDailyRouteItem[] = [
    {
      id: "briefing",
      step: "01",
      title: "Прочитать бриф",
      detail: unreadAnnouncement
        ? unreadAnnouncement.title
        : "Важных объявлений для роли сейчас нет.",
      href: unreadAnnouncement
        ? `#team-announcement-${encodeURIComponent(unreadAnnouncement.id)}`
        : "#team-announcements",
      status: unreadAnnouncement ? "важно" : "прочитано",
      action: unreadAnnouncement ? "Подтвердить" : "Проверить",
      ready: !unreadAnnouncement,
      tone: unreadAnnouncement ? "work" : "ready",
    },
    {
      id: "learning",
      step: "02",
      title: "Закрыть допуск",
      detail: learningReady
        ? "Обязательные стандарты не блокируют смену."
        : nextLearning
          ? `${nextLearning.title} · ${nextLearning.timeLabel}`
          : "Нужно пройти обязательные материалы роли.",
      href: "#learning-progress",
      status: learningReady ? "допущен" : "нужен допуск",
      action: learningReady ? "Открыть обучение" : "Пройти",
      ready: learningReady,
      tone: learningReady
        ? "ready"
        : input.learning?.admissionStatus === "not_started"
          ? "risk"
          : "setup",
    },
    {
      id: "task",
      step: "03",
      title: "Сделать задачу",
      detail: nextTask
        ? nextTask.title
        : "Открытых задач на сотрудника или роль нет.",
      href: "#team-actions",
      status: nextTask
        ? urgentTask
          ? "срочно"
          : `${openTasks.length} открыто`
        : "нет задач",
      action: nextTask ? "Открыть" : "Проверить",
      ready: !nextTask,
      tone: urgentTask ? "risk" : nextTask ? "work" : "ready",
    },
    {
      id: "shift_memory",
      step: "04",
      title: "Оставить итог смены",
      detail: latestNote
        ? trimProfileDetail(latestNote.body)
        : "После смены зафиксируйте гостей, стоп-лист, конфликт, погоду и что проверить утром.",
      href: "#shift-summary",
      status: latestNote ? "есть итог" : "нет итога",
      action: latestNote ? "Дополнить" : "Записать",
      ready: Boolean(latestNote),
      tone: latestNote ? "work" : "setup",
    },
  ];

  const readyCount = items.filter((item) => item.ready).length;
  const focus = items.find((item) => !item.ready) ?? items[items.length - 1];

  return {
    readyCount,
    totalCount: items.length,
    headline:
      readyCount === items.length
        ? "Смена закрыта в памяти ресторана."
        : "Сделайте минимум, чтобы смена попала в память ресторана.",
    focus,
    items,
  };
}

export function buildMemberSecondBrainProfile(input: {
  member: StaffMember;
  tasks: TeamTask[];
  comments?: TeamTaskComment[];
  schedule: MemberShiftScheduleItem[];
  laborProfile: MemberLaborProfile | null;
  learning: TeamLearningMemberSummary | null;
  nextLearning?: { title: string; timeLabel: string } | null;
}): MemberSecondBrainProfile {
  const role = getTeamRole(input.member.roleId);
  const openTasks = input.tasks.filter(isOpenTask);
  const urgentTasks = openTasks.filter((task) => task.priority === "high");
  const ownNotes = (input.comments ?? []).filter((comment) =>
    isLikelySameTeamMemberName(comment.authorName, input.member.name),
  );
  const latestNote = ownNotes[ownNotes.length - 1] ?? null;
  const fieldMemory = summarizeFieldNoteReadiness(
    ownNotes.map((note) => note.body),
  );
  const nextLearning = input.nextLearning ?? input.learning?.nextItem ?? null;

  const facts: MemberSecondBrainFact[] = [
    {
      label: "Роль",
      value: role.title,
      detail: input.member.shiftLabel || "смена не назначена",
      tone: input.member.status === "active" ? "ready" : "setup",
    },
    learningFact(input.learning, nextLearning),
    laborFact(input.laborProfile, input.schedule),
    taskFact(openTasks.length, urgentTasks.length),
    fieldFact(latestNote, ownNotes.length, fieldMemory),
  ];

  const primary =
    facts.find((fact) => fact.tone === "risk") ??
    facts.find((fact) => fact.tone === "setup") ??
    facts.find((fact) => fact.tone === "work") ??
    facts[0];

  return {
    title: `${input.member.name}: рабочий контекст`,
    summary: primary
      ? `${primary.label}: ${primary.detail}`
      : "Профиль сотрудника собирается из роли, обучения, смен, задач и заметок после смены.",
    tags: [
      role.shortTitle,
      input.member.status === "active" ? "активен" : input.member.status,
      input.learning?.canWorkShift ? "допущен" : "нужен допуск",
      fieldMemory.complete > 0
        ? "итог полный"
        : latestNote
          ? "итог неполный"
          : "нет итога смены",
    ],
    facts,
    nextQuestion: memberNextQuestion({
      learning: input.learning,
      nextLearning,
      latestNote,
      fieldMemory,
      urgentTasks,
      openTasks,
      laborProfile: input.laborProfile,
    }),
    memoryLink: memberMemoryLink({
      learning: input.learning,
      nextLearning,
      latestNote,
      fieldMemory,
      urgentTasks,
      openTasks,
    }),
  };
}

function learningFact(
  learning: TeamLearningMemberSummary | null,
  nextLearning: { title: string; timeLabel: string } | null,
): MemberSecondBrainFact {
  if (!learning) {
    return {
      label: "Обучение",
      value: "нет данных",
      detail: "Прогресс обучения еще не собран.",
      tone: "setup",
    };
  }

  if (!learning.canWorkShift) {
    return {
      label: "Обучение",
      value:
        learning.admissionStatus === "not_started"
          ? "не начато"
          : "не закрыто",
      detail: nextLearning
        ? `Следующий стандарт: ${nextLearning.title}.`
        : `Не закрыто обязательных модулей: ${learning.requiredMissing}.`,
      tone: "risk",
    };
  }

  return {
    label: "Обучение",
    value: `${learning.averageBest}%`,
    detail:
      learning.completedCount > 0
        ? `Закрыто модулей: ${learning.completedCount}/${learning.totalCount}.`
        : "Обязательные стандарты не блокируют смену.",
    tone: learning.status === "complete" ? "ready" : "work",
  };
}

function laborFact(
  laborProfile: MemberLaborProfile | null,
  schedule: MemberShiftScheduleItem[],
): MemberSecondBrainFact {
  if (laborProfile?.status === "missing_rate") {
    return {
      label: "Смены",
      value: "нет ставки",
      detail:
        "Сотрудник есть в сменах, но стоимость работы не участвует в экономике.",
      tone: "risk",
    };
  }

  if (laborProfile?.status === "ready") {
    return {
      label: "Смены",
      value: `${laborProfile.shifts}`,
      detail: `${formatMoney(laborProfile.sales)} продаж за период, ${laborProfile.hours.toLocaleString("ru-RU")} ч.`,
      tone: "ready",
    };
  }

  return {
    label: "Смены",
    value: schedule.length > 0 ? `${schedule.length}` : "нет",
    detail:
      schedule.length > 0
        ? "Есть план/факт смен, но профиль ФОТ еще не доказан."
        : "В выбранном периоде смены сотрудника не найдены.",
    tone: schedule.length > 0 ? "work" : "setup",
  };
}

function taskFact(openTasks: number, urgentTasks: number): MemberSecondBrainFact {
  if (urgentTasks > 0) {
    return {
      label: "Задачи",
      value: `${urgentTasks} срочно`,
      detail: "Есть срочная задача, которую надо разобрать до смены.",
      tone: "risk",
    };
  }

  return {
    label: "Задачи",
    value: `${openTasks}`,
    detail:
      openTasks > 0
        ? "Есть открытые действия по роли или лично сотруднику."
        : "Открытых задач нет.",
    tone: openTasks > 0 ? "work" : "ready",
  };
}

function fieldFact(
  latestNote: TeamTaskComment | null,
  count: number,
  readiness: FieldNoteReadinessSummary,
): MemberSecondBrainFact {
  if (!latestNote) {
    return {
      label: "Поле",
      value: "нет итога",
      detail:
        "Сотрудник еще не оставлял факты смены. Советнику не хватает живого контекста.",
      tone: "setup",
    };
  }

  if (readiness.complete === 0) {
    return {
      label: "Поле",
      value: `${readiness.complete}/${readiness.total}`,
      detail: `Итог есть, но советнику не хватает: ${readiness.bestMissing.join(", ")}.`,
      tone: "setup",
    };
  }

  return {
    label: "Поле",
    value: `${readiness.complete}/${count}`,
    detail: trimProfileDetail(latestNote.body),
    tone: readiness.complete === count ? "ready" : "work",
  };
}

function memberNextQuestion(input: {
  learning: TeamLearningMemberSummary | null;
  nextLearning: { title: string; timeLabel: string } | null;
  latestNote: TeamTaskComment | null;
  fieldMemory: FieldNoteReadinessSummary;
  urgentTasks: TeamTask[];
  openTasks: TeamTask[];
  laborProfile: MemberLaborProfile | null;
}): string {
  if (input.learning && !input.learning.canWorkShift) {
    return input.nextLearning
      ? `Что мешает пройти стандарт «${input.nextLearning.title}» до смены?`
      : "Какой обязательный стандарт мешает уверенно выпускать сотрудника в смену?";
  }
  if (input.laborProfile?.status === "missing_rate") {
    return "Какая ставка или схема оплаты должна быть у этого сотрудника?";
  }
  if (input.urgentTasks[0]) {
    return `Что мешает закрыть срочную задачу «${input.urgentTasks[0].title}»?`;
  }
  if (input.latestNote && input.fieldMemory.complete === 0) {
    return `В итоге смены не хватает: ${input.fieldMemory.bestMissing.join(", ")}. Что произошло, почему это важно, когда/сколько и что проверить утром?`;
  }
  if (!input.latestNote) {
    return "Что произошло на последней смене: гости, стоп-лист, конфликт, продажи или что проверить утром?";
  }
  if (input.openTasks[0]) {
    return `Какой следующий шаг по задаче «${input.openTasks[0].title}»?`;
  }
  return "Что сотрудник заметил на смене и какой один стандарт стоит усилить?";
}

function memberMemoryLink(input: {
  learning: TeamLearningMemberSummary | null;
  nextLearning: { title: string; timeLabel: string } | null;
  latestNote: TeamTaskComment | null;
  fieldMemory: FieldNoteReadinessSummary;
  urgentTasks: TeamTask[];
  openTasks: TeamTask[];
}): MemberSecondBrainMemoryLink {
  if (input.learning && !input.learning.canWorkShift) {
    return {
      label: "Связать обучение",
      detail: input.nextLearning
        ? `Закрывает пробел в памяти роли: ${input.nextLearning.title}.`
        : "Закрывает пробел допуска в памяти сотрудника.",
      href: "#learning-progress",
      action: "Открыть обучение",
      tone: "risk",
    };
  }

  if (input.urgentTasks[0]) {
    return {
      label: "Связать задачу",
      detail: `Срочная задача станет частью памяти смены: ${input.urgentTasks[0].title}.`,
      href: "#team-actions",
      action: "Открыть задачу",
      tone: "risk",
    };
  }

  if (!input.latestNote) {
    return {
      label: "Собрать итог",
      detail:
        "После смены этот итог свяжет человека, событие и утренний разбор.",
      href: "#shift-summary",
      action: "Записать итог",
      tone: "setup",
    };
  }

  if (input.fieldMemory.complete === 0) {
    return {
      label: "Дополнить итог",
      detail: `Чтобы память стала полезной, добавьте: ${input.fieldMemory.bestMissing.join(", ")}.`,
      href: "#shift-summary",
      action: "Дополнить",
      tone: "setup",
    };
  }

  if (input.openTasks[0]) {
    return {
      label: "Связать задачу",
      detail: `Следующий шаг по задаче попадет в рабочий контекст: ${input.openTasks[0].title}.`,
      href: "#team-actions",
      action: "Открыть задачу",
      tone: "work",
    };
  }

  return {
    label: "Память связана",
    detail:
      "Роль, обучение, задачи и итог смены уже дают советнику рабочий контекст.",
    href: "#shift-summary",
    action: "Добавить наблюдение",
    tone: "ready",
  };
}

function trimProfileDetail(value: string): string {
  const normalized = value.replace(/\s+/g, " ").trim();
  if (normalized.length <= 150) return normalized;
  return `${normalized.slice(0, 147).trim()}...`;
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
        (worker) => isLikelySameTeamMemberName(worker.name, member.name),
      ) ??
      null
    );
  }

  if (!isLikelySameTeamMemberName(shift.employee, member.name)) {
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
  return normalizeTeamMemberName(value);
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
