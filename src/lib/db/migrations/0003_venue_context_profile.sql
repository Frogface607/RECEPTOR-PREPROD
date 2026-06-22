-- Venue Context Profile
-- Stores the structured Context Engine questionnaire answers for Copilot,
-- Daily Brief, module selection and team workflows.

alter table venues
  add column if not exists context_profile jsonb;

comment on column venues.context_profile is
  'Structured restaurant OS context questionnaire: identity, economics, team, systems and AI/data policy.';
