@echo off
echo ============================================
echo 🚀 STARTING EXCEL MASCOT PHOTO BOOTH SYSTEM
echo ============================================
echo.

echo 1. Starting Web Gallery Server...
start "Mascot Web Server" python python/web_gallery.py

echo 2. Waiting for server to initialize...
timeout /t 3

echo 3. Starting Camera System...
python python/camera_main.py

pause
