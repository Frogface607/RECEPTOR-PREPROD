-- Team OS Announcement Reads
-- Read receipts turn announcements from broadcast into a measurable loop.

create table if not exists team_announcement_reads (
  id uuid primary key default gen_random_uuid(),
  venue_id uuid not null references venues(id) on delete cascade,
  announcement_id uuid not null references team_announcements(id) on delete cascade,
  membership_id uuid not null references venue_memberships(id) on delete cascade,
  read_at timestamptz not null default now(),
  created_at timestamptz not null default now(),
  unique (announcement_id, membership_id)
);

create index if not exists idx_team_announcement_reads_venue
  on team_announcement_reads(venue_id, read_at desc);
create index if not exists idx_team_announcement_reads_announcement
  on team_announcement_reads(announcement_id, read_at desc);
create index if not exists idx_team_announcement_reads_membership
  on team_announcement_reads(membership_id, read_at desc);

comment on table team_announcement_reads is
  'Read receipts for Team OS announcements by membership.';

alter table team_announcement_reads enable row level security;

drop policy if exists team_announcement_reads_owner_all on team_announcement_reads;
create policy team_announcement_reads_owner_all on team_announcement_reads
  for all using (
    venue_id in (select id from venues where owner_user_id = auth.uid())
  ) with check (
    venue_id in (select id from venues where owner_user_id = auth.uid())
  );

drop policy if exists team_announcement_reads_manager_select on team_announcement_reads;
create policy team_announcement_reads_manager_select on team_announcement_reads
  for select using (
    exists (
      select 1
      from venue_memberships vm
      where vm.venue_id = team_announcement_reads.venue_id
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

drop policy if exists team_announcement_reads_staff_select on team_announcement_reads;
create policy team_announcement_reads_staff_select on team_announcement_reads
  for select using (
    exists (
      select 1
      from venue_memberships vm
      where vm.id = team_announcement_reads.membership_id
        and vm.venue_id = team_announcement_reads.venue_id
        and vm.user_id = auth.uid()
        and vm.status = 'active'
    )
  );

drop policy if exists team_announcement_reads_staff_insert on team_announcement_reads;
create policy team_announcement_reads_staff_insert on team_announcement_reads
  for insert with check (
    exists (
      select 1
      from venue_memberships vm
      join team_announcements ta on ta.id = team_announcement_reads.announcement_id
      where vm.id = team_announcement_reads.membership_id
        and vm.venue_id = team_announcement_reads.venue_id
        and ta.venue_id = team_announcement_reads.venue_id
        and vm.user_id = auth.uid()
        and vm.status = 'active'
        and (
          ta.audience_type = 'venue'
          or ta.audience_role = vm.role
          or vm.role in ('owner', 'operations_manager', 'venue_manager')
        )
    )
  );

drop policy if exists team_announcement_reads_staff_update on team_announcement_reads;
create policy team_announcement_reads_staff_update on team_announcement_reads
  for update using (
    exists (
      select 1
      from venue_memberships vm
      where vm.id = team_announcement_reads.membership_id
        and vm.venue_id = team_announcement_reads.venue_id
        and vm.user_id = auth.uid()
        and vm.status = 'active'
    )
  ) with check (
    exists (
      select 1
      from venue_memberships vm
      where vm.id = team_announcement_reads.membership_id
        and vm.venue_id = team_announcement_reads.venue_id
        and vm.user_id = auth.uid()
        and vm.status = 'active'
    )
  );
