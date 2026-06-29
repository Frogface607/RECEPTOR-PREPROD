import type { StaffMember } from "./team-os";

export function normalizeTeamMemberName(value: string | null | undefined): string {
  return (value ?? "")
    .toLowerCase()
    .replace(/ё/g, "е")
    .replace(/[^\p{L}\p{N}\s-]+/gu, " ")
    .replace(/-/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

export function teamMemberNameTokens(value: string | null | undefined): string[] {
  const normalized = normalizeTeamMemberName(value);
  if (!normalized) return [];
  return normalized.split(" ").filter((token) => token.length >= 2);
}

export function isLikelySameTeamMemberName(
  left: string | null | undefined,
  right: string | null | undefined,
): boolean {
  const leftName = normalizeTeamMemberName(left);
  const rightName = normalizeTeamMemberName(right);
  if (!leftName || !rightName) return false;
  if (leftName === rightName) return true;
  if (leftName === "смена" || rightName === "смена") return false;

  const leftTokens = teamMemberNameTokens(leftName);
  const rightTokens = teamMemberNameTokens(rightName);
  if (leftTokens.length === 0 || rightTokens.length === 0) return false;

  const leftSet = new Set(leftTokens);
  const rightSet = new Set(rightTokens);
  const shared = leftTokens.filter((token) => rightSet.has(token));

  if (leftTokens.length >= 2 && rightTokens.length >= 2) {
    return shared.length >= Math.min(leftSet.size, rightSet.size, 2);
  }

  const shortTokens = leftTokens.length <= rightTokens.length ? leftTokens : rightTokens;
  const longTokens = leftTokens.length <= rightTokens.length ? rightTokens : leftTokens;
  const token = shortTokens[0];
  if (!token || token.length < 4) return false;

  return longTokens[0] === token || longTokens.includes(token);
}

export function findStaffMemberByName(
  staff: Iterable<StaffMember>,
  name: string | null | undefined,
): StaffMember | undefined {
  const members = [...staff];
  const exactName = normalizeTeamMemberName(name);
  if (!exactName || exactName === "смена") return undefined;

  const exact = members.find(
    (member) => normalizeTeamMemberName(member.name) === exactName,
  );
  if (exact) return exact;

  const matches = members.filter((member) =>
    isLikelySameTeamMemberName(member.name, name),
  );

  return matches.length === 1 ? matches[0] : undefined;
}
