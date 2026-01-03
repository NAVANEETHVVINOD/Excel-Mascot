# 🎭 Excel Mascot Photo Booth

An interactive IoT Photo Booth for **Excel Techfest 2025** featuring gesture-controlled capture, animated Arduino mascot, and real-time cloud gallery.

![Excel Techfest 2025](https://img.shields.io/badge/Excel-Techfest%202025-gold)
![Python](https://img.shields.io/badge/Python-3.9+-blue)
![Next.js](https://img.shields.io/badge/Next.js-16-black)
![Supabase](https://img.shields.io/badge/Supabase-Cloud-green)

## 🌟 Features

- **Touchless Capture**: Show thumbs up 👍 to take photos
- **Interactive Mascot**: LED eyes + servo arm react to gestures
- **Multiple Modes**: Single, Burst (4-photo collage), GIF
- **Photo Filters**: Glitch, Neon, Dreamy, Retro, Noir, B&W
- **Real-time Gallery**: Photos appear instantly on web
- **PWA Ready**: Install as mobile app
- **Excel Theme**: Matches excelmec.org design

## 🔗 Live Demo

- **Gallery**: [excel-mascot.vercel.app](https://excel-mascot.vercel.app/)

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    SYSTEM ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐     Serial      ┌──────────────────┐     │
│  │   ARDUINO    │◄───(COM3)──────►│  Python Client   │     │
│  │  Controller  │                 │  (camera_main)   │     │
│  └──────────────┘                 └────────┬─────────┘     │
│        │                                   │               │
│        ▼                                   ▼               │
│  ┌──────────────┐              ┌─────────────────────┐     │
│  │ • LED Eyes   │              │     SUPABASE        │     │
│  │ • Servo Arm  │              │  • Storage (photos) │     │
│  │ • Stepper    │              │  • Database (urls)  │     │
│  │ • Ultrasonic │              │  • Realtime (sync)  │     │
│  └──────────────┘              └──────────┬──────────┘     │
│                                           │               │
│                                           ▼               │
│                                ┌─────────────────────┐     │
│                                │   VERCEL WEBSITE    │     │
│                                │  (Next.js Gallery)  │     │
│                                └─────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
mascot_photobooth/
├── arduino/
│   └── mascot_controller/     # Arduino code for mascot
├── python/
│   ├── camera_main.py         # Main application
│   ├── gestures.py            # Hand gesture detection
│   ├── filters.py             # Photo filters
│   ├── capture_modes.py       # Single/Burst/GIF modes
│   ├── arduino_bridge.py      # Serial communication
│   ├── supabase_upload.py     # Cloud upload
│   └── remote_control.py      # Realtime commands
├── web/
│   ├── pages/index.js         # Gallery UI
│   └── public/manifest.json   # PWA config
└── photos/                    # Local photo storage
```

## 🔧 Hardware Setup

### Arduino Pin Configuration

| Component | Pin |
|-----------|-----|
| Ultrasonic TRIG | 9 |
| Ultrasonic ECHO | 10 |
| Servo Signal | 11 |
| LED Strip 1 (Left Eye) | 6 |
| LED Strip 2 | 7 |
| LED Strip 3 (Right Eye) | 8 |
| Stepper STEP | 2 |
| Stepper DIR | 3 |
| Stepper ENA | 4 |

### Required Libraries (Arduino)
- Adafruit NeoPixel
- Servo

## 🚀 Quick Start

### 1. Arduino Setup
```bash
# Open Arduino IDE
# Install libraries: Adafruit NeoPixel, Servo
# Upload arduino/mascot_controller/mascot_controller.ino
```

### 2. Python Setup
```bash
cd python
pip install -r requirements.txt

# Create config.py from config_example.py
# Add your Supabase credentials

python camera_main.py
```

### 3. Web Gallery
```bash
cd web
npm install
npm run dev
# Open http://localhost:3000
```

## 🎮 Controls

### Camera Controls
| Key | Action |
|-----|--------|
| Q | Quit application |
| ESC | Toggle fullscreen |
| M | Minimize window |

### Gestures
| Gesture | Action |
|---------|--------|
| 👍 Thumbs Up | Capture photo |
| ✌️ Peace Sign | Love animation |
| ☝️ Pointing | Suspicious animation |

## 🎨 Web Gallery Features

- **Timeline Design**: Photos displayed on animated timeline
- **Polaroid Style**: Vintage photo cards with tape decoration
- **B&W to Color**: Photos colorize on hover
- **Download**: Save photos directly
- **Real-time**: New photos appear instantly
- **Mobile Friendly**: Responsive design
- **PWA**: Installable as app

## ⚙️ Configuration

### Python (config.py)
```python
SUPABASE_URL = "your-supabase-url"
SUPABASE_KEY = "your-anon-key"
BUCKET_NAME = "photos"
```

### Environment Variables
```bash
ROBOFLOW_API_KEY=xxx      # Optional: AI detection
ROBOFLOW_MODEL_ID=xxx     # Optional: AI detection
```

## 📱 PWA Installation

1. Open [excel-mascot.vercel.app](https://excel-mascot.vercel.app/) on mobile
2. Tap "Add to Home Screen"
3. Access gallery like a native app

## 🛠️ Tech Stack

- **Hardware**: Arduino Uno, NeoPixel LEDs, Servo, Stepper Motor
- **Backend**: Python 3.9+, OpenCV, MediaPipe
- **Cloud**: Supabase (Storage + Database + Realtime)
- **Frontend**: Next.js 16, React, Vercel
- **Design**: Excel Techfest 2025 theme (Gold/Orange palette)

## 📄 License

MIT License - Excel Techfest 2025, Model Engineering College

---

Made with ❤️ for Excel Techfest 2025
