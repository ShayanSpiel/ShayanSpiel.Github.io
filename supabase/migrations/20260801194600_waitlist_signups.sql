-- Isolated waitlist table for the SpielOS waitlist signup form.
-- Public can only INSERT (RLS). No SELECT/UPDATE/DELETE for anon/authenticated.

create table public.waitlist_signups (
  id bigint generated always as identity primary key,
  email text not null,
  locale text not null default 'en',
  created_at timestamptz not null default now(),
  constraint waitlist_signups_email_key unique (email),
  constraint waitlist_signups_email_check check (email ~* '^[^@\s]+@[^@\s]+\.[^@\s]+$'),
  constraint waitlist_signups_locale_check check (locale in ('en', 'fa'))
);

alter table public.waitlist_signups enable row level security;

create policy "waitlist_signups_public_insert"
  on public.waitlist_signups
  for insert
  to anon
  with check (true);
