begin;
select plan(8);

select has_table('public', 'meals', 'meals table exists');
select has_table('public', 'meal_ingredients', 'meal_ingredients table exists');
select has_table('public', 'meal_instructions', 'meal_instructions table exists');
select has_table('public', 'meal_tags', 'meal_tags table exists');

select col_is_pk('public', 'meal_tags', array['meal_id', 'tag'],
  'meal_tags PK is (meal_id, tag)');
select fk_ok('public', 'meal_ingredients', 'meal_id', 'public', 'meals', 'id',
  'meal_ingredients.meal_id references meals.id');

select is((select relforcerowsecurity from pg_class where oid = 'public.meals'::regclass),
  true, 'RLS forced on meals');
select policies_are('public', 'meal_ingredients', array['owner_all'],
  'meal_ingredients inherits ownership via one policy');

select * from finish();
rollback;
