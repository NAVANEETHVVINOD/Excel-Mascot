"""
Sync storage files to database - create DB records for any files in storage
that don't have corresponding database entries.
"""
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY, BUCKET_NAME
from datetime import datetime
import re

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def extract_timestamp_from_filename(filename):
    """Extract timestamp from filename like photo_1768029562_xxx.jpg"""
    match = re.search(r'photo_(\d+)_', filename)
    if match:
        timestamp = int(match.group(1))
        return datetime.utcfromtimestamp(timestamp).isoformat() + '+00:00'
    return datetime.utcnow().isoformat() + '+00:00'

def sync_storage_to_db():
    print("📁 Getting storage files...")
    files = supabase.storage.from_(BUCKET_NAME).list()
    storage_files = [f for f in files if f.get('name') and f.get('name') != '.emptyFolderPlaceholder']
    print(f"   Found {len(storage_files)} files in storage")
    
    print("\n📊 Getting database records...")
    response = supabase.table("photos").select("image_url").execute()
    db_urls = set(r.get('image_url', '') for r in response.data)
    db_filenames = set(url.split('/')[-1] for url in db_urls if url)
    print(f"   Found {len(db_filenames)} records in database")
    
    # Find files in storage without DB records
    base_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/"
    missing = []
    
    for f in storage_files:
        filename = f.get('name')
        if filename not in db_filenames:
            missing.append({
                'filename': filename,
                'url': base_url + filename,
                'created_at': extract_timestamp_from_filename(filename)
            })
    
    print(f"\n📊 Results:")
    print(f"   ✅ Already in DB: {len(storage_files) - len(missing)}")
    print(f"   ❌ Missing from DB: {len(missing)}")
    
    if missing:
        print(f"\n➕ Adding {len(missing)} missing records to database...")
        for i, item in enumerate(missing):
            print(f"   [{i+1}] {item['filename']}")
        
        # Insert missing records
        records_to_insert = [
            {
                'image_url': item['url'],
                'created_at': item['created_at']
            }
            for item in missing
        ]
        
        try:
            result = supabase.table("photos").insert(records_to_insert).execute()
            print(f"\n✅ Added {len(result.data)} records to database!")
        except Exception as e:
            print(f"\n❌ Error inserting records: {e}")
    else:
        print("\n✅ All storage files have database records!")
    
    # Final count
    final = supabase.table("photos").select("id", count="exact").execute()
    print(f"\n📈 Final count: {final.count} records in database")

if __name__ == "__main__":
    sync_storage_to_db()
