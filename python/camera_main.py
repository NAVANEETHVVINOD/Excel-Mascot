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

# Configuration
PHOTO_DIR = web_gallery.PHOTO_DIR
CAPTURE_COOLDOWN = 6.0 # Increased for countdown

def apply_cartoon(img):
    # Edges
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 5)
    edges = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 9)
    # Color
    color = cv2.bilateralFilter(img, 9, 75, 75)
    return cv2.bitwise_and(color, color, mask=edges)

def apply_vintage(img):
    # Sepia Filter
    kernel = np.array([[0.272, 0.534, 0.131],
                       [0.349, 0.686, 0.168],
                       [0.393, 0.769, 0.189]])
    sepia = cv2.transform(img, kernel)
    sepia = np.clip(sepia, 0, 255)
    
    # Add Noise
    noise = np.random.normal(0, 15, sepia.shape).astype(np.uint8)
    vintage = cv2.add(sepia.astype(np.uint8), noise)
    return vintage

def apply_polaroid_frame(img):
    # White Border
    # Top, Left, Right = 20, Bottom = 100
    row, col = img.shape[:2]
    bottom = int(row * 0.25) # 25% of height for bottom
    border = int(col * 0.05) # 5% for sides
    
    # White Color
    white = [255, 255, 255]
    
    # Add border
    polaroid = cv2.copyMakeBorder(img, border, bottom, border, border, cv2.BORDER_CONSTANT, value=white)
    
    # Add Text
    text = "Mascot 2025"
    font = cv2.FONT_HERSHEY_SCRIPT_SIMPLEX
    font_scale = 1.5
    thickness = 2
    
    # Centered text in bottom area
    text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
    text_x = (polaroid.shape[1] - text_size[0]) // 2
    text_y = polaroid.shape[0] - (bottom // 2) + (text_size[1] // 2)
    
    cv2.putText(polaroid, text, (text_x, text_y), font, font_scale, (50, 50, 50), thickness)
    return polaroid

def main():
    print("🚀 Starting Mascot Photo Booth System...")
    
    # 1. Start Web Gallery
    web_gallery.start_gallery_thread()
    print(f"🌐 Gallery: {web_gallery.gallery_url}")
    print(f"📷 QR Code generated for mobile access.")

    # 2. Init Arduino Bridge
    arduino = ArduinoBridge(port="COM3", baud_rate=9600)

    # 3. Init Hand Detector
    recognizer = GestureRecognizer()

    # 4. Start Camera
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
        
        if gesture_name:
            if gesture_name == "THUMBS_UP":
                current_command = "PHOTO_TRIGGER"
            elif gesture_name == "LOVE":
                current_command = "LOVE"
            elif gesture_name == "SUS":
                current_command = "SUS"
        
        # Handle Photo Capture
        if current_command == "PHOTO_TRIGGER":
            if time.time() - last_capture_time > CAPTURE_COOLDOWN:
                last_capture_time = time.time()
                
                # 2. Capture IMMEDIATELY (Instant Snap)
                print("📸 Snapping photo!")
                # Optional small delay if we want to ensure Arduino Flash is ON frame?
                # Arduino flash starts instantly. 60+60+60*3 ~ 400ms total. 
                # If we grab frame now, we might get the flash.
                # Let's wait 100ms.
                time.sleep(0.1)
                
                # 3. Capture & Filter
                ret, fresh_frame = cap.read()
                if ret:
                    clean_frame = fresh_frame.copy()
                    
                    # Apply Filter
                    mode = web_gallery.current_filter
                    print(f"Applying Filter: {mode}")
                    
                    final_img = clean_frame
                    
                    if mode == "CARTOON":
                        final_img = apply_cartoon(clean_frame)
                    elif mode == "VINTAGE":
                        final_img = apply_vintage(clean_frame)
                    elif mode == "BW":
                        gray = cv2.cvtColor(clean_frame, cv2.COLOR_BGR2GRAY)
                        final_img = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
                    elif mode == "POLAROID":
                        # Apply Border
                        final_img = apply_polaroid_frame(clean_frame)

                    # Save
                    timestamp = int(time.time())
                    filename = f"photo_{timestamp}.jpg"
                    filepath = os.path.join(PHOTO_DIR, filename)
                    cv2.imwrite(filepath, final_img)
                    
                    # Upload to Cloud (Non-blocking ideally, but blocking for safety first as requested)
                    print("🚀 Uploading to Supabase...")
                    upload_photo(filepath)
                    
                    # Flash Effect
                    flash = np.ones_like(frame) * 255
                    cv2.imshow("Mascot View", flash)
                    cv2.waitKey(100)
                
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
        
        # Show specific filter status text small in corner
        cv2.putText(display_frame, f"Filter: {web_gallery.current_filter}", (10, 470), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                    
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
