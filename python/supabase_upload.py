import os
import time
import uuid
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY, BUCKET_NAME

# Initialize Client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def upload_photo(local_path):
    """
    Uploads a photo to Supabase Storage and inserts metadata into DB.
    Retries 3 times on failure.
    Returns the public URL on success, or None on failure.
    """
    if not os.path.exists(local_path):
        print(f"❌ File not found: {local_path}")
        return None

    # Generate Safe Filename
    # photo_170000_uuid.jpg
    timestamp = int(time.time())
    unique_id = str(uuid.uuid4())[:8]
    filename = f"photo_{timestamp}_{unique_id}.jpg"
    
    # Path in bucket
    storage_path = filename

    public_url = None

    # Retry Logic
    for attempt in range(1, 4):
        try:
            print(f"☁️ Uploading {filename} (Attempt {attempt}/3)...")
            
            # 1. Upload to Storage
            with open(local_path, "rb") as f:
                res = supabase.storage.from_(BUCKET_NAME).upload(
                    path=storage_path,
                    file=f,
                    file_options={"content-type": "image/jpeg"}
                )
            
            # 2. Get Public URL
            # Manually construct to ensure it works (or use get_public_url)
            public_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/{storage_path}"
            
            # 3. Insert into Database
            data = {
                "image_url": public_url
            }
            supabase.table("photos").insert(data).execute()
            
            print(f"✅ Success! Uploaded to Cloud: {public_url}")
            return public_url

        except Exception as e:
            print(f"⚠️ Upload Failed: {e}")
            time.sleep(1) # Wait before retry

    print("❌ Failed to upload after 3 attempts.")
    return None

if __name__ == "__main__":
    # Test
    print("Test run...")
