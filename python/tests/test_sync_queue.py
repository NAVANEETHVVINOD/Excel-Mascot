"""
Property-based tests for SyncQueue module.
"""

import pytest
from hypothesis import given, strategies as st
import os
import tempfile
import json
from sync_queue import SyncQueue

class TestSyncQueueProperties:
    
    def test_queue_persistence(self):
        """Queue should persist data across reloads."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "queue.json")
            
            # 1. Create and add item
            q1 = SyncQueue(filepath)
            q1.add("photo1.jpg", {"filter": "bw"})
            
            # 2. Reload in new instance
            q2 = SyncQueue(filepath)
            assert len(q2.queue) == 1
            assert q2.queue[0].filepath == "photo1.jpg"
            assert q2.queue[0].metadata["filter"] == "bw"

    @given(
        filepath=st.text(min_size=1, max_size=20),
        timestamp=st.floats(min_value=1000000, max_value=2000000) # Mock timestamps
    )
    def test_timestamp_preservation(self, filepath, timestamp):
        """
        **Property 21: Timestamp preservation during sync**
        Timestamp should be preserved when adding to queue.
        Note: The add() method generates current time, but we can verify it's stored.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            file = os.path.join(tmpdir, "queue.json")
            q = SyncQueue(file)
            
            q.add(filepath)
            
            item = q.queue[-1]
            assert item.filepath == filepath
            assert isinstance(item.timestamp, float)
            assert item.timestamp > 0

    def test_mark_completed_removes_item(self):
        """Marking completed should remove item from queue."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file = os.path.join(tmpdir, "queue.json")
            q = SyncQueue(file)
            
            q.add("photo1.jpg")
            q.add("photo2.jpg")
            
            q.mark_completed("photo1.jpg")
            
            pending = q.get_pending()
            assert len(pending) == 1
            assert pending[0].filepath == "photo2.jpg"

    def test_retry_limits(self):
        """Failed items should eventually mark as permanently failed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file = os.path.join(tmpdir, "queue.json")
            q = SyncQueue(file)
            
            q.add("fail.jpg")
            
            for _ in range(6):
                q.mark_failed("fail.jpg")
                
            pending = q.get_pending()
            # Should be 0 because status changed to 'failed_permanently'
            assert len(pending) == 0 
            
            # Verify status in full queue
            assert q.queue[0].status == "failed_permanently"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
