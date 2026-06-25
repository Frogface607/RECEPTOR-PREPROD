import { CloudIikoClient } from "./cloud-client";
import {
  DEMO_ANCHOR,
  resolveIikoClientConfig,
  type IikoClientConfig,
} from "./config";
import { RmsIikoClient } from "./rms-client";
import type { ResolvedVenue } from "@/lib/venues/get-venue";

export type IikoDiagnosticStatus = "ok" | "warn" | "fail";

export type IikoDiagnosticCheck = {
  id: "credentials" | "organization" | "olap" | "dishes";
  title: string;
  status: IikoDiagnosticStatus;
  detail: string;
  action?: string;
};

export type IikoDiagnosticReport = {
  checkedAt: string;
  mode: "live" | "mock";
  channel: "cloud" | "rms" | null;
  summary: string;
  checks: IikoDiagnosticCheck[];
};

type RealIikoProbe = CloudIikoClient | RmsIikoClient;

function createProbe(config: IikoClientConfig): RealIikoProbe | null {
  if (config.mode === "mock") return null;

  if (config.channel === "cloud") {
    return new CloudIikoClient({
      apiLogin: config.apiLogin,
      organizationId: config.organizationId,
      today: config.today,
    });
  }

  return new RmsIikoClient({
    host: config.host,
    login: config.login,
    password: config.password,
    today: config.today,
  });
}

function friendlyIikoError(error: unknown): string {
  const message = error instanceof Error ? error.message : String(error);

  if (/api key|api login|401|unauthorized|auth failed|не принял api/i.test(message)) {
    return "iiko не принял ключ или логин. Скопируйте полный ключ из iiko Web и проверьте, что интеграция активна.";
  }

  if (/olap|reports\/olap|not allowed|forbidden|403/i.test(message)) {
    return "Нет доступа к OLAP-отчетам. Попросите iiko включить права на reports/olap для этой интеграции.";
  }

  if (/423|лиценз/i.test(message)) {
    return "Ключ распознан, но лицензия iiko Cloud API не дает получать данные. Нужно продлить или включить Cloud API.";
  }

  if (/network|fetch failed|ENOTFOUND|ECONNREFUSED|ETIMEDOUT/i.test(message)) {
    return "Не удалось достучаться до iiko. Проверьте адрес сервера, доступ из интернета и сетевые ограничения.";
  }

  return "iiko вернул ошибку. Проверьте права интеграции и попробуйте еще раз.";
}

function ok(
  id: IikoDiagnosticCheck["id"],
  title: string,
  detail: string,
): IikoDiagnosticCheck {
  return { id, title, status: "ok", detail };
}

function warn(
  id: IikoDiagnosticCheck["id"],
  title: string,
  detail: string,
  action?: string,
): IikoDiagnosticCheck {
  return { id, title, status: "warn", detail, action };
}

function fail(
  id: IikoDiagnosticCheck["id"],
  title: string,
  error: unknown,
  action?: string,
): IikoDiagnosticCheck {
  return { id, title, status: "fail", detail: friendlyIikoError(error), action };
}

export async function runIikoDiagnostics(
  venue: ResolvedVenue,
  env: Record<string, string | undefined>,
  today = new Date().toISOString().slice(0, 10),
): Promise<IikoDiagnosticReport> {
  const config = resolveIikoClientConfig(venue, env, today);
  const checkedAt = new Date().toISOString();
  const probe = createProbe(config);
  const checks: IikoDiagnosticCheck[] = [];

  if (!probe || config.mode === "mock") {
    checks.push(
      warn(
        "credentials",
        "Ключ iiko",
        "Для этого заведения нет сохраненного live-доступа. Кабинет работает на демо-данных.",
        "Подключите iiko в настройках заведения.",
      ),
    );

    return {
      checkedAt,
      mode: "mock",
      channel: null,
      summary: "Live-данные пока не подключены",
      checks,
    };
  }

  checks.push(
    ok(
      "credentials",
      "Ключ iiko",
      config.channel === "cloud"
        ? "Сохранен Cloud API ключ."
        : "Сохранены RMS host, логин и пароль.",
    ),
  );

  try {
    const organizations = await probe.listOrganizations();
    const selected =
      config.channel === "cloud"
        ? organizations.find((org) => org.id === config.organizationId)
        : organizations[0];

    if (selected) {
      checks.push(
        ok(
          "organization",
          "Организация",
          `${selected.name || selected.id} доступна для интеграции.`,
        ),
      );
    } else {
      checks.push(
        warn(
          "organization",
          "Организация",
          "Ключ работает, но выбранная организация не найдена в списке доступных.",
          "Проверьте организацию iiko в настройках подключения.",
        ),
      );
    }
  } catch (error) {
    checks.push(
      fail(
        "organization",
        "Организация",
        error,
        "Проверьте ключ и права интеграции.",
      ),
    );
  }

  try {
    const summary = await probe.getRevenueSummary({ type: "LAST_WEEK" });
    checks.push(
      ok(
        "olap",
        "BI / OLAP",
        summary.revenue > 0
          ? `OLAP отвечает. За прошлую неделю найдено ${Math.round(summary.revenue).toLocaleString("ru-RU")} ₽.`
          : "OLAP отвечает, но за прошлую неделю продаж не найдено.",
      ),
    );
  } catch (error) {
    checks.push(
      fail(
        "olap",
        "BI / OLAP",
        error,
        "Попросите iiko включить права reports/olap.",
      ),
    );
  }

  try {
    const dishes = await probe.getDishStatistics({ type: "LAST_WEEK" }, 5);
    checks.push(
      dishes.length > 0
        ? ok("dishes", "Блюда в продажах", `BI вернул ${dishes.length} позиций с продажами.`)
        : warn(
            "dishes",
            "Блюда в продажах",
            "Запрос блюд прошел, но продаж за прошлую неделю нет.",
            "Проверьте период или точку продаж.",
          ),
    );
  } catch (error) {
    checks.push(
      fail(
        "dishes",
        "Блюда в продажах",
        error,
        "Проверьте права OLAP на блюда и группы блюд.",
      ),
    );
  }

  const failed = checks.filter((check) => check.status === "fail").length;
  const warnings = checks.filter((check) => check.status === "warn").length;

  return {
    checkedAt,
    mode: "live",
    channel: config.channel,
    summary:
      failed > 0
        ? "iiko подключен, но часть проверок не прошла"
        : warnings > 0
          ? "iiko отвечает, есть предупреждения"
          : "iiko готов к live BI",
    checks,
  };
}

export function getMockIikoDiagnosticReport(): IikoDiagnosticReport {
  return {
    checkedAt: new Date().toISOString(),
    mode: "mock",
    channel: null,
    summary: "Live-данные пока не подключены",
    checks: [
      warn(
        "credentials",
        "Ключ iiko",
        `Кабинет работает на демо-датасете от ${DEMO_ANCHOR}.`,
        "Подключите iiko в настройках заведения.",
      ),
    ],
  };
}
