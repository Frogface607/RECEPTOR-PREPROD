import {
  AlertTriangle,
  ArrowRight,
  Banknote,
  CheckCircle2,
  Clock3,
  Percent,
  SearchCheck,
  Settings2,
  UsersRound,
} from "lucide-react";
import type { ReactNode } from "react";
import { LinkButton } from "@/components/ui/link-button";
import { formatInteger, formatRubles } from "@/lib/format";
import {
  buildLaborMarginBridge,
  type LaborMarginBridge,
} from "@/lib/labor-margin-bridge";
import type { MenuMarginReadiness } from "@/lib/menu-margin-readiness";
import {
  buildLaborEmployeeDiagnostics,
  buildLaborNextAction,
  buildLaborInsights,
  type LaborBlocker,
  type LaborBiSummary,
  type LaborEmployeeDiagnostic,
  type LaborInsightTone,
  type LaborNextAction,
} from "@/lib/team/labor-bi";
import type { TeamLaborSetupProgress } from "@/lib/team/team-labor-readiness";

function formatPct(value: number | null): string {
  if (value === null) return "—";
  return `${value.toLocaleString("ru-RU", { maximumFractionDigits: 1 })}%`;
}

function formatHours(value: number): string {
  return `${value.toLocaleString("ru-RU", { maximumFractionDigits: 1 })} ч`;
}

function formatRatio(value: number | null): string {
  return value === null ? "—" : formatRubles(value);
}

