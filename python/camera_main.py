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
from filters import get_filter_from_string, apply_filter, FilterType
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


def apply_retro_preview(image):
    """
    Apply RETRO filter color grading for live preview (without polaroid frame).
    This is a simplified version for real-time display.
    """
    result = image.copy()
    
    # Apply warm sepia-like tone
    sepia_filter = np.array([
        [0.272, 0.534, 0.131],
        [0.349, 0.686, 0.168],
        [0.393, 0.769, 0.189]
    ])
    
    # Apply sepia transform
    sepia = cv2.transform(result, sepia_filter)
    sepia = np.clip(sepia, 0, 255).astype(np.uint8)
    
    # Blend with original for less intense effect
    result = cv2.addWeighted(result, 0.35, sepia, 0.65, 0)
    
    # Matte blacks - lift shadows
    lab = cv2.cvtColor(result, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    l = np.clip(l.astype(np.float32) + 15, 0, 255).astype(np.uint8)
    lab = cv2.merge([l, a, b])
    result = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    
    # Add warm cast
    b_ch, g_ch, r_ch = cv2.split(result)
    r_ch = cv2.convertScaleAbs(r_ch, alpha=1.08, beta=8)
    g_ch = cv2.convertScaleAbs(g_ch, alpha=1.02, beta=3)
    b_ch = cv2.convertScaleAbs(b_ch, alpha=0.95, beta=-5)
    result = cv2.merge([b_ch, g_ch, r_ch])
    
    return result



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
    
    # Track filter/mode changes for visual feedback
    last_filter = web_gallery.current_filter
    last_mode = web_gallery.current_mode
    filter_change_time = 0
    mode_change_time = 0
    
    # Available filters and modes
    FILTERS = ["NORMAL", "GLITCH", "CYBERPUNK", "PASTEL", "BW", "POLAROID"]
    MODES = ["SINGLE", "BURST", "GIF"]
    
    print("📷 Camera active.")
    print("🎮 Keyboard Controls:")
    print("   1-6: Change Filter (1=NORMAL, 2=GLITCH, 3=NEON, 4=DREAMY, 5=NOIR, 6=RETRO)")
    print("   7-9: Change Mode (7=SINGLE, 8=BURST, 9=GIF)")
    print("   Q: Quit | ESC: Toggle Fullscreen | M: Minimize")

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
        
        # ===== LIVE FILTER PREVIEW =====
        # Apply the selected filter to the live preview so users can see how they'll look
        current_filter_name = web_gallery.current_filter
        if current_filter_name and current_filter_name != "NORMAL":
            filter_type = get_filter_from_string(current_filter_name)
            if filter_type != FilterType.NONE:
                try:
                    # Apply filter to the display frame for live preview
                    # Skip RETRO/POLAROID frame for preview (it adds borders)
                    if filter_type == FilterType.RETRO:
                        # For RETRO, apply the color grading but skip the polaroid frame
                        display_frame = apply_retro_preview(display_frame)
                    else:
                        display_frame = apply_filter(display_frame, filter_type)
                except Exception as e:
                    # If filter fails, just use original frame
                    pass
        
        # Check for filter/mode changes and show notification
        current_time = time.time()
        
        if web_gallery.current_filter != last_filter:
            last_filter = web_gallery.current_filter
            filter_change_time = current_time
            print(f"🎨 Filter changed to: {last_filter}")
            
        if web_gallery.current_mode != last_mode:
            last_mode = web_gallery.current_mode
            mode_change_time = current_time
            print(f"📸 Mode changed to: {last_mode}")
        
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
        
        # Show "LIVE PREVIEW" indicator when filter is active
        if web_gallery.current_filter and web_gallery.current_filter != "NORMAL":
            preview_text = "LIVE PREVIEW"
            cv2.putText(display_frame, preview_text, (display_frame.shape[1] // 2 - 80, 45), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        # Show BIG notification when filter/mode changes (visible for 2 seconds)
        notification_duration = 2.0
        
        if current_time - filter_change_time < notification_duration:
            # Big filter change notification
            notif_text = f"FILTER: {web_gallery.current_filter}"
            text_size = cv2.getTextSize(notif_text, cv2.FONT_HERSHEY_SIMPLEX, 1.5, 3)[0]
            text_x = (display_frame.shape[1] - text_size[0]) // 2
            text_y = display_frame.shape[0] // 2 - 30
            
            # Draw background box
            cv2.rectangle(display_frame, 
                         (text_x - 20, text_y - 50), 
                         (text_x + text_size[0] + 20, text_y + 20), 
                         (0, 0, 0), -1)
            cv2.rectangle(display_frame, 
                         (text_x - 20, text_y - 50), 
                         (text_x + text_size[0] + 20, text_y + 20), 
                         (0, 215, 255), 3)
            
            cv2.putText(display_frame, notif_text, (text_x, text_y), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 215, 255), 3)
        
        if current_time - mode_change_time < notification_duration:
            # Big mode change notification
            notif_text = f"MODE: {web_gallery.current_mode}"
            text_size = cv2.getTextSize(notif_text, cv2.FONT_HERSHEY_SIMPLEX, 1.5, 3)[0]
            text_x = (display_frame.shape[1] - text_size[0]) // 2
            text_y = display_frame.shape[0] // 2 + 50
            
            # Draw background box
            cv2.rectangle(display_frame, 
                         (text_x - 20, text_y - 50), 
                         (text_x + text_size[0] + 20, text_y + 20), 
                         (0, 0, 0), -1)
            cv2.rectangle(display_frame, 
                         (text_x - 20, text_y - 50), 
                         (text_x + text_size[0] + 20, text_y + 20), 
                         (0, 255, 0), 3)
            
            cv2.putText(display_frame, notif_text, (text_x, text_y), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)
        
        # Show controls hint
        controls_text = "1-6:Filter | 7-9:Mode | Q:Quit | ESC:Fullscreen"
        cv2.putText(display_frame, controls_text, (display_frame.shape[1] - 450, 25), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)
        
        # Draw Filter/Mode Selection Panel at bottom
        panel_height = 80
        panel_y = display_frame.shape[0] - panel_height
        
        # Semi-transparent panel background
        overlay = display_frame.copy()
        cv2.rectangle(overlay, (0, panel_y), (display_frame.shape[1], display_frame.shape[0]), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, display_frame, 0.3, 0, display_frame)
        
        # Draw Filter buttons (top row of panel) - smaller buttons to fit all 6
        filter_y = panel_y + 25
        filter_start_x = 10
        filter_btn_width = 75  # Smaller width
        filter_spacing = 5     # Less spacing
        
        cv2.putText(display_frame, "FILTER:", (filter_start_x, filter_y), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150, 150, 150), 1)
        
        for i, f in enumerate(FILTERS):
            btn_x = filter_start_x + 60 + i * (filter_btn_width + filter_spacing)
            is_active = (web_gallery.current_filter == f)
            
            # Button background
            color = (0, 215, 255) if is_active else (60, 60, 60)
            text_color = (0, 0, 0) if is_active else (200, 200, 200)
            
            cv2.rectangle(display_frame, (btn_x, filter_y - 16), 
                         (btn_x + filter_btn_width, filter_y + 4), color, -1)
            cv2.rectangle(display_frame, (btn_x, filter_y - 16), 
                         (btn_x + filter_btn_width, filter_y + 4), (100, 100, 100), 1)
            
            # Button text with number key hint - shorter labels
            short_name = f[:5] if len(f) > 5 else f
            label = f"{i+1}:{short_name}"
            cv2.putText(display_frame, label, (btn_x + 3, filter_y - 1), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.35, text_color, 1)
        
        # Draw Mode buttons (bottom row of panel)
        mode_y = panel_y + 55
        mode_start_x = 10
        mode_btn_width = 85
        mode_spacing = 10
        
        cv2.putText(display_frame, "MODE:", (mode_start_x, mode_y), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150, 150, 150), 1)
        
        for i, m in enumerate(MODES):
            btn_x = mode_start_x + 60 + i * (mode_btn_width + mode_spacing)
            is_active = (web_gallery.current_mode == m)
            
            # Button background
            color = (0, 255, 0) if is_active else (60, 60, 60)
            text_color = (0, 0, 0) if is_active else (200, 200, 200)
            
            cv2.rectangle(display_frame, (btn_x, mode_y - 16), 
                         (btn_x + mode_btn_width, mode_y + 4), color, -1)
            cv2.rectangle(display_frame, (btn_x, mode_y - 16), 
                         (btn_x + mode_btn_width, mode_y + 4), (100, 100, 100), 1)
            
            # Button text with number key hint (7, 8, 9)
            label = f"{i+7}:{m}"
            cv2.putText(display_frame, label, (btn_x + 5, mode_y - 1), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, text_color, 1)
        
        # Thumbs up hint (moved to right side of panel)
        cv2.putText(display_frame, "THUMBS UP to capture!", 
                    (display_frame.shape[1] - 230, mode_y - 5), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # Show Roboflow status
        if roboflow and roboflow.is_available():
            status = f"AI: {len(roboflow_detections)} detections"
            cv2.putText(display_frame, status, (display_frame.shape[1] - 200, 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

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
        # Filter selection (1-6 keys)
        elif key == ord('1'):
            web_gallery.current_filter = "NORMAL"
            filter_change_time = time.time()
            print("🎨 Filter: NORMAL")
        elif key == ord('2'):
            web_gallery.current_filter = "GLITCH"
            filter_change_time = time.time()
            print("🎨 Filter: GLITCH")
        elif key == ord('3'):
            web_gallery.current_filter = "CYBERPUNK"
            filter_change_time = time.time()
            print("🎨 Filter: CYBERPUNK (NEON)")
        elif key == ord('4'):
            web_gallery.current_filter = "PASTEL"
            filter_change_time = time.time()
            print("🎨 Filter: PASTEL (DREAMY)")
        elif key == ord('5'):
            web_gallery.current_filter = "BW"
            filter_change_time = time.time()
            print("🎨 Filter: BW (NOIR)")
        elif key == ord('6'):
            web_gallery.current_filter = "POLAROID"
            filter_change_time = time.time()
            print("🎨 Filter: POLAROID (RETRO)")
        # Mode selection (F1-F3 keys) - OpenCV key codes
        elif key == 190:  # F1
            web_gallery.current_mode = "SINGLE"
            mode_change_time = time.time()
            print("📸 Mode: SINGLE")
        elif key == 191:  # F2
            web_gallery.current_mode = "BURST"
            mode_change_time = time.time()
            print("📸 Mode: BURST")
        elif key == 192:  # F3
            web_gallery.current_mode = "GIF"
            mode_change_time = time.time()
            print("📸 Mode: GIF")
        # Alternative: Use 7, 8, 9 for modes (easier than F-keys)
        elif key == ord('7'):
            web_gallery.current_mode = "SINGLE"
            mode_change_time = time.time()
            print("📸 Mode: SINGLE")
        elif key == ord('8'):
            web_gallery.current_mode = "BURST"
            mode_change_time = time.time()
            print("📸 Mode: BURST")
        elif key == ord('9'):
            web_gallery.current_mode = "GIF"
            mode_change_time = time.time()
            print("📸 Mode: GIF")

    cap.release()
    cv2.destroyAllWindows()
    arduino.close()

if __name__ == "__main__":
    main()
