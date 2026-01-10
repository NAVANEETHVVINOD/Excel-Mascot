"""
Fast cleanup - delete all DB records that don't match storage files.
"""
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY, BUCKET_NAME

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def fast_cleanup():
    print("📁 Getting storage files...")
    files = supabase.storage.from_(BUCKET_NAME).list()
    storage_filenames = set(f.get('name') for f in files if f.get('name') != '.emptyFolderPlaceholder')
    print(f"   Found {len(storage_filenames)} files in storage")
    
    print("\n📊 Getting database records...")
    # Get all records
    all_records = []
    offset = 0
    while True:
        response = supabase.table("photos").select("id, image_url").range(offset, offset + 999).execute()
        if not response.data:
            break
        all_records.extend(response.data)
        offset += 1000
        print(f"   Fetched {len(all_records)} records...")
    
    print(f"   Total: {len(all_records)} records in database")
    
    # Find orphaned records
    orphaned_ids = []
    valid_ids = []
    
    for record in all_records:
        url = record.get('image_url', '')
        filename = url.split('/')[-1] if url else ''
        
        if filename in storage_filenames:
            valid_ids.append(record['id'])
        else:
            orphaned_ids.append(record['id'])
    
    print(f"\n📊 Results:")
    print(f"   ✅ Valid: {len(valid_ids)}")
    print(f"   ❌ Orphaned: {len(orphaned_ids)}")
    
    if orphaned_ids:
        print(f"\n🗑️ Deleting {len(orphaned_ids)} orphaned records...")
        
        # Delete in batches of 50 using IN clause
        for i in range(0, len(orphaned_ids), 50):
            batch = orphaned_ids[i:i+50]
            try:
                supabase.table("photos").delete().in_("id", batch).execute()
                print(f"   Deleted batch {i//50 + 1} ({len(batch)} records)")
            except Exception as e:
                print(f"   Error in batch {i//50 + 1}: {e}")
        
        print("\n✅ Cleanup complete!")
    else:
        print("\n✅ No orphaned records to delete!")
    
    # Verify
    count = supabase.table("photos").select("id", count="exact").execute()
    print(f"\n📈 Final count: {count.count} records in database")

if __name__ == "__main__":
    fast_cleanup()