export function LaborBiCard({
  labor,
  ratesHref,
  setupProgress,
  margin,
}: {
  labor: LaborBiSummary;
  ratesHref?: string;
  setupProgress?: TeamLaborSetupProgress;
  margin?: MenuMarginReadiness;
}) {
  const insights = buildLaborInsights(labor);
  const nextAction = buildLaborNextAction(labor);
  const nextActionHref = buildLaborActionHref(ratesHref, nextAction);
  const laborMarginBridge = margin
    ? buildLaborMarginBridge({ labor, margin })
    : null;
  const employeeDiagnostics = buildLaborEmployeeDiagnostics(labor)
    .filter((item) => item.kind !== "healthy")
    .slice(0, 3);
  const coverageLabel = formatPct(labor.revenueCoveragePct);
  const unpricedDetail =
    labor.unpricedStaffShifts > 0
      ? `${formatInteger(labor.unpricedStaffShifts)} записей · ${formatRubles(labor.unpricedRevenue)} под вопросом`
      : "вся выручка смен покрыта";
  const statusCopy =
    nextAction.kind === "missing-shifts"
      ? {
          label: "Нет смен",
          title: "iiko пока не вернула смены",
          detail:
            "Для ФОТ нужны сотрудники и часы из смен. Проверьте период, права OLAP и доступ к сменам.",
          className: "border-border/60 bg-background/45 text-muted-foreground",
        }
      : nextAction.kind === "expensive-labor"
        ? {
            label: "ФОТ выше нормы",
            title: "Ставки есть, но смена дорогая",
            detail:
              "Стоимость команды считается, теперь можно разбирать расписание, роли, часы и загрузку зала.",
            className:
              "border-destructive/35 bg-destructive/10 text-destructive",
          }
        : nextAction.kind === "low-productivity"
          ? {
              label: "Слабая смена",
              title: "ФОТ считается, но команда не добрала выручку",
              detail:
                "Ставки закрыты. Следующий разбор — где смена дала мало выручки на человеко-час: лишние руки, слабые часы, посадка или средний чек.",
              className: "border-amber-400/35 bg-amber-400/10 text-amber-200",
            }
          : labor.laborReadinessStatus === "ready"
            ? {
                label: "ФОТ считается",
                title: "Стоимость смен под контролем",
                detail: `Ставки заведены, точность ФОТ ${coverageLabel}. Можно сравнивать выручку, человеко-часы и нагрузку команды.`,
                className: "border-brand/35 bg-brand/10 text-brand",
              }
            : labor.laborReadinessStatus === "partial"
              ? {
                  label: "ФОТ частичный",
                  title: "ФОТ считается не по всем сменам",
                  detail: `Точная часть покрывает ${coverageLabel} сменной выручки. ${formatRubles(labor.unpricedRevenue)} пока без ставки или карточки сотрудника.`,
                  className:
                    "border-amber-400/35 bg-amber-400/10 text-amber-200",
                }
              : {
                  label: "ФОТ не доказан",
                  title: "Смены видны, но ФОТ еще нельзя считать",
                  detail:
                    "Receptor видит смены и часы, но не нашел ни одной точной ставки. Сначала свяжите сотрудников и задайте правила ФОТ в Team OS.",
                  className:
                    "border-amber-400/35 bg-amber-400/10 text-amber-200",
                };

  const topEmployees = labor.employees.slice(0, 4);
  const topBlockers = labor.topBlockers.slice(0, 3);

  return (
    <section className="rounded-xl border border-border/60 bg-card/50 p-5 sm:p-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex min-w-0 items-start gap-4">
          <div className="flex size-10 shrink-0 items-center justify-center rounded-lg border border-border/60 bg-background/45 text-brand">
            <UsersRound className="size-5" />
          </div>
          <div className="min-w-0">
            <p className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
              Смены и ФОТ
            </p>
            <h2 className="mt-2 text-xl font-medium leading-tight text-foreground">
              {statusCopy.title}
            </h2>
            <p className="mt-2 max-w-2xl text-[13px] leading-relaxed text-muted-foreground">
              {statusCopy.detail}
            </p>
          </div>
        </div>

        <span
          className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-[11px] uppercase tracking-[0.14em] ${statusCopy.className}`}
        >
          <Percent className="size-3.5" />
          {statusCopy.label}
        </span>
      </div>

      <LaborNextActionCard action={nextAction} href={nextActionHref} />

      {setupProgress ? (
        <LaborSetupProgressStrip
          progress={setupProgress}
          href={buildSetupProgressHref(ratesHref, setupProgress)}
        />
      ) : null}

      {laborMarginBridge ? (
        <LaborMarginBridgeStrip bridge={laborMarginBridge} />
      ) : null}

      <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <Metric
          icon={<Banknote className="size-4" />}
          label="ФОТ периода"
          value={formatRubles(labor.laborCost)}
          detail={`${formatPct(labor.laborCostPct)} от выручки`}
        />
        <Metric
          icon={<Clock3 className="size-4" />}
          label="Человеко-часы"
          value={formatHours(labor.staffHours)}
          detail={`${formatRatio(labor.revenuePerLaborHour)} / час`}
        />
        <Metric
          icon={<UsersRound className="size-4" />}
          label="Смены команды"
          value={formatInteger(labor.staffShifts)}
          detail={`${labor.averageStaffPerShift.toLocaleString("ru-RU")} человека на смену`}
        />
        <Metric
          icon={<Percent className="size-4" />}
          label="Точность ФОТ"
          value={coverageLabel}
          detail={
            labor.revenueCoveragePct === null
              ? "нет сменных данных"
              : unpricedDetail
          }
        />
      </div>

      {topBlockers.length > 0 ? (
        <div className="mt-5 border-y border-border/45 py-4">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
                Сначала закрыть
              </p>
              <h3 className="mt-1 text-base font-medium text-foreground">
                Сменные сотрудники без точного ФОТ
              </h3>
            </div>
            <p className="max-w-md text-xs leading-relaxed text-muted-foreground">
              Эти имена из iiko сильнее всего искажают стоимость команды.
            </p>
          </div>

          <div className="mt-3 grid gap-2 lg:grid-cols-3">
            {topBlockers.map((blocker) => (
              <LaborBlockerCard
                key={`${blocker.name}-${blocker.reason}`}
                blocker={blocker}
              />
            ))}
          </div>
        </div>
      ) : null}

      {employeeDiagnostics.length > 0 ? (
        <div className="mt-5 border-y border-border/45 py-4">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
                Кого разобрать
              </p>
              <h3 className="mt-1 text-base font-medium text-foreground">
                Персональные риски ФОТ
              </h3>
            </div>
            <p className="max-w-md text-xs leading-relaxed text-muted-foreground">
              Владелец сразу видит, какого сотрудника открыть в Team OS.
            </p>
          </div>

          <div className="mt-3 grid gap-2 lg:grid-cols-3">
            {employeeDiagnostics.map((employee) => (
              <EmployeeDiagnosticCard
                key={employee.memberId ?? employee.name}
                employee={employee}
                href={buildEmployeeDiagnosticHref(ratesHref, employee)}
              />
            ))}
          </div>
        </div>
      ) : null}

      <div className="mt-5 grid gap-3 lg:grid-cols-3">
        {insights.map((insight) => (
          <InsightCard
            key={`${insight.tone}-${insight.title}`}
            tone={insight.tone}
            title={insight.title}
            detail={insight.detail}
            action={insight.action}
          />
        ))}
      </div>

      {topEmployees.length > 0 ? (
        <div className="mt-5 overflow-x-auto rounded-lg border border-border/45 bg-background/25">
          <table className="w-full text-left text-[13px]">
            <thead>
              <tr className="border-b border-border/40 text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
                <th className="py-3 pl-3 pr-4 font-normal">Сотрудник</th>
                <th className="py-3 pr-4 text-right font-normal">Часы</th>
                <th className="py-3 pr-4 text-right font-normal">Продажи</th>
                <th className="py-3 pr-3 text-right font-normal">ФОТ</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/25">
              {topEmployees.map((employee) => (
                <tr key={employee.memberId ?? employee.name}>
                  <td className="py-3 pl-3 pr-4 text-foreground">
                    {employee.name}
                  </td>
                  <td className="numeric py-3 pr-4 text-right font-mono text-muted-foreground">
                    {formatHours(employee.hours)}
                  </td>
                  <td className="numeric py-3 pr-4 text-right font-mono text-foreground">
                    {formatRubles(employee.sales)}
                  </td>
                  <td className="numeric py-3 pr-3 text-right font-mono text-foreground">
                    {employee.missingRate
                      ? "—"
                      : formatRubles(employee.laborCost)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </section>
  );
}

function buildLaborActionHref(
  ratesHref: string | undefined,
  action: LaborNextAction,
): string | null {
  if (!ratesHref) return null;
  const [path] = ratesHref.split("#");

  if (action.kind === "missing-member" && action.blocker) {
    return addQueryAndHash(
      path,
      "prefillMemberName",
      action.blocker.name,
      "team-actions",
    );
  }

  if (action.kind === "missing-rate" && action.blocker?.memberId) {
    return addQueryAndHash(
      path,
      "focusMemberId",
      action.blocker.memberId,
      `labor-member-${action.blocker.memberId}`,
    );
  }

  if (action.kind === "expensive-labor" || action.kind === "low-productivity") {
    return `${path}#iiko-shift-diagnostics`;
  }

  if (action.kind === "missing-shifts") {
    return null;
  }

  if (action.kind === "ready") {
    return null;
  }

  return ratesHref;
}

