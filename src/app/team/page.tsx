import type { Metadata } from "next";
import Link from "next/link";
import { redirect } from "next/navigation";
import type { ReactNode } from "react";
import {
  AlertTriangle,
  ArrowRight,
  Banknote,
  CalendarDays,
  CheckCircle2,
  ClipboardCheck,
  ClipboardList,
  Clock3,
  GraduationCap,
  KeyRound,
  ListChecks,
  SearchCheck,
  ShieldCheck,
  Trophy,
  UsersRound,
} from "lucide-react";
import { AppShell } from "@/components/dashboard/app-shell";
import { Badge } from "@/components/ui/badge";
import { LinkButton } from "@/components/ui/link-button";
import { TeamActionsPanel } from "./team-actions-panel";
import { TeamCommunicationPanel } from "./team-communication-panel";
import { TeamFollowUpTaskButton } from "./team-followup-task-button";
import { LearningAdmissionTaskButton } from "./learning-admission-task-button";
import { TeamShiftPlanPanel } from "./team-shift-plan-panel";
import { saveTeamLearningStandardAction } from "./actions";
import {
  formatPeriodLabel,
  parsePeriodSearchParams,
  periodToSearchParams,
} from "@/lib/venues/period";
import {
  buildRoleHome,
  getTeamRole,
  listTasksForMember,
  TEAM_ROLES,
  type StaffMember,
  type TeamAnnouncement,
  type TeamAnnouncementRead,
  type TeamRoleId,
  type TeamTask,
  type TeamTaskComment,
} from "@/lib/team/team-os";
import {
  listShiftChecklistForRole,
  type TeamLearningItem,
} from "@/lib/team/team-learning";
import { listLearningItemsForRoleWithStandards } from "@/lib/team/team-learning-standards";
import {
  buildShiftOverview,
  type ShiftRoleCoverage,
} from "@/lib/team/team-shift-planner";
import {
  buildTeamShiftRoster,
  type TeamShiftRoster,
  type TeamShiftRosterCell,
  type TeamShiftRosterCellStatus,
  type TeamShiftRosterRowStatus,
} from "@/lib/team/team-shift-roster";
import {
  buildTeamShiftPlanSummary,
  type TeamShiftPlanSummary,
} from "@/lib/team/team-shift-plan";
import {
  buildTeamShiftPlanVariance,
  type TeamShiftPlanVarianceIssue,
  type TeamShiftPlanVarianceStatus,
  type TeamShiftPlanVarianceSummary,
  type TeamShiftPlanVarianceTone,
} from "@/lib/team/team-shift-plan-variance";
import {
  buildTeamLearningSummaries,
  summarizeTeamLearning,
  type TeamLearningMemberSummary,
} from "@/lib/team/team-learning-progress";
import {
  buildLearningAdmissionTaskDraft,
  buildTeamLearningFocusPlan,
  buildTeamLearningRolePlans,
  findOpenLearningAdmissionTask,
  type TeamLearningFocusItem,
  type TeamLearningFocusTone,
  type TeamLearningRolePlan,
} from "@/lib/team/team-learning-role-plan";
import {
  buildTeamFieldContextDigest,
  type TeamFieldContextDigest,
} from "@/lib/team/team-field-context";
import {
  summarizeFieldNoteReadiness,
  type FieldNoteReadinessSummary,
} from "@/lib/team/field-note-input";
import { buildTeamLaborReadiness } from "@/lib/team/team-labor-readiness";
import {
  buildTeamOpsReadiness,
  type TeamOpsReadinessStatus,
} from "@/lib/team/team-ops-readiness";
import {
  buildTeamManagerFollowUp,
  type TeamManagerFollowUp,
  type TeamManagerFollowUpItem,
  type TeamManagerFollowUpStatus,
  type TeamManagerFollowUpTone,
} from "@/lib/team/team-manager-followup";
import { buildTeamCommunicationDrafts } from "@/lib/team/team-communication-drafts";
import {
  buildTeamDailyWorkflow,
  type TeamDailyWorkflowStep,
  type TeamDailyWorkflowTone,
} from "@/lib/team/team-daily-workflow";
import {
  buildLaborEmployeeDiagnostics,
  buildLaborShiftDiagnostics,
  type LaborEmployeeDiagnostic,
  type LaborShiftDiagnostic,
} from "@/lib/team/labor-bi";
import {
  loadTeamLabor,
  type TeamLaborLoadResult,
} from "@/lib/team/team-labor-load";
import {
  buildMemberOperationPlan,
  buildMemberLaborProfile,
  buildMemberShiftSchedule,
  buildMemberSecondBrainProfile,
  type MemberLaborProfile,
  type MemberLaborProfileStatus,
  type MemberOperationPlanItem,
  type MemberOperationPlanTone,
  type MemberSecondBrainFact,
  type MemberSecondBrainProfile,
  type MemberSecondBrainTone,
  type MemberShiftScheduleItem,
} from "@/lib/team/member-shift-schedule";
import { getTeamWorkspace } from "@/lib/team/team-store";
import { getCurrentUser } from "@/lib/auth/session";
import { isSupabaseConfigured } from "@/lib/db/env";
import { formatInteger, formatRubles } from "@/lib/format";
import type { Period } from "@/lib/iiko/models";

export const metadata: Metadata = {
  title: "Команда — RECEPTOR",
  description:
    "Роли, права, сотрудники, задачи, обучение и смены внутри Receptor.",
};

async function saveTeamLearningStandardFormAction(
  formData: FormData,
): Promise<void> {
  "use server";

  await saveTeamLearningStandardAction(formData);
}

const ROLE_PARAM_VALUES = new Set<TeamRoleId>(
  TEAM_ROLES.map((role) => role.id),
);

function parseRole(value: string | string[] | undefined): TeamRoleId {
  const raw = Array.isArray(value) ? value[0] : value;
  return raw && ROLE_PARAM_VALUES.has(raw as TeamRoleId)
    ? (raw as TeamRoleId)
    : "owner";
}

function parseVenueId(value: string | string[] | undefined): string {
  const raw = Array.isArray(value) ? value[0] : value;
  return raw?.trim() || "dev-venue";
}

function parseOptionalText(value: string | string[] | undefined): string {
  const raw = Array.isArray(value) ? value[0] : value;
  return raw?.trim() ?? "";
}

function teamHref(
  venueId: string,
  roleId: TeamRoleId,
  period: Period,
  memberId = "",
): string {
  const params = new URLSearchParams({
    role: roleId,
    venueId,
    ...periodToSearchParams(period),
  });
  if (memberId) params.set("memberId", memberId);
  return `/team?${params.toString()}`;
}

function dashboardHref(venueId: string, period: Period): string {
  const params = new URLSearchParams(periodToSearchParams(period));
  return `/dashboard/${encodeURIComponent(venueId)}?${params.toString()}`;
}

function priorityClass(priority: TeamTask["priority"]): string {
  if (priority === "high") {
    return "border-destructive/30 bg-destructive/10 text-destructive";
  }
  if (priority === "medium") {
    return "border-[color:var(--pro)]/30 bg-[color:var(--pro)]/10 text-[color:var(--pro)]";
  }
  return "border-border bg-muted/40 text-muted-foreground";
}

function statusLabel(status: TeamTask["status"]): string {
  if (status === "new") return "новая";
  if (status === "accepted") return "принята";
  if (status === "in_progress") return "в работе";
  if (status === "done") return "сделано";
  return "проверено";
}

function sourceBadgeLabel(task: TeamTask): string | null {
  return task.sourceLabel ?? (task.source === "copilot" ? "Receptor" : null);
}

