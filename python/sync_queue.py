"""
Synchronized Queue for Offline Support.
Handling local storage of metadata when offline and syncing when online.
"""

import json
import os
import time
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict

@dataclass
class QueuedItem:
    filepath: str
    timestamp: float
    metadata: Dict
    status: str = "pending" # pending, uploaded, failed
    retries: int = 0

class SyncQueue:
    """
    Manages a persistent queue of items to be synced.
    """
    def __init__(self, storage_file: str = "sync_queue.json"):
        self.storage_file = storage_file
        self.queue: List[QueuedItem] = []
        self.load()

    def load(self):
        """Load queue from disk."""
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r') as f:
                    data = json.load(f)
                    self.queue = [QueuedItem(**item) for item in data]
            except Exception as e:
                print(f"Error loading sync queue: {e}")
                self.queue = []

    def save(self):
        """Save queue to disk."""
        try:
            with open(self.storage_file, 'w') as f:
                json.dump([asdict(item) for item in self.queue], f, indent=2)
        except Exception as e:
            print(f"Error saving sync queue: {e}")

    def add(self, filepath: str, metadata: Dict = None):
        """Add a new item to the queue."""
        item = QueuedItem(
            filepath=filepath,
            timestamp=time.time(),
            metadata=metadata or {}
        )
        self.queue.append(item)
        self.save()

    def get_pending(self) -> List[QueuedItem]:
        """Get list of pending items."""
        return [item for item in self.queue if item.status == "pending"]

    def mark_completed(self, filepath: str):
        """Mark an item as completed (remove from queue)."""
        self.queue = [item for item in self.queue if item.filepath != filepath]
        self.save()

    def mark_failed(self, filepath: str):
        """Update retry count for failed item."""
        for item in self.queue:
            if item.filepath == filepath:
                item.retries += 1
                if item.retries > 5:
                    item.status = "failed_permanently"
        self.save()

    def clear(self):
        """Clear the queue."""
        self.queue = []
        self.save()