function buildSetupProgressHref(
  ratesHref: string | undefined,
  progress: TeamLaborSetupProgress,
): string | null {
  if (!ratesHref || !progress.target || !progress.ctaLabel) return null;
  const [path] = ratesHref.split("#");
  return `${path}#${progress.target}`;
}

function addQueryAndHash(
  path: string,
  key: string,
  value: string,
  hash: string,
): string {
  const separator = path.includes("?") ? "&" : "?";
  return `${path}${separator}${key}=${encodeURIComponent(value)}#${hash}`;
}

function setupProgressClass(tone: TeamLaborSetupProgress["tone"]): string {
  if (tone === "risk")
    return "border-destructive/35 bg-destructive/10 text-destructive";
  if (tone === "watch")
    return "border-amber-400/35 bg-amber-400/10 text-amber-200";
  return "border-brand/35 bg-brand/10 text-brand";
}

function LaborSetupProgressStrip({
  progress,
  href,
}: {
  progress: TeamLaborSetupProgress;
  href: string | null;
}) {
  const toneClass = setupProgressClass(progress.tone);

  return (
    <div className="mt-4 rounded-lg border border-border/45 bg-background/30 p-3">
      <div className="grid gap-3 xl:grid-cols-[minmax(0,1fr)_auto] xl:items-center">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span
              className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-[10px] uppercase tracking-[0.14em] ${toneClass}`}
            >
              {progress.status === "ready" ? (
                <CheckCircle2 className="size-3.5" />
              ) : (
                <Settings2 className="size-3.5" />
              )}
              настройка ФОТ
            </span>
            <p className="text-[13px] font-medium text-foreground">
              {progress.title}
            </p>
          </div>
          <p className="mt-2 max-w-3xl text-[12px] leading-relaxed text-muted-foreground">
            {progress.detail}
          </p>
        </div>

        {href && progress.ctaLabel ? (
          <LinkButton
            href={href}
            variant="outline"
            className="h-9 shrink-0 border-brand/45 bg-brand/10 px-3 text-[12px] text-brand hover:bg-brand/15"
          >
            {progress.ctaLabel}
            <ArrowRight className="size-3.5" />
          </LinkButton>
        ) : null}
      </div>

      <div className="mt-3 grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
        <SetupProgressMetric
          label="точность"
          value={`${progress.coveragePct}%`}
          detail={`${formatRubles(progress.unpricedRevenue)} под вопросом`}
        />
        <SetupProgressMetric
          label="ставки"
          value={`${progress.readyStaff}/${progress.activeStaff}`}
          detail="активной команды"
        />
        <SetupProgressMetric
          label="карточки"
          value={formatInteger(progress.missingStaffCards)}
          detail="не связаны с iiko"
        />
        <SetupProgressMetric
          label="закрыть пачкой"
          value={formatInteger(progress.bulkRateTargets.length)}
          detail={`${formatInteger(progress.unpricedShifts)} сменных записей`}
        />
      </div>

      {progress.setupBlockers.length > 0 ? (
        <div className="mt-3 grid gap-2 sm:grid-cols-2 xl:grid-cols-3">
          {progress.setupBlockers.map((blocker) => (
            <div
              key={`${blocker.name}-${blocker.reason}`}
              className="rounded-lg border border-border/45 bg-card/35 p-3"
            >
              <div className="flex items-start justify-between gap-3">
                <p className="min-w-0 truncate text-[12px] font-medium text-foreground">
                  {blocker.name}
                </p>
                <span className="shrink-0 rounded-md border border-amber-400/30 bg-amber-400/10 px-2 py-1 text-[10px] uppercase tracking-[0.12em] text-amber-200">
                  {setupBlockerLabel(blocker)}
                </span>
              </div>
              <p className="mt-2 text-[11px] leading-relaxed text-muted-foreground">
                {formatInteger(blocker.shifts)} смен ·{" "}
                {formatHours(blocker.hours)} · {formatRubles(blocker.revenue)}{" "}
                без точного ФОТ
              </p>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}

function setupBlockerLabel(
  blocker: TeamLaborSetupProgress["setupBlockers"][number],
): string {
  return blocker.action === "add-member" ? "карточка" : "ставка";
}

function LaborMarginBridgeStrip({ bridge }: { bridge: LaborMarginBridge }) {
  return (
    <div className="mt-4 rounded-lg border border-border/45 bg-background/30 p-3">
      <div className="grid gap-3 xl:grid-cols-[minmax(0,1fr)_auto] xl:items-center">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span
              className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-[10px] uppercase tracking-[0.14em] ${insightClass(bridge.tone)}`}
            >
              {bridge.tone === "good" ? (
                <CheckCircle2 className="size-3.5" />
              ) : (
                <SearchCheck className="size-3.5" />
              )}
              ФОТ + маржа
            </span>
            <p className="text-[13px] font-medium text-foreground">
              {bridge.title}
            </p>
          </div>
          <p className="mt-2 max-w-3xl text-[12px] leading-relaxed text-muted-foreground">
            {bridge.detail}
          </p>
          <p className="mt-1 max-w-3xl text-[12px] leading-relaxed text-foreground/85">
            {bridge.action}
          </p>
        </div>

        <div className="grid gap-2 sm:grid-cols-3 xl:min-w-[420px]">
          <MiniMetric
            label={bridge.employee ? "риск ФОТ" : "ФОТ"}
            value={
              bridge.laborCostPct !== null
                ? formatPct(bridge.laborCostPct)
                : "—"
            }
          />
          <MiniMetric label="маржа" value={`${bridge.marginCoveragePct}%`} />
          <MiniMetric
            label="валовая"
            value={
              bridge.averageGrossMarginPct !== null
                ? formatPct(bridge.averageGrossMarginPct)
                : "—"
            }
          />
        </div>
      </div>
    </div>
  );
}

