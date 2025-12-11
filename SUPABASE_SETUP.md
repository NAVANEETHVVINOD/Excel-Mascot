# ⚡ Supabase Setup Guide

Follow these steps exactly to enable Cloud Uploads for your Mascot Photo Booth.

## 1. Create Project
1.  Go to [Supabase.com](https://supabase.com) and create a **New Project**.
2.  Give it a name (e.g., `MascotBooth`) and a strong password.
3.  Wait for the database to start.

## 2. Run SQL Setup (One-Click)
Go to the **SQL Editor** (sidebar icon 📝) -> **New Query**.
Paste this entire block and click **Run**:

```sql
-- 1. Create the 'photos' table
create table public.photos (
  id uuid default gen_random_uuid() primary key,
  image_url text not null,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- 2. Enable Row Level Security (RLS)
alter table public.photos enable row level security;

-- 3. Policy: Allow "Anon" (public) users to INSERT photos (Upload)
create policy "Allow Anon Insert Photos"
on public.photos for insert
to anon
with check (true);

-- 4. Policy: Allow "Anon" users to VIEW photos (Gallery)
create policy "Allow Anon Select Photos"
on public.photos for select
to anon
using (true);

-- 5. Create the Storage Bucket 'photos'
insert into storage.buckets (id, name, public)
values ('photos', 'photos', true);

-- 6. Storage Policy: Allow Anon Uploads
create policy "Allow Anon Uploads"
on storage.objects for insert
to anon
with check ( bucket_id = 'photos' );

-- 7. Storage Policy: Allow Public Viewing
create policy "Allow Public Viewing"
on storage.objects for select
to anon
using ( bucket_id = 'photos' );
```

## 3. Get Your Credentials
1.  Go to **Project Settings** (Cog icon ⚙️) -> **API**.
2.  Copy the **Project URL** (e.g., `https://xyz.supabase.co`).
3.  Copy the **`anon` public key**.

**✅ You are ready!**
Paste these two values into the `python/config.py` file I am creating for you.