export default async function TeamPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const sp = await searchParams;
  const roleId = parseRole(sp.role);
  const venueId = parseVenueId(sp.venueId);
  const period = parsePeriodSearchParams(sp);
  const memberId = parseOptionalText(sp.memberId);
  const focusMemberId = parseOptionalText(sp.focusMemberId);
  const focusTaskId = parseOptionalText(sp.focusTaskId);
  const prefillMemberName = parseOptionalText(sp.prefillMemberName);
  const user = await getCurrentUser();
  if (isSupabaseConfigured() && !user && venueId !== "dev-venue") {
    const nextParams = new URLSearchParams({
      role: roleId,
      venueId,
      ...periodToSearchParams(period),
    });
    if (memberId) nextParams.set("memberId", memberId);
    if (focusMemberId) nextParams.set("focusMemberId", focusMemberId);
    if (focusTaskId) nextParams.set("focusTaskId", focusTaskId);
    if (prefillMemberName)
      nextParams.set("prefillMemberName", prefillMemberName);
    const nextPath = `/team?${nextParams.toString()}`;
    redirect(`/auth?next=${encodeURIComponent(nextPath)}`);
  }

  const workspace = await getTeamWorkspace(venueId);
  const home = buildRoleHome(roleId, workspace.tasks);
  const shiftOverview = buildShiftOverview(workspace.staff, workspace.tasks);
  const learningSummaries = buildTeamLearningSummaries(
    workspace.staff,
    workspace.learningProgress,
    workspace.learningStandards,
  );
  const learningOverview = summarizeTeamLearning(learningSummaries);
  const learningRolePlans = buildTeamLearningRolePlans(
    learningSummaries,
    workspace.learningStandards,
  );
  const learningFieldContext = buildTeamFieldContextDigest({
    comments: workspace.comments,
    tasks: workspace.tasks,
  });
  const fieldNoteReadiness = summarizeFieldNoteReadiness(
    workspace.comments.map((comment) => comment.body),
  );
  const learningFocusPlan = buildTeamLearningFocusPlan({
    plans: learningRolePlans,
    fieldContext: learningFieldContext,
  });
  const laborLoad = await loadTeamLabor({
    venueId,
    staff: workspace.staff,
    period,
  });
  const laborReadiness = buildTeamLaborReadiness(
    workspace.staff,
    laborLoad.laborBi,
  );
  const opsReadiness = buildTeamOpsReadiness({
    shiftOverview,
    laborReadiness,
    learningSummaries,
    tasks: workspace.tasks,
  });
  const shiftDiagnostics = laborLoad.laborBi
    ? buildLaborShiftDiagnostics(laborLoad.laborBi).slice(0, 5)
    : [];
  const employeeDiagnostics = laborLoad.laborBi
    ? buildLaborEmployeeDiagnostics(laborLoad.laborBi)
        .filter((item) => item.kind !== "healthy")
        .slice(0, 4)
    : [];
  const shiftRoster = buildTeamShiftRoster({
    staff: workspace.staff,
    shifts: laborLoad.shifts,
    labor: laborLoad.laborBi,
  });
  const shiftPlanSummary = buildTeamShiftPlanSummary({
    staff: workspace.staff,
    plans: workspace.shiftPlans,
  });
  const shiftPlanVariance = buildTeamShiftPlanVariance({
    plan: shiftPlanSummary,
    roster: shiftRoster,
  });
  const managerFollowUp = buildTeamManagerFollowUp({
    staff: workspace.staff,
    tasks: workspace.tasks,
    laborReadiness,
    labor: laborLoad.laborBi,
    learningSummaries,
    shiftPlanVariance,
    announcements: workspace.announcements,
    announcementReads: workspace.announcementReads,
  });
  const communicationDrafts = buildTeamCommunicationDrafts({
    learningRolePlans,
    laborReadiness,
    shiftPlanVariance,
  });
  const dailyWorkflow = buildTeamDailyWorkflow({
    opsReadiness,
    managerFollowUp,
    learningFocus: learningFocusPlan,
    fieldContext: learningFieldContext,
  });
  const selectedMemberId = memberId || focusMemberId;
  const selectedMember = selectedMemberId
    ? (workspace.staff.find((member) => member.id === selectedMemberId) ?? null)
    : null;
  const visibleStaffBase = workspace.staff.filter((member) =>
    roleId === "owner" ||
    roleId === "operations_manager" ||
    roleId === "venue_manager"
      ? true
      : member.roleId === roleId,
  );
  const visibleStaff =
    selectedMember &&
    !visibleStaffBase.some((member) => member.id === selectedMember.id)
      ? [selectedMember, ...visibleStaffBase]
      : visibleStaffBase;
  const representativeMember =
    selectedMember ??
    workspace.staff.find((member) => member.roleId === roleId) ??
    workspace.staff[0];
  const memberTasks = representativeMember
    ? listTasksForMember(
        representativeMember.id,
        workspace.staff,
        workspace.tasks,
      )
    : [];
  const memberLearning = representativeMember
    ? listLearningItemsForRoleWithStandards(
        representativeMember.roleId,
        workspace.learningStandards,
      ).slice(0, 3)
    : [];
  const memberChecklist = representativeMember
    ? listShiftChecklistForRole(representativeMember.roleId).slice(0, 3)
    : [];
  const representativeLearning = representativeMember
    ? (learningSummaries.find(
        (summary) => summary.member.id === representativeMember.id,
      ) ?? null)
    : null;
  const memberSchedule = representativeMember
    ? buildMemberShiftSchedule({
        member: representativeMember,
        shifts: laborLoad.shifts,
      }).slice(0, 7)
    : [];
  const memberLaborProfile = representativeMember
    ? buildMemberLaborProfile({
        member: representativeMember,
        labor: laborLoad.laborBi,
      })
    : null;

  return (
    <AppShell
      activeHref="/team"
      venueId={workspace.venueId}
      venueName={workspace.venueName}
      venueMeta={workspace.venueMeta}
    >
      <main className="flex-1">
        <section className="border-b border-border/40">
          <div className="mx-auto grid max-w-7xl gap-5 px-6 py-7 lg:grid-cols-[0.7fr_1.3fr]">
            <div>
              <Badge variant="outline" className="border-brand/30 text-brand">
                Команда
              </Badge>
              <h1 className="mt-4 max-w-xl text-balance text-[clamp(1.9rem,3.2vw,2.75rem)] font-medium leading-[1.04]">
                Контроль смены.
              </h1>
              <p className="mt-4 max-w-xl text-sm leading-relaxed text-muted-foreground">
                Сначала закрываем то, что мешает смене: срочные задачи, ФОТ,
                допуск, связь и план/факт.
              </p>
              <div className="mt-5 flex flex-wrap gap-3">
                <LinkButton
                  href={dashboardHref(workspace.venueId, period)}
                  className="bg-brand text-primary-foreground hover:bg-brand-hover"
                >
                  Панель владельца
                  <ArrowRight className="size-4" />
                </LinkButton>
                <LinkButton href="#shift-roster" variant="outline">
                  Сменная сетка
                </LinkButton>
                <LinkButton
                  href="#learning-progress"
                  variant="outline"
                  className="hidden sm:inline-flex"
                >
                  Допуск
                </LinkButton>
              </div>
            </div>

            <div className="rounded-lg border border-border/60 bg-card/60 p-5">
              <div className="grid gap-5 xl:grid-cols-[0.55fr_1fr]">
                <div>
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-[11px] uppercase tracking-[0.22em] text-muted-foreground">
                        Готовность команды
                      </p>
                      <div className="mt-3 flex items-end gap-3">
                        <p className="numeric text-5xl font-medium leading-none">
                          {opsReadiness.score}%
                        </p>
                        <Badge
                          variant="outline"
                          className={opsStatusClass(opsReadiness.status)}
                        >
                          {opsStatusLabel(opsReadiness.status)}
                        </Badge>
                      </div>
                    </div>
                    <CheckCircle2 className="size-5 shrink-0 text-brand" />
                  </div>

                  <p className="mt-4 text-sm leading-relaxed text-muted-foreground">
                    {home.role.title}: {home.role.description}
                  </p>

                  <div className="mt-4 grid gap-2">
                    <ReadinessMetric
                      label="Роли"
                      value={`${opsReadiness.roleCoveragePct}%`}
                    />
                    <ReadinessMetric
                      label="ФОТ"
                      value={`${opsReadiness.laborCoveragePct}%`}
                    />
                    <ReadinessMetric
                      label="Допуск"
                      value={`${opsReadiness.learningAdmissionPct}%`}
                    />
                  </div>
                </div>

                <TeamManagerFollowUpCard
                  venueId={workspace.venueId}
                  followUp={managerFollowUp}
                />
              </div>
            </div>
          </div>
        </section>

        <section className="border-b border-border/40">
          <div className="mx-auto max-w-7xl px-6 py-6">
            <TeamDailyWorkflowStrip steps={dailyWorkflow} />
          </div>
        </section>

        <section className="border-b border-border/40">
          <div className="mx-auto max-w-7xl px-6 py-6">
            <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
              <p className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground lg:w-36">
                Кабинет
              </p>
              <div className="grid flex-1 gap-2 sm:grid-cols-2 lg:grid-cols-7">
                {TEAM_ROLES.map((role) => {
                  const active = role.id === roleId;
                  return (
                    <Link
                      key={role.id}
                      href={teamHref(workspace.venueId, role.id, period)}
                      className={
                        "rounded-lg border px-3 py-2 transition-colors " +
                        (active
                          ? "border-brand/50 bg-card"
                          : "border-border/60 bg-card/45 hover:bg-card/75")
                      }
                    >
                      <div className="flex items-center justify-between gap-2">
                        <p className="truncate text-sm font-medium">
                          {role.title}
                        </p>
                        <span className="text-[10px] uppercase tracking-[0.12em] text-muted-foreground">
                          {role.shortTitle}
                        </span>
                      </div>
                    </Link>
                  );
                })}
              </div>
            </div>
          </div>
        </section>

        <RolePersonalBrief
          member={representativeMember}
          tasks={memberTasks}
          checklist={memberChecklist}
          learning={representativeLearning}
          learningFallback={memberLearning}
          schedule={memberSchedule}
          announcements={workspace.announcements}
          announcementReads={workspace.announcementReads}
          comments={workspace.comments}
          laborSource={laborLoad.source}
          periodLabel={formatPeriodLabel(period)}
          laborProfile={memberLaborProfile}
        />

        <TeamShiftMemorySection
          digest={learningFieldContext}
          readiness={fieldNoteReadiness}
        />

        <ShiftOperationsRoute
          roster={shiftRoster}
          plan={shiftPlanSummary}
          variance={shiftPlanVariance}
          laborCoveragePct={laborLoad.laborBi?.revenueCoveragePct ?? null}
        />

        <TeamShiftRosterSection
          roster={shiftRoster}
          laborSource={laborLoad.source}
          periodLabel={formatPeriodLabel(period)}
          error={laborLoad.error}
        />

        <TeamShiftPlanPanel
          venueId={workspace.venueId}
          staff={workspace.staff}
          plans={workspace.shiftPlans}
        />

        <TeamShiftPlanVarianceSection
          variance={shiftPlanVariance}
          laborSource={laborLoad.source}
          periodLabel={formatPeriodLabel(period)}
        />

        <section
          id="iiko-shift-diagnostics"
          className="scroll-mt-24 border-b border-border/40"
        >
          <div className="mx-auto grid max-w-7xl gap-5 px-6 py-8 lg:grid-cols-[0.72fr_1.28fr]">
            <div className="rounded-lg border border-border/60 bg-card/50 p-5">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-[11px] uppercase tracking-[0.22em] text-brand">
                    Смены из iiko
                  </p>
                  <h2 className="mt-3 text-2xl font-medium">
                    Какая смена требует разбора
                  </h2>
                  <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                    Сначала проверяем, можно ли верить ФОТ, потом ищем дорогие и
                    слабые смены.
                  </p>
                </div>
                <SearchCheck className="size-6 shrink-0 text-brand" />
              </div>

              <div className="mt-5 grid grid-cols-3 gap-3">
                <ShiftMetric
                  icon={<CalendarDays className="size-4" />}
                  label="Смен"
                  value={formatInteger(laborLoad.laborBi?.shifts ?? 0)}
                />
                <ShiftMetric
                  icon={<Banknote className="size-4" />}
                  label="ФОТ"
                  value={formatRubles(laborLoad.laborBi?.laborCost ?? 0)}
                />
                <ShiftMetric
                  icon={<Clock3 className="size-4" />}
                  label="Часы"
                  value={formatHours(laborLoad.laborBi?.staffHours ?? 0)}
                />
              </div>

              <p className="mt-4 text-xs leading-relaxed text-muted-foreground">
                Источник: {laborSourceLabel(laborLoad.source)} за{" "}
                {formatPeriodLabel(period)}.
              </p>
            </div>

            <div className="rounded-lg border border-border/60 bg-card/50 p-5">
              <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
                <div>
                  <p className="text-[11px] uppercase tracking-[0.22em] text-muted-foreground">
                    Очередь разбора
                  </p>
                  <h2 className="mt-2 text-xl font-medium">
                    ФОТ, выручка и человеко-часы
                  </h2>
                </div>
                <p className="text-xs text-muted-foreground">
                  точность ФОТ:{" "}
                  {formatPct(laborLoad.laborBi?.revenueCoveragePct ?? null)}
                </p>
              </div>

              <div className="mt-5 grid gap-3">
                {shiftDiagnostics.length > 0 ? (
                  shiftDiagnostics.map((shift) => (
                    <ShiftDiagnosticRow key={shift.shiftId} shift={shift} />
                  ))
                ) : (
                  <div className="rounded-lg border border-border/45 bg-background/35 p-4">
                    <p className="text-sm font-medium">
                      Смены за период не загружены
                    </p>
                    <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
                      {laborLoad.error ??
                        "Проверьте период, права интеграции и доступ к сменам iiko."}
                    </p>
                  </div>
                )}
              </div>

              <EmployeeLaborDiagnostics
                diagnostics={employeeDiagnostics}
                employeeCount={laborLoad.laborBi?.employees.length ?? 0}
                roleId={roleId}
                venueId={workspace.venueId}
                period={period}
              />
            </div>
          </div>
        </section>

        <section
          id="shift-coverage"
          className="scroll-mt-24 border-b border-border/40"
        >
          <div className="mx-auto grid max-w-7xl gap-6 px-6 py-8 lg:grid-cols-[0.82fr_1.18fr]">
            <div className="rounded-lg border border-border/60 bg-card/50 p-5">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-[11px] uppercase tracking-[0.22em] text-brand">
                    Смена сегодня
                  </p>
                  <h2 className="mt-3 text-2xl font-medium">Состав и риски</h2>
                  <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                    Короткая проверка перед посадкой: кто активен, где нет
                    человека и сколько важных задач висит на смене.
                  </p>
                </div>
                <CalendarDays className="size-6 shrink-0 text-brand" />
              </div>

              <div className="mt-5 grid grid-cols-2 gap-3">
                <Metric label="Активны" value={shiftOverview.activeStaff} />
                <Metric
                  label="Важных задач"
                  value={shiftOverview.importantTasks}
                />
                <Metric
                  label="Ролей закрыто"
                  value={shiftOverview.coveredRoles}
                />
                <Metric
                  label="Без человека"
                  value={shiftOverview.uncoveredRoles.length}
                />
              </div>

              {shiftOverview.uncoveredRoles.length > 0 ? (
                <div className="mt-5 rounded-lg border border-amber-400/25 bg-amber-400/10 p-4">
                  <div className="flex items-start gap-3">
                    <AlertTriangle className="mt-0.5 size-4 shrink-0 text-amber-200" />
                    <div>
                      <p className="text-sm font-medium text-amber-100">
                        Проверить покрытие ролей
                      </p>
                      <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
                        {shiftOverview.uncoveredRoles
                          .slice(0, 4)
                          .map((item) => item.title)
                          .join(", ")}
                      </p>
                    </div>
                  </div>
                </div>
              ) : null}
            </div>

            <div className="rounded-lg border border-border/60 bg-card/50 p-5">
              <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
                <div>
                  <p className="text-[11px] uppercase tracking-[0.22em] text-muted-foreground">
                    Покрытие
                  </p>
                  <h2 className="mt-2 text-xl font-medium">Роли и задачи</h2>
                </div>
                <p className="text-xs text-muted-foreground">
                  {shiftOverview.openTasks} открытых задач
                </p>
              </div>
              <div className="mt-5 grid gap-3">
                {shiftOverview.coverage.map((coverage) => (
                  <ShiftCoverageRow key={coverage.roleId} coverage={coverage} />
                ))}
              </div>
            </div>
          </div>
        </section>

        <section
          id="learning-progress"
          className="scroll-mt-24 border-b border-border/40"
        >
          <div className="mx-auto max-w-7xl px-6 py-8">
            <div className="grid gap-6 lg:grid-cols-[0.78fr_1.22fr]">
              <div className="rounded-lg border border-border/60 bg-card/50 p-5">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-[11px] uppercase tracking-[0.22em] text-brand">
                      Обучение команды
                    </p>
                    <h2 className="mt-3 text-2xl font-medium">
                      Стандарты под контролем
                    </h2>
                    <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                      Допуск к смене считается по обязательным материалам.
                      Остальное — развитие и точки роста.
                    </p>
                  </div>
                  <GraduationCap className="size-6 shrink-0 text-brand" />
                </div>

                <div className="mt-5 grid grid-cols-2 gap-3">
                  <Metric
                    label="Допущены"
                    value={learningOverview.admittedMembers}
                  />
                  <Metric
                    label="Нет допуска"
                    value={learningOverview.blockedMembers}
                  />
                  <Metric
                    label="Нужен фокус"
                    value={learningOverview.attentionMembers}
                  />
                  <Metric
                    label="Средний %"
                    value={learningOverview.averageBest}
                  />
                </div>
              </div>

              <div className="rounded-lg border border-border/60 bg-card/50 p-5">
                <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
                  <div>
                    <p className="text-[11px] uppercase tracking-[0.22em] text-muted-foreground">
                      Допуск
                    </p>
                    <h2 className="mt-2 text-xl font-medium">
                      Прогресс по сотрудникам
                    </h2>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {workspace.learningProgress.length} попыток сохранено
                  </p>
                </div>
                <div className="mt-5 grid gap-3">
                  {learningSummaries.map((summary) => (
                    <LearningSummaryRow
                      key={summary.member.id}
                      summary={summary}
                    />
                  ))}
                </div>
              </div>
            </div>

            <div className="mt-6">
              <LearningFocusPanel items={learningFocusPlan} />
            </div>

            <div className="mt-6">
              <LearningRolePlanGrid
                venueId={workspace.venueId}
                plans={learningRolePlans}
                tasks={workspace.tasks}
              />
            </div>
          </div>
        </section>

        <TeamActionsPanel
          venueId={workspace.venueId}
          staff={workspace.staff}
          tasks={workspace.tasks}
          comments={workspace.comments}
          auditEvents={workspace.auditEvents}
          focusMemberId={focusMemberId}
          focusTaskId={focusTaskId}
          prefillMemberName={prefillMemberName}
          laborBi={laborLoad.laborBi}
          laborSource={{
            status: laborLoad.source,
            periodLabel: formatPeriodLabel(period),
            error: laborLoad.error,
          }}
        />

        <TeamCommunicationPanel
          venueId={workspace.venueId}
          roleId={roleId}
          tasks={workspace.tasks}
          comments={workspace.comments}
          announcements={workspace.announcements}
          announcementReads={workspace.announcementReads}
          drafts={communicationDrafts}
        />

        <section className="border-b border-border/40">
          <div className="mx-auto max-w-7xl px-6 py-8">
            <details className="group rounded-lg border border-border/60 bg-card/35 p-4">
              <summary className="flex cursor-pointer list-none flex-col gap-3 rounded-md outline-none transition-colors hover:bg-background/30 focus-visible:ring-2 focus-visible:ring-brand/50 sm:flex-row sm:items-center sm:justify-between">
                <span className="flex min-w-0 items-start gap-3">
                  <KeyRound className="mt-1 size-5 shrink-0 text-brand" />
                  <span>
                    <span className="block text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
                      Подробности управления
                    </span>
                    <span className="mt-1 block text-lg font-medium text-foreground">
                      Доступы, сотрудники и полный список задач
                    </span>
                  </span>
                </span>
                <span className="inline-flex items-center gap-2 text-[12px] uppercase tracking-[0.14em] text-muted-foreground">
                  открыть
                  <ArrowRight className="size-4 transition-transform group-open:rotate-90" />
                </span>
              </summary>

              <div className="mt-5 grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
                <div className="rounded-lg border border-border/60 bg-background/30 p-5">
                  <div className="flex items-center gap-3">
                    <ShieldCheck className="size-5 text-brand" />
                    <h2 className="text-xl font-medium">Права кабинета</h2>
                  </div>
                  <div className="mt-5 grid gap-3">
                    {home.permissions.map((permission) => (
                      <div
                        key={permission.id}
                        className="rounded-lg border border-border/45 bg-background/35 p-3"
                      >
                        <p className="text-sm font-medium">{permission.title}</p>
                        <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
                          {permission.description}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="rounded-lg border border-border/60 bg-background/30 p-5">
                  <div className="flex items-center gap-3">
                    <ClipboardList className="size-5 text-brand" />
                    <h2 className="text-xl font-medium">Задачи в этом кабинете</h2>
                  </div>
                  <div className="mt-5 grid gap-3">
                    {home.visibleTasks.map((task) => (
                      <TaskRow
                        key={task.id}
                        task={task}
                        anchorId={`team-task-${task.id}`}
                        focused={focusTaskId === task.id}
                      />
                    ))}
                  </div>
                </div>
              </div>

              <div className="mt-6 grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
                <div className="rounded-lg border border-border/60 bg-background/30 p-5">
                  <div className="flex items-center gap-3">
                    <UsersRound className="size-5 text-brand" />
                    <h2 className="text-xl font-medium">Сотрудники</h2>
                  </div>
                  <div className="mt-5 grid gap-3 lg:grid-cols-2">
                    {visibleStaff.map((member) => (
                      <StaffRow
                        key={member.id}
                        member={member}
                        href={teamHref(
                          workspace.venueId,
                          member.roleId,
                          period,
                          member.id,
                        )}
                        selected={representativeMember?.id === member.id}
                      />
                    ))}
                  </div>
                </div>

                <div className="rounded-lg border border-border/60 bg-background/30 p-6">
                  <div className="flex items-start gap-3">
                    <KeyRound className="mt-1 size-5 shrink-0 text-brand" />
                    <div>
                      <h2 className="text-xl font-medium">Сменный чат позже.</h2>
                      <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
                        Сейчас достаточно задач, объявлений, комментариев и итогов
                        смены. Чат добавим, когда этот ритм станет привычным для
                        команды.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </details>
          </div>
        </section>
      </main>
    </AppShell>
  );
}

function Metric({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="rounded-lg border border-border/50 bg-background/35 p-3">
      <p className="numeric text-2xl font-medium text-foreground">{value}</p>
      <p className="mt-1 text-[11px] uppercase tracking-[0.16em] text-muted-foreground">
        {label}
      </p>
    </div>
  );
}

function opsStatusLabel(status: TeamOpsReadinessStatus): string {
  if (status === "ready") return "готово";
  if (status === "attention") return "внимание";
  return "блокер";
}

function opsStatusClass(status: TeamOpsReadinessStatus): string {
  if (status === "ready") return "border-brand/35 bg-brand/10 text-brand";
  if (status === "attention") {
    return "border-amber-400/30 bg-amber-400/10 text-amber-100";
  }
  return "border-destructive/30 bg-destructive/10 text-destructive";
}

function managerFollowUpStatusClass(status: TeamManagerFollowUpStatus): string {
  if (status === "ready") return "border-brand/35 bg-brand/10 text-brand";
  if (status === "attention") {
    return "border-amber-400/30 bg-amber-400/10 text-amber-100";
  }
  return "border-destructive/30 bg-destructive/10 text-destructive";
}

function managerFollowUpToneClass(tone: TeamManagerFollowUpTone): string {
  if (tone === "good") return "border-brand/35 bg-brand/10 text-brand";
  if (tone === "risk") {
    return "border-destructive/30 bg-destructive/10 text-destructive";
  }
  return "border-amber-400/30 bg-amber-400/10 text-amber-100";
}

function managerFollowUpStatusLabel(status: TeamManagerFollowUpStatus): string {
  if (status === "ready") return "готово";
  if (status === "attention") return "внимание";
  return "блокер";
}

function ReadinessMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between rounded-lg border border-border/45 bg-background/35 px-3 py-2">
      <span className="text-[11px] uppercase tracking-[0.16em] text-muted-foreground">
        {label}
      </span>
      <span className="numeric text-sm font-medium text-foreground">
        {value}
      </span>
    </div>
  );
}

