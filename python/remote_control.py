
import asyncio
import threading
from supabase import create_async_client
from settings import settings
import web_gallery

class RemoteController:
    def __init__(self):
        self.url = settings.supabase_url
        self.key = settings.supabase_key
        self.running = False
        self.loop = None

    async def handle_broadcast(self, payload):
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
            print(f"❌ Error handling command: {e}")

    async def run_async(self):
        print("📡 Connecting to Async Cloud Remote Control...")
        try:
            self.client = await create_async_client(self.url, self.key)
            
            channel = self.client.channel('booth_control')
            
            def on_event(payload):
                # Bridge from callback to async handler if needed, 
                # or just run logic directly since it's simple state update.
                # The callback might be sync or async depending on lib.
                # Usually python realtime callbacks are sync functions but run in loop context?
                # Actually, let's look at standard usage.
                # If on_event is sync, we can just update globals given GIL.
                
                event = payload.get('payload', {})
                event_type = event.get('type')
                print(f"📡 Remote Command: {event_type}")
                
                if event_type == "SET_FILTER":
                   web_gallery.current_filter = event.get('filter', '').upper()
                elif event_type == "SET_MODE":
                   web_gallery.current_mode = event.get('mode', '').upper()

            # Enable broadcast listening
            # Using on_broadcast for AsyncClient
            channel.on_broadcast(event='command', callback=on_event)
            await channel.subscribe()

            print("✅ Async Remote Control Active!")

            # Keep alive
            while self.running:
                await asyncio.sleep(1)

        except Exception as e:
            print(f"❌ Async Remote Control Error: {e}")
            import traceback
            traceback.print_exc()

    def start_loop(self):
        self.running = True
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.run_async())

remote = RemoteController()

def start_remote_thread():
    t = threading.Thread(target=remote.start_loop)
    t.daemon = True
    t.start()
