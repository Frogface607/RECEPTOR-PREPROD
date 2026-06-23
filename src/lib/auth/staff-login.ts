export const STAFF_LOGIN_DOMAIN = "staff.receptorai.pro";

export function normalizeStaffLoginToEmail(value: string): string | null {
  const login = value.trim().toLowerCase();
  if (!login) return null;
  if (login.includes("@")) return login;

  if (!/^[a-z0-9._-]{3,40}$/.test(login)) return null;
  return `${login}@${STAFF_LOGIN_DOMAIN}`;
}
