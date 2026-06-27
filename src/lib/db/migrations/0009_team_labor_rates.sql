-- Labor rates for Team OS.
-- Used by Owner Dashboard to calculate управленческий ФОТ from shifts.

alter table venue_memberships
  add column if not exists hourly_rate numeric(12,2) default 0 check (hourly_rate >= 0),
  add column if not exists shift_pay numeric(12,2) default 0 check (shift_pay >= 0),
  add column if not exists revenue_bonus_pct numeric(6,3) default 0 check (revenue_bonus_pct >= 0);

comment on column venue_memberships.hourly_rate is
  'Hourly labor rate in RUB for управленческий ФОТ.';
comment on column venue_memberships.shift_pay is
  'Fixed payment per shift in RUB for управленческий ФОТ.';
comment on column venue_memberships.revenue_bonus_pct is
  'Revenue bonus percentage for управленческий ФОТ.';
