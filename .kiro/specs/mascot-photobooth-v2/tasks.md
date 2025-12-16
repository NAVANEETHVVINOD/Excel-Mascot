# Implementation Plan

- [x] 1. Fix Vercel deployment and project setup

  - [x] 1.1 Add missing @supabase/supabase-js dependency to package.json


    - Already done - verify build works
    - _Requirements: 7.1_
  - [x] 1.2 Create requirements.txt for Python dependencies


    - Add opencv-python, mediapipe, pyserial, supabase, requests, Pillow
    - _Requirements: 1.1, 2.1_



- [ ] 2. Implement Roboflow Rapid integration
  - [x] 2.1 Create roboflow_detector.py module


    - Implement RoboflowDetector class with detect() and draw_detections() methods

    - Add timeout handling (2s fallback to MediaPipe)
    - _Requirements: 2.1, 2.2, 2.3, 2.4_
  - [ ] 2.2 Write property test for detection confidence threshold
    - **Property 5: Detection confidence animation trigger**
    - **Validates: Requirements 2.5**
  - [x] 2.3 Integrate Roboflow detector into camera_main.py

    - Add optional Roboflow detection alongside MediaPipe gestures
    - Trigger custom animations based on detections
    - _Requirements: 2.5, 2.6_

- [x] 3. Enhance filter system

  - [x] 3.1 Refactor filters into separate filters.py module


    - Create FilterType enum and apply_filter() function
    - Move existing filter functions from camera_main.py
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

  - [x] 3.2 Write property tests for filters

    - **Property 6: Black-and-white filter correctness**
    - **Property 7: Polaroid filter dimension increase**
    - **Property 8: No-filter identity**
    - **Validates: Requirements 3.3, 3.4, 3.5**

- [ ] 4. Implement capture modes
  - [x] 4.1 Create capture_modes.py module


    - Implement CaptureMode enum (SINGLE, BURST, GIF)
    - Add capture_burst() for 4 rapid photos
    - Add capture_gif() for 8-frame animated GIF
    - Add create_collage() for burst mode output
    - _Requirements: 5.1, 5.2, 5.5_

  - [ ] 4.2 Write property tests for capture modes

    - **Property 11: Burst mode photo count**
    - **Property 12: GIF frame count**
    - **Validates: Requirements 5.1, 5.2**
  - [ ] 4.3 Add countdown display before capture
    - Show 3-2-1 countdown on screen
    - _Requirements: 5.3_

- [ ] 5. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 6. Implement offline sync queue
  - [ ] 6.1 Create sync_queue.py module
    - Implement SyncQueue class with add(), process_queue(), get_pending_count()
    - Store queue in local JSON file
    - _Requirements: 8.1, 8.2, 8.5_
  - [ ] 6.2 Write property tests for sync queue
    - **Property 21: Timestamp preservation during sync**
    - **Validates: Requirements 8.5**
  - [ ] 6.3 Integrate sync queue into upload flow
    - Queue photos when offline, sync when connected
    - Preserve original timestamps
    - _Requirements: 8.1, 8.2, 8.3_

- [ ] 7. Enhance configuration management
  - [ ] 7.1 Create enhanced config.py with dataclass
    - Add Config dataclass with all settings
    - Add load_config() and validate_config() functions
    - Support environment variable overrides
    - _Requirements: 10.1, 10.2, 10.3_
  - [ ] 7.2 Write property tests for configuration
    - **Property 25: Configuration round-trip**
    - **Validates: Requirements 10.4, 10.5**

- [ ] 8. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 9. Enhance web gallery with social sharing
  - [ ] 9.1 Add share buttons component
    - Create ShareButtons component with Twitter, Facebook, WhatsApp
    - Use Web Share API where available
    - _Requirements: 4.1, 4.2_
  - [ ] 9.2 Add QR code generation for photos
    - Generate QR code linking to individual photo
    - Display QR on photo detail view
    - _Requirements: 4.3, 4.4_
  - [ ] 9.3 Write property test for QR code
    - **Property 10: QR code URL encoding correctness**
    - **Validates: Requirements 4.4**

- [ ] 10. Add admin dashboard
  - [ ] 10.1 Create admin page with photo management
    - List all photos with delete/hide actions
    - Add moderation mode toggle
    - _Requirements: 6.1, 6.2, 6.3_
  - [ ] 10.2 Add basic analytics display
    - Show total photos, photos per day chart
    - Display filter usage breakdown
    - _Requirements: 6.1, 6.4_
  - [ ] 10.3 Add CSV export functionality
    - Export photo metadata to CSV file
    - _Requirements: 6.5_

- [ ] 11. Improve realtime gallery
  - [ ] 11.1 Add reconnection handling
    - Auto-reconnect WebSocket on disconnect
    - Fetch missed photos after reconnection
    - _Requirements: 7.4, 7.5_
  - [ ] 11.2 Write property test for gallery ordering
    - **Property 16: Gallery chronological ordering**
    - **Validates: Requirements 7.2**

- [ ] 12. Final Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
