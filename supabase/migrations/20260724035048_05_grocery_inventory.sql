-- Grocery inventory on hand. Matched + unmatched unified in one table;
-- unmatched items have a null nutrient_data_bank_number.

create table public.grocery_inventory_items (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null default public.default_owner_id() references auth.users(id) on delete cascade,
  raw_phrase text,
  standardized_item text,
  unit text,
  quantity numeric,
  category text,
  nutrient_data_bank_number text references public.usda_foods(nutrient_data_bank_number),
  corgis_description text,
  corgis_category text,
  corgis_style_query text,
  confidence_score numeric,
  confidence_level text,
  should_auto_save boolean,
  source text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index grocery_inventory_items_owner_id_idx
  on public.grocery_inventory_items(owner_id);
create index grocery_inventory_items_ndbn_idx
  on public.grocery_inventory_items(nutrient_data_bank_number);

create trigger set_updated_at before update on public.grocery_inventory_items
  for each row execute function public.set_updated_at();

alter table public.grocery_inventory_items enable row level security;
alter table public.grocery_inventory_items force row level security;
create policy owner_all on public.grocery_inventory_items for all to authenticated
  using (owner_id = auth.uid()) with check (owner_id = auth.uid());
