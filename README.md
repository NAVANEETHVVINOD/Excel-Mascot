# Mascot Photo Booth System

A hybrid IoT Photo Booth that captures photos using a Python-controlled webcam, interacts with users via an animated Arduino Mascot, and instantly uploads photos to a Cloud Gallery.

## 🚀 Project Overview

The **Mascot Photo Booth** is designed to provide an interactive and seamless photo-taking experience. It replaces the traditional "press a button" interface with a touchless, gesture-controlled AI system. The physical "Mascot" (Arduino-based) provides personality and feedback, while the cloud backend ensures photos are immediately available on a sleek web gallery.

### Key Features
*   **Touchless Control**: Snap photos using hand gestures (Thumps Up).
*   **Interactive Mascot**: Animated eyes (NeoPixel) and hand (Servo) react to users.
*   **Instant Cloud Sync**: Photos upload to Supabase and appear on the web gallery in < 2 seconds.
*   **Resilient Connectivity**: Robust offline fallback and retry logic for unstable networks.

---

## 🧠 Current Model & Architecture

The system operates on a 4-layer architecture, combining local edge processing with cloud scalability.

### 1. Hardware Layer (The Mascot)
*   **Controller**: Arduino Uno
*   **Components**: 
    *   **NeoPixel Matrix**: Displays animated eyes (Blink, Heart, Angry).
    *   **Servo Motor**: Physically waves to users.
    *   **Ultrasonic Sensor**: Detects when a user approaches to wake up the system.
*   **Communication**: Serial (USB) connection to the local PC.

### 2. Edge Layer (Local Intelligence)
*   **Language**: Python 3.9+
*   **Computer Vision**: `OpenCV` for image capture and processing.
*   **AI Model**: **MediaPipe Hands** (Google).
    *   **Model Type**: Lightweight Single-Shot Detector (SSD) based implementation.
    *   **Latency**: Real-time (~30 FPS on standard CPUs).
    *   **Logic**:
        *   **`THUMBS_UP`**: Triggers the countdown and photo capture.
        *   **`LOVE` (Peace Sign)**: Triggers "Love" animation on the Mascot.
        *   **`SUS` (Pointing)**: Triggers "Suspicious" animation.
*   **Upload Service**: A dedicated background thread securely uploads images to Supabase using Anon Keys and RLS policies.

### 3. Cloud Layer (Backend)
*   **Provider**: **Supabase** (PostgreSQL + Storage).
*   **Storage**: Public `photos` bucket for hosting images.
*   **Database**: `photos` table stores metadata (timestamps, public URLs).
*   **Security**: Row Level Security (RLS) ensures only authenticated apps can upload, while reads are public.

### 4. Frontend Layer (User Gallery)
*   **Framework**: **Next.js** (React).
*   **Hosting**: **Vercel**.
*   **Real-time**: Uses Supabase Realtime to push new photos to connected clients instantly without refreshing.

---

## 🔮 Roadmap & Next Steps

We have successfully built the core capture-to-cloud pipeline. Here is the plan for the next phase of development.

### Immediate Next Steps
1.  **AI Assistant Integration**:
    *   **Goal**: Give the Mascot a voice.
    *   **Tech**: Integrate a lightweight LLM (e.g., Gemini API or local Llama) to allow users to "talk" to the mascot.
    *   **Interaction**: "Hey Mascot, take a picture of us!" -> Mascot replies and snaps photo.

2.  **3D Web Experience**:
    *   **Goal**: Make the web gallery visually stunning.
    *   **Tech**: Three.js / React Three Fiber.
    *   **Feature**: Transition from a 2D grid to a 3D environment where photos float in space or are held by a 3D avatar of the mascot.

### Planned Features (Backlog)
*   **QR Code Sharing**: Display a unique QR code on the capabilities screen after a photo is taken for instant download.
*   **Filter Selection**: Use gestures (swipe left/right) to change camera filters (B&W, Sepia, Cartoon) before taking the shot.
*   **Smart Framing**: Use Face Mesh to automatically crop/zoom the photo to perfectly center the users.

---

## 🛠️ Setup Instructions

### Prerequisites
*   Python 3.9+
*   Node.js 18+
*   Arduino IDE
*   Supabase Account

### 1. Arduino Setup
1.  Open `arduino/mascot_controller/mascot_controller.ino`.
2.  Install libraries: **Adafruit NeoPixel**, **Servo**.
3.  Upload code to Arduino Uno.

### 2. Python Client Setup
1.  Navigate to `python/`.
2.  Install dependencies:
    ```bash
    pip install opencv-python mediapipe pyserial supabase
    ```
3.  Create `config.py` from `config_example.py` and add your Supabase URL/Key.
4.  Run the main loop:
    ```bash
    python camera_main.py
    ```

### 3. Web Gallery Setup
1.  Navigate to `web/`.
2.  Install dependencies:
    ```bash
    npm install
    ```
3.  Set up local environment variables in `.env.local` or hardcode in `supabaseClient.js` (for dev).
4.  Run development server:
    ```bash
    npm run dev
    ```