function TeamManagerFollowUpCard({
  venueId,
  followUp,
}: {
  venueId: string;
  followUp: TeamManagerFollowUp;
}) {
  const primaryItem = followUp.items[0] ?? null;
  const secondaryItems = followUp.items.slice(1, 3);

  return (
    <div>
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-[11px] uppercase tracking-[0.22em] text-muted-foreground">
            Контроль смены
          </p>
          <h2 className="mt-2 text-lg font-medium">{followUp.title}</h2>
        </div>
        <Badge
          variant="outline"
          className={managerFollowUpStatusClass(followUp.status)}
        >
          {managerFollowUpStatusLabel(followUp.status)}
        </Badge>
      </div>

      <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
        {followUp.detail}
      </p>

      <div className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-4">
        <FollowUpMetric
          label="Срочно"
          value={formatInteger(followUp.urgentTasks)}
        />
        <FollowUpMetric
          label="Допуск"
          value={formatInteger(followUp.blockedAdmissions)}
        />
        <FollowUpMetric label="ФОТ" value={`${followUp.laborCoveragePct}%`} />
        <FollowUpMetric
          label="Связь"
          value={formatInteger(followUp.unreadImportantAnnouncements)}
        />
      </div>

      {primaryItem ? (
        <div className="mt-4 rounded-lg border border-brand/30 bg-brand/10 p-4">
          <Link href={primaryItem.href} className="block">
            <div className="flex flex-wrap items-center gap-2">
              <span
                className={
                  "inline-flex size-7 items-center justify-center rounded-md border " +
                  managerFollowUpToneClass(primaryItem.tone)
                }
              >
                <span className="size-2 rounded-full bg-current" />
              </span>
              <span className="rounded-md border border-border/45 bg-background/40 px-2 py-1 text-[10px] uppercase tracking-[0.12em] text-muted-foreground">
                {primaryItem.metric}
              </span>
            </div>
            <h3 className="mt-3 text-base font-medium leading-snug text-foreground">
              {primaryItem.title}
            </h3>
            <p className="mt-2 line-clamp-3 text-sm leading-relaxed text-muted-foreground">
              {primaryItem.detail}
            </p>
            {primaryItem.taskDraft?.learningChecklistTitle ? (
              <div className="mt-3 inline-flex max-w-full items-center gap-2 rounded-md border border-sky-400/25 bg-sky-400/10 px-2.5 py-1.5 text-[11px] text-sky-100">
                <GraduationCap className="size-3.5 shrink-0" />
                <span className="shrink-0 uppercase tracking-[0.12em]">
                  стандарт
                </span>
                <span className="truncate text-muted-foreground">
                  {primaryItem.taskDraft.learningChecklistTitle}
                </span>
              </div>
            ) : null}
          </Link>
          <div className="mt-4 flex flex-wrap gap-2">
            <LinkButton
              href={primaryItem.href}
              className="h-9 px-3 text-[13px]"
            >
              Открыть
              <ArrowRight className="size-3.5" />
            </LinkButton>
            {primaryItem.taskDraft ? (
              <TeamFollowUpTaskButton
                venueId={venueId}
                draft={primaryItem.taskDraft}
              />
            ) : null}
          </div>
        </div>
      ) : null}

      {secondaryItems.length > 0 ? (
        <div className="mt-4 grid gap-2">
          <p className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
            Следом
          </p>
          {secondaryItems.map((item) => (
            <TeamManagerFollowUpRow
              key={item.id}
              venueId={venueId}
              item={item}
            />
          ))}
        </div>
      ) : null}
    </div>
  );
}

function FollowUpMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-border/45 bg-background/35 px-3 py-2">
      <p className="numeric text-sm font-medium text-foreground">{value}</p>
      <p className="mt-1 text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
        {label}
      </p>
    </div>
  );
}

function TeamManagerFollowUpRow({
  venueId,
  item,
}: {
  venueId: string;
  item: TeamManagerFollowUpItem;
}) {
  return (
    <div className="grid gap-2 rounded-lg border border-border/45 bg-background/35 p-3 transition-colors hover:border-brand/35 hover:bg-background/55 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center">
      <Link
        href={item.href}
        className="grid min-w-0 gap-3 sm:grid-cols-[auto_1fr_auto] sm:items-center"
      >
        <span
          className={
            "size-2 rounded-full border " + managerFollowUpToneClass(item.tone)
          }
        />
        <span className="min-w-0">
          <span className="block text-sm font-medium text-foreground">
            {item.title}
          </span>
          <span className="mt-1 block truncate text-xs text-muted-foreground">
            {item.detail}
          </span>
        </span>
        <span className="flex items-center gap-2 text-[11px] uppercase tracking-[0.12em] text-muted-foreground">
          {item.taskDraft?.learningChecklistTitle ? (
            <span className="inline-flex items-center gap-1 rounded-md border border-sky-400/25 bg-sky-400/10 px-2 py-1 text-sky-100">
              <GraduationCap className="size-3" />
              стандарт
            </span>
          ) : null}
          {item.metric}
          <ArrowRight className="size-4" />
        </span>
      </Link>
      {item.taskDraft ? (
        <TeamFollowUpTaskButton venueId={venueId} draft={item.taskDraft} />
      ) : null}
    </div>
  );
}

function isOpenTask(task: TeamTask): boolean {
  return task.status !== "done" && task.status !== "verified";
}

