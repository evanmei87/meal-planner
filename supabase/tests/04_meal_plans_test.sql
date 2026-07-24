begin;
select plan(9);

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

-- Deleting a meal must detach it from any plan that snapshot-referenced it
-- (ON DELETE SET NULL), not cascade-delete or corrupt the plan-meal row.
insert into auth.users (id) values (public.default_owner_id());

insert into public.meals (name) values ('ON DELETE SET NULL fixture meal');
insert into public.meal_plans (plan_id) values ('on-delete-set-null-fixture-plan');

insert into public.meal_plan_meals (meal_plan_id, day, name, meal_id)
select p.id, 'monday', 'ON DELETE SET NULL fixture meal', m.id
from public.meal_plans p, public.meals m
where p.plan_id = 'on-delete-set-null-fixture-plan'
  and m.name = 'ON DELETE SET NULL fixture meal';

delete from public.meals where name = 'ON DELETE SET NULL fixture meal';

select is(
  (select count(*)::int from public.meal_plan_meals
    where name = 'ON DELETE SET NULL fixture meal'),
  1,
  'meal_plan_meals row survives deletion of the referenced meal');
select is(
  (select meal_id from public.meal_plan_meals
    where name = 'ON DELETE SET NULL fixture meal'),
  null::uuid,
  'meal_plan_meals.meal_id is set to NULL after the referenced meal is deleted');

select * from finish();
rollback;
