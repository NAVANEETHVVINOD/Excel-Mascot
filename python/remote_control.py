"""
Remote Control Module
Listens to Supabase Realtime events to control the photo booth from the cloud.
"""

import threading
import time
from supabase import create_client, Client
from settings import settings
import web_gallery
from filters import get_filter_from_string

class RemoteController:
    def __init__(self):
        self.supabase: Client = create_client(settings.supabase_url, settings.supabase_key)
        self.channel = None
        self.running = False

    def handle_broadcast(self, payload):
        """Handle incoming broadcast messages."""
        try:
            event = payload.get('payload', {})
            event_type = event.get('type')
            
            print(f"📡 Remote Command Received: {event_type}")
            
            if event_type == "SET_FILTER":
                filter_name = event.get('filter')
                if filter_name:
                    print(f"   -> Setting Filter to {filter_name}")
                    web_gallery.current_filter = filter_name.upper()
                    
            elif event_type == "SET_MODE":
                mode_name = event.get('mode')
                if mode_name:
                    print(f"   -> Setting Mode to {mode_name}")
                    web_gallery.current_mode = mode_name.upper()
                    
        except Exception as e:
            print(f"❌ Error handling remote command: {e}")

    def start(self):
        """Start listening to the 'booth_control' channel."""
        self.running = True
        
        # Define callback
        def on_message(payload):
            self.handle_broadcast(payload)

        print("📡 Connecting to Cloud Remote Control...")
        
        try:
            # Subscribe to broadcast channel
            # Note: Ensure supabase-py supports RealtimeClient via .channel
            if hasattr(self.supabase, 'channel'):
                self.channel = self.supabase.channel('booth_control')
            else:
                # Fallback or check for .realtime
                print("⚠️ Warning: Client has no 'channel' method. Checking realtime...")
                # self.channel = self.supabase.realtime.channel(...) # Potential alternative
                # For now just try the standard way or fail gracefully
                self.channel = self.supabase.channel('booth_control')

            self.channel.on("broadcast", {"event": "command"}, on_message).subscribe()
            print("✅ Remote Control Active! Waiting for commands...")
            
        except Exception as e:
            print(f"❌ Failed to start Remote Control: {e}")
            import traceback
            traceback.print_exc()
            self.running = False

    def stop(self):
        try:
            if self.channel:
                self.channel.unsubscribe()
        except Exception as e:
            print(f"Error stopping channel: {e}")
        self.running = False

# Singleton
remote = RemoteController()

def start_remote_thread():
    t = threading.Thread(target=remote.start)
    t.daemon = True
    t.start()