function ShiftOperationsRoute({
  roster,
  plan,
  variance,
  laborCoveragePct,
}: {
  roster: TeamShiftRoster;
  plan: TeamShiftPlanSummary;
  variance: TeamShiftPlanVarianceSummary;
  laborCoveragePct: number | null;
}) {
  const steps: Array<{
    index: string;
    label: string;
    title: string;
    detail: string;
    metric: string;
    href: string;
    tone: "good" | "watch" | "risk";
    icon: ReactNode;
  }> = [
    {
      index: "01",
      label: "Факт",
      title: "Кто работал",
      detail: "Смены, часы, выручка и ФОТ из iiko.",
      metric: `${formatInteger(roster.totalShifts)} смен`,
      href: "#shift-roster",
      tone: roster.rowsMissingRates > 0 ? "watch" : "good",
      icon: <UsersRound className="size-4" />,
    },
    {
      index: "02",
      label: "План",
      title: "Кого ставим",
      detail: "График, выходные и прогноз ФОТ до смены.",
      metric: `${formatInteger(plan.plannedShifts)} план`,
      href: "#shift-plan",
      tone: plan.missingRateShifts > 0 ? "watch" : "good",
      icon: <CalendarDays className="size-4" />,
    },
    {
      index: "03",
      label: "Отклонения",
      title: "Что не совпало",
      detail: "План против факта: выходные, прогулы и часы.",
      metric: `${formatInteger(variance.issues.length)} сигналов`,
      href: "#shift-plan-variance",
      tone: variance.issues.some((issue) => issue.tone === "risk")
        ? "risk"
        : variance.issues.length > 0
          ? "watch"
          : "good",
      icon: <ClipboardCheck className="size-4" />,
    },
    {
      index: "04",
      label: "Диагностика",
      title: "Где копать",
      detail: "Дорогие смены, слабая выручка и ставки.",
      metric: formatPct(laborCoveragePct),
      href: "#iiko-shift-diagnostics",
      tone:
        laborCoveragePct === null
          ? "watch"
          : laborCoveragePct < 80
            ? "risk"
            : laborCoveragePct < 100
              ? "watch"
              : "good",
      icon: <SearchCheck className="size-4" />,
    },
  ];

  return (
    <section className="border-b border-border/40">
      <div className="mx-auto max-w-7xl px-6 py-6">
        <div className="rounded-lg border border-border/60 bg-card/45 p-4">
          <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <p className="text-[11px] uppercase tracking-[0.2em] text-brand">
                Маршрут смены
              </p>
              <h2 className="mt-2 text-xl font-medium">
                Факт, план и отклонения в одном порядке
              </h2>
            </div>
            <p className="max-w-xl text-sm leading-relaxed text-muted-foreground">
              Сначала смотрим реальные смены из iiko, затем график команды,
              расхождения и точечную диагностику ФОТ.
            </p>
          </div>

          <div className="mt-5 grid gap-2 md:grid-cols-2 xl:grid-cols-4">
            {steps.map((step) => (
              <Link
                key={step.href}
                href={step.href}
                className="group rounded-lg border border-border/45 bg-background/35 p-3 transition-colors hover:border-brand/35 hover:bg-background/55"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex min-w-0 items-start gap-3">
                    <span
                      className={
                        "inline-flex size-9 shrink-0 items-center justify-center rounded-lg border text-[11px] font-medium " +
                        shiftRouteToneClass(step.tone)
                      }
                    >
                      {step.index}
                    </span>
                    <span className="min-w-0">
                      <span className="block text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
                        {step.label}
                      </span>
                      <span className="mt-1 block text-sm font-medium text-foreground">
                        {step.title}
                      </span>
                    </span>
                  </div>
                  <span
                    className={
                      "inline-flex size-8 shrink-0 items-center justify-center rounded-lg border " +
                      shiftRouteToneClass(step.tone)
                    }
                  >
                    {step.icon}
                  </span>
                </div>
                <p className="mt-3 text-xs leading-relaxed text-muted-foreground">
                  {step.detail}
                </p>
                <div className="mt-3 flex items-center justify-between gap-3">
                  <span className="numeric text-sm font-medium text-foreground">
                    {step.metric}
                  </span>
                  <span className="inline-flex items-center gap-1 text-[11px] uppercase tracking-[0.12em] text-muted-foreground transition-colors group-hover:text-brand">
                    открыть
                    <ArrowRight className="size-3.5" />
                  </span>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

function shiftRouteToneClass(tone: "good" | "watch" | "risk"): string {
  if (tone === "risk") {
    return "border-destructive/35 bg-destructive/10 text-destructive";
  }
  if (tone === "watch") {
    return "border-amber-400/35 bg-amber-400/10 text-amber-100";
  }
  return "border-brand/35 bg-brand/10 text-brand";
}

function TeamShiftRosterSection({
  roster,
  laborSource,
  periodLabel,
  error,
}: {
  roster: TeamShiftRoster;
  laborSource: TeamLaborLoadResult["source"];
  periodLabel: string;
  error: string | null;
}) {
  return (
    <section
      id="shift-roster"
      className="scroll-mt-24 border-b border-border/40"
    >
      <div className="mx-auto max-w-7xl px-6 py-8">
        <div className="rounded-lg border border-border/60 bg-card/50 p-5">
          <div className="grid gap-5 xl:grid-cols-[0.46fr_1.54fr]">
            <div>
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-[11px] uppercase tracking-[0.22em] text-brand">
                    Сменная сетка
                  </p>
                  <h2 className="mt-3 text-2xl font-medium">
                    Кто работал и сколько стоила смена
                  </h2>
                  <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                    Фактические смены из iiko связаны с карточками сотрудников и
                    ставками ФОТ.
                  </p>
                </div>
                <UsersRound className="size-6 shrink-0 text-brand" />
              </div>

              <div className="mt-5 grid grid-cols-2 gap-3">
                <Metric label="В сменах" value={roster.rowsWithShifts} />
                <Metric label="Смен" value={roster.totalShifts} />
                <Metric label="Часов" value={formatHours(roster.totalHours)} />
                <Metric label="Без ставки" value={roster.rowsMissingRates} />
              </div>

              <p className="mt-4 text-xs leading-relaxed text-muted-foreground">
                Источник: {laborSourceLabel(laborSource)} за {periodLabel}.
              </p>
            </div>

            <div className="min-w-0">
              <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
                <div>
                  <p className="text-[11px] uppercase tracking-[0.22em] text-muted-foreground">
                    Сетка периода
                  </p>
                  <h3 className="mt-2 text-xl font-medium">
                    Сотрудники, дни, ФОТ
                  </h3>
                </div>
                <div className="grid grid-cols-2 gap-2 text-right sm:min-w-[260px]">
                  <RosterTotal
                    label="Выручка"
                    value={formatRubles(roster.totalRevenue)}
                  />
                  <RosterTotal
                    label="ФОТ"
                    value={formatRubles(roster.totalLaborCost)}
                  />
                </div>
              </div>

              {roster.days.length > 0 ? (
                <div className="mt-5 overflow-x-auto">
                  <table className="w-full min-w-[960px] border-separate border-spacing-0 text-left">
                    <thead>
                      <tr className="text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
                        <th className="sticky left-0 z-10 w-[230px] bg-card/95 px-3 py-2 font-normal">
                          Сотрудник
                        </th>
                        {roster.days.map((day) => (
                          <th
                            key={day.dateKey}
                            className="w-[116px] px-2 py-2 text-center font-normal"
                          >
                            {day.label}
                          </th>
                        ))}
                        <th className="w-[168px] px-3 py-2 text-right font-normal">
                          Итог
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {roster.rows.map((row) => (
                        <tr key={row.member.id} className="align-top">
                          <td className="sticky left-0 z-10 border-t border-border/35 bg-card/95 px-3 py-3">
                            <div className="min-w-0">
                              <div className="flex flex-wrap items-center gap-2">
                                <p className="truncate text-sm font-medium">
                                  {row.member.name}
                                </p>
                                <Badge
                                  variant="outline"
                                  className={rosterRowStatusClass(row.status)}
                                >
                                  {rosterRowStatusLabel(row.status)}
                                </Badge>
                              </div>
                              <p className="mt-1 text-xs text-muted-foreground">
                                {row.roleTitle}
                              </p>
                            </div>
                          </td>
                          {row.cells.map((cell) => (
                            <td
                              key={`${row.member.id}-${cell.dateKey}`}
                              className="border-t border-border/35 px-2 py-3"
                            >
                              <RosterCell cell={cell} />
                            </td>
                          ))}
                          <td className="border-t border-border/35 px-3 py-3 text-right">
                            <p className="numeric text-sm font-medium text-foreground">
                              {formatRubles(row.revenue)}
                            </p>
                            <p className="mt-1 text-[11px] text-muted-foreground">
                              {formatHours(row.hours)} · ФОТ{" "}
                              {formatPct(row.laborCostPct)}
                            </p>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="mt-5 rounded-lg border border-border/45 bg-background/35 p-4">
                  <p className="text-sm font-medium">Смены не загрузились</p>
                  <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
                    {error ??
                      "Для сменной сетки нужны права iiko на смены за выбранный период."}
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function TeamShiftPlanVarianceSection({
  variance,
  laborSource,
  periodLabel,
}: {
  variance: TeamShiftPlanVarianceSummary;
  laborSource: TeamLaborLoadResult["source"];
  periodLabel: string;
}) {
  return (
    <section
      id="shift-plan-variance"
      className="scroll-mt-24 border-b border-border/40"
    >
      <div className="mx-auto grid max-w-7xl gap-5 px-6 py-8 lg:grid-cols-[0.56fr_1.44fr]">
        <div className="rounded-lg border border-border/60 bg-card/50 p-5">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-[11px] uppercase tracking-[0.22em] text-brand">
                План vs факт
              </p>
              <h2 className="mt-3 text-2xl font-medium">
                Где график разошелся с реальностью
              </h2>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                Сверяем график команды с фактическими сменами iiko: кто вышел без
                плана, кто не вышел и где ФОТ уехал по часам.
              </p>
            </div>
            <ClipboardCheck className="size-6 shrink-0 text-brand" />
          </div>

          <div className="mt-5 grid grid-cols-2 gap-3">
            <VarianceMetric
              label="Покрытие"
              value={`${variance.planCoveragePct}%`}
            />
            <VarianceMetric
              label="Вне графика"
              value={formatInteger(
                variance.unplannedActualShifts + variance.dayOffWorkedShifts,
              )}
            />
            <VarianceMetric
              label="Δ часы"
              value={formatSignedHours(variance.hoursDelta)}
            />
            <VarianceMetric
              label="Δ ФОТ"
              value={formatSignedRubles(variance.laborDelta)}
            />
          </div>

          <p className="mt-4 text-xs leading-relaxed text-muted-foreground">
            Источник факта: {laborSourceLabel(laborSource)} за {periodLabel}.
          </p>
        </div>

        <div className="rounded-lg border border-border/60 bg-card/50 p-5">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="text-[11px] uppercase tracking-[0.22em] text-muted-foreground">
                Отклонения
              </p>
              <h3 className="mt-2 text-xl font-medium">
                Что разобрать с управляющим
              </h3>
            </div>
            <p className="text-xs text-muted-foreground">
              план {variance.plannedShifts} · факт {variance.actualShifts}
            </p>
          </div>

          <div className="mt-5 grid gap-3">
            {variance.issues.length > 0 ? (
              variance.issues.map((issue) => (
                <ShiftPlanVarianceIssueRow key={issue.id} issue={issue} />
              ))
            ) : (
              <div className="rounded-lg border border-brand/25 bg-brand/10 p-4">
                <p className="text-sm font-medium text-foreground">
                  План и факт без критичных расхождений
                </p>
                <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
                  Если смены уже закрыты в iiko, можно переходить к разбору
                  выручки, ФОТ и маржи по сменам.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}

function VarianceMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-border/45 bg-background/35 p-3">
      <p className="numeric text-lg font-medium text-foreground">{value}</p>
      <p className="mt-1 text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
        {label}
      </p>
    </div>
  );
}

function ShiftPlanVarianceIssueRow({
  issue,
}: {
  issue: TeamShiftPlanVarianceIssue;
}) {
  return (
    <div className="grid gap-3 rounded-lg border border-border/45 bg-background/35 p-3 xl:grid-cols-[minmax(0,1fr)_auto] xl:items-center">
      <div className="min-w-0">
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="outline" className={varianceToneClass(issue.tone)}>
            {varianceStatusLabel(issue.status)}
          </Badge>
          <p className="text-sm font-medium text-foreground">
            {issue.member.name}
          </p>
          <span className="text-xs text-muted-foreground">
            {issue.roleTitle}
          </span>
        </div>
        <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
          {varianceIssueDetail(issue)}
        </p>
      </div>

      <div className="grid grid-cols-3 gap-2 text-[11px] text-muted-foreground sm:min-w-[340px]">
        <ShiftValue label="часы" value={formatSignedHours(issue.hoursDelta)} />
        <ShiftValue label="ФОТ" value={formatSignedRubles(issue.laborDelta)} />
        <ShiftValue label="выручка" value={formatRubles(issue.revenue)} />
      </div>
    </div>
  );
}

function varianceStatusLabel(
  status: Exclude<TeamShiftPlanVarianceStatus, "matched">,
): string {
  if (status === "day_off_worked") return "вышел в выходной";
  if (status === "unplanned_actual") return "без плана";
  if (status === "missed_plan") return "не вышел";
  if (status === "over_hours") return "сверх часов";
  if (status === "under_hours") return "меньше часов";
  return "нет ставки";
}

function varianceIssueDetail(issue: TeamShiftPlanVarianceIssue): string {
  const plan = `${issue.plannedShifts} план · ${formatHours(
    issue.plannedHours,
  )}`;
  const fact = `${issue.actualShifts} факт · ${formatHours(issue.actualHours)}`;

  if (issue.status === "day_off_worked") {
    return `${issue.dateLabel}: был выходной, но есть фактическая смена. ${fact}.`;
  }
  if (issue.status === "unplanned_actual") {
    return `${issue.dateLabel}: фактическая смена есть, в плане ее не было. ${fact}.`;
  }
  if (issue.status === "missed_plan") {
    return `${issue.dateLabel}: смена была в плане, но в iiko факта нет. ${plan}.`;
  }
  if (issue.status === "missing_rate") {
    return `${issue.dateLabel}: смена есть, но ФОТ не считается без ставки. ${plan} / ${fact}.`;
  }
  return `${issue.dateLabel}: ${plan} / ${fact}. Проверьте причину расхождения.`;
}

function varianceToneClass(tone: TeamShiftPlanVarianceTone): string {
  if (tone === "risk")
    return "border-destructive/35 bg-destructive/10 text-destructive";
  if (tone === "setup") {
    return "border-amber-400/35 bg-amber-400/10 text-amber-100";
  }
  if (tone === "watch") {
    return "border-[color:var(--pro)]/30 bg-[color:var(--pro)]/10 text-[color:var(--pro)]";
  }
  return "border-brand/35 bg-brand/10 text-brand";
}

function RosterTotal({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-border/45 bg-background/35 px-3 py-2">
      <p className="numeric text-sm font-medium text-foreground">{value}</p>
      <p className="mt-1 text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
        {label}
      </p>
    </div>
  );
}

function RosterCell({ cell }: { cell: TeamShiftRosterCell }) {
  if (cell.status === "no_shift") {
    return (
      <div className="h-[72px] rounded-lg border border-border/30 bg-background/20 px-2 py-2 text-center text-[11px] text-muted-foreground">
        —
      </div>
    );
  }

  return (
    <div
      className={
        "min-h-[72px] rounded-lg border px-2 py-2 " +
        rosterCellStatusClass(cell.status)
      }
    >
      <p className="numeric text-sm font-medium text-foreground">
        {formatRubles(cell.revenue)}
      </p>
      <p className="mt-1 truncate text-[11px] text-muted-foreground">
        {cell.timeLabels.join(", ")}
      </p>
      <p className="mt-1 text-[10px] uppercase tracking-[0.12em] text-muted-foreground">
        {formatHours(cell.hours)} · {formatInteger(cell.items)} поз.
      </p>
    </div>
  );
}

function rosterCellStatusClass(status: TeamShiftRosterCellStatus): string {
  if (status === "missing_rate") {
    return "border-amber-400/30 bg-amber-400/10";
  }
  if (status === "ready") {
    return "border-brand/25 bg-brand/10";
  }
  return "border-border/30 bg-background/20";
}

function rosterRowStatusLabel(status: TeamShiftRosterRowStatus): string {
  if (status === "ready") return "ФОТ есть";
  if (status === "missing_rate") return "нет ставки";
  return "нет смен";
}

function rosterRowStatusClass(status: TeamShiftRosterRowStatus): string {
  if (status === "ready") return "border-brand/35 bg-brand/10 text-brand";
  if (status === "missing_rate") {
    return "border-amber-400/30 bg-amber-400/10 text-amber-100";
  }
  return "border-border bg-muted/40 text-muted-foreground";
}

function RolePersonalBrief({
  member,
  tasks,
  checklist,
  learning,
  learningFallback,
  schedule,
  announcements,
  announcementReads,
  comments,
  laborSource,
  periodLabel,
  laborProfile,
}: {
  member: StaffMember | undefined;
  tasks: TeamTask[];
  checklist: string[];
  learning: TeamLearningMemberSummary | null;
  learningFallback: TeamLearningItem[];
  schedule: MemberShiftScheduleItem[];
  announcements: TeamAnnouncement[];
  announcementReads: TeamAnnouncementRead[];
  comments: TeamTaskComment[];
  laborSource: TeamLaborLoadResult["source"];
  periodLabel: string;
  laborProfile: MemberLaborProfile | null;
}) {
  if (!member) {
    return (
      <section className="border-b border-border/40">
        <div className="mx-auto max-w-7xl px-6 py-8">
          <div className="rounded-lg border border-border/60 bg-card/50 p-5">
            <p className="text-sm text-muted-foreground">
              Для этой роли пока нет сотрудника. Добавьте его в команду, чтобы
              появился личный кабинет.
            </p>
          </div>
        </div>
      </section>
    );
  }

  const role = getTeamRole(member.roleId);
  const openTasks = tasks.filter(isOpenTask);
  const urgentTasks = openTasks.filter((task) => task.priority === "high");
  const nextLearning = learning?.nextItem ?? learningFallback[0] ?? null;
  const learningPct = learning ? `${learning.averageBest}%` : "0%";
  const admissionStatus = learning?.admissionStatus ?? "not_started";
  const operationPlan = buildMemberOperationPlan({
    member,
    tasks,
    schedule,
    laborProfile,
    learning,
    announcements,
    announcementReads,
    nextLearning,
  });
  const secondBrainProfile = buildMemberSecondBrainProfile({
    member,
    tasks,
    comments,
    schedule,
    laborProfile,
    learning,
    nextLearning,
  });

  return (
    <section className="border-b border-border/40">
      <div className="mx-auto grid max-w-7xl gap-5 px-6 py-8 lg:grid-cols-[0.78fr_1.22fr]">
        <div className="rounded-lg border border-border/60 bg-card/50 p-5">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-[11px] uppercase tracking-[0.22em] text-brand">
                Личный кабинет
              </p>
              <h2 className="mt-3 text-2xl font-medium">{member.name}</h2>
              <p className="mt-2 text-sm text-muted-foreground">
                {role.title} · {member.shiftLabel || "смена не назначена"}
              </p>
            </div>
            <Badge
              variant="outline"
              className={learningAdmissionClass(admissionStatus)}
            >
              {learningAdmissionLabel(admissionStatus)}
            </Badge>
          </div>

          <div className="mt-5 grid grid-cols-3 gap-3">
            <PersonalMetric
              label="Открыто"
              value={formatInteger(openTasks.length)}
              detail="задач"
            />
            <PersonalMetric
              label="Срочно"
              value={formatInteger(urgentTasks.length)}
              detail="в фокусе"
            />
            <PersonalMetric
              label="Обучение"
              value={learningPct}
              detail="средний"
            />
          </div>

          <div className="mt-5 grid gap-2">
            {laborProfile ? (
              <MemberLaborProfileCard profile={laborProfile} />
            ) : null}
            <LinkButton
              href="#learning-progress"
              variant="outline"
              className="justify-between"
            >
              Открыть стандарты
              <ArrowRight className="size-4" />
            </LinkButton>
            <LinkButton
              href="#shift-coverage"
              variant="outline"
              className="justify-between"
            >
              Состав смены
              <ArrowRight className="size-4" />
            </LinkButton>
          </div>
        </div>

        <div className="grid gap-5">
          <MemberSecondBrainCard profile={secondBrainProfile} />

          <MemberOperationPlanCard items={operationPlan} />

          <details className="group border-t border-border/35 pt-2">
            <summary className="flex cursor-pointer list-none items-center justify-between gap-3 rounded-lg px-1 py-2 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground">
              <span>Подробности кабинета</span>
              <span className="flex flex-wrap items-center justify-end gap-2 text-[10px] uppercase tracking-[0.12em]">
                <span className="rounded-md border border-border/45 bg-card/45 px-2 py-1">
                  смен {formatInteger(schedule.length)}
                </span>
                <span className="rounded-md border border-border/45 bg-card/45 px-2 py-1">
                  задач {formatInteger(openTasks.length)}
                </span>
                <span className="rounded-md border border-border/45 bg-card/45 px-2 py-1">
                  чеклист {formatInteger(checklist.length)}
                </span>
              </span>
            </summary>

            <div className="mt-3 grid gap-5">
              <div className="rounded-lg border border-border/60 bg-card/50 p-5">
                <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                  <div className="flex items-center gap-3">
                    <CalendarDays className="size-5 text-brand" />
                    <div>
                      <h3 className="text-lg font-medium">Смены периода</h3>
                      <p className="mt-1 text-xs text-muted-foreground">
                        {periodLabel} · {laborSourceLabel(laborSource)}
                      </p>
                    </div>
                  </div>
                  <Badge variant="outline">{schedule.length}</Badge>
                </div>

                <div className="mt-4 grid gap-2">
                  {schedule.length > 0 ? (
                    schedule.map((shift) => (
                      <MemberShiftRow key={shift.shiftId} shift={shift} />
                    ))
                  ) : (
                    <div className="rounded-lg border border-border/45 bg-background/35 p-3">
                      <p className="text-sm font-medium">
                        Смен по сотруднику нет
                      </p>
                      <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
                        Если сотрудник был на смене, проверьте совпадение имени
                        в iiko и карточках сотрудников или права на выгрузку смен.
                      </p>
                    </div>
                  )}
                </div>
              </div>

              <div className="grid gap-5 lg:grid-cols-2">
                <div className="rounded-lg border border-border/60 bg-card/50 p-5">
                  <div className="flex items-center gap-3">
                    <ClipboardCheck className="size-5 text-brand" />
                    <h3 className="text-lg font-medium">На смену</h3>
                  </div>
                  <div className="mt-4 grid gap-2">
                    {checklist.map((item) => (
                      <div
                        key={item}
                        className="rounded-lg border border-border/45 bg-background/35 p-3 text-[13px] leading-relaxed text-foreground/85"
                      >
                        {item}
                      </div>
                    ))}
                    {nextLearning ? (
                      <Link
                        href="#learning-progress"
                        className="rounded-lg border border-brand/25 bg-brand/10 p-3 transition-colors hover:border-brand/45"
                      >
                        <p className="text-[10px] uppercase tracking-[0.16em] text-brand">
                          Следующий стандарт
                        </p>
                        <p className="mt-1 text-sm font-medium">
                          {nextLearning.title}
                        </p>
                        <p className="mt-1 text-xs text-muted-foreground">
                          {nextLearning.timeLabel}
                        </p>
                      </Link>
                    ) : null}
                  </div>
                </div>

                <div className="rounded-lg border border-border/60 bg-card/50 p-5">
                  <div className="flex items-center justify-between gap-3">
                    <div className="flex items-center gap-3">
                      <ClipboardList className="size-5 text-brand" />
                      <h3 className="text-lg font-medium">Мои задачи</h3>
                    </div>
                    <Badge variant="outline">{openTasks.length}</Badge>
                  </div>
                  <div className="mt-4 grid gap-3">
                    {openTasks.slice(0, 3).map((task) => (
                      <TaskRow key={task.id} task={task} compact />
                    ))}
                    {openTasks.length === 0 ? (
                      <div className="rounded-lg border border-border/45 bg-background/35 p-3">
                        <p className="text-sm font-medium">Задач нет</p>
                        <p className="mt-1 text-xs text-muted-foreground">
                          Можно принимать смену без незакрытой очереди.
                        </p>
                      </div>
                    ) : null}
                  </div>
                </div>
              </div>
            </div>
          </details>
        </div>
      </div>
    </section>
  );
}

function MemberSecondBrainCard({
  profile,
}: {
  profile: MemberSecondBrainProfile;
}) {
  return (
    <div className="rounded-lg border border-brand/25 bg-card/55 p-5">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-start gap-3">
          <SearchCheck className="mt-0.5 size-5 text-brand" />
          <div>
            <p className="text-[11px] uppercase tracking-[0.22em] text-brand">
              Профиль сотрудника
            </p>
            <h3 className="mt-2 text-lg font-medium">{profile.title}</h3>
            <p className="mt-1 text-sm leading-relaxed text-muted-foreground">
              {profile.summary}
            </p>
          </div>
        </div>
        <div className="flex flex-wrap gap-2 sm:justify-end">
          {profile.tags.map((tag) => (
            <Badge key={tag} variant="outline">
              {tag}
            </Badge>
          ))}
        </div>
      </div>

      <div className="mt-4 grid gap-2 md:grid-cols-2">
        {profile.facts.map((fact) => (
          <MemberSecondBrainFactRow key={fact.label} fact={fact} />
        ))}
      </div>

      <div className="mt-4 rounded-lg border border-border/45 bg-background/35 p-3">
        <p className="text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
          Следующий вопрос
        </p>
        <p className="mt-1 text-sm leading-relaxed text-foreground/90">
          {profile.nextQuestion}
        </p>
      </div>
    </div>
  );
}

function MemberSecondBrainFactRow({
  fact,
}: {
  fact: MemberSecondBrainFact;
}) {
  return (
    <div
      className={
        "rounded-lg border p-3 " + memberSecondBrainToneClass(fact.tone)
      }
    >
      <p className="text-[10px] uppercase tracking-[0.15em] opacity-75">
        {fact.label}
      </p>
      <p className="mt-1 text-sm font-medium">{fact.value}</p>
      <p className="mt-1 text-xs leading-relaxed opacity-80">{fact.detail}</p>
    </div>
  );
}

function memberSecondBrainToneClass(tone: MemberSecondBrainTone): string {
  if (tone === "risk") {
    return "border-destructive/30 bg-destructive/10 text-destructive";
  }
  if (tone === "setup") {
    return "border-amber-400/30 bg-amber-400/10 text-amber-100";
  }
  if (tone === "work") {
    return "border-[color:var(--pro)]/30 bg-[color:var(--pro)]/10 text-[color:var(--pro)]";
  }
  return "border-brand/30 bg-brand/10 text-brand";
}

function MemberOperationPlanCard({
  items,
}: {
  items: MemberOperationPlanItem[];
}) {
  return (
    <div className="rounded-lg border border-border/60 bg-card/50 p-5">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-center gap-3">
          <ListChecks className="size-5 text-brand" />
          <div>
            <h3 className="text-lg font-medium">Что сделать сейчас</h3>
            <p className="mt-1 text-xs text-muted-foreground">
              План собран из смен, ФОТ, обучения и задач.
            </p>
          </div>
        </div>
        <Badge variant="outline">{items.length}</Badge>
      </div>

      <div className="mt-4 grid gap-2">
        {items.map((item) => (
          <Link
            key={item.id}
            href={item.href}
            className="grid gap-3 rounded-lg border border-border/45 bg-background/35 p-3 transition-colors hover:border-brand/35 hover:bg-background/55 sm:grid-cols-[auto_1fr_auto] sm:items-center"
          >
            <span
              className={
                "size-2 rounded-full border " +
                memberOperationPlanToneDotClass(item.tone)
              }
            />
            <span className="min-w-0">
              <span className="block text-sm font-medium text-foreground">
                {item.title}
              </span>
              <span className="mt-1 block text-xs leading-relaxed text-muted-foreground sm:truncate">
                {item.detail}
              </span>
            </span>
            <span
              className={
                "rounded-md border px-2 py-1 text-[10px] uppercase tracking-[0.12em] " +
                memberOperationPlanToneClass(item.tone)
              }
            >
              {item.badge}
            </span>
          </Link>
        ))}
      </div>
    </div>
  );
}

function memberOperationPlanToneDotClass(
  tone: MemberOperationPlanTone,
): string {
  if (tone === "risk") return "border-destructive bg-destructive";
  if (tone === "setup") return "border-amber-200 bg-amber-200";
  if (tone === "work") return "border-[color:var(--pro)] bg-[color:var(--pro)]";
  return "border-brand bg-brand";
}

function memberOperationPlanToneClass(tone: MemberOperationPlanTone): string {
  if (tone === "risk")
    return "border-destructive/30 bg-destructive/10 text-destructive";
  if (tone === "setup")
    return "border-amber-400/30 bg-amber-400/10 text-amber-100";
  if (tone === "work")
    return "border-[color:var(--pro)]/30 bg-[color:var(--pro)]/10 text-[color:var(--pro)]";
  return "border-brand/30 bg-brand/10 text-brand";
}

function MemberLaborProfileCard({ profile }: { profile: MemberLaborProfile }) {
  return (
    <div className="rounded-lg border border-border/45 bg-background/35 p-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-[11px] uppercase tracking-[0.16em] text-muted-foreground">
          Экономика сотрудника
        </p>
        <Badge
          variant="outline"
          className={memberLaborStatusClass(profile.status)}
        >
          {memberLaborStatusLabel(profile.status)}
        </Badge>
      </div>
      <div className="mt-3 grid grid-cols-3 gap-2">
        <PersonalMetric
          label="Выручка"
          value={formatRubles(profile.sales)}
          detail={`${formatInteger(profile.shifts)} смен`}
        />
        <PersonalMetric
          label="ФОТ"
          value={formatRubles(profile.laborCost)}
          detail={formatPct(profile.laborCostPct)}
        />
        <PersonalMetric
          label="₽ / час"
          value={
            profile.revenuePerHour ? formatRubles(profile.revenuePerHour) : "—"
          }
          detail={formatHours(profile.hours)}
        />
      </div>
      {profile.status !== "ready" ? (
        <p className="mt-3 text-xs leading-relaxed text-muted-foreground">
          {profile.status === "missing_rate"
            ? "Ставка не закрыта: ФОТ и прибыль по этому сотруднику пока нельзя считать точными."
            : "В выбранном периоде нет смен этого сотрудника из iiko."}
        </p>
      ) : null}
    </div>
  );
}

function memberLaborStatusLabel(status: MemberLaborProfileStatus): string {
  if (status === "ready") return "считается";
  if (status === "missing_rate") return "нет ставки";
  return "нет смен";
}

function memberLaborStatusClass(status: MemberLaborProfileStatus): string {
  if (status === "ready") return "border-brand/35 bg-brand/10 text-brand";
  if (status === "missing_rate") {
    return "border-amber-400/30 bg-amber-400/10 text-amber-100";
  }
  return "border-border bg-muted/40 text-muted-foreground";
}

function MemberShiftRow({ shift }: { shift: MemberShiftScheduleItem }) {
  return (
    <div className="grid gap-3 rounded-lg border border-border/45 bg-background/35 p-3 sm:grid-cols-[1fr_auto] sm:items-center">
      <div className="min-w-0">
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="outline">{shift.dayLabel}</Badge>
          <p className="text-sm font-medium">{shift.timeLabel}</p>
        </div>
        <p className="mt-1 text-xs text-muted-foreground">
          {formatInteger(shift.items)} позиций · {formatHours(shift.hours)}
        </p>
      </div>
      <div className="numeric text-sm font-medium text-foreground sm:text-right">
        {formatRubles(shift.revenue)}
      </div>
    </div>
  );
}

function PersonalMetric({
  label,
  value,
  detail,
}: {
  label: string;
  value: string;
  detail: string;
}) {
  return (
    <div className="rounded-lg border border-border/45 bg-background/35 p-3">
      <p className="numeric text-xl font-medium text-foreground">{value}</p>
      <p className="mt-1 text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
        {label}
      </p>
      <p className="mt-1 text-[11px] text-muted-foreground">{detail}</p>
    </div>
  );
}

function formatPct(value: number | null): string {
  if (value === null) return "—";
  return `${value.toLocaleString("ru-RU", { maximumFractionDigits: 1 })}%`;
}

function formatHours(value: number): string {
  return `${value.toLocaleString("ru-RU", { maximumFractionDigits: 1 })} ч`;
}

function formatSignedHours(value: number): string {
  if (value === 0) return formatHours(0);
  return `${value > 0 ? "+" : "-"}${formatHours(Math.abs(value))}`;
}

function formatSignedRubles(value: number): string {
  if (value === 0) return formatRubles(0);
  return `${value > 0 ? "+" : "-"}${formatRubles(Math.abs(value))}`;
}

function formatShiftDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value.slice(0, 10);

  return new Intl.DateTimeFormat("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function laborSourceLabel(source: TeamLaborLoadResult["source"]): string {
  if (source === "live") return "живые смены iiko";
  if (source === "demo") return "тестовые смены";
  return "смены недоступны";
}

function ShiftMetric({
  icon,
  label,
  value,
}: {
  icon: ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-lg border border-border/45 bg-background/35 p-3">
      <div className="flex items-center justify-between gap-2 text-brand">
        <span className="text-muted-foreground">{icon}</span>
        <span className="text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
          {label}
        </span>
      </div>
      <p className="numeric mt-3 text-lg font-medium text-foreground">
        {value}
      </p>
    </div>
  );
}

function TeamDailyWorkflowStrip({ steps }: { steps: TeamDailyWorkflowStep[] }) {
  return (
    <div className="grid gap-4 lg:grid-cols-[220px_1fr] lg:items-start">
      <div>
        <p className="text-[11px] uppercase tracking-[0.22em] text-brand">
          Ритм дня
        </p>
        <h2 className="mt-2 text-xl font-medium">Как ведем смену</h2>
        <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
          Один маршрут: подготовить, обучить, собрать факт и принять решение.
        </p>
      </div>
      <div className="grid gap-2 md:grid-cols-2 xl:grid-cols-4">
        {steps.map((step) => (
          <TeamDailyWorkflowStepLink key={step.id} step={step} />
        ))}
      </div>
    </div>
  );
}

function TeamDailyWorkflowStepLink({
  step,
}: {
  step: TeamDailyWorkflowStep;
}) {
  return (
    <Link
      href={step.href}
      className="group flex min-h-[150px] flex-col justify-between rounded-lg border border-border/55 bg-card/45 p-4 transition-colors hover:border-brand/40 hover:bg-card/70"
    >
      <div>
        <div className="flex items-center justify-between gap-3">
          <span
            className={
              "rounded-md border px-2 py-1 text-[10px] uppercase tracking-[0.12em] " +
              dailyWorkflowToneClass(step.tone)
            }
          >
            {step.label}
          </span>
          <ArrowRight className="size-4 text-muted-foreground transition-transform group-hover:translate-x-0.5 group-hover:text-brand" />
        </div>
        <h3 className="mt-3 text-sm font-medium leading-snug text-foreground">
          {step.title}
        </h3>
      </div>
      <p className="mt-3 line-clamp-3 text-xs leading-relaxed text-muted-foreground">
        {step.detail}
      </p>
    </Link>
  );
}

function dailyWorkflowToneClass(tone: TeamDailyWorkflowTone): string {
  if (tone === "risk")
    return "border-destructive/30 bg-destructive/10 text-destructive";
  if (tone === "work") return "border-brand/30 bg-brand/10 text-brand";
  return "border-[color:var(--pro)]/30 bg-[color:var(--pro)]/10 text-[color:var(--pro)]";
}

function TeamShiftMemorySection({
  digest,
  readiness,
}: {
  digest: TeamFieldContextDigest | null;
  readiness: FieldNoteReadinessSummary;
}) {
  return (
    <section
      id="shift-summary"
      className="scroll-mt-24 border-b border-border/40"
    >
      <div className="mx-auto grid max-w-7xl gap-5 px-6 py-7 lg:grid-cols-[0.72fr_1.28fr]">
        <div>
          <p className="text-[11px] uppercase tracking-[0.22em] text-brand">
            Память смены
          </p>
          <h2 className="mt-2 text-2xl font-medium">
            Что команда заметила на поле
          </h2>
          <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
            Цифры объясняют результат, но причина часто живет в коротком итоге
            смены.
          </p>
        </div>

        <div className="rounded-lg border border-border/60 bg-card/50 p-5">
          {digest ? (
            <div className="grid gap-4">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <p className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
                    Главный сигнал
                  </p>
                  <p className="mt-2 text-sm leading-relaxed text-foreground">
                    {digest.summary}
                  </p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <Badge variant="outline">{digest.totalNotes} заметок</Badge>
                  <Badge
                    variant="outline"
                    className={
                      readiness.complete > 0
                        ? "border-brand/30 text-brand"
                        : "border-amber-400/30 text-amber-200"
                    }
                  >
                    Полных итогов {readiness.complete}/{readiness.total}
                  </Badge>
                </div>
              </div>
              {readiness.complete === 0 ? (
                <div className="rounded-lg border border-amber-400/25 bg-amber-400/10 p-3 text-[12px] leading-relaxed text-amber-100">
                  <p>
                    Чтобы советник понял смену, добавьте в итог:{" "}
                    {readiness.bestMissing.join(", ")}.
                  </p>
                  <div className="mt-2 grid gap-1.5 sm:grid-cols-2">
                    {readiness.followUpQuestions.map((question) => (
                      <span
                        key={question}
                        className="rounded-md border border-amber-300/20 bg-background/30 px-2 py-1.5"
                      >
                        {question}
                      </span>
                    ))}
                  </div>
                </div>
              ) : null}
              <div className="flex flex-wrap gap-2">
                {digest.signals.map((signal) => (
                  <span
                    key={signal.kind}
                    className="rounded-md border border-brand/25 bg-brand/10 px-2.5 py-1 text-[11px] text-brand"
                  >
                    {signal.title} · {signal.sourceCount}
                  </span>
                ))}
              </div>
            </div>
          ) : (
            <div className="grid gap-3">
              <p className="text-sm font-medium text-foreground">
                Итог смены еще не собран
              </p>
              <p className="text-sm leading-relaxed text-muted-foreground">
                После смены попросите коротко зафиксировать: посадку, гостей,
                стоп-лист, конфликт, погоду, что продавали и что проверить
                утром.
              </p>
              <div className="grid gap-1.5 sm:grid-cols-2">
                {readiness.followUpQuestions.map((question) => (
                  <span
                    key={question}
                    className="rounded-md border border-border/50 bg-background/35 px-2.5 py-2 text-[12px] leading-relaxed text-muted-foreground"
                  >
                    {question}
                  </span>
                ))}
              </div>
            </div>
          )}

          <div className="mt-4 flex flex-wrap gap-2">
            <LinkButton href="#team-actions" variant="outline">
              Открыть задачи и заметки
              <ArrowRight className="size-4" />
            </LinkButton>
            <LinkButton href="#learning-progress" variant="outline">
              Связать с обучением
            </LinkButton>
          </div>
        </div>
      </div>
    </section>
  );
}

function shiftDiagnosticToneClass(tone: LaborShiftDiagnostic["tone"]): string {
  if (tone === "risk")
    return "border-destructive/30 bg-destructive/10 text-destructive";
  if (tone === "setup")
    return "border-amber-400/30 bg-amber-400/10 text-amber-100";
  if (tone === "watch")
    return "border-[color:var(--pro)]/30 bg-[color:var(--pro)]/10 text-[color:var(--pro)]";
  return "border-brand/30 bg-brand/10 text-brand";
}

function shiftDiagnosticHref(shift: LaborShiftDiagnostic): string {
  if (shift.kind === "missing-rates") return "#labor-rates";
  return "#shift-coverage";
}

function ShiftDiagnosticRow({ shift }: { shift: LaborShiftDiagnostic }) {
  return (
    <Link
      href={shiftDiagnosticHref(shift)}
      className="grid gap-3 rounded-lg border border-border/45 bg-background/35 p-3 transition-colors hover:border-brand/35 hover:bg-background/55 xl:grid-cols-[minmax(0,1fr)_auto] xl:items-center"
    >
      <div className="min-w-0">
        <div className="flex flex-wrap items-center gap-2">
          <span
            className={
              "rounded-md border px-2 py-1 text-[10px] uppercase tracking-[0.12em] " +
              shiftDiagnosticToneClass(shift.tone)
            }
          >
            {formatShiftDate(shift.openTime)}
          </span>
          <p className="text-sm font-medium text-foreground">{shift.title}</p>
        </div>
        <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
          {shift.detail}
        </p>
        <p className="mt-1 text-xs leading-relaxed text-foreground/85">
          {shift.action}
        </p>
      </div>

      <div className="grid grid-cols-2 gap-2 text-[11px] text-muted-foreground sm:grid-cols-4 xl:min-w-[420px]">
        <ShiftValue label="выручка" value={formatRubles(shift.revenue)} />
        <ShiftValue label="ФОТ" value={formatPct(shift.laborCostPct)} />
        <ShiftValue label="часы" value={formatHours(shift.hours)} />
        <ShiftValue
          label="без ставок"
          value={formatInteger(shift.missingRates)}
        />
      </div>
    </Link>
  );
}

function EmployeeLaborDiagnostics({
  diagnostics,
  employeeCount,
  roleId,
  venueId,
  period,
}: {
  diagnostics: LaborEmployeeDiagnostic[];
  employeeCount: number;
  roleId: TeamRoleId;
  venueId: string;
  period: Period;
}) {
  return (
    <div className="mt-5 border-t border-border/35 pt-5">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-[11px] uppercase tracking-[0.22em] text-muted-foreground">
            Сотрудники
          </p>
          <h3 className="mt-2 text-lg font-medium">Кого разобрать по ФОТ</h3>
        </div>
        <p className="text-xs text-muted-foreground">
          {formatInteger(employeeCount)} в сменах
        </p>
      </div>

      <div className="mt-3 grid gap-2">
        {diagnostics.length > 0 ? (
          diagnostics.map((employee) => (
            <EmployeeLaborDiagnosticRow
              key={employee.memberId ?? employee.name}
              employee={employee}
              roleId={roleId}
              venueId={venueId}
              period={period}
            />
          ))
        ) : (
          <div className="rounded-lg border border-brand/25 bg-brand/10 p-3">
            <p className="text-sm font-medium text-foreground">
              Явных рисков по сотрудникам не видно
            </p>
            <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
              Ставки и выручка на час выглядят управляемо. Дальше разбирайте
              смены, маржу и план/факт.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

function EmployeeLaborDiagnosticRow({
  employee,
  roleId,
  venueId,
  period,
}: {
  employee: LaborEmployeeDiagnostic;
  roleId: TeamRoleId;
  venueId: string;
  period: Period;
}) {
  const targetRole = employee.roleId ?? roleId;

  return (
    <Link
      href={employeeDiagnosticHref({
        employee,
        roleId: targetRole,
        venueId,
        period,
      })}
      className="grid gap-3 rounded-lg border border-border/45 bg-background/35 p-3 transition-colors hover:border-brand/35 hover:bg-background/55 xl:grid-cols-[minmax(0,1fr)_auto] xl:items-center"
    >
      <div className="min-w-0">
        <div className="flex flex-wrap items-center gap-2">
          <span
            className={
              "rounded-md border px-2 py-1 text-[10px] uppercase tracking-[0.12em] " +
              employeeDiagnosticToneClass(employee.tone)
            }
          >
            {employeeDiagnosticKindLabel(employee.kind)}
          </span>
          <p className="text-sm font-medium text-foreground">{employee.name}</p>
          <span className="text-xs text-muted-foreground">
            {employee.roleId ? getTeamRole(employee.roleId).title : "iiko"}
          </span>
        </div>
        <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
          {employee.detail}
        </p>
        <p className="mt-1 text-xs leading-relaxed text-foreground/85">
          {employee.action}
        </p>
      </div>

      <div className="grid grid-cols-2 gap-2 text-[11px] text-muted-foreground sm:grid-cols-4 xl:min-w-[420px]">
        <ShiftValue label="выручка" value={formatRubles(employee.sales)} />
        <ShiftValue label="ФОТ" value={formatPct(employee.laborCostPct)} />
        <ShiftValue
          label="₽ / час"
          value={
            employee.revenuePerHour
              ? formatRubles(employee.revenuePerHour)
              : "—"
          }
        />
        <ShiftValue label="смен" value={formatInteger(employee.shifts)} />
      </div>
    </Link>
  );
}

function employeeDiagnosticHref(input: {
  employee: LaborEmployeeDiagnostic;
  roleId: TeamRoleId;
  venueId: string;
  period: Period;
}): string {
  if (input.employee.memberId) {
    return `${teamHref(
      input.venueId,
      input.roleId,
      input.period,
      input.employee.memberId,
    )}#labor-member-${encodeURIComponent(input.employee.memberId)}`;
  }

  if (input.employee.kind === "missing-rate") return "#team-actions";
  return "#iiko-shift-diagnostics";
}

function employeeDiagnosticToneClass(
  tone: LaborEmployeeDiagnostic["tone"],
): string {
  if (tone === "risk")
    return "border-destructive/30 bg-destructive/10 text-destructive";
  if (tone === "setup")
    return "border-amber-400/30 bg-amber-400/10 text-amber-100";
  if (tone === "watch")
    return "border-[color:var(--pro)]/30 bg-[color:var(--pro)]/10 text-[color:var(--pro)]";
  return "border-brand/30 bg-brand/10 text-brand";
}

function employeeDiagnosticKindLabel(
  kind: LaborEmployeeDiagnostic["kind"],
): string {
  if (kind === "missing-rate") return "нет ставки";
  if (kind === "expensive-employee") return "дорого";
  if (kind === "low-productivity") return "низкий час";
  return "норма";
}

function ShiftValue({ label, value }: { label: string; value: string }) {
  return (
    <span className="rounded-md border border-border/45 bg-card/45 px-2 py-1.5">
      <span className="block text-[10px] uppercase tracking-[0.12em] text-muted-foreground">
        {label}
      </span>
      <span className="numeric mt-1 block font-mono text-[12px] text-foreground">
        {value}
      </span>
    </span>
  );
}

function coverageStatusLabel(status: ShiftRoleCoverage["status"]): string {
  if (status === "covered") return "закрыто";
  if (status === "invited") return "ждет входа";
  return "нет человека";
}

function coverageStatusClass(status: ShiftRoleCoverage["status"]): string {
  if (status === "covered") {
    return "border-brand/35 bg-brand/10 text-brand";
  }
  if (status === "invited") {
    return "border-[color:var(--pro)]/30 bg-[color:var(--pro)]/10 text-[color:var(--pro)]";
  }
  return "border-amber-400/30 bg-amber-400/10 text-amber-100";
}

function ShiftCoverageRow({ coverage }: { coverage: ShiftRoleCoverage }) {
  const names = coverage.staff.map((member) => member.name).join(", ");
  const shift = coverage.shiftLabels.join(", ");

  return (
    <div className="grid gap-3 rounded-lg border border-border/45 bg-background/35 p-3 sm:grid-cols-[1fr_auto] sm:items-center">
      <div className="min-w-0">
        <div className="flex flex-wrap items-center gap-2">
          <p className="text-sm font-medium">{coverage.title}</p>
          <Badge
            variant="outline"
            className={coverageStatusClass(coverage.status)}
          >
            {coverageStatusLabel(coverage.status)}
          </Badge>
        </div>
        <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
          {names || "Сотрудник не назначен"}
          {shift ? ` · ${shift}` : ""}
        </p>
      </div>
      <div className="flex flex-wrap gap-2 text-[11px] uppercase tracking-[0.14em] text-muted-foreground sm:justify-end">
        <span className="rounded-md border border-border/50 bg-card/45 px-2 py-1">
          задач {coverage.openTasks}
        </span>
        {coverage.importantTasks > 0 ? (
          <span className="rounded-md border border-destructive/30 bg-destructive/10 px-2 py-1 text-destructive">
            важно {coverage.importantTasks}
          </span>
        ) : null}
      </div>
    </div>
  );
}

function LearningFocusPanel({ items }: { items: TeamLearningFocusItem[] }) {
  return (
    <div className="rounded-lg border border-brand/25 bg-card/55 p-5">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-start gap-3">
          <GraduationCap className="mt-0.5 size-5 text-brand" />
          <div>
            <p className="text-[11px] uppercase tracking-[0.22em] text-brand">
              Что учить сегодня
            </p>
            <h2 className="mt-2 text-xl font-medium">Фокус обучения</h2>
            <p className="mt-2 max-w-2xl text-sm leading-relaxed text-muted-foreground">
              Система поднимает стандарты из заметок смены, задач и допуска к
              работе.
            </p>
          </div>
        </div>
        <Badge variant="outline">
          {formatInteger(items.length)} приоритета
        </Badge>
      </div>

      <div className="mt-5 grid gap-3 lg:grid-cols-2">
        {items.map((item) => (
          <LearningFocusCard key={item.id} item={item} />
        ))}
      </div>
    </div>
  );
}

function LearningFocusCard({ item }: { item: TeamLearningFocusItem }) {
  return (
    <Link
      href={item.href}
      className="grid gap-3 rounded-lg border border-border/45 bg-background/35 p-4 transition-colors hover:border-brand/40 hover:bg-background/55"
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span
              className={
                "rounded-md border px-2 py-1 text-[10px] uppercase tracking-[0.12em] " +
                learningFocusToneClass(item.tone)
              }
            >
              {learningFocusToneLabel(item.tone)}
            </span>
            <p className="text-sm font-medium text-foreground">{item.title}</p>
          </div>
          <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
            {item.reason}
          </p>
        </div>
        <ArrowRight className="size-4 shrink-0 text-muted-foreground" />
      </div>

      <div className="rounded-lg border border-border/35 bg-card/40 p-3">
        <p className="text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
          Материал
        </p>
        <p className="mt-1 text-sm font-medium text-foreground">
          {item.moduleTitle}
        </p>
        <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
          {item.detail}
        </p>
      </div>
    </Link>
  );
}

function learningFocusToneLabel(tone: TeamLearningFocusTone): string {
  if (tone === "risk") return "допуск";
  if (tone === "field") return "поле";
  if (tone === "setup") return "стандарт";
  return "развитие";
}

function learningFocusToneClass(tone: TeamLearningFocusTone): string {
  if (tone === "risk")
    return "border-destructive/30 bg-destructive/10 text-destructive";
  if (tone === "field") return "border-brand/30 bg-brand/10 text-brand";
  if (tone === "setup")
    return "border-amber-400/30 bg-amber-400/10 text-amber-100";
  return "border-[color:var(--pro)]/30 bg-[color:var(--pro)]/10 text-[color:var(--pro)]";
}

function LearningRolePlanGrid({
  venueId,
  plans,
  tasks,
}: {
  venueId: string;
  plans: TeamLearningRolePlan[];
  tasks: TeamTask[];
}) {
  const visiblePlans = plans.filter(
    (plan) => plan.members > 0 || plan.totalItems > 0,
  );

  return (
    <div className="rounded-lg border border-border/60 bg-card/50 p-5">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-[11px] uppercase tracking-[0.22em] text-muted-foreground">
            Учебный план
          </p>
          <h2 className="mt-2 text-xl font-medium">Материалы по ролям</h2>
          <p className="mt-2 max-w-2xl text-sm leading-relaxed text-muted-foreground">
            Управляющий видит, какие стандарты нужны каждой роли и кто не
            допущен к смене по обязательным материалам.
          </p>
        </div>
        <Badge variant="outline">{visiblePlans.length} ролей</Badge>
      </div>

      <div className="mt-5 grid gap-3 lg:grid-cols-2">
        {visiblePlans.map((plan) => (
          <LearningRolePlanCard
            key={plan.roleId}
            venueId={venueId}
            plan={plan}
            tasks={tasks}
          />
        ))}
      </div>
    </div>
  );
}

function LearningRolePlanCard({
  venueId,
  plan,
  tasks,
}: {
  venueId: string;
  plan: TeamLearningRolePlan;
  tasks: TeamTask[];
}) {
  const taskDraft = buildLearningAdmissionTaskDraft(plan);
  const existingTask = taskDraft
    ? findOpenLearningAdmissionTask(tasks, taskDraft)
    : null;
  const blockedLabel =
    plan.blockedMembers.length > 0
      ? plan.blockedMembers
          .slice(0, 3)
          .map((member) => member.memberName)
          .join(", ")
      : "обязательные закрыты";

  return (
    <div className="rounded-lg border border-border/45 bg-background/35 p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="text-sm font-medium text-foreground">
              {plan.roleTitle}
            </h3>
            <Badge variant="outline">{formatInteger(plan.members)} чел.</Badge>
          </div>
          <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
            {formatInteger(plan.totalItems)} материалов · обязательных{" "}
            {formatInteger(plan.requiredItems)}
            {plan.customStandards > 0
              ? ` · настроено ${formatInteger(plan.customStandards)}`
              : ""}
          </p>
        </div>
        <Badge
          variant="outline"
          className={rolePlanAdmissionClass(plan.admissionPct)}
        >
          допуск {plan.admissionPct}%
        </Badge>
      </div>

      <div className="mt-4 grid grid-cols-3 gap-2">
        <ReadinessMetric label="обяз." value={`${plan.requiredProgressPct}%`} />
        <ReadinessMetric
          label="готово"
          value={formatInteger(plan.readyItems)}
        />
        <ReadinessMetric label="скоро" value={formatInteger(plan.soonItems)} />
      </div>

      <div className="mt-4 rounded-lg border border-border/40 bg-card/40 p-3">
        <p className="text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
          Следующий фокус
        </p>
        <p className="mt-1 text-sm font-medium text-foreground">
          {plan.nextItem ? plan.nextItem.title : "Роль закрыта по материалам"}
        </p>
        <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
          {plan.nextItem
            ? `${learningItemStatusLabel(plan.nextItem.status)} · ${plan.nextItem.timeLabel} · проходной ${plan.nextItem.passPercentage}%`
            : "Новые материалы можно добавить позже под стандарты заведения."}
        </p>
      </div>

      <details className="group mt-3 border-t border-border/35 pt-3">
        <summary className="flex cursor-pointer list-none items-center justify-between gap-3 text-xs font-medium text-muted-foreground transition-colors hover:text-foreground">
          <span>Настройка стандарта роли</span>
          <span className="rounded-md border border-border/45 bg-card/45 px-2 py-1 text-[10px] uppercase tracking-[0.14em]">
            {plan.customStandards > 0
              ? `${formatInteger(plan.customStandards)} измен.`
              : "база"}
          </span>
        </summary>
        <div className="mt-3 grid gap-2">
          {plan.items.map((item) => (
            <div
              key={item.id}
              className="grid gap-2 border-t border-border/25 py-2 first:border-t-0 first:pt-0 sm:grid-cols-[1fr_auto] sm:items-center"
            >
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <p className="truncate text-xs font-medium text-foreground">
                    {item.title}
                  </p>
                  <Badge
                    variant="outline"
                    className={learningStandardStatusClass(item.status)}
                  >
                    {learningItemStatusLabel(item.status)}
                  </Badge>
                </div>
                <p className="mt-1 text-[11px] leading-relaxed text-muted-foreground">
                  {item.timeLabel} · проходной {item.passPercentage}%
                </p>
              </div>
              <form
                action={saveTeamLearningStandardFormAction}
                className="flex flex-wrap gap-1 sm:justify-end"
              >
                <input type="hidden" name="venueId" value={venueId} />
                <input type="hidden" name="roleId" value={plan.roleId} />
                <input type="hidden" name="moduleId" value={item.id} />
                <button
                  type="submit"
                  name="status"
                  value="required"
                  disabled={item.status === "required"}
                  className={learningStandardButtonClass(
                    item.status === "required",
                  )}
                >
                  Допуск
                </button>
                <button
                  type="submit"
                  name="status"
                  value="ready"
                  disabled={item.status === "ready"}
                  className={learningStandardButtonClass(
                    item.status === "ready",
                  )}
                >
                  Развитие
                </button>
              </form>
            </div>
          ))}
        </div>
      </details>

      <div className="mt-3 flex flex-wrap items-center justify-between gap-2">
        <p className="text-xs leading-relaxed text-muted-foreground">
          Не допущены:{" "}
          <span className="text-foreground/85">{blockedLabel}</span>
        </p>
        {existingTask ? (
          <Link
            href="#team-actions"
            className="inline-flex items-center gap-2 rounded-md border border-brand/25 bg-brand/10 px-3 py-2 text-xs font-medium text-brand transition hover:border-brand/45 hover:bg-brand/15"
          >
            <CheckCircle2 className="size-3.5" />
            <span>Задача уже есть</span>
            <span className="text-muted-foreground">
              {statusLabel(existingTask.status)}
            </span>
          </Link>
        ) : taskDraft ? (
          <LearningAdmissionTaskButton venueId={venueId} draft={taskDraft} />
        ) : null}
      </div>
    </div>
  );
}

function learningItemStatusLabel(status: TeamLearningItem["status"]): string {
  if (status === "required") return "обязательно";
  if (status === "ready") return "готово";
  return "скоро";
}

function learningStandardStatusClass(
  status: TeamLearningItem["status"],
): string {
  if (status === "required") return "border-brand/35 bg-brand/10 text-brand";
  if (status === "ready") {
    return "border-[color:var(--pro)]/30 bg-[color:var(--pro)]/10 text-[color:var(--pro)]";
  }
  return "border-border bg-muted/40 text-muted-foreground";
}

function learningStandardButtonClass(active: boolean): string {
  return (
    "h-7 rounded-md border px-2.5 text-[11px] font-medium transition " +
    (active
      ? "border-brand/35 bg-brand/10 text-brand disabled:opacity-100"
      : "border-border/60 bg-background/40 text-muted-foreground hover:border-brand/35 hover:text-foreground")
  );
}

function rolePlanAdmissionClass(value: number): string {
  if (value >= 90) return "border-brand/35 bg-brand/10 text-brand";
  if (value >= 50) return "border-amber-400/30 bg-amber-400/10 text-amber-100";
  return "border-destructive/30 bg-destructive/10 text-destructive";
}

function learningSummaryStatusLabel(
  status: TeamLearningMemberSummary["status"],
): string {
  if (status === "complete") return "сдано";
  if (status === "attention") return "в работе";
  return "не начал";
}

function learningSummaryStatusClass(
  status: TeamLearningMemberSummary["status"],
): string {
  if (status === "complete") {
    return "border-brand/35 bg-brand/10 text-brand";
  }
  if (status === "attention") {
    return "border-amber-400/30 bg-amber-400/10 text-amber-100";
  }
  return "border-border bg-muted/40 text-muted-foreground";
}

function learningAdmissionLabel(
  status: TeamLearningMemberSummary["admissionStatus"],
): string {
  if (status === "admitted") return "допуск";
  if (status === "needs_training") return "дожать";
  return "нет допуска";
}

function learningAdmissionClass(
  status: TeamLearningMemberSummary["admissionStatus"],
): string {
  if (status === "admitted") {
    return "border-brand/35 bg-brand/10 text-brand";
  }
  if (status === "needs_training") {
    return "border-amber-400/30 bg-amber-400/10 text-amber-100";
  }
  return "border-destructive/30 bg-destructive/10 text-destructive";
}

function formatLearningDate(value: string): string {
  if (!value) return "нет попыток";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "нет попыток";

  return new Intl.DateTimeFormat("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function LearningSummaryRow({
  summary,
}: {
  summary: TeamLearningMemberSummary;
}) {
  const role = getTeamRole(summary.member.roleId);

  return (
    <div className="grid gap-3 rounded-lg border border-border/45 bg-background/35 p-3 lg:grid-cols-[1.05fr_0.95fr_auto] lg:items-center">
      <div className="min-w-0">
        <div className="flex flex-wrap items-center gap-2">
          <p className="truncate text-sm font-medium">{summary.member.name}</p>
          <Badge variant="outline">{role.title}</Badge>
          <Badge
            variant="outline"
            className={learningSummaryStatusClass(summary.status)}
          >
            {learningSummaryStatusLabel(summary.status)}
          </Badge>
          <Badge
            variant="outline"
            className={learningAdmissionClass(summary.admissionStatus)}
          >
            {learningAdmissionLabel(summary.admissionStatus)}
          </Badge>
        </div>
        <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
          Обязательные: {summary.requiredCompleted}/{summary.requiredCount || 0}{" "}
          · всего: {summary.completedCount}/{summary.totalCount}
        </p>
      </div>
      <div className="min-w-0">
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <ListChecks className="size-3.5 text-brand" />
          <span className="truncate">
            {summary.nextItem
              ? `Дальше: ${summary.nextItem.title}`
              : "Все материалы роли закрыты"}
          </span>
        </div>
        <div className="mt-2 flex items-center gap-2 text-xs text-muted-foreground">
          <Trophy className="size-3.5 text-brand" />
          <span>
            Последняя попытка: {formatLearningDate(summary.lastCompletedAt)}
          </span>
        </div>
      </div>
      <div className="rounded-lg border border-border/50 bg-card/45 px-3 py-2 text-left lg:text-right">
        <p className="numeric text-xl font-medium text-foreground">
          {summary.averageBest}%
        </p>
        <p className="mt-1 text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
          средний
        </p>
      </div>
    </div>
  );
}

function TaskRow({
  task,
  compact = false,
  anchorId,
  focused = false,
}: {
  task: TeamTask;
  compact?: boolean;
  anchorId?: string;
  focused?: boolean;
}) {
  const sourceLabel = sourceBadgeLabel(task);

  return (
    <div
      id={anchorId}
      className={
        "rounded-lg border p-3 " +
        (focused
          ? "border-brand/45 bg-brand/10 ring-1 ring-brand/25 "
          : "border-border/45 bg-background/35 ") +
        (anchorId ? "operational-target scroll-mt-24" : "")
      }
    >
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant="outline" className={priorityClass(task.priority)}>
          {task.priority}
        </Badge>
        <Badge variant="outline">{statusLabel(task.status)}</Badge>
        {sourceLabel ? (
          <Badge
            variant="outline"
            className="border-brand/30 bg-brand/10 text-brand"
          >
            {sourceLabel}
          </Badge>
        ) : null}
        {task.impactLabel ? (
          <Badge
            variant="outline"
            className="border-amber-500/30 bg-amber-500/10 text-amber-200"
          >
            {task.impactLabel}
          </Badge>
        ) : null}
        <span className="text-[11px] uppercase tracking-[0.16em] text-muted-foreground">
          {task.dueLabel}
        </span>
      </div>
      <p
        className={
          "mt-3 leading-relaxed text-foreground/90 " +
          (compact ? "text-[13px]" : "text-sm")
        }
      >
        {task.title}
      </p>
    </div>
  );
}

function StaffRow({
  member,
  href,
  selected,
}: {
  member: StaffMember;
  href: string;
  selected: boolean;
}) {
  const role = getTeamRole(member.roleId);

  return (
    <Link
      href={href}
      className={
        "grid gap-3 rounded-lg border p-3 transition-colors sm:grid-cols-[1fr_auto] sm:items-center " +
        (selected
          ? "border-brand/45 bg-brand/10"
          : "border-border/45 bg-background/35 hover:border-brand/35 hover:bg-background/55")
      }
    >
      <div>
        <div className="flex flex-wrap items-center gap-2">
          <p className="text-sm font-medium">{member.name}</p>
          <Badge variant="outline">{role.title}</Badge>
          {selected ? (
            <Badge variant="outline" className="border-brand/30 text-brand">
              открыт
            </Badge>
          ) : null}
        </div>
        <p className="mt-1 text-xs text-muted-foreground">
          {member.shiftLabel}
        </p>
      </div>
      <div className="flex items-center gap-2 text-[12px] text-muted-foreground sm:justify-end">
        {member.status === "active" ? (
          <CheckCircle2 className="size-4 text-brand" />
        ) : (
          <Clock3 className="size-4 text-amber-100" />
        )}
        <span>{member.status === "active" ? "активен" : member.status}</span>
        <ArrowRight className="size-4" />
      </div>
    </Link>
  );
}
