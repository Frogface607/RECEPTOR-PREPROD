import type { MenuMarginReadiness } from "@/lib/menu-margin-readiness";
import {
  buildLaborEmployeeDiagnostics,
  type LaborBiSummary,
  type LaborEmployeeDiagnostic,
} from "@/lib/team/labor-bi";

export type LaborMarginBridgeTone = "risk" | "watch" | "good" | "setup";

export type LaborMarginBridge = {
  tone: LaborMarginBridgeTone;
  title: string;
  detail: string;
  action: string;
  employee: LaborEmployeeDiagnostic | null;
  marginRiskDish: string | null;
  laborCostPct: number | null;
  marginCoveragePct: number;
  averageGrossMarginPct: number | null;
};

export function buildLaborMarginBridge(input: {
  labor: LaborBiSummary;
  margin: MenuMarginReadiness;
}): LaborMarginBridge {
  const employeeIssue =
    buildLaborEmployeeDiagnostics(input.labor).find(
      (item) => item.kind !== "healthy",
    ) ?? null;
  const marginRisk = input.margin.topMarginRisks[0] ?? null;
  const marginCoveragePct = input.margin.revenueCoveragePct;
  const averageGrossMarginPct = input.margin.averageGrossMarginPct;

  const base = {
    employee: employeeIssue,
    marginRiskDish: marginRisk?.dishName ?? null,
    laborCostPct: input.labor.laborCostPct,
    marginCoveragePct,
    averageGrossMarginPct,
  };

  if (!employeeIssue && input.margin.status === "ready") {
    return {
      ...base,
      tone: "good",
      title: "ФОТ и маржа можно разбирать вместе",
      detail: `Себестоимость покрывает ${marginCoveragePct}% выручки, явных персональных ФОТ-рисков не видно.`,
      action:
        "Дальше сравнивайте состав смен с блюдами слабой маржи и закрепляйте удачные сменные модели.",
    };
  }

  if (!employeeIssue) {
    return {
      ...base,
      tone: input.margin.status === "blocked" ? "setup" : "watch",
      title: "Сначала доказать маржу периода",
      detail: `${formatRubles(input.margin.blockedRevenue)} выручки пока без доказанной себестоимости. ФОТ выглядит без персонального риска, но прибыль периода еще шумная.`,
      action:
        "Закройте связи с iiko, техкарты и закупочные цены, затем сравнивайте ФОТ с валовой маржой.",
    };
  }

  if (input.margin.status !== "ready") {
    return {
      ...base,
      tone: input.margin.status === "blocked" ? "risk" : "watch",
      title: `ФОТ по ${employeeIssue.name} требует маржу рядом`,
      detail: `${employeeIssue.detail} Но себестоимость покрывает только ${marginCoveragePct}% выручки, поэтому решение по часам без маржи может быть ложным.`,
      action:
        "Сначала закройте себестоимость топовых блюд, потом решайте: менять график, ставку, роль или меню.",
    };
  }

  if (marginRisk) {
    return {
      ...base,
      tone: employeeIssue.tone === "risk" ? "risk" : "watch",
      title: `Проверить смену: ${employeeIssue.name} и слабая маржа`,
      detail: `${employeeIssue.detail} В этом же периоде слабая доказанная маржа у «${marginRisk.dishName}»: ${marginRisk.grossMarginPct}%.`,
      action:
        "Разберите, что продавалось в смены этого сотрудника: если упор был на слабую маржу, проблема может быть в меню, а не только в ФОТ.",
    };
  }

  return {
    ...base,
    tone: employeeIssue.tone === "risk" ? "risk" : "watch",
    title: `Разобрать ФОТ по ${employeeIssue.name}`,
    detail: `${employeeIssue.detail} Маржа периода доказана на ${marginCoveragePct}% выручки, значит можно принимать управленческое решение по сменам.`,
    action:
      "Сравните часы, роль и продажи сотрудника с валовой маржой периода и создайте задачу управляющему.",
  };
}

function formatRubles(value: number): string {
  return `${Math.round(value).toLocaleString("ru-RU")} ₽`;
}
