begin;
select plan(7);

select has_table('public', 'exercises', 'exercises table exists');
select has_table('public', 'exercise_presets', 'exercise_presets table exists');
select has_table('public', 'exercise_preset_items', 'exercise_preset_items table exists');

select col_type_is('public', 'exercises', 'date', 'date', 'exercises.date is a date column');
select fk_ok('public', 'exercise_preset_items', 'preset_id',
  'public', 'exercise_presets', 'id',
  'exercise_preset_items.preset_id references exercise_presets.id');
select policies_are('public', 'exercises', array['owner_all'],
  'exercises has exactly the owner_all policy');
select policies_are('public', 'exercise_preset_items', array['owner_all'],
  'exercise_preset_items inherits ownership via one policy');

select * from finish();
rollback;
