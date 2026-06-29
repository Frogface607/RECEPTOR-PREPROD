-- Team task impact labels
-- Stores the compact business weight of an owner-created task, for example
-- "ФОТ 35%" or "20 000 ₽", so Team OS keeps the same priority context.

alter table team_tasks
  add column if not exists impact_label text;

comment on column team_tasks.impact_label is
  'Compact business weight copied from Owner Dashboard task drafts.';
