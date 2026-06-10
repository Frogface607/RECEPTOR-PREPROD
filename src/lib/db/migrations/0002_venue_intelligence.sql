-- Venue Intelligence Profile
-- Stores researched/manual business context for Copilot and owner BI.

alter table venues
  add column if not exists intelligence_profile jsonb;

comment on column venues.intelligence_profile is
  'Venue context: format, audience, strengths, guest pains, owner goals, risks, decision rules.';
