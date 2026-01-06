import os
import time
import uuid
from datetime import datetime
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY, BUCKET_NAME

from sync_queue import SyncQueue

# Initialize Client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
sync_queue = SyncQueue()

def cleanup_storage(limit=600):
    """
    Enforces a rolling window of photos.
    Keeps only the latest `limit` photos.
    Deletes older ones from Storage & DB.
    """
    try:
        # Fetch all photos sorted by Time (Oldest -> Newest)
        # We don't use 'id' as it might not be primary or reliable. Filename is our key.
        resp = supabase.table("photos").select("filename, image_url, created_at").order("created_at", desc=False).execute()
        photos = resp.data
        
        count = len(photos)
        if count > limit:
            extra = count - limit
            print(f"🧹 Cleanup: Found {count} photos. Limit is {limit}. Deleting {extra} old photos...")
            
            for i in range(extra):
                old = photos[i]
                
                fname = old.get("filename")
                if fname:
                    # 1. Delete from Storage
                    try:
                        supabase.storage.from_(BUCKET_NAME).remove([fname])
                    except Exception as stor_err:
                        print(f"⚠️ Storage delete error for {fname}: {stor_err}")

                    # 2. Delete from DB (Match by filename)
                    # Use filename instead of id since id crashed previously
                    supabase.table("photos").delete().eq("filename", fname).execute()
                    
                    print(f"🗑️ Deleted Old Photo: {fname}")
                
    except Exception as e:
        print(f"⚠️ Cleanup Error: {e}")

def upload_photo(local_path, metadata=None):
    """
    Uploads a photo to Supabase.
    If online: Uploads immediately.
    If offline/fail: Adds to SyncQueue.
    """
    if not os.path.exists(local_path):
        print(f"❌ File not found: {local_path}")
        return None

    # Generate Safe Filename
    timestamp = int(time.time())
    unique_id = str(uuid.uuid4())[:8]
    filename = f"photo_{timestamp}_{unique_id}.jpg"
    storage_path = filename

    public_url = None

    # Retry Logic for Online Upload
    for attempt in range(1, 4):
        try:
            print(f"☁️ Uploading {filename} (Attempt {attempt}/3)...")
            
            with open(local_path, "rb") as f:
                res = supabase.storage.from_(BUCKET_NAME).upload(
                    path=storage_path,
                    file=f,
                    file_options={"content-type": "image/jpeg"}
                )
            
            public_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/{storage_path}"
            
            data = {"image_url": public_url}
            if metadata: 
                data.update(metadata)

            supabase.table("photos").insert(data).execute()
            
            print(f"✅ Success! Uploaded to Cloud: {public_url}")
            
            # If success, also try to process pending queue!
            process_queue()
            
            # Enforce Storage Limit
            cleanup_storage(600)
            
            return public_url

        except Exception as e:
            print(f"⚠️ Upload Failed: {e}")
            time.sleep(1)

    print("❌ Upload failed. Queuing for offline sync.")
    sync_queue.add(local_path, metadata)
    return None

def upload_bytes(file_bytes, filename, metadata=None):
    """
    Uploads bytes directly to Supabase without local file.
    Cloud-only mode: Does NOT save locally if upload fails.
    """
    storage_path = filename
    public_url = None

    for attempt in range(1, 4):
        try:
            print(f"☁️ Uploading Bytes {filename} (Attempt {attempt}/3)...")
            
            # Determine content type
            content_type = "image/jpeg"
            if filename.endswith(".gif"):
                content_type = "image/gif"
            elif filename.endswith(".png"):
                content_type = "image/png"
            
            res = supabase.storage.from_(BUCKET_NAME).upload(
                path=storage_path,
                file=file_bytes,
                file_options={"content-type": content_type}
            )
            
            public_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/{storage_path}"
            
            data = {"image_url": public_url}
            if metadata: 
                data.update(metadata)

            supabase.table("photos").insert(data).execute()
            
            print(f"✅ Success! Uploaded to Cloud: {public_url}")
            
            # Enforce Storage Limit
            cleanup_storage(600)
            
            return public_url

        except Exception as e:
            print(f"⚠️ Bytes Upload Failed (Attempt {attempt}): {e}")
            time.sleep(1)

    # Cloud-only mode: Do NOT save locally
    print("❌ Upload failed after 3 attempts. Photo discarded (cloud-only mode).")
    return None

def process_queue():
    """Process pending items in the offline queue."""
    pending = sync_queue.get_pending()
    if not pending: return

    print(f"🔄 Processing {len(pending)} offline items...")
    
    for item in pending:
        try:
            # We recursively call upload_photo? No, that would loop.
            # We need a direct upload logic or careful call.
            # Let's verify connectivity first or just try one.
            
            # Simple approach: Re-implement upload logic or refactor.
            # Refactor is better but let's do inline for now to avoid circular deps if any.
            
            local_path = item.filepath
            if not os.path.exists(local_path):
                print(f"⚠️ File missing: {local_path}")
                sync_queue.mark_failed(local_path)
                continue
                
            filename = os.path.basename(local_path)
            # Use original timestamp for name if needed, or simple name
            storage_path = f"sync_{int(item.timestamp)}_{filename}"
            
            with open(local_path, "rb") as f:
                supabase.storage.from_(BUCKET_NAME).upload(
                    path=storage_path,
                    file=f,
                    file_options={"content-type": "image/jpeg"}
                )
            
            public_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/{storage_path}"
            data = {"image_url": public_url, "created_at": str(datetime.fromtimestamp(item.timestamp))} 
            # Note: Supabase 'created_at' usually auto-generated. We might need a separate field or override.
            # For this simple retry, we accept new created_at or try to pass it if schema allows.
            
            supabase.table("photos").insert(data).execute()
            
            print(f"✅ Synced: {filename}")
            sync_queue.mark_completed(local_path)
            
        except Exception as e:
            print(f"❌ Sync failed for {item.filepath}: {e}")
            sync_queue.mark_failed(item.filepath)

if __name__ == "__main__":
    # Test
    print("Test run...")
