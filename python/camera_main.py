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
from supabase_upload import upload_photo
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
    print("🚀 Starting Mascot Photo Booth System...")
    
    # 1. Start Web Gallery & Remote Control
    web_gallery.start_gallery_thread()
    start_remote_thread()
    
    print(f"🌐 Local Gallery: {web_gallery.gallery_url}")
    print(f"☁️ Cloud Site: {settings.vercel_app_url}")
    print("📷 QR Code pointing to Cloud Site.")

    # 2. Init Arduino Bridge
    arduino = ArduinoBridge(port="COM3", baud_rate=9600)

    # 3. Init Hand Detector
    recognizer = GestureRecognizer()

    # 3.5 Init Capture Manager
    capture_manager = CaptureManager(PHOTO_DIR)

    # 4. Init Roboflow Detector (optional)
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
        
        # Gesture detection (MediaPipe) - takes priority for photo trigger
        if gesture_name:
            if gesture_name == "THUMBS_UP":
                current_command = "PHOTO_TRIGGER"
            elif gesture_name == "LOVE" and current_command == "NORMAL":
                current_command = "LOVE"
            elif gesture_name == "SUS" and current_command == "NORMAL":
                current_command = "SUS"
        
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
                
                # Countdown ONLY for BURST (User Request)
                if mode == "BURST":
                    time.sleep(0.5) # Wait for LED flash to settle? 
                    capture_manager.show_countdown(cap, seconds=3)
                else:
                    time.sleep(0.5) # Short delay for others
                
                # 3. Capture based on Mode
                result = None
                
                if mode == "BURST":
                    result = capture_manager.capture_burst(cap, filter_type=filter_type, save_to_disk=False)
                elif mode == "GIF":
                    result = capture_manager.capture_gif(cap, filter_type=filter_type, save_to_disk=False)
                else: # SINGLE
                    # Read fresh frame for high quality single shot
                    ret, fresh_frame = cap.read()
                    if ret:
                        result = capture_manager.capture_single(fresh_frame, filter_type=filter_type, save_to_disk=False)
                
                if result:
                    print("✅ Capture complete! (Memory Mode)")
                    
                    # Flash Effect
                    flash = np.ones_like(frame) * 255
                    cv2.imshow("Mascot View", flash)
                    cv2.waitKey(100)
                    
                    # Prepare Data for Upload
                    file_bytes = None
                    filename = ""
                    base_ts = int(time.time())
                    
                    try:
                        if mode == "GIF" and result.gif_bytes:
                            file_bytes = result.gif_bytes
                            filename = f"mascot_gif_{base_ts}.gif"
                        elif mode == "BURST" and result.collage_image is not None:
                            # Encode Collage
                            success, buffer = cv2.imencode(".jpg", result.collage_image)
                            if success:
                                file_bytes = buffer.tobytes()
                                filename = f"mascot_burst_{base_ts}.jpg"
                        elif result.images:
                            # Single Image
                            success, buffer = cv2.imencode(".jpg", result.images[0])
                            if success:
                                file_bytes = buffer.tobytes()
                                filename = f"mascot_photo_{base_ts}.jpg"
                        
                        if file_bytes:
                            print(f"🚀 Uploading {len(file_bytes)} bytes to Supabase...")
                            import supabase_upload
                            supabase_upload.upload_bytes(file_bytes, filename)
                        else:
                            print("❌ Error: No image data to upload.")
                            
                    except Exception as e:
                         print(f"❌ Processing Error: {e}")
                else:
                    print("❌ Capture Failed")
                
            else:
                pass

        # Send Command (Non-Blocking)
        if current_command != "PHOTO_TRIGGER" and current_command != "NORMAL":
             if current_command != last_command:
                arduino.send_command(current_command)
                last_command = current_command
                command_resend_timer = time.time()
        
        if current_command == "NORMAL":
             last_command = "NORMAL"

        # Overlay Info
        display_frame = frame.copy()
        
        # Draw Roboflow detections if any
        if roboflow and roboflow_detections:
            display_frame = roboflow.draw_detections(display_frame, roboflow_detections)
        
        # Show specific filter status text small in corner
        cv2.putText(display_frame, f"Filter: {web_gallery.current_filter}", (10, 470), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Show Roboflow status
        if roboflow and roboflow.is_available():
            status = f"AI: {len(roboflow_detections)} detections"
            cv2.putText(display_frame, status, (10, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    
        # Show URL in corner?
        # cv2.putText(display_frame, "Scan for Photos!", (450, 470), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        cv2.imshow("Mascot View", display_frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    arduino.close()

if __name__ == "__main__":
    main()
