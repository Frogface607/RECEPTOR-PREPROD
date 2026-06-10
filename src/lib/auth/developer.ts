import { createHash } from "node:crypto";

export const DEVELOPER_SESSION_COOKIE = "receptor_dev_session";

export type DeveloperAccessConfig = {
  enabled: boolean;
  email: string;
  keyHash: string;
};

function isEnabled(value: string | undefined): boolean {
  return value?.trim().toLowerCase() === "true";
}

function isExplicitlyDisabled(value: string | undefined): boolean {
  return value?.trim().toLowerCase() === "false";
}

function hashAccessKey(value: string): string {
  return createHash("sha256").update(value).digest("hex");
}

export function getDeveloperAccessConfig(
  env: Record<string, string | undefined> = process.env,
): DeveloperAccessConfig | null {
  const accessKey =
    env.RECEPTOR_DEV_ACCESS_KEY?.trim() ||
    (env.NODE_ENV !== "production" ? "receptor-preview" : "");
  const email = env.RECEPTOR_DEV_EMAIL?.trim() || "developer@receptor.local";

  if (!accessKey || isExplicitlyDisabled(env.RECEPTOR_DEV_MODE)) return null;
  if (!isEnabled(env.RECEPTOR_DEV_MODE) && !env.RECEPTOR_DEV_ACCESS_KEY?.trim()) {
    return null;
  }

  return {
    enabled: true,
    email,
    keyHash: hashAccessKey(accessKey),
  };
}

export function isDeveloperAccessEnabled(
  env: Record<string, string | undefined> = process.env,
): boolean {
  return getDeveloperAccessConfig(env) !== null;
}

export function isPresentationAccessVisible(
  env: Record<string, string | undefined> = process.env,
): boolean {
  return isDeveloperAccessEnabled(env) || env.NODE_ENV !== "production";
}

export function verifyDeveloperAccessKey(value: string): boolean {
  const config = getDeveloperAccessConfig();
  if (!config) return false;
  return hashAccessKey(value.trim()) === config.keyHash;
}

export function developerSessionCookieValue(): string {
  const config = getDeveloperAccessConfig();
  if (!config) throw new Error("Developer access is not configured");
  return config.keyHash;
}

export function isValidDeveloperSessionCookie(value: string | undefined): boolean {
  const config = getDeveloperAccessConfig();
  return Boolean(config && value === config.keyHash);
}
