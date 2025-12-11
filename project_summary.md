# 🤖 Mascot Photo Booth - Project Summary

## 📌 Overview
We have built an interactive **Mascot Photo Booth** system that combines **Computer Vision** (OpenCV/MediaPipe) with **Physical Hardware** (Arduino, LEDs, Servo).

The system allows a mascot to "see" gestures, express emotions with its eyes/hand, and take stylized photos that are instantly available on a local web gallery.

---

## 🛠️ Technology Stack
*   **Hardware**: Arduino Uno, NeoPixel Rings (x3), Servo Motor, Ultrasonic Sensor, Webcam.
*   **Software (Python)**: OpenCV, MediaPipe, Flask, PySerial.
*   **Software (Arduino)**: C++ Sketch with Adafruit_NeoPixel & Servo libraries.

---

## ✨ Features Implemented

### 1. 📷 Smart Camera System (`camera_main.py`)
*   **Gesture Recognition**: Detects **Thumbs Up** 👍 to trigger a photo.
*   **Filters**: Applies **Cartoon** or **Vintage** effects based on user selection.
*   **Clean Capture**: Saves high-quality images without on-screen debug text.
*   **Countdown Sync**: Waits for the Arduino LED countdown before snapping.

### 2. 🎡 Interactive Emotions (`mascot_controller.ino`)
The Mascot has a **Hybrid Brain**:
*   **Manual Override**: Python sends commands (Love, Sus, Photo) based on gestures.
*   **Autonomous Mode**: When idle, the **Ultrasonic Sensor** controls emotions based on distance:
    *   **< 20cm**: **LOVE** (Pink Heart Eyes + Hand Wave).
    *   **20-60cm**: **SUS** (Yellow Squinting Eyes + Breathing effect).
    *   **> 60cm**: **NORMAL** (Blue Eyes, LED 14 OFF).
*   **Photo Mode**: 3-2-1 LED Countdown followed by a Bright White Flash.

### 3. 🌐 Polaroid Web Gallery (`web_gallery.py`)
*   **Local Network Access**: Accessible via `http://<YOUR_IP>:5000/gallery` on any phone/laptop on the WiFi.
*   **Polaroid Style**: Photos appear as tilted polaroids with shadows.
*   **Live Updates**: Gallery refreshes automatically without reloading the page.
*   **Remote Control**: Change the photo filter (Cartoon/Normal/Vintage) *from the website*.
*   **Download**: One-click download button for every photo.

---

## 📂 Project Structure

```text
mascot_photobooth/
├── arduino/
│   └── mascot_controller/
│       └── mascot_controller.ino  # The BRAIN (LEDs, Servo, Ultrasonic)
├── python/
│   ├── camera_main.py    # The EYES (Webcam, Gestures, Main Loop)
│   ├── web_gallery.py    # The DISPLAY (Flask Web Server)
│   ├── gestures.py       # Hand Detection Logic
│   └── arduino_bridge.py # Serial Communication Helper
└── photos/               # Saved Images
```

---

## 🚀 How to Run

### Step 1: Hardware Setup
1.  Connect **Arduino** to USB.
2.  Connect **Webcam** to USB.
3.  Upload `mascot_controller.ino` via Arduino IDE.

### Step 2: Start the System
Open a terminal in the project folder:
```powershell
python python/camera_main.py
```

### Step 3: Use It!
1.  **Stand back**: Mascot reacts to distance (Normal/Sus/Love).
2.  **Show 👍**: Photo Countdown starts (3-2-1-FLASH!).
3.  **Check Gallery**: Open the URL printed in the terminal (e.g. `http://192.168.x.x:5000/gallery`) on your phone to see/download the pic!
