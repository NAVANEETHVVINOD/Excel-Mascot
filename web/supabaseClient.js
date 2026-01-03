import { createClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || "https://vpmbylsfprzlzrbpvpwj.supabase.co";
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZwbWJ5bHNmcHJ6bHpyYnB2cHdqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjU0NDA3MzYsImV4cCI6MjA4MTAxNjczNn0.x8PSU32HC6_oI1k4bRDAH_K_uch2WJQW5ahcPR1npIE";

export const supabase = createClient(supabaseUrl, supabaseAnonKey);
