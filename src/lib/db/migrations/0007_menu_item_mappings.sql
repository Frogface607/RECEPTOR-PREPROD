-- Menu item mappings
-- Links sales rows from iiko BI to nomenclature products and later tech cards.
-- Idempotent: safe to re-run after 0001_init.sql and Team OS migrations.

create table if not exists menu_item_mappings (
  id uuid primary key default gen_random_uuid(),
  venue_id uuid not null references venues(id) on delete cascade,
  dish_key text not null,
  dish_name text not null,
  dish_group text default '',
  iiko_product_id text,
  iiko_product_name text,
  iiko_article text,
  tech_card_id uuid,
  mapping_type text not null default 'manual' check (
    mapping_type in ('manual', 'auto', 'imported')
  ),
  status text not null default 'active' check (
    status in ('active', 'ignored', 'needs_review')
  ),
  confidence numeric(4, 3) default 1.0,
  note text default '',
  created_by uuid references profiles(user_id) on delete set null,
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  unique (venue_id, dish_key)
);

create index if not exists idx_menu_item_mappings_venue
  on menu_item_mappings(venue_id);
create index if not exists idx_menu_item_mappings_product
  on menu_item_mappings(venue_id, iiko_product_id);
create index if not exists idx_menu_item_mappings_article
  on menu_item_mappings(venue_id, iiko_article);

comment on table menu_item_mappings is
  'Manual and automatic links between sold dishes, iiko nomenclature products and future tech cards.';

alter table menu_item_mappings enable row level security;

drop policy if exists menu_item_mappings_owner_all on menu_item_mappings;
create policy menu_item_mappings_owner_all on menu_item_mappings
  for all using (
    venue_id in (select id from venues where owner_user_id = auth.uid())
  ) with check (
    venue_id in (select id from venues where owner_user_id = auth.uid())
  );

drop policy if exists menu_item_mappings_staff_select on menu_item_mappings;
create policy menu_item_mappings_staff_select on menu_item_mappings
  for select using (
    exists (
      select 1
      from venue_memberships vm
      where vm.venue_id = menu_item_mappings.venue_id
        and vm.user_id = auth.uid()
        and vm.status = 'active'
    )
  );

drop policy if exists menu_item_mappings_staff_write on menu_item_mappings;
create policy menu_item_mappings_staff_write on menu_item_mappings
  for all using (
    exists (
      select 1
      from venue_memberships vm
      where vm.venue_id = menu_item_mappings.venue_id
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
      where vm.venue_id = menu_item_mappings.venue_id
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
