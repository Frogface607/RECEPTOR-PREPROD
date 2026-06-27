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
  type TeamRoleId,
  type TeamTask,
} from "@/lib/team/team-os";
import {
  listLearningItemsForRole,
  listShiftChecklistForRole,
  type TeamLearningItem,
} from "@/lib/team/team-learning";
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
  buildTeamLearningSummaries,
  summarizeTeamLearning,
  type TeamLearningMemberSummary,
} from "@/lib/team/team-learning-progress";
import { buildTeamLaborReadiness } from "@/lib/team/team-labor-readiness";
import {
  buildTeamOpsReadiness,
  type TeamOpsAction,
  type TeamOpsActionTone,
  type TeamOpsReadinessStatus,
} from "@/lib/team/team-ops-readiness";
import {
  buildLaborBi,
  buildLaborShiftDiagnostics,
  type LaborShiftInput,
  type LaborBiSummary,
  type LaborShiftDiagnostic,
} from "@/lib/team/labor-bi";
import {
  buildMemberOperationPlan,
  buildMemberLaborProfile,
  buildMemberShiftSchedule,
  type MemberLaborProfile,
  type MemberLaborProfileStatus,
  type MemberOperationPlanItem,
  type MemberOperationPlanTone,
  type MemberShiftScheduleItem,
} from "@/lib/team/member-shift-schedule";
import { getTeamWorkspace } from "@/lib/team/team-store";
import { getCurrentUser } from "@/lib/auth/session";
import { getVenueAccess } from "@/lib/auth/venue-access";
import { isSupabaseConfigured } from "@/lib/db/env";
import { formatInteger, formatRubles } from "@/lib/format";
import { DEMO_ANCHOR, getDashboardClient } from "@/lib/iiko/config";
import { MockIikoClient } from "@/lib/iiko/mock-client";
import type { Period } from "@/lib/iiko/models";

export const metadata: Metadata = {
  title: "Команда — RECEPTOR",
  description:
    "Роли, права, сотрудники, задачи, обучение и смены внутри Receptor.",
};

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

type TeamLaborLoadResult = {
  laborBi: LaborBiSummary | null;
  shifts: LaborShiftInput[];
  source: "live" | "demo" | "unavailable";
  error: string | null;
};

function laborLoadErrorMessage(error: unknown): string {
  const message = error instanceof Error ? error.message : String(error);
  if (/401|auth|unauthorized/i.test(message)) {
    return "iiko не дала доступ к сменам. Проверьте права интеграции.";
  }
  if (/OLAP|reports|shifts|смен/i.test(message)) {
    return "iiko не вернула смены за выбранный период. Проверьте период и права OLAP.";
  }
  return "Смены iiko временно недоступны. Показываем только ставки Team OS.";
}

