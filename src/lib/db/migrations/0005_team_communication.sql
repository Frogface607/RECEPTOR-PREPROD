-- Team OS Communication
-- Task comments and operational announcements. This is the controlled
-- communication layer before a full realtime chat.

create table if not exists team_task_comments (
  id uuid primary key default gen_random_uuid(),
  venue_id uuid not null references venues(id) on delete cascade,
  task_id uuid not null references team_tasks(id) on delete cascade,
  author_membership_id uuid references venue_memberships(id) on delete set null,
  author_user_id uuid references profiles(user_id) on delete set null,
  body text not null,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create index if not exists idx_team_task_comments_task
  on team_task_comments(task_id, created_at asc);
create index if not exists idx_team_task_comments_venue
  on team_task_comments(venue_id, created_at desc);

create table if not exists team_announcements (
  id uuid primary key default gen_random_uuid(),
  venue_id uuid not null references venues(id) on delete cascade,
  title text not null,
  body text not null,
  priority text not null default 'normal' check (
    priority in ('normal', 'important')
  ),
  audience_type text not null check (
    audience_type in ('role', 'venue')
  ),
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
  created_by uuid references profiles(user_id) on delete set null,
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  constraint team_announcements_audience_check check (
    (audience_type = 'role' and audience_role is not null)
    or audience_type = 'venue'
  )
);

create index if not exists idx_team_announcements_venue
  on team_announcements(venue_id, created_at desc);
create index if not exists idx_team_announcements_role
  on team_announcements(venue_id, audience_role, created_at desc);

comment on table team_task_comments is
  'Task-scoped communication for Team OS.';

comment on table team_announcements is
  'Operational announcements addressed to a venue or role.';

alter table team_task_comments enable row level security;
alter table team_announcements enable row level security;

-- Owners can manage all task comments for owned venues.
drop policy if exists team_task_comments_owner_all on team_task_comments;
create policy team_task_comments_owner_all on team_task_comments
  for all using (
    venue_id in (select id from venues where owner_user_id = auth.uid())
  ) with check (
    venue_id in (select id from venues where owner_user_id = auth.uid())
  );

-- Active staff can read comments for tasks visible to their membership.
drop policy if exists team_task_comments_staff_select on team_task_comments;
create policy team_task_comments_staff_select on team_task_comments
  for select using (
    exists (
      select 1
      from venue_memberships vm
      join team_tasks tt on tt.id = team_task_comments.task_id
      where vm.venue_id = team_task_comments.venue_id
        and vm.user_id = auth.uid()
        and vm.status = 'active'
        and (
          tt.audience_type = 'venue'
          or (tt.audience_type = 'role' and tt.audience_role = vm.role)
          or (tt.audience_type = 'member' and tt.audience_member_id = vm.id)
          or vm.role in (
            'owner',
            'operations_manager',
            'venue_manager',
            'chef',
            'marketing'
          )
        )
    )
  );

-- Active staff can comment on tasks visible to them.
drop policy if exists team_task_comments_staff_insert on team_task_comments;
create policy team_task_comments_staff_insert on team_task_comments
  for insert with check (
    author_user_id = auth.uid()
    and exists (
      select 1
      from venue_memberships vm
      join team_tasks tt on tt.id = team_task_comments.task_id
      where vm.venue_id = team_task_comments.venue_id
        and vm.user_id = auth.uid()
        and vm.status = 'active'
        and (
          tt.audience_type = 'venue'
          or (tt.audience_type = 'role' and tt.audience_role = vm.role)
          or (tt.audience_type = 'member' and tt.audience_member_id = vm.id)
          or vm.role in (
            'owner',
            'operations_manager',
            'venue_manager',
            'chef',
            'marketing'
          )
        )
    )
  );

-- Owners can manage announcements for owned venues.
drop policy if exists team_announcements_owner_all on team_announcements;
create policy team_announcements_owner_all on team_announcements
  for all using (
    venue_id in (select id from venues where owner_user_id = auth.uid())
  ) with check (
    venue_id in (select id from venues where owner_user_id = auth.uid())
  );

-- Active staff can read venue-wide announcements and announcements for their role.
drop policy if exists team_announcements_staff_select on team_announcements;
create policy team_announcements_staff_select on team_announcements
  for select using (
    exists (
      select 1
      from venue_memberships vm
      where vm.venue_id = team_announcements.venue_id
        and vm.user_id = auth.uid()
        and vm.status = 'active'
        and (
          team_announcements.audience_type = 'venue'
          or team_announcements.audience_role = vm.role
          or vm.role in ('owner', 'operations_manager', 'venue_manager')
        )
    )
  );

-- Managers/chefs/marketers can create operational announcements.
drop policy if exists team_announcements_staff_insert on team_announcements;
create policy team_announcements_staff_insert on team_announcements
  for insert with check (
    created_by = auth.uid()
    and exists (
      select 1
      from venue_memberships vm
      where vm.venue_id = team_announcements.venue_id
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
