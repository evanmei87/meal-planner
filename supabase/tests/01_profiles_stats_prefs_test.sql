begin;
select plan(9);

select has_table('public', 'profiles', 'profiles table exists');
select has_table('public', 'user_stats', 'user_stats table exists');
select has_table('public', 'user_preferences', 'user_preferences table exists');

select col_is_pk('public', 'profiles', 'id', 'profiles PK is id');
select col_type_is('public', 'user_preferences', 'normalized_exclusions', 'text[]',
  'user_preferences.normalized_exclusions is text[]');

select is((select relrowsecurity from pg_class where oid = 'public.user_stats'::regclass),
  true, 'RLS enabled on user_stats');
select is((select relforcerowsecurity from pg_class where oid = 'public.user_preferences'::regclass),
  true, 'RLS forced on user_preferences');

select policies_are('public', 'user_stats', array['owner_all'],
  'user_stats has exactly the owner_all policy');
select policies_are('public', 'profiles', array['owner_all'],
  'profiles has exactly the owner_all policy');

select * from finish();
rollback;
