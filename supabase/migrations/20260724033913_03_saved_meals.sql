-- Saved meals and their ordered children. Per-ingredient macros are
-- independent estimates and are intentionally NOT constrained to sum to
-- the meal totals.

create table public.meals (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null default public.default_owner_id() references auth.users(id) on delete cascade,
  name text not null,
  version text,
  category text,
  servings integer,
  calories integer,
  protein integer,
  carbs integer,
  fat integer,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.meal_ingredients (
  id uuid primary key default gen_random_uuid(),
  meal_id uuid not null references public.meals(id) on delete cascade,
  name text not null,
  serving text,
  calories integer,
  protein integer,
  carbs integer,
  fat integer,
  position integer not null default 0
);

create table public.meal_instructions (
  id uuid primary key default gen_random_uuid(),
  meal_id uuid not null references public.meals(id) on delete cascade,
  step_order integer not null,
  text text not null
);

create table public.meal_tags (
  meal_id uuid not null references public.meals(id) on delete cascade,
  tag text not null,
  primary key (meal_id, tag)
);

create index meals_owner_id_idx on public.meals(owner_id);
create index meal_ingredients_meal_id_idx on public.meal_ingredients(meal_id);
create index meal_instructions_meal_id_idx on public.meal_instructions(meal_id);

create trigger set_updated_at before update on public.meals
  for each row execute function public.set_updated_at();

alter table public.meals enable row level security;
alter table public.meals force row level security;
create policy owner_all on public.meals for all to authenticated
  using (owner_id = auth.uid()) with check (owner_id = auth.uid());

alter table public.meal_ingredients enable row level security;
alter table public.meal_ingredients force row level security;
create policy owner_all on public.meal_ingredients for all to authenticated
  using (exists (select 1 from public.meals m where m.id = meal_ingredients.meal_id and m.owner_id = auth.uid()))
  with check (exists (select 1 from public.meals m where m.id = meal_ingredients.meal_id and m.owner_id = auth.uid()));

alter table public.meal_instructions enable row level security;
alter table public.meal_instructions force row level security;
create policy owner_all on public.meal_instructions for all to authenticated
  using (exists (select 1 from public.meals m where m.id = meal_instructions.meal_id and m.owner_id = auth.uid()))
  with check (exists (select 1 from public.meals m where m.id = meal_instructions.meal_id and m.owner_id = auth.uid()));

alter table public.meal_tags enable row level security;
alter table public.meal_tags force row level security;
create policy owner_all on public.meal_tags for all to authenticated
  using (exists (select 1 from public.meals m where m.id = meal_tags.meal_id and m.owner_id = auth.uid()))
  with check (exists (select 1 from public.meals m where m.id = meal_tags.meal_id and m.owner_id = auth.uid()));
