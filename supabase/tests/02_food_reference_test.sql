begin;
select plan(6);

select has_table('public', 'usda_foods', 'usda_foods table exists');
select col_is_pk('public', 'usda_foods', 'nutrient_data_bank_number',
  'usda_foods PK is nutrient_data_bank_number');
select has_column('public', 'usda_foods', 'protein', 'usda_foods has protein column');
select has_column('public', 'usda_foods', 'fat_monounsaturated',
  'misspelled CSV header normalized to fat_monounsaturated');
select is((select relrowsecurity from pg_class where oid = 'public.usda_foods'::regclass),
  true, 'RLS enabled on usda_foods');
select policies_are('public', 'usda_foods', array['read_all_authenticated'],
  'usda_foods exposes only a read policy');

select * from finish();
rollback;
