# Mascot Photo Booth System - Final Cloud Architecture

## 🚀 Project Overview
A hybrid IoT Photo Booth that captures photos using a Python-controlled webcam, interacts with users via an animated Arduino Mascot, and instantly uploads photos to a Cloud Gallery (Supabase + Next.js).

## 🏗️ Architecture
### 1. Hardware Layer (The Mascot)
*   **Microcontroller**: Arduino Uno.
*   **Output**: NeoPixel LED Matrix (Eyes) + Servo Motor (Hand Wave).
*   **Sensors**: Ultrasonic Distance Sensor (detects users).
*   **Communication**: Serial (USB) to PC.

### 2. Edge Layer (Local PC/Pi)
*   **Core Logic**: `python/camera_main.py` (OpenCV).
*   **Features**:
    *   **Gesture Detection**: MediaPipe (Thumbs Up to snap).
    *   **Filters**: B&W, Polaroid Frame (OpenCV processing).
    *   **Automation**: Triggers Arduino animations (Wink, Flash, Love).
*   **Cloud Uploader**: `python/supabase_upload.py`.
    *   Uploads every photo to Supabase Storage.
    *   Inserts metadata to Supabase Database.
    *   Uses **Robust Retry Logic** for unstable networks.

### 3. Cloud Layer (Backend)
*   **Platform**: **Supabase**.
*   **Storage**: `photos` bucket (Public).
*   **Database**: `photos` table (Realtime enabled).
*   **Security**: Row Level Security (RLS) allows anonymous uploads but prevents deletion.

### 4. Frontend Layer (Web Gallery)
*   **Framework**: **Next.js** (React).
*   **Hosting**: **Vercel**.
*   **Features**:
    *   **Realtime**: Gallery updates instantly when a photo is taken.
    *   **Responsive**: Works on Mobile and Desktop.
    *   **Live Mode**: Show the latest photo in full screen.

## 📂 Project Structure
```text
mascot_photobooth/
├── arduino/
│   └── mascot_controller/mascot_controller.ino  # Arduino Firmware
├── python/
│   ├── camera_main.py       # Main Application
│   ├── gestures.py          # Hand Detection
│   ├── arduino_bridge.py    # Serial Communication
│   ├── supabase_upload.py   # Cloud Upload Script
│   ├── config.py            # Credentials (URL + Anon Key)
│   └── web_gallery.py       # (Legacy) Local Flask Gallery
└── web/                     # Next.js Frontend
    ├── pages/index.js       # Realtime Gallery
    ├── supabaseClient.js    # DB Connection
    └── ...
```

## 🛠️ Setup Instructions

### 1. Arduino
1.  Upload `mascot_controller.ino` via Arduino IDE.
2.  Connect to PC via USB.

### 2. Python (Local)
1.  Install requirements: `pip install opencv-python mediapipe pyserial supabase`
2.  Configure `python/config.py` with Supabase keys.
3.  Run: `python python/camera_main.py`

### 3. Vercel (Web)
1.  Push code to GitHub.
2.  Import to Vercel.
3.  Set Environment Variables (`NEXT_PUBLIC_SUPABASE_URL`, etc).
4.  Deploy.

## 🌟 Key Features
*   **Instant Cloud Sync**: Photos appear online in < 2 seconds.
*   **Interactive Mascot**: Winks when idle, flashes when snapping.
*   **Safe Security**: Uses Anon keys with RLS policies.
*   **Offline Fallback**: Saves photos locally even if internet fails (retry logic).
