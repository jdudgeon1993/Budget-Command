-- Cadence · split buckets (bill schedule)
-- Run once in the Supabase SQL editor. Safe to re-run.
-- Uses TEXT ids to match this project's bcc_buckets.id (which is text), and casts
-- auth.uid() to text in the policy so it works whether user_id is text or uuid.

-- 1) Mark a bucket as "split" (itemised into a bill schedule).
alter table public.bcc_buckets
  add column if not exists split boolean not null default false;

-- 2) The line-items that make up a split bucket (Netflix, Disney+, …).
create table if not exists public.bcc_bucket_items (
  id          text primary key default gen_random_uuid()::text,
  user_id     text    not null,
  bucket_id   text    not null references public.bcc_buckets (id) on delete cascade,
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
  using (auth.uid()::text = user_id)
  with check (auth.uid()::text = user_id);
