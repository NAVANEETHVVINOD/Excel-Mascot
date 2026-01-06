import cv2
import time
import os
import sys
import numpy as np

# Ensure we can import modules from the same directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gestures import GestureRecognizer
from arduino_bridge import ArduinoBridge
import web_gallery
# from supabase_upload import upload_photo, upload_bytes
import threading
from roboflow_detector import RoboflowDetector, AnimationType
from capture_modes import CaptureManager
from filters import get_filter_from_string
from remote_control import start_remote_thread
from settings import settings

# Configuration
PHOTO_DIR = web_gallery.PHOTO_DIR
CAPTURE_COOLDOWN = 6.0 # Increased for countdown

# Roboflow Configuration (optional - set these to enable AI detection)
ROBOFLOW_API_KEY = os.environ.get("ROBOFLOW_API_KEY", None)
ROBOFLOW_MODEL_ID = os.environ.get("ROBOFLOW_MODEL_ID", None)
ROBOFLOW_CONFIDENCE = float(os.environ.get("ROBOFLOW_CONFIDENCE", "0.8"))
ROBOFLOW_ENABLED = bool(ROBOFLOW_API_KEY and ROBOFLOW_MODEL_ID)



def main():
    # Fix for Windows Unicode printing
    if sys.platform.startswith('win'):
        sys.stdout.reconfigure(encoding='utf-8')

    print("🚀 Starting Mascot Photo Booth System...")
    
    # 1. Start Web Gallery & Remote Control
    web_gallery.start_gallery_thread()
    start_remote_thread()
    
    print(f"🌐 Local Gallery: {web_gallery.gallery_url}")
    print(f"☁️ Cloud Site: {settings.vercel_app_url}")
    print("📷 QR Code pointing to Cloud Site.")

    # 2. Init Arduino Bridge
    arduino = ArduinoBridge(port="COM4", baud_rate=9600)

    # 3. Init Hand Detector
    recognizer = GestureRecognizer()

    # Initialize Managers
    capture_manager = CaptureManager(web_gallery.PHOTO_DIR) # Single Directory for Backup & Upload
    # Init Roboflow Detector (optional)
    roboflow = None
    if ROBOFLOW_ENABLED:
        roboflow = RoboflowDetector(
            api_key=ROBOFLOW_API_KEY,
            model_id=ROBOFLOW_MODEL_ID,
            confidence_threshold=ROBOFLOW_CONFIDENCE
        )
        print(f"🤖 Roboflow AI detection enabled (model: {ROBOFLOW_MODEL_ID})")
    else:
        print("ℹ️ Roboflow AI detection disabled (set ROBOFLOW_API_KEY and ROBOFLOW_MODEL_ID to enable)")

    # 5. Start Camera
    cv2.namedWindow("Mascot View", cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty("Mascot View", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    
    cap = cv2.VideoCapture(1) # Try Ext first
    if not cap.isOpened():
        cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("❌ Error: Could not open any webcam.")
        return

    last_capture_time = 0
    last_command = "NORMAL"
    command_resend_timer = time.time()
    
    print("📷 Camera active.")

    while True:
        ret, frame = cap.read()
        if not ret: continue

        # Filter Preview?
        # Maybe show the raw frame for mirror, but apply filter on save?
        # Or apply filter on preview? Let's apply on preview if user wants to see it.
        # But for 'Mascot' experience, maybe users want to see themselves clearly?
        # User request: "choose filter in the website" -> usually implies result.
        # I'll apply filter to the SAVED image only to keep preview high FPS.
        
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results, gesture_name = recognizer.process_frame(rgb)
        
        current_command = "NORMAL"
        roboflow_detections = []
        
        # Run Roboflow detection (if enabled)
        if roboflow and roboflow.is_available():
            detection_result = roboflow.detect(frame)
            if detection_result.success:
                roboflow_detections = detection_result.detections
                # Check for animation triggers from detections
                triggered = roboflow.get_triggered_animations(roboflow_detections)
                if triggered:
                    # Use the first high-confidence detection's animation
                    _, animation = triggered[0]
                    if animation == AnimationType.LOVE:
                        current_command = "LOVE"
                    elif animation == AnimationType.SUS:
                        current_command = "SUS"
                    elif animation == AnimationType.RAINBOW:
                        current_command = "RAINBOW"
                    elif animation == AnimationType.WELCOME:
                        current_command = "WELCOME"
        
        # Gesture detection (MediaPipe) - ONLY thumbs up triggers photo
        if gesture_name:
            if gesture_name == "THUMBS_UP":
                current_command = "PHOTO_TRIGGER"
            elif gesture_name == "LOVE" and current_command == "NORMAL":
                current_command = "LOVE"  # Animation only, no photo
            elif gesture_name == "SUS" and current_command == "NORMAL":
                current_command = "SUS"   # Animation only, no photo
        
        # Handle Photo Capture
        if current_command == "PHOTO_TRIGGER":
            if time.time() - last_capture_time > CAPTURE_COOLDOWN:
                last_capture_time = time.time()
                
                # 2. Capture Sequence
                print("📸 Starting Capture Sequence!")
                
                mode = web_gallery.current_mode
                filter_name = web_gallery.current_filter
                filter_type = get_filter_from_string(filter_name)
                
                print(f"Mode: {mode}, Filter: {filter_name}")

                # Trigger LED immediately for all modes (visual feedback of trigger)
                arduino.send_command("PHOTO")
                
                # No countdown before first photo in BURST mode - timer will be between photos
                if mode == "BURST":
                    time.sleep(0.3) # Brief delay for LED flash to settle
                else:
                    time.sleep(0.5) # Short delay for others
                
                # 3. Capture based on Mode (Cloud-only: don't save to disk)
                result = None
                
                # 3. Capture based on Mode
                # We handle saving manually for Single/Burst to ensure optimization (1600px)
                # GIF is complex to encode, so we let CaptureManager handle it.
                
                result = None
                base_ts = int(time.time())
                
                if mode == "BURST":
                    # Don't save individual frames, we want to save optimal collage manually
                    result = capture_manager.capture_burst(cap, filter_type=filter_type, save_to_disk=False)
                elif mode == "GIF":
                    # Let CaptureManager save the GIF directly to PHOTO_DIR
                    result = capture_manager.capture_gif(cap, filter_type=filter_type, save_to_disk=True)
                else: # SINGLE
                    ret, fresh_frame = cap.read()
                    if ret:
                        # Capture raw frame, we'll resize and save below
                        result = capture_manager.capture_single(fresh_frame, filter_type=filter_type, save_to_disk=False)
                
                if result:
                    print(f"✅ Capture complete! Processing...")
                    
                    # Flash Effect
                    flash = np.ones_like(frame) * 255
                    cv2.imshow("Mascot View", flash)
                    cv2.waitKey(100)
                    
                    # --- UNIFIED STORAGE LOGIC (Backup + Upload) ---
                    # 1. Prepare the final image (Resize to 1600px if needed)
                    # 2. Save to E:\mascot (Backup)
                    # 3. Upload that file to Supabase (Cloud)
                    
                    final_path = None
                    upload_needed = False
                    
                    try:
                        if mode == "GIF":
                            # GIF already saved by CaptureManager
                            final_path = result.output_path
                            upload_needed = True
                            
                        else:
                            # Handle Single & Burst (Collage)
                            src_image = None
                            filename = ""
                            
                            if mode == "BURST" and result.collage_image is not None:
                                src_image = result.collage_image
                                filename = f"mascot_burst_{base_ts}.jpg"
                            elif result.images:
                                src_image = result.images[0]
                                filename = f"mascot_photo_{base_ts}.jpg"
                                
                            if src_image is not None:
                                # Optimize to 1600px (High Quality Web ~1MB)
                                target_size = 1600
                                h, w = src_image.shape[:2]
                                scale = target_size / max(h, w)
                                
                                if scale < 1.0:
                                    new_size = (int(w * scale), int(h * scale))
                                    final_image = cv2.resize(src_image, new_size, interpolation=cv2.INTER_AREA)
                                else:
                                    final_image = src_image
                                    
                                # Save to E:\mascot
                                final_path = os.path.join(web_gallery.PHOTO_DIR, filename)
                                cv2.imwrite(final_path, final_image, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
                                upload_needed = True
                        
                        # --- CLOUD SYNC ---
                        if upload_needed and final_path and os.path.exists(final_path):
                            print(f"💾 Backup Saved: {final_path}")
                            print(f"🚀 Starting Cloud Upload...")
                            
                            def background_upload(fpath):
                                import supabase_upload
                                # Upload the file (this also triggers the 600 limit cleanup)
                                supabase_upload.upload_photo(fpath)
                                
                            threading.Thread(target=background_upload, args=(final_path,), daemon=True).start()
                        else:
                            print("❌ Error: No file created to upload.")

                    except Exception as e:
                        print(f"❌ Storage/Upload Error: {e}")

        # Send Command (Non-Blocking)
        if current_command != "PHOTO_TRIGGER" and current_command != "NORMAL":
             if current_command != last_command:
                arduino.send_command(current_command)
                last_command = current_command
                command_resend_timer = time.time()
        
        # Force reset last_command if we just triggered a photo, so next NORMAL sends correctly
        if current_command == "PHOTO_TRIGGER":
             last_command = "PHOTO_TRIGGER" 

        if current_command == "NORMAL":
             # Only send NORMAL if we weren't already normal
             if last_command != "NORMAL":
                 arduino.send_command("NORMAL")
                 last_command = "NORMAL"

        # Overlay Info
        display_frame = frame.copy()
        
        # Draw Roboflow detections if any
        if roboflow and roboflow_detections:
            display_frame = roboflow.draw_detections(display_frame, roboflow_detections)
        
        # Draw control overlay
        overlay_height = 60
        cv2.rectangle(display_frame, (0, 0), (display_frame.shape[1], overlay_height), (0, 0, 0), -1)
        cv2.rectangle(display_frame, (0, 0), (display_frame.shape[1], overlay_height), (50, 50, 50), 1)
        
        # Show current mode and filter
        mode_text = f"MODE: {web_gallery.current_mode}"
        filter_text = f"FILTER: {web_gallery.current_filter}"
        
        cv2.putText(display_frame, mode_text, (15, 25), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 215, 255), 2)  # Gold color
        cv2.putText(display_frame, filter_text, (15, 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 215, 255), 2)
        
        # Show controls hint
        controls_text = "Q:Quit | ESC:Fullscreen | M:Minimize"
        cv2.putText(display_frame, controls_text, (display_frame.shape[1] - 350, 25), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)
        
        # Show Roboflow status
        if roboflow and roboflow.is_available():
            status = f"AI: {len(roboflow_detections)} detections"
            cv2.putText(display_frame, status, (display_frame.shape[1] - 200, 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        # Show gesture hint at bottom
        cv2.putText(display_frame, "Show THUMBS UP to capture!", 
                    (display_frame.shape[1]//2 - 150, display_frame.shape[0] - 20), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        cv2.imshow("Mascot View", display_frame)
        
        # Handle key events
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == ord('Q'):
            print("👋 Closing application...")
            break
        elif key == 27:  # ESC key - toggle fullscreen
            # Toggle between fullscreen and windowed
            current_prop = cv2.getWindowProperty("Mascot View", cv2.WND_PROP_FULLSCREEN)
            if current_prop == cv2.WINDOW_FULLSCREEN:
                cv2.setWindowProperty("Mascot View", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)
                print("📺 Windowed mode")
            else:
                cv2.setWindowProperty("Mascot View", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
                print("📺 Fullscreen mode")
        elif key == ord('m') or key == ord('M'):
            # Minimize window (Windows specific)
            import ctypes
            hwnd = ctypes.windll.user32.FindWindowW(None, "Mascot View")
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, 6)  # SW_MINIMIZE
                print("📺 Window minimized")

    cap.release()
    cv2.destroyAllWindows()
    arduino.close()

if __name__ == "__main__":
    main()