async function loadTeamLabor(input: {
  venueId: string;
  staff: StaffMember[];
  period: Period;
}): Promise<TeamLaborLoadResult> {
  if (input.venueId === "dev-venue") {
    const shifts = await new MockIikoClient({ today: DEMO_ANCHOR }).getShifts(
      input.period,
    );
    return {
      laborBi: buildLaborBi({ shifts, staff: input.staff }),
      shifts,
      source: "demo",
      error: null,
    };
  }

  const access = await getVenueAccess(input.venueId);
  if (!access.ok) {
    return {
      laborBi: null,
      shifts: [],
      source: "unavailable",
      error: "Нет доступа к заведению для загрузки смен iiko.",
    };
  }

  try {
    const shifts = await getDashboardClient(access.venue).getShifts(
      input.period,
    );
    return {
      laborBi: buildLaborBi({ shifts, staff: input.staff }),
      shifts,
      source: "live",
      error: null,
    };
  } catch (error) {
    console.error("[team] Failed to load iiko labor shifts", {
      venueId: input.venueId,
      error: error instanceof Error ? error.message : String(error),
    });
    return {
      laborBi: null,
      shifts: [],
      source: "unavailable",
      error: laborLoadErrorMessage(error),
    };
  }
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

function sourceBadgeLabel(source: TeamTask["source"]): string | null {
  return source === "copilot" ? "Receptor" : null;
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
  );
  const learningOverview = summarizeTeamLearning(learningSummaries);
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
  const shiftRoster = buildTeamShiftRoster({
    staff: workspace.staff,
    shifts: laborLoad.shifts,
    labor: laborLoad.laborBi,
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
    ? listLearningItemsForRole(representativeMember.roleId).slice(0, 3)
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
                Штаб смены и команды.
              </h1>
              <p className="mt-4 max-w-xl text-sm leading-relaxed text-muted-foreground">
                Доступы, ставки, обучение и задачи в одном рабочем контуре.
              </p>
              <div className="mt-5 flex flex-wrap gap-3">
                <LinkButton
                  href={dashboardHref(workspace.venueId, period)}
                  className="bg-brand text-primary-foreground hover:bg-brand-hover"
                >
                  Панель владельца
                  <ArrowRight className="size-4" />
                </LinkButton>
                <LinkButton
                  href={teamHref(workspace.venueId, "service", period)}
                  variant="outline"
                >
                  Вид официанта
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

                <div>
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-[11px] uppercase tracking-[0.22em] text-muted-foreground">
                      Что закрыть первым
                    </p>
                    <span className="rounded-md border border-border/50 bg-background/35 px-2.5 py-1 text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
                      {workspace.venueName}
                    </span>
                  </div>
                  <div className="mt-3 grid gap-2">
                    {opsReadiness.actions.map((action) => (
                      <TeamOpsActionRow key={action.id} action={action} />
                    ))}
                  </div>
                </div>
              </div>
            </div>
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
          laborSource={laborLoad.source}
          periodLabel={formatPeriodLabel(period)}
          laborProfile={memberLaborProfile}
        />

        <TeamShiftRosterSection
          roster={shiftRoster}
          laborSource={laborLoad.source}
          periodLabel={formatPeriodLabel(period)}
          error={laborLoad.error}
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
          <div className="mx-auto grid max-w-7xl gap-6 px-6 py-8 lg:grid-cols-[0.78fr_1.22fr]">
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
        </section>

        <TeamActionsPanel
          venueId={workspace.venueId}
          staff={workspace.staff}
          tasks={workspace.tasks}
          auditEvents={workspace.auditEvents}
          focusMemberId={focusMemberId}
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
        />

        <section className="border-b border-border/40">
          <div className="mx-auto grid max-w-7xl gap-6 px-6 py-14 lg:grid-cols-[0.9fr_1.1fr]">
            <div className="rounded-lg border border-border/60 bg-card/50 p-5">
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

            <div className="rounded-lg border border-border/60 bg-card/50 p-5">
              <div className="flex items-center gap-3">
                <ClipboardList className="size-5 text-brand" />
                <h2 className="text-xl font-medium">Задачи в этом кабинете</h2>
              </div>
              <div className="mt-5 grid gap-3">
                {home.visibleTasks.map((task) => (
                  <TaskRow key={task.id} task={task} />
                ))}
              </div>
            </div>
          </div>
        </section>

        <section className="border-b border-border/40">
          <div className="mx-auto max-w-7xl px-6 py-14">
            <div className="rounded-lg border border-border/60 bg-card/50 p-5">
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
          </div>
        </section>

        <section>
          <div className="mx-auto max-w-7xl px-6 py-14">
            <div className="rounded-lg border border-border/60 bg-card/50 p-6">
              <div className="flex items-start gap-3">
                <KeyRound className="mt-1 size-5 shrink-0 text-brand" />
                <div>
                  <h2 className="text-xl font-medium">Далее: сменный чат.</h2>
                  <p className="mt-3 max-w-3xl text-sm leading-relaxed text-muted-foreground">
                    Сейчас фиксируем задачи, объявления и комментарии. Чат
                    добавим поверх этой структуры.
                  </p>
                </div>
              </div>
            </div>
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

function opsActionToneClass(tone: TeamOpsActionTone): string {
  if (tone === "good") return "border-brand/35 bg-brand/10 text-brand";
  if (tone === "risk") {
    return "border-destructive/30 bg-destructive/10 text-destructive";
  }
  if (tone === "setup") {
    return "border-amber-400/30 bg-amber-400/10 text-amber-100";
  }
  return "border-border/60 bg-background/45 text-muted-foreground";
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

function isOpenTask(task: TeamTask): boolean {
  return task.status !== "done" && task.status !== "verified";
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
                    Фактические смены из iiko связаны с сотрудниками Team OS и
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
              Для этой роли пока нет сотрудника. Добавьте его в Team OS, чтобы
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
              Открыть обучение
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
          <MemberOperationPlanCard items={operationPlan} />

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
                  <p className="text-sm font-medium">Смен по сотруднику нет</p>
                  <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
                    Если сотрудник был на смене, проверьте совпадение имени в
                    iiko и Team OS или права на выгрузку смен.
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
                      Следующий урок
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
      </div>
    </section>
  );
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
  if (source === "demo") return "демо-смены";
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

function TeamOpsActionRow({ action }: { action: TeamOpsAction }) {
  return (
    <Link
      href={action.href}
      className="grid gap-3 rounded-lg border border-border/45 bg-background/35 p-3 transition-colors hover:border-brand/35 hover:bg-background/55 sm:grid-cols-[auto_1fr_auto] sm:items-center"
    >
      <span
        className={
          "size-2 rounded-full border " + opsActionToneClass(action.tone)
        }
      />
      <span className="min-w-0">
        <span className="block text-sm font-medium text-foreground">
          {action.title}
        </span>
        <span className="mt-1 block truncate text-xs text-muted-foreground">
          {action.detail}
        </span>
      </span>
      <ArrowRight className="size-4 text-muted-foreground" />
    </Link>
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
}: {
  task: TeamTask;
  compact?: boolean;
}) {
  const sourceLabel = sourceBadgeLabel(task.source);

  return (
    <div className="rounded-lg border border-border/45 bg-background/35 p-3">
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
