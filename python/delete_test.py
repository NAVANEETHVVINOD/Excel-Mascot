"""
Test delete functionality
"""
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY, BUCKET_NAME

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Get one orphaned record
response = supabase.table("photos").select("id, image_url").limit(1).execute()
if response.data:
    record = response.data[0]
    print(f"Testing delete on: {record['id']}")
    print(f"URL: {record['image_url']}")
    
    # Try to delete
    try:
        result = supabase.table("photos").delete().eq("id", record['id']).execute()
        print(f"Delete result: {result}")
    except Exception as e:
        print(f"Delete error: {e}")
    
    # Check if it's still there
    check = supabase.table("photos").select("id").eq("id", record['id']).execute()
    if check.data:
        print("❌ Record still exists - DELETE not working!")
        print("This is likely a Row Level Security (RLS) issue.")
        print("You need to either:")
        print("1. Disable RLS on the photos table in Supabase dashboard")
        print("2. Add a policy allowing deletes for anon users")
        print("3. Use a service_role key instead of anon key")
    else:
        print("✅ Record deleted successfully!")
