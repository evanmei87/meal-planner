-- Dated exercise entries and reusable day-of-week presets.

create table public.exercises (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null default public.default_owner_id() references auth.users(id) on delete cascade,
  date date not null,
  day_name text,
  type text not null check (type in ('running','walking','biking','swimming','strength')),
  distance_miles numeric,
  duration_minutes numeric,
  sets integer,
  reps integer,
  calories integer,
  notes text,
  position integer not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.exercise_presets (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null default public.default_owner_id() references auth.users(id) on delete cascade,
  day_of_week text not null check (day_of_week in
    ('Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (owner_id, day_of_week)
);

create table public.exercise_preset_items (
  id uuid primary key default gen_random_uuid(),
  preset_id uuid not null references public.exercise_presets(id) on delete cascade,
  type text not null check (type in ('running','walking','biking','swimming','strength')),
  distance_miles numeric,
  duration_minutes numeric,
  sets integer,
  reps integer,
  notes text,
  position integer not null default 0
);

create index exercises_owner_date_idx on public.exercises(owner_id, date);
create index exercise_presets_owner_id_idx on public.exercise_presets(owner_id);
create index exercise_preset_items_preset_id_idx
  on public.exercise_preset_items(preset_id);

create trigger set_updated_at before update on public.exercises
  for each row execute function public.set_updated_at();
create trigger set_updated_at before update on public.exercise_presets
  for each row execute function public.set_updated_at();

alter table public.exercises enable row level security;
alter table public.exercises force row level security;
create policy owner_all on public.exercises for all to authenticated
  using (owner_id = auth.uid()) with check (owner_id = auth.uid());

alter table public.exercise_presets enable row level security;
alter table public.exercise_presets force row level security;
create policy owner_all on public.exercise_presets for all to authenticated
  using (owner_id = auth.uid()) with check (owner_id = auth.uid());

alter table public.exercise_preset_items enable row level security;
alter table public.exercise_preset_items force row level security;
create policy owner_all on public.exercise_preset_items for all to authenticated
  using (exists (select 1 from public.exercise_presets p where p.id = exercise_preset_items.preset_id and p.owner_id = auth.uid()))
  with check (exists (select 1 from public.exercise_presets p where p.id = exercise_preset_items.preset_id and p.owner_id = auth.uid()));
