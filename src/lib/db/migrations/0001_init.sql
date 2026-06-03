-- Receptor v2 — initial schema
-- Run once in the Supabase SQL editor (receptor-prod project).
-- Idempotent: safe to re-run. RLS enabled on every table — a user only ever
-- sees their own venues and everything hanging off them.

-- ── Profiles ────────────────────────────────────────────────────────────────
create table if not exists profiles (
  user_id uuid primary key references auth.users on delete cascade,
  full_name text,
  phone text,
  created_at timestamptz default now()
);

-- ── Venues ──────────────────────────────────────────────────────────────────
create table if not exists venues (
  id uuid primary key default gen_random_uuid(),
  owner_user_id uuid references profiles(user_id) on delete cascade,
  name text not null,
  type text check (type in ('restaurant','cafe','coffee','bar','chain','other')),
  city text,
  timezone text default 'Asia/Irkutsk',
  created_at timestamptz default now()
);
create index if not exists idx_venues_owner on venues(owner_user_id);

-- ── iiko credentials (encrypted at rest) ────────────────────────────────────
create table if not exists iiko_credentials (
  id uuid primary key default gen_random_uuid(),
  venue_id uuid references venues(id) on delete cascade,
  channel text check (channel in ('cloud','rms')),
  creds_encrypted bytea not null,
  iv bytea not null,
  iiko_org_id text,
  iiko_org_name text,
  last_validated_at timestamptz,
  token_expires_at timestamptz,
  status text default 'active',
  created_at timestamptz default now()
);
create index if not exists idx_iiko_creds_venue on iiko_credentials(venue_id);

-- ── Nomenclature cache ──────────────────────────────────────────────────────
create table if not exists iiko_nomenclature (
  venue_id uuid references venues(id) on delete cascade,
  product_id text not null,
  payload jsonb not null,
  synced_at timestamptz default now(),
  primary key (venue_id, product_id)
);

-- ── BI snapshot cache ───────────────────────────────────────────────────────
create table if not exists bi_snapshots (
  id uuid primary key default gen_random_uuid(),
  venue_id uuid references venues(id) on delete cascade,
  metric_type text,
  period_type text,
  period_from date,
  period_to date,
  payload jsonb,
  cached_at timestamptz default now()
);
create index if not exists idx_bi_snapshots_venue_period
  on bi_snapshots(venue_id, period_type, cached_at desc);

-- ── AI chat ─────────────────────────────────────────────────────────────────
create table if not exists ai_conversations (
  id uuid primary key default gen_random_uuid(),
  venue_id uuid references venues(id) on delete cascade,
  user_id uuid references profiles(user_id),
  title text,
  created_at timestamptz default now()
);
create table if not exists ai_messages (
  id uuid primary key default gen_random_uuid(),
  conversation_id uuid references ai_conversations(id) on delete cascade,
  role text check (role in ('user','assistant','tool')),
  content text,
  tool_calls jsonb,
  tokens_in int,
  tokens_out int,
  created_at timestamptz default now()
);
create index if not exists idx_ai_messages_conversation on ai_messages(conversation_id, created_at);

-- ── Subscriptions (YooKassa) ────────────────────────────────────────────────
create table if not exists subscriptions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles(user_id) on delete cascade,
  plan text check (plan in ('free','pro','team')) default 'free',
  yookassa_subscription_id text,
  status text default 'active',
  current_period_start timestamptz,
  current_period_end timestamptz,
  created_at timestamptz default now()
);

-- ── Audit log ───────────────────────────────────────────────────────────────
create table if not exists audit_logs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid,
  venue_id uuid,
  action text,
  payload jsonb,
  created_at timestamptz default now()
);
create index if not exists idx_audit_user on audit_logs(user_id, created_at desc);

-- ════════════════════════════════════════════════════════════════════════════
-- Row-Level Security — owner-only access everywhere.
-- ════════════════════════════════════════════════════════════════════════════

alter table profiles            enable row level security;
alter table venues              enable row level security;
alter table iiko_credentials    enable row level security;
alter table iiko_nomenclature   enable row level security;
alter table bi_snapshots        enable row level security;
alter table ai_conversations    enable row level security;
alter table ai_messages         enable row level security;
alter table subscriptions       enable row level security;
alter table audit_logs          enable row level security;

-- profiles: a user sees/edits only their own row
drop policy if exists profiles_self on profiles;
create policy profiles_self on profiles
  for all using (user_id = auth.uid()) with check (user_id = auth.uid());

-- venues: owner-only
drop policy if exists venues_owner on venues;
create policy venues_owner on venues
  for all using (owner_user_id = auth.uid()) with check (owner_user_id = auth.uid());

-- helper predicate: does the current user own this venue?
-- (inlined per-table to avoid a SECURITY DEFINER function for v1)

drop policy if exists iiko_creds_owner on iiko_credentials;
create policy iiko_creds_owner on iiko_credentials
  for all using (
    venue_id in (select id from venues where owner_user_id = auth.uid())
  ) with check (
    venue_id in (select id from venues where owner_user_id = auth.uid())
  );

drop policy if exists nomenclature_owner on iiko_nomenclature;
create policy nomenclature_owner on iiko_nomenclature
  for all using (
    venue_id in (select id from venues where owner_user_id = auth.uid())
  ) with check (
    venue_id in (select id from venues where owner_user_id = auth.uid())
  );

drop policy if exists bi_snapshots_owner on bi_snapshots;
create policy bi_snapshots_owner on bi_snapshots
  for all using (
    venue_id in (select id from venues where owner_user_id = auth.uid())
  ) with check (
    venue_id in (select id from venues where owner_user_id = auth.uid())
  );

drop policy if exists conversations_owner on ai_conversations;
create policy conversations_owner on ai_conversations
  for all using (user_id = auth.uid()) with check (user_id = auth.uid());

drop policy if exists messages_owner on ai_messages;
create policy messages_owner on ai_messages
  for all using (
    conversation_id in (select id from ai_conversations where user_id = auth.uid())
  ) with check (
    conversation_id in (select id from ai_conversations where user_id = auth.uid())
  );

drop policy if exists subscriptions_self on subscriptions;
create policy subscriptions_self on subscriptions
  for all using (user_id = auth.uid()) with check (user_id = auth.uid());

drop policy if exists audit_self on audit_logs;
create policy audit_self on audit_logs
  for select using (user_id = auth.uid());

-- ════════════════════════════════════════════════════════════════════════════
-- Auto-provision a profile + free subscription on signup.
-- ════════════════════════════════════════════════════════════════════════════

create or replace function handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into profiles (user_id, full_name)
  values (new.id, coalesce(new.raw_user_meta_data->>'full_name', ''))
  on conflict (user_id) do nothing;

  insert into subscriptions (user_id, plan, status)
  values (new.id, 'free', 'active')
  on conflict do nothing;

  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function handle_new_user();
