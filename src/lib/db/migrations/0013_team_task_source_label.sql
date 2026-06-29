-- Team task source labels
-- Stores the operational contour (for example, "ФОТ и маржа") on the task
-- itself so staff cabinets can show context without reading audit events.

alter table team_tasks
  add column if not exists source_label text;

comment on column team_tasks.source_label is
  'Human-readable operational contour copied from Owner/Manager task drafts.';
