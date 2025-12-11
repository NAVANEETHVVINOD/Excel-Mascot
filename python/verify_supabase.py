import os
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY, BUCKET_NAME

print("[INFO] Verifying Supabase Connection...")
print(f"   URL: {SUPABASE_URL}")
print(f"   Bucket: {BUCKET_NAME}")

try:
    # 1. Connect
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("[OK] Client initialized.")

    # 2. Check Table
    print("   Checking 'photos' table...")
    try:
        res = supabase.table("photos").select("*").limit(1).execute()
        print("[OK] Table 'photos' exists and is accessible.")
    except Exception as e:
        print(f"[FAIL] Table Check Error: {e}")

    # 3. Check Storage
    print("   Checking Storage Bucket...")
    try:
        res = supabase.storage.list_buckets()
        bucket_found = False
        for b in res:
            if b.name == BUCKET_NAME:
                bucket_found = True
                break
        
        if bucket_found:
            print(f"[OK] Bucket '{BUCKET_NAME}' exists.")
            
            # 4. Test Upload
            print("   Testing Upload Policy...")
            with open("verify_test.txt", "w", encoding="utf-8") as f: f.write("Connection Test")
            
            try:
                with open("verify_test.txt", "rb") as f:
                    supabase.storage.from_(BUCKET_NAME).upload("test_connection.txt", f, {"upsert": "true"})
                print("[OK] Upload successful.")
            except Exception as e:
                print(f"[FAIL] Upload Error: {e}")
        else:
            print(f"[FAIL] Bucket '{BUCKET_NAME}' NOT found.")

    except Exception as e:
        print(f"[FAIL] Storage Check Error: {e}")

except Exception as e:
    print(f"[FAIL] Verification Failed: {e}")
