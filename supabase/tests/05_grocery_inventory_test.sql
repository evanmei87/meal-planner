begin;
select plan(5);

select has_table('public', 'grocery_inventory_items', 'grocery_inventory_items table exists');
select col_is_null('public', 'grocery_inventory_items', 'nutrient_data_bank_number',
  'nutrient_data_bank_number is nullable (unmatched items)');
select fk_ok('public', 'grocery_inventory_items', 'nutrient_data_bank_number',
  'public', 'usda_foods', 'nutrient_data_bank_number',
  'match FK references usda_foods');
select is((select relforcerowsecurity from pg_class where oid = 'public.grocery_inventory_items'::regclass),
  true, 'RLS forced on grocery_inventory_items');
select policies_are('public', 'grocery_inventory_items', array['owner_all'],
  'grocery_inventory_items has exactly the owner_all policy');

select * from finish();
rollback;
