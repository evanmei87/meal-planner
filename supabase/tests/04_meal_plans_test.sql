begin;
select plan(7);

select has_table('public', 'meal_plans', 'meal_plans table exists');
select has_table('public', 'meal_plan_meals', 'meal_plan_meals table exists');
select has_table('public', 'meal_plan_grocery_items', 'meal_plan_grocery_items table exists');

select col_type_is('public', 'meal_plans', 'inventory_usage', 'jsonb',
  'meal_plans.inventory_usage is jsonb');
select col_is_null('public', 'meal_plan_meals', 'meal_id',
  'meal_plan_meals.meal_id is nullable (provenance only)');
select fk_ok('public', 'meal_plan_meals', 'meal_plan_id', 'public', 'meal_plans', 'id',
  'meal_plan_meals.meal_plan_id references meal_plans.id');
select policies_are('public', 'meal_plan_grocery_items', array['owner_all'],
  'meal_plan_grocery_items inherits ownership via one policy');

select * from finish();
rollback;