function SetupProgressMetric({
  label,
  value,
  detail,
}: {
  label: string;
  value: string;
  detail: string;
}) {
  return (
    <div className="rounded-lg border border-border/35 bg-card/35 px-3 py-2">
      <p className="text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
        {label}
      </p>
      <p className="numeric mt-1 text-lg font-medium text-foreground">
        {value}
      </p>
      <p className="mt-0.5 truncate text-[11px] text-muted-foreground">
        {detail}
      </p>
    </div>
  );
}

function LaborNextActionCard({
  action,
  href,
}: {
  action: LaborNextAction;
  href: string | null;
}) {
  const buttonLabel =
    action.kind === "missing-member"
      ? "Добавить в Team OS"
      : action.kind === "missing-rate"
        ? "Открыть ставку"
        : action.kind === "expensive-labor" ||
            action.kind === "low-productivity"
          ? "Открыть смены"
          : "Открыть Team OS";

  return (
    <div className="mt-4 grid gap-3 rounded-lg border border-border/45 bg-background/30 p-3 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center">
      <div className="min-w-0">
        <p className="text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
          Следующее действие
        </p>
        <p className="mt-1 text-[13px] font-medium text-foreground">
          {action.title}
        </p>
        <p className="mt-1 text-[12px] leading-relaxed text-muted-foreground">
          {action.detail}
        </p>
        <p className="mt-2 text-[12px] leading-relaxed text-foreground/80">
          {action.action}
        </p>
      </div>
      {href ? (
        <LinkButton
          href={href}
          variant="outline"
          className="w-full border-brand/45 bg-brand/10 text-brand hover:bg-brand/15 sm:w-auto"
        >
          {buttonLabel}
          <ArrowRight className="size-4" />
        </LinkButton>
      ) : null}
    </div>
  );
}

