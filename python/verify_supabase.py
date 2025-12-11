import os
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY, BUCKET_NAME

print("🔍 Verifying Supabase Connection...")
print(f"   URL: {SUPABASE_URL}")
print(f"   Bucket: {BUCKET_NAME}")

try:
    # 1. Connect
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Client initialized.")

    # 2. Check Table
    print("   Checking 'photos' table...")
    # Try to fetch 1 row. If table missing, this throws error.
    res = supabase.table("photos").select("*").limit(1).execute()
    print("✅ Table 'photos' exists and is accessible.")

    # 3. Check Storage
    print("   Checking Storage Bucket...")
    # List buckets
    res = supabase.storage.list_buckets()
    bucket_found = False
    for b in res:
        if b.name == BUCKET_NAME:
            bucket_found = True
            break
    
    if bucket_found:
        print(f"✅ Bucket '{BUCKET_NAME}' exists.")
        
        # 4. Test Upload (Policy Check)
        print("   Testing Upload Policy...")
        with open("verify_test.txt", "w") as f: f.write("Connection Test")
        
        try:
            with open("verify_test.txt", "rb") as f:
                supabase.storage.from_(BUCKET_NAME).upload("test_connection.txt", f, {"upsert": "true"})
            print("✅ Upload successful (Policies are correct).")
        except Exception as e:
            print(f"❌ Upload Failed: {e}")
            print("   -> Check your Storage Policies in Supabase!")
            
    else:
        print(f"❌ Bucket '{BUCKET_NAME}' NOT found.")

except Exception as e:
    print(f"❌ Verification Failed: {e}")
    print("   -> Check your Credentials or SQL Setup.")
