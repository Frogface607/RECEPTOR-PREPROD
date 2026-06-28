-- Team OS Learning Standards
-- Venue-specific required/optional learning rules for shift admission.

create table if not exists team_learning_standards (
  id uuid primary key default gen_random_uuid(),
  venue_id uuid not null references venues(id) on delete cascade,
  role text not null check (
    role in (
      'owner',
      'operations_manager',
      'venue_manager',
      'chef',
      'line_cook',
      'service',
      'marketing'
    )
  ),
  module_id text not null,
  status text not null default 'ready' check (
    status in ('required', 'ready', 'hidden')
  ),
  updated_by uuid references profiles(user_id) on delete set null,
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  unique (venue_id, role, module_id)
);

create index if not exists idx_team_learning_standards_venue_role
  on team_learning_standards(venue_id, role);

comment on table team_learning_standards is
  'Team OS learning standards: venue-specific role requirements for shift admission.';

alter table team_learning_standards enable row level security;

drop policy if exists team_learning_standards_owner_all on team_learning_standards;
create policy team_learning_standards_owner_all on team_learning_standards
  for all using (
    venue_id in (select id from venues where owner_user_id = auth.uid())
  ) with check (
    venue_id in (select id from venues where owner_user_id = auth.uid())
  );

drop policy if exists team_learning_standards_manager_all on team_learning_standards;
create policy team_learning_standards_manager_all on team_learning_standards
  for all using (
    exists (
      select 1
      from venue_memberships vm
      where vm.venue_id = team_learning_standards.venue_id
        and vm.user_id = auth.uid()
        and vm.status = 'active'
        and vm.role in (
          'owner',
          'operations_manager',
          'venue_manager'
        )
    )
  ) with check (
    exists (
      select 1
      from venue_memberships vm
      where vm.venue_id = team_learning_standards.venue_id
        and vm.user_id = auth.uid()
        and vm.status = 'active'
        and vm.role in (
          'owner',
          'operations_manager',
          'venue_manager'
        )
    )
  );

drop policy if exists team_learning_standards_staff_select on team_learning_standards;
create policy team_learning_standards_staff_select on team_learning_standards
  for select using (
    exists (
      select 1
      from venue_memberships vm
      where vm.venue_id = team_learning_standards.venue_id
        and vm.user_id = auth.uid()
        and vm.status = 'active'
    )
  );

alter table if exists team_audit_events
  drop constraint if exists team_audit_events_event_type_check;

alter table if exists team_audit_events
  add constraint team_audit_events_event_type_check check (
    event_type in (
      'member_invited',
      'member_status_updated',
      'member_password_reset',
      'member_labor_rate_updated',
      'task_created',
      'task_status_updated',
      'comment_added',
      'announcement_created',
      'shift_plan_updated',
      'learning_standard_updated'
    )
  );

alter table if exists team_audit_events
  drop constraint if exists team_audit_events_target_type_check;

alter table if exists team_audit_events
  add constraint team_audit_events_target_type_check check (
    target_type in (
      'member',
      'task',
      'comment',
      'announcement',
      'shift_plan',
      'learning_standard'
    )
  );
