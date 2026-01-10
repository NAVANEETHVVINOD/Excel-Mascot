"""
Cleanup script to remove orphaned database records.
These are records in the 'photos' table that point to files
that no longer exist in Supabase Storage.
"""
import requests
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY, BUCKET_NAME

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def cleanup_orphaned_records():
    """
    Find and delete database records where the image file no longer exists.
    """
    print("🔍 Fetching all photo records from database...")
    
    # Get all records from database
    response = supabase.table("photos").select("id, image_url").execute()
    records = response.data
    
    print(f"📊 Found {len(records)} records in database")
    
    orphaned = []
    valid = []
    
    for i, record in enumerate(records):
        image_url = record.get('image_url', '')
        record_id = record.get('id')
        
        if not image_url:
            orphaned.append(record_id)
            continue
        
        # Check if image exists by making a HEAD request
        try:
            resp = requests.head(image_url, timeout=5)
            if resp.status_code == 200:
                valid.append(record_id)
            else:
                orphaned.append(record_id)
                print(f"❌ Orphaned: {record_id} (HTTP {resp.status_code})")
        except Exception as e:
            orphaned.append(record_id)
            print(f"❌ Orphaned: {record_id} (Error: {e})")
        
        # Progress indicator
        if (i + 1) % 50 == 0:
            print(f"   Checked {i + 1}/{len(records)}...")
    
    print(f"\n📊 Results:")
    print(f"   ✅ Valid: {len(valid)}")
    print(f"   ❌ Orphaned: {len(orphaned)}")
    
    if orphaned:
        print(f"\n🗑️ Deleting {len(orphaned)} orphaned records...")
        
        # Delete in batches of 100
        for i in range(0, len(orphaned), 100):
            batch = orphaned[i:i+100]
            for record_id in batch:
                try:
                    supabase.table("photos").delete().eq("id", record_id).execute()
                except Exception as e:
                    print(f"   Failed to delete {record_id}: {e}")
            print(f"   Deleted batch {i//100 + 1}")
        
        print("✅ Cleanup complete!")
    else:
        print("✅ No orphaned records found!")

if __name__ == "__main__":
    cleanup_orphaned_records()
