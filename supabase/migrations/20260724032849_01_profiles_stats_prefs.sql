-- Profiles, TDEE stats, and free-form preferences. One row per user.

create table public.profiles (
  id uuid primary key default public.default_owner_id() references auth.users(id) on delete cascade,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.user_stats (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null default public.default_owner_id() references auth.users(id) on delete cascade,
  height_cm numeric,
  weight_kg numeric,
  age integer,
  gender text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.user_preferences (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null default public.default_owner_id() references auth.users(id) on delete cascade,
  preferences_text text,
  normalized_exclusions text[] not null default '{}',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index user_stats_owner_id_idx on public.user_stats(owner_id);
create index user_preferences_owner_id_idx on public.user_preferences(owner_id);

create trigger set_updated_at before update on public.profiles
  for each row execute function public.set_updated_at();
create trigger set_updated_at before update on public.user_stats
  for each row execute function public.set_updated_at();
create trigger set_updated_at before update on public.user_preferences
  for each row execute function public.set_updated_at();

alter table public.profiles enable row level security;
alter table public.profiles force row level security;
create policy owner_all on public.profiles for all to authenticated
  using (id = auth.uid()) with check (id = auth.uid());

alter table public.user_stats enable row level security;
alter table public.user_stats force row level security;
create policy owner_all on public.user_stats for all to authenticated
  using (owner_id = auth.uid()) with check (owner_id = auth.uid());

alter table public.user_preferences enable row level security;
alter table public.user_preferences force row level security;
create policy owner_all on public.user_preferences for all to authenticated
  using (owner_id = auth.uid()) with check (owner_id = auth.uid());
