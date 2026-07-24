-- Shared schema helpers. The seeded owner UUID lives here and only here.

create extension if not exists pgtap with schema extensions;

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create or replace function public.default_owner_id()
returns uuid
language sql
stable
as $$
  select '6372763b-3785-4e07-9a1e-24cb588ba5f3'::uuid;
$$;