function blockerReasonLabel(reason: LaborBlocker["reason"]): string {
  if (reason === "missing-member") return "нет в Team OS";
  return "нет ставки";
}

function LaborBlockerCard({ blocker }: { blocker: LaborBlocker }) {
  return (
    <div className="rounded-lg border border-border/45 bg-background/30 p-3">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="truncate text-[13px] font-medium text-foreground">
            {blocker.name}
          </p>
          <p className="mt-1 text-[11px] text-muted-foreground">
            {blocker.shifts} смен · {formatHours(blocker.hours)}
          </p>
        </div>
        <span className="shrink-0 rounded-md border border-amber-400/35 bg-amber-400/10 px-2 py-1 text-[10px] uppercase tracking-[0.12em] text-amber-200">
          {blockerReasonLabel(blocker.reason)}
        </span>
      </div>
      <p className="numeric mt-3 text-lg font-medium text-foreground">
        {formatRubles(blocker.sales)}
      </p>
      <p className="mt-1 text-[11px] text-muted-foreground">
        выручки без точного ФОТ
      </p>
    </div>
  );
}

function buildEmployeeDiagnosticHref(
  ratesHref: string | undefined,
  employee: LaborEmployeeDiagnostic,
): string | null {
  if (!ratesHref) return null;
  const [path] = ratesHref.split("#");

  if (employee.memberId) {
    const separator = path.includes("?") ? "&" : "?";
    const memberId = encodeURIComponent(employee.memberId);
    return `${path}${separator}memberId=${memberId}&focusMemberId=${memberId}#labor-member-${memberId}`;
  }

  if (employee.kind === "missing-rate") return `${path}#team-actions`;
  return `${path}#iiko-shift-diagnostics`;
}

function employeeDiagnosticLabel(
  kind: LaborEmployeeDiagnostic["kind"],
): string {
  if (kind === "missing-rate") return "нет ставки";
  if (kind === "expensive-employee") return "дорого";
  if (kind === "low-productivity") return "низкий час";
  return "норма";
}

