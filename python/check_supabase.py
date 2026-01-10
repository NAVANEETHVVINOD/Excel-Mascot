"""
Diagnostic script to check Supabase database and storage status.
"""
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY, BUCKET_NAME

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def check_database():
    """Check what's in the photos database table."""
    print("=" * 50)
    print("📊 CHECKING DATABASE (photos table)")
    print("=" * 50)
    
    response = supabase.table("photos").select("*").order("created_at", desc=True).limit(10).execute()
    records = response.data
    
    print(f"Total records in first 10: {len(records)}")
    
    if records:
        print("\nFirst 5 records:")
        for i, record in enumerate(records[:5]):
            print(f"\n  [{i+1}] ID: {record.get('id', 'N/A')}")
            print(f"      URL: {record.get('image_url', 'N/A')[:80]}...")
            print(f"      Created: {record.get('created_at', 'N/A')}")
    else:
        print("❌ No records found in database!")
    
    # Get total count
    count_response = supabase.table("photos").select("id", count="exact").execute()
    print(f"\n📈 Total records in database: {count_response.count}")
    
    return records

def check_storage():
    """Check what's in the photos storage bucket."""
    print("\n" + "=" * 50)
    print("📁 CHECKING STORAGE (photos bucket)")
    print("=" * 50)
    
    try:
        files = supabase.storage.from_(BUCKET_NAME).list()
        print(f"Files in bucket: {len(files)}")
        
        if files:
            print("\nFirst 5 files:")
            for i, f in enumerate(files[:5]):
                print(f"  [{i+1}] {f.get('name', 'N/A')} - {f.get('metadata', {}).get('size', 'N/A')} bytes")
        else:
            print("❌ No files found in storage bucket!")
            
        return files
    except Exception as e:
        print(f"❌ Error accessing storage: {e}")
        return []

def check_url_format():
    """Show the expected URL format."""
    print("\n" + "=" * 50)
    print("🔗 URL FORMAT CHECK")
    print("=" * 50)
    
    expected_base = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/"
    print(f"Expected URL base: {expected_base}")
    print(f"Example full URL: {expected_base}example_photo.jpg")

if __name__ == "__main__":
    print("\n🔍 SUPABASE DIAGNOSTIC CHECK\n")
    
    db_records = check_database()
    storage_files = check_storage()
    check_url_format()
    
    # Cross-reference
    print("\n" + "=" * 50)
    print("🔄 CROSS-REFERENCE CHECK")
    print("=" * 50)
    
    if db_records and storage_files:
        storage_names = set(f.get('name') for f in storage_files)
        
        matched = 0
        orphaned = 0
        
        for record in db_records:
            url = record.get('image_url', '')
            filename = url.split('/')[-1] if url else ''
            
            if filename in storage_names:
                matched += 1
            else:
                orphaned += 1
                print(f"  ❌ Orphaned DB record: {filename}")
        
        print(f"\n✅ Matched: {matched}")
        print(f"❌ Orphaned: {orphaned}")
    
    print("\n" + "=" * 50)
    print("✅ DIAGNOSTIC COMPLETE")
    print("=" * 50)
