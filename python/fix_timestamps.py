"""
Fix timestamps for all records based on filename.
"""
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY
from datetime import datetime
import re

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def extract_timestamp_from_filename(filename):
    """Extract timestamp from filename like photo_1768029562_xxx.jpg"""
    match = re.search(r'photo_(\d+)_', filename)
    if match:
        timestamp = int(match.group(1))
        return datetime.utcfromtimestamp(timestamp).isoformat() + '+00:00'
    return None

def fix_timestamps():
    print("📊 Getting all records...")
    response = supabase.table("photos").select("id, image_url, created_at").execute()
    records = response.data
    print(f"   Found {len(records)} records")
    
    updated = 0
    for record in records:
        url = record.get('image_url', '')
        filename = url.split('/')[-1] if url else ''
        
        new_timestamp = extract_timestamp_from_filename(filename)
        if new_timestamp:
            try:
                supabase.table("photos").update({
                    'created_at': new_timestamp
                }).eq('id', record['id']).execute()
                updated += 1
            except Exception as e:
                print(f"   Error updating {record['id']}: {e}")
    
    print(f"\n✅ Updated {updated} records with correct timestamps")

if __name__ == "__main__":
    fix_timestamps()
