# 🚀 Vercel Deployment Guide

## 1. Import Project
1.  Go to **[Vercel Dashboard](https://vercel.com/dashboard)**.
2.  Click **Add New...** -> **Project**.
3.  Select **`Excel-Mascot`** from the list (Import).

## 2. Configure Project (Critical Step!)
Before clicking Deploy, edit these settings:

*   **Framework Preset**: Ensure it is **Next.js**.
*   **Root Directory**: Click "Edit" and select **`web`**.
    *   (The logic is in the `web` folder, not the root).

## 3. Environment Variables
Expand the **Environment Variables** section and add these two:

| Name | Value |
| :--- | :--- |
| `NEXT_PUBLIC_SUPABASE_URL` | `https://vpmbylsfprzlzrbpvpwj.supabase.co` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZwbWJ5bHNmcHJ6bHpyYnB2cHdqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjU0NDA3MzYsImV4cCI6MjA4MTAxNjczNn0.x8PSU32HC6_oI1k4bRDAH_K_uch2WJQW5ahcPR1npIE` |

*(These are copied from your `python/config.py`)*

## 4. Deploy
1.  Click **Deploy**.
2.  Wait ~1 minute for the build to finish.
3.  You will get a URL like `https://excel-mascot.vercel.app`.

## 5. Test It!
1.  Open the URL on your phone.
2.  Run the Python script locally: `python python/camera_main.py`
3.  Take a photo (Thumbs Up 👍).
4.  Watch it appear on the website instantly!
