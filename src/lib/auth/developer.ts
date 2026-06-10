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

function hashAccessKey(value: string): string {
  return createHash("sha256").update(value).digest("hex");
}

export function getDeveloperAccessConfig(
  env: Record<string, string | undefined> = process.env,
): DeveloperAccessConfig | null {
  const accessKey = env.RECEPTOR_DEV_ACCESS_KEY?.trim();
  const email = env.RECEPTOR_DEV_EMAIL?.trim() || "developer@receptor.local";

  if (!isEnabled(env.RECEPTOR_DEV_MODE) || !accessKey) return null;

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
