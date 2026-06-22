-- Team OS
-- Role-based memberships and operational tasks for restaurant teams.
-- Idempotent: safe to re-run after 0001_init.sql.

create table if not exists venue_memberships (
  id uuid primary key default gen_random_uuid(),
  venue_id uuid not null references venues(id) on delete cascade,
  user_id uuid references profiles(user_id) on delete set null,
  full_name text not null,
  email text,
  phone text,
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
  status text not null default 'active' check (
    status in ('active', 'invited', 'paused')
  ),
  shift_label text default '',
  created_by uuid references profiles(user_id) on delete set null,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create index if not exists idx_venue_memberships_venue
  on venue_memberships(venue_id);
create index if not exists idx_venue_memberships_user
  on venue_memberships(user_id);
create unique index if not exists idx_venue_memberships_venue_user
  on venue_memberships(venue_id, user_id)
  where user_id is not null;

create table if not exists team_tasks (
  id uuid primary key default gen_random_uuid(),
  venue_id uuid not null references venues(id) on delete cascade,
  title text not null,
  source text not null default 'manager' check (
    source in ('owner', 'copilot', 'manager', 'chef')
  ),
  priority text not null default 'medium' check (
    priority in ('high', 'medium', 'low')
  ),
  status text not null default 'new' check (
    status in ('new', 'accepted', 'in_progress', 'done', 'verified')
  ),
  audience_type text not null check (
    audience_type in ('member', 'role', 'venue')
  ),
  audience_member_id uuid references venue_memberships(id) on delete set null,
  audience_role text check (
    audience_role in (
      'owner',
      'operations_manager',
      'venue_manager',
      'chef',
      'line_cook',
      'service',
      'marketing'
    )
  ),
  due_at timestamptz,
  due_label text default '',
  created_by uuid references profiles(user_id) on delete set null,
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  constraint team_tasks_audience_check check (
    (audience_type = 'member' and audience_member_id is not null)
    or (audience_type = 'role' and audience_role is not null)
    or (audience_type = 'venue')
  )
);

create index if not exists idx_team_tasks_venue_status
  on team_tasks(venue_id, status, created_at desc);
create index if not exists idx_team_tasks_audience_member
  on team_tasks(audience_member_id);
create index if not exists idx_team_tasks_audience_role
  on team_tasks(venue_id, audience_role);

comment on table venue_memberships is
  'Team OS memberships: who has access to a venue and which restaurant role they have.';

comment on table team_tasks is
  'Team OS operational tasks assigned to a member, role, or the whole venue.';

alter table venue_memberships enable row level security;
alter table team_tasks enable row level security;

-- Memberships:
-- Owner can manage all memberships for owned venues.
-- Staff can read their own membership row.
drop policy if exists venue_memberships_owner_all on venue_memberships;
create policy venue_memberships_owner_all on venue_memberships
  for all using (
    venue_id in (select id from venues where owner_user_id = auth.uid())
  ) with check (
    venue_id in (select id from venues where owner_user_id = auth.uid())
  );

drop policy if exists venue_memberships_self_select on venue_memberships;
create policy venue_memberships_self_select on venue_memberships
  for select using (user_id = auth.uid());

-- Tasks:
-- Owners can manage tasks for owned venues.
drop policy if exists team_tasks_owner_all on team_tasks;
create policy team_tasks_owner_all on team_tasks
  for all using (
    venue_id in (select id from venues where owner_user_id = auth.uid())
  ) with check (
    venue_id in (select id from venues where owner_user_id = auth.uid())
  );

-- Active staff can read tasks for their venue if assigned to:
-- the whole venue, their role, or their own membership.
drop policy if exists team_tasks_staff_select on team_tasks;
create policy team_tasks_staff_select on team_tasks
  for select using (
    exists (
      select 1
      from venue_memberships vm
      where vm.venue_id = team_tasks.venue_id
        and vm.user_id = auth.uid()
        and vm.status = 'active'
        and (
          team_tasks.audience_type = 'venue'
          or (
            team_tasks.audience_type = 'role'
            and team_tasks.audience_role = vm.role
          )
          or (
            team_tasks.audience_type = 'member'
            and team_tasks.audience_member_id = vm.id
          )
        )
    )
  );

-- Managers/chefs/marketers can create and update operational tasks for their
-- venue. Line staff complete tasks through narrow future actions, not direct
-- broad write access.
drop policy if exists team_tasks_staff_write on team_tasks;
create policy team_tasks_staff_write on team_tasks
  for all using (
    exists (
      select 1
      from venue_memberships vm
      where vm.venue_id = team_tasks.venue_id
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
  ) with check (
    exists (
      select 1
      from venue_memberships vm
      where vm.venue_id = team_tasks.venue_id
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
