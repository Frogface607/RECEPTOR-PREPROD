-- Team OS Learning Progress
-- Persistent lesson/test progress for employee cabinets and manager oversight.
-- Idempotent: safe to re-run after Team OS migrations.

create table if not exists team_learning_progress (
  id uuid primary key default gen_random_uuid(),
  venue_id uuid not null references venues(id) on delete cascade,
  membership_id uuid not null references venue_memberships(id) on delete cascade,
  user_id uuid references profiles(user_id) on delete set null,
  module_id text not null,
  best_percentage integer not null default 0 check (
    best_percentage >= 0 and best_percentage <= 100
  ),
  last_percentage integer not null default 0 check (
    last_percentage >= 0 and last_percentage <= 100
  ),
  correct_count integer not null default 0 check (correct_count >= 0),
  total_questions integer not null default 0 check (total_questions >= 0),
  passed boolean not null default false,
  answers jsonb not null default '[]'::jsonb,
  completed_at timestamptz default now(),
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  unique (venue_id, membership_id, module_id)
);

create index if not exists idx_team_learning_progress_venue
  on team_learning_progress(venue_id, completed_at desc);
create index if not exists idx_team_learning_progress_member
  on team_learning_progress(membership_id, module_id);
create index if not exists idx_team_learning_progress_module
  on team_learning_progress(venue_id, module_id);

comment on table team_learning_progress is
  'Team OS training progress: lesson checks completed by staff members.';

alter table team_learning_progress enable row level security;

drop policy if exists team_learning_progress_owner_all on team_learning_progress;
create policy team_learning_progress_owner_all on team_learning_progress
  for all using (
    venue_id in (select id from venues where owner_user_id = auth.uid())
  ) with check (
    venue_id in (select id from venues where owner_user_id = auth.uid())
  );

drop policy if exists team_learning_progress_manager_select on team_learning_progress;
create policy team_learning_progress_manager_select on team_learning_progress
  for select using (
    exists (
      select 1
      from venue_memberships vm
      where vm.venue_id = team_learning_progress.venue_id
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

drop policy if exists team_learning_progress_staff_select on team_learning_progress;
create policy team_learning_progress_staff_select on team_learning_progress
  for select using (
    exists (
      select 1
      from venue_memberships vm
      where vm.id = team_learning_progress.membership_id
        and vm.venue_id = team_learning_progress.venue_id
        and vm.user_id = auth.uid()
        and vm.status = 'active'
    )
  );

drop policy if exists team_learning_progress_staff_insert on team_learning_progress;
create policy team_learning_progress_staff_insert on team_learning_progress
  for insert with check (
    user_id = auth.uid()
    and exists (
      select 1
      from venue_memberships vm
      where vm.id = team_learning_progress.membership_id
        and vm.venue_id = team_learning_progress.venue_id
        and vm.user_id = auth.uid()
        and vm.status = 'active'
    )
  );

drop policy if exists team_learning_progress_staff_update on team_learning_progress;
create policy team_learning_progress_staff_update on team_learning_progress
  for update using (
    user_id = auth.uid()
    and exists (
      select 1
      from venue_memberships vm
      where vm.id = team_learning_progress.membership_id
        and vm.venue_id = team_learning_progress.venue_id
        and vm.user_id = auth.uid()
        and vm.status = 'active'
    )
  ) with check (
    user_id = auth.uid()
    and exists (
      select 1
      from venue_memberships vm
      where vm.id = team_learning_progress.membership_id
        and vm.venue_id = team_learning_progress.venue_id
        and vm.user_id = auth.uid()
        and vm.status = 'active'
    )
  );
