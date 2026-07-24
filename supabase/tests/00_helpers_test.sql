begin;
select plan(2);

select has_function(
  'public', 'set_updated_at', array[]::text[],
  'set_updated_at() trigger function exists'
);

select has_function(
  'public', 'default_owner_id', array[]::text[],
  'default_owner_id() function exists'
);

select * from finish();
rollback;