function EmployeeDiagnosticCard({
  employee,
  href,
}: {
  employee: LaborEmployeeDiagnostic;
  href: string | null;
}) {
  return (
    <div className="rounded-lg border border-border/45 bg-background/30 p-3">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="truncate text-[13px] font-medium text-foreground">
            {employee.name}
          </p>
          <p className="mt-1 text-[11px] text-muted-foreground">
            {employee.shifts} смен · {formatHours(employee.hours)}
          </p>
        </div>
        <span
          className={`shrink-0 rounded-md border px-2 py-1 text-[10px] uppercase tracking-[0.12em] ${insightClass(employee.tone)}`}
        >
          {employeeDiagnosticLabel(employee.kind)}
        </span>
      </div>

      <p className="mt-3 text-[12px] leading-relaxed text-muted-foreground">
        {employee.detail}
      </p>

      <div className="mt-3 grid grid-cols-3 gap-2">
        <MiniMetric label="ФОТ" value={formatPct(employee.laborCostPct)} />
        <MiniMetric label="выручка" value={formatRubles(employee.sales)} />
        <MiniMetric
          label="на час"
          value={
            employee.revenuePerHour
              ? formatRubles(employee.revenuePerHour)
              : "—"
          }
        />
      </div>

      {href ? (
        <LinkButton
          href={href}
          variant="outline"
          className="mt-3 h-8 w-full justify-between border-brand/35 bg-brand/10 px-3 text-[12px] text-brand hover:bg-brand/15"
        >
          Открыть в Team OS
          <ArrowRight className="size-3.5" />
        </LinkButton>
      ) : null}
    </div>
  );
}

function MiniMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-border/35 bg-card/35 px-2 py-1.5">
      <p className="text-[9px] uppercase tracking-[0.12em] text-muted-foreground">
        {label}
      </p>
      <p className="numeric mt-1 truncate font-mono text-[11px] text-foreground">
        {value}
      </p>
    </div>
  );
}

function InsightIcon({ tone }: { tone: LaborInsightTone }) {
  if (tone === "risk") return <AlertTriangle className="size-4" />;
  if (tone === "watch") return <SearchCheck className="size-4" />;
  if (tone === "setup") return <Settings2 className="size-4" />;
  return <CheckCircle2 className="size-4" />;
}

function insightClass(tone: LaborInsightTone): string {
  if (tone === "risk")
    return "border-destructive/35 bg-destructive/10 text-destructive";
  if (tone === "watch")
    return "border-amber-400/35 bg-amber-400/10 text-amber-200";
  if (tone === "setup")
    return "border-border/60 bg-background/45 text-muted-foreground";
  return "border-brand/35 bg-brand/10 text-brand";
}

function InsightCard({
  tone,
  title,
  detail,
  action,
}: {
  tone: LaborInsightTone;
  title: string;
  detail: string;
  action: string;
}) {
  return (
    <div className="rounded-lg border border-border/45 bg-background/30 p-3">
      <div className="flex items-start gap-3">
        <span
          className={`inline-flex size-8 shrink-0 items-center justify-center rounded-lg border ${insightClass(tone)}`}
        >
          <InsightIcon tone={tone} />
        </span>
        <div className="min-w-0">
          <p className="text-[13px] font-medium leading-snug text-foreground">
            {title}
          </p>
          <p className="mt-1 text-[12px] leading-relaxed text-muted-foreground">
            {detail}
          </p>
          <p className="mt-2 text-[12px] leading-relaxed text-foreground/85">
            {action}
          </p>
        </div>
      </div>
    </div>
  );
}

function Metric({
  icon,
  label,
  value,
  detail,
}: {
  icon: ReactNode;
  label: string;
  value: string;
  detail: string;
}) {
  return (
    <div className="rounded-lg border border-border/45 bg-background/35 p-3">
      <div className="flex items-center justify-between gap-3">
        <p className="text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
          {label}
        </p>
        <span className="text-brand">{icon}</span>
      </div>
      <p className="numeric mt-3 text-xl font-medium text-foreground">
        {value}
      </p>
      <p className="mt-1 text-[12px] leading-relaxed text-muted-foreground">
        {detail}
      </p>
    </div>
  );
}
