-- USDA nutrition reference. Static, shared, read-only to clients.
-- Wide table mirroring src/data/food.csv (one column per nutrient).

create table public.usda_foods (
  nutrient_data_bank_number text primary key,
  category text,
  description text,
  alpha_carotene numeric,
  beta_carotene numeric,
  beta_cryptoxanthin numeric,
  carbohydrate numeric,
  cholesterol numeric,
  choline numeric,
  fiber numeric,
  lutein_zeaxanthin numeric,
  lycopene numeric,
  niacin numeric,
  protein numeric,
  retinol numeric,
  riboflavin numeric,
  selenium numeric,
  sugar_total numeric,
  thiamin numeric,
  water numeric,
  fat_monounsaturated numeric,
  fat_polyunsaturated numeric,
  fat_saturated numeric,
  fat_total_lipid numeric,
  calcium numeric,
  copper numeric,
  iron numeric,
  magnesium numeric,
  phosphorus numeric,
  potassium numeric,
  sodium numeric,
  zinc numeric,
  vitamin_a_rae numeric,
  vitamin_b12 numeric,
  vitamin_b6 numeric,
  vitamin_c numeric,
  vitamin_e numeric,
  vitamin_k numeric
);

create index usda_foods_category_idx on public.usda_foods(category);
create index usda_foods_description_idx on public.usda_foods(description);

alter table public.usda_foods enable row level security;
alter table public.usda_foods force row level security;
create policy read_all_authenticated on public.usda_foods for select to authenticated
  using (true);
