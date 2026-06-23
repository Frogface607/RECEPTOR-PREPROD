-- Team OS Audit Events
-- Lightweight operational history for staff access, tasks and communications.

create table if not exists team_audit_events (
  id uuid primary key default gen_random_uuid(),
  venue_id uuid not null references venues(id) on delete cascade,
  actor_user_id uuid references profiles(user_id) on delete set null,
  actor_membership_id uuid references venue_memberships(id) on delete set null,
  event_type text not null check (
    event_type in (
      'member_invited',
      'member_status_updated',
      'member_password_reset',
      'task_created',
      'task_status_updated',
      'comment_added',
      'announcement_created'
    )
  ),
  target_type text not null check (
    target_type in ('member', 'task', 'comment', 'announcement')
  ),
  target_id uuid,
  summary text not null,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz default now()
);

create index if not exists idx_team_audit_events_venue_created
  on team_audit_events(venue_id, created_at desc);
create index if not exists idx_team_audit_events_actor
  on team_audit_events(actor_user_id, created_at desc);

comment on table team_audit_events is
  'Team OS audit log for access changes and operational actions.';

alter table team_audit_events enable row level security;

drop policy if exists team_audit_events_owner_all on team_audit_events;
create policy team_audit_events_owner_all on team_audit_events
  for all using (
    venue_id in (select id from venues where owner_user_id = auth.uid())
  ) with check (
    venue_id in (select id from venues where owner_user_id = auth.uid())
  );

drop policy if exists team_audit_events_staff_select on team_audit_events;
create policy team_audit_events_staff_select on team_audit_events
  for select using (
    exists (
      select 1
      from venue_memberships vm
      where vm.venue_id = team_audit_events.venue_id
        and vm.user_id = auth.uid()
        and vm.status = 'active'
        and vm.role in (
          'owner',
          'operations_manager',
          'venue_manager',
          'chef',
          'marketing'
        )
    )
  );

drop policy if exists team_audit_events_staff_insert on team_audit_events;
create policy team_audit_events_staff_insert on team_audit_events
  for insert with check (
    actor_user_id = auth.uid()
    and exists (
      select 1
      from venue_memberships vm
      where vm.venue_id = team_audit_events.venue_id
        and vm.user_id = auth.uid()
        and vm.status = 'active'
        and vm.role in (
          'owner',
          'operations_manager',
          'venue_manager',
          'chef',
          'marketing'
        )
    )
  );
