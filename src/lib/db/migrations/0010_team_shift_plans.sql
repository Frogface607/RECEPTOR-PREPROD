-- Team OS Shift Plans
-- Planned rota and forecast labor cost before actual iiko/RMS shifts arrive.

create table if not exists team_shift_plans (
  id uuid primary key default gen_random_uuid(),
  venue_id uuid not null references venues(id) on delete cascade,
  membership_id uuid not null references venue_memberships(id) on delete cascade,
  shift_date date not null,
  shift_start time,
  shift_end time,
  is_day_off boolean not null default false,
  note text not null default '',
  created_by uuid references profiles(user_id) on delete set null,
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  unique (venue_id, membership_id, shift_date),
  constraint team_shift_plans_time_check check (
    is_day_off or (shift_start is not null and shift_end is not null)
  )
);

create index if not exists idx_team_shift_plans_venue_date
  on team_shift_plans(venue_id, shift_date);
create index if not exists idx_team_shift_plans_member_date
  on team_shift_plans(membership_id, shift_date);

comment on table team_shift_plans is
  'Team OS planned rota: scheduled shifts, days off and forecast labor cost inputs.';

alter table team_shift_plans enable row level security;

drop policy if exists team_shift_plans_owner_all on team_shift_plans;
create policy team_shift_plans_owner_all on team_shift_plans
  for all using (
    venue_id in (select id from venues where owner_user_id = auth.uid())
  ) with check (
    venue_id in (select id from venues where owner_user_id = auth.uid())
  );

drop policy if exists team_shift_plans_manager_all on team_shift_plans;
create policy team_shift_plans_manager_all on team_shift_plans
  for all using (
    exists (
      select 1
      from venue_memberships vm
      where vm.venue_id = team_shift_plans.venue_id
        and vm.user_id = auth.uid()
        and vm.status = 'active'
        and vm.role in (
          'owner',
          'operations_manager',
          'venue_manager',
          'chef'
        )
    )
  ) with check (
    exists (
      select 1
      from venue_memberships vm
      where vm.venue_id = team_shift_plans.venue_id
        and vm.user_id = auth.uid()
        and vm.status = 'active'
        and vm.role in (
          'owner',
          'operations_manager',
          'venue_manager',
          'chef'
        )
    )
  );

drop policy if exists team_shift_plans_staff_select on team_shift_plans;
create policy team_shift_plans_staff_select on team_shift_plans
  for select using (
    exists (
      select 1
      from venue_memberships vm
      where vm.id = team_shift_plans.membership_id
        and vm.venue_id = team_shift_plans.venue_id
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
      'shift_plan_updated'
    )
  );

alter table if exists team_audit_events
  drop constraint if exists team_audit_events_target_type_check;

alter table if exists team_audit_events
  add constraint team_audit_events_target_type_check check (
    target_type in ('member', 'task', 'comment', 'announcement', 'shift_plan')
  );
