-- Generated meal plans. Meals are stored as snapshots decoupled from the
-- saved meals they came from.

create table public.meal_plans (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null default public.default_owner_id() references auth.users(id) on delete cascade,
  plan_id text,
  current_day text,
  inventory_usage jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.meal_plan_meals (
  id uuid primary key default gen_random_uuid(),
  meal_plan_id uuid not null references public.meal_plans(id) on delete cascade,
  day text not null,
  position integer not null default 0,
  name text not null,
  calories integer,
  protein integer,
  carbs integer,
  fat integer,
  ingredients jsonb not null default '[]',
  meal_id uuid references public.meals(id) on delete set null
);

create table public.meal_plan_grocery_items (
  id uuid primary key default gen_random_uuid(),
  meal_plan_id uuid not null references public.meal_plans(id) on delete cascade,
  item text not null,
  quantity numeric,
  unit text,
  category text
);

create index meal_plans_owner_id_idx on public.meal_plans(owner_id);
create index meal_plan_meals_plan_day_pos_idx
  on public.meal_plan_meals(meal_plan_id, day, position);
create index meal_plan_grocery_items_plan_id_idx
  on public.meal_plan_grocery_items(meal_plan_id);

create trigger set_updated_at before update on public.meal_plans
  for each row execute function public.set_updated_at();

alter table public.meal_plans enable row level security;
alter table public.meal_plans force row level security;
create policy owner_all on public.meal_plans for all to authenticated
  using (owner_id = auth.uid()) with check (owner_id = auth.uid());

alter table public.meal_plan_meals enable row level security;
alter table public.meal_plan_meals force row level security;
create policy owner_all on public.meal_plan_meals for all to authenticated
  using (exists (select 1 from public.meal_plans p where p.id = meal_plan_meals.meal_plan_id and p.owner_id = auth.uid()))
  with check (exists (select 1 from public.meal_plans p where p.id = meal_plan_meals.meal_plan_id and p.owner_id = auth.uid()));

alter table public.meal_plan_grocery_items enable row level security;
alter table public.meal_plan_grocery_items force row level security;
create policy owner_all on public.meal_plan_grocery_items for all to authenticated
  using (exists (select 1 from public.meal_plans p where p.id = meal_plan_grocery_items.meal_plan_id and p.owner_id = auth.uid()))
  with check (exists (select 1 from public.meal_plans p where p.id = meal_plan_grocery_items.meal_plan_id and p.owner_id = auth.uid()));
