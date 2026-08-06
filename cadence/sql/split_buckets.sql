-- Cadence · split buckets (bill schedule)
-- Run this once in the Supabase SQL editor to enable split buckets on live data.
-- Safe to re-run: every statement is guarded with IF NOT EXISTS / OR REPLACE.

-- 1) Mark a bucket as "split" (itemised into a bill schedule).
alter table public.bcc_buckets
  add column if not exists split boolean not null default false;

-- 2) The line-items that make up a split bucket (Netflix, Disney+, …).
--    NOTE: if your bcc_buckets.id / user ids are TEXT rather than UUID, change the
--    two uuid types below to text and drop the "references" clauses to match.
create table if not exists public.bcc_bucket_items (
  id          uuid primary key default gen_random_uuid(),
  user_id     uuid    not null references auth.users (id) on delete cascade,
  bucket_id   uuid    not null references public.bcc_buckets (id) on delete cascade,
  name        text    not null default 'Item',
  amount      numeric not null default 0,
  due_day     text,                       -- '1'..'31' or 'eom'
  paid        boolean not null default false,
  sort_order  integer not null default 0,
  created_at  timestamptz not null default now()
);

create index if not exists bcc_bucket_items_user_idx   on public.bcc_bucket_items (user_id);
create index if not exists bcc_bucket_items_bucket_idx on public.bcc_bucket_items (bucket_id);

-- 3) Row-level security — each user sees and writes only their own items.
alter table public.bcc_bucket_items enable row level security;

drop policy if exists "own bucket items" on public.bcc_bucket_items;
create policy "own bucket items" on public.bcc_bucket_items
  for all
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);
