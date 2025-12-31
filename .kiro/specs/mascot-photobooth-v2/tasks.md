# Implementation Plan

- [x] 1. Fix Vercel deployment and project setup

  - [x] 1.1 Add missing @supabase/supabase-js dependency to package.json


    - Already done - verify build works
    - _Requirements: 7.1_
  - [x] 1.2 Create requirements.txt for Python dependencies


    - Add opencv-python, mediapipe, pyserial, supabase, requests, Pillow
    - _Requirements: 1.1, 2.1_



- [x] 2. Implement Roboflow Rapid integration
  - [x] 2.1 Create roboflow_detector.py module


    - Implement RoboflowDetector class with detect() and draw_detections() methods

    - Add timeout handling (2s fallback to MediaPipe)
    - _Requirements: 2.1, 2.2, 2.3, 2.4_
  - [x] 2.2 Write property test for detection confidence threshold
    - **Property 5: Detection confidence animation trigger**
    - **Validates: Requirements 2.5**
    - Implemented in test_roboflow_detector.py
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

    - **Property 6: Noir filter correctness**
    - **Property 7: Retro filter dimension increase**
    - **Property 8: No-filter identity**
    - **Validates: Requirements 3.5, 3.4, 3.6**

- [x] 4. Implement capture modes
  - [x] 4.1 Create capture_modes.py module


    - Implement CaptureMode enum (SINGLE, BURST, GIF)
    - Add capture_burst() for 4 rapid photos with 4-second countdown
    - Add capture_gif() for 8-frame animated GIF
    - Add create_collage() for 2x2 burst mode output
    - Add show_countdown() for 4-second timer display
    - Add show_preview() to display 4 photos on camera screen
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

  - [x] 4.2 Write property tests for capture modes

    - **Property 11: Burst mode photo count (4 photos, 1 collage)**
    - **Property 12: GIF frame count (8 frames)**
    - **Property 28: Burst countdown duration (4 seconds)**
    - **Validates: Requirements 5.1, 5.2, 5.4, 5.5, 5.6**
    - Implemented in test_capture_modes.py
  - [x] 4.3 Update burst mode to show preview and save only collage
    - Display all 4 photos on camera screen after capture
    - Create 2x2 collage and upload only the collage
    - _Requirements: 5.3, 5.4, 5.5_

- [x] 5. Checkpoint - Ensure all tests pass
  - All core tests pass (filters, capture modes, roboflow detector)

- [x] 6. ~~Implement offline sync queue~~ (SUPERSEDED by cloud-only mode - Requirement 14)
  - [x] 6.1 ~~Create sync_queue.py module~~ (N/A - cloud-only mode implemented)
    - sync_queue.py exists but is no longer used
    - Cloud-only mode (Requirement 14) supersedes offline sync requirements
    - _Requirements: 8.1, 8.2, 8.5 - SUPERSEDED by 14.1, 14.2, 14.3_
  - [x] 6.2 ~~Write property tests for sync queue~~ (N/A - not needed for cloud-only)
  - [x] 6.3 ~~Integrate sync queue into upload flow~~ (N/A - cloud-only mode)

- [x] 7. Enhance configuration management
  - [x] 7.1 Create enhanced config.py with dataclass
    - Config dataclass implemented in settings.py with all settings
    - load() and validate() methods implemented
    - Environment variable overrides supported
    - _Requirements: 10.1, 10.2, 10.3_
  - [ ] 7.2 Write property tests for configuration
    - **Property 25: Configuration round-trip**
    - **Validates: Requirements 10.4, 10.5**

- [x] 8. Checkpoint - Ensure all tests pass
  - All core tests pass (filters, capture modes, roboflow detector)

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

- [x] 13. Update web gallery to Excel Techfest design
  - [x] 13.1 Redesign photo cards to polaroid style with pin decorations
    - Add polaroid-style white border with shadow
    - Add pin/clip decoration at top of each card
    - Display REC_DATE and LOC metadata fields
    - Add [EXCELETED] badge
    - _Requirements: 11.1, 11.3_
  - [x] 13.2 Add vertical timeline connector between photos
    - Create golden/orange vertical line connecting photo cards
    - Position photos along timeline
    - _Requirements: 11.4_
  - [x] 13.3 Update header with Excel 2025 branding
    - Add Excel 2025 logo
    - Match navigation style from excelmec.org
    - Use gold/orange color scheme (#FFD700, #FF8C00)
    - _Requirements: 11.2, 11.5_
  - [x] 13.4 Update filter buttons with active state (no reset button)
    - Remove RESET button
    - Add active state styling matching capture mode buttons
    - Click active filter to deselect
    - _Requirements: 12.1, 12.2, 12.4_

- [x] 14. Add camera window controls
  - [x] 14.1 Add close and minimize buttons to camera window
    - Create custom title bar with window controls
    - Handle ESC key to exit fullscreen
    - Handle Q key to close application
    - _Requirements: 13.1, 13.2, 13.3, 13.4_

- [x] 15. Implement cloud-only storage mode
  - [x] 15.1 Remove local file saving and offline queue
    - Upload directly to Supabase without local save
    - Show error message on upload failure
    - Remove offline_cache directory usage
    - _Requirements: 14.1, 14.2, 14.3_

- [x] 16. Fix photo display and realtime updates
  - [x] 16.1 Debug and fix photo not showing on website
    - Verify Supabase storage bucket permissions
    - Check image_url generation and storage
    - _Requirements: 15.1_
  - [x] 16.2 Add loading indicator and entrance animation
    - Show spinner while loading photos
    - Animate new photo cards on arrival
    - _Requirements: 15.2, 15.3_

- [x] 17. Ensure thumbs-up only triggers photo capture
  - [x] 17.1 Update gesture handling logic
    - Only THUMBS_UP triggers photo capture
    - Other gestures only trigger animations
    - _Requirements: 16.1, 16.2, 16.3_

- [x] 18. Final V2.1 Checkpoint
  - Ensure all tests pass, ask the user if questions arise.

- [x] 19. Update web gallery with enhanced timeline design
  - [x] 19.1 Remove navbar and add MASCOT heading
    - Remove navigation bar (single page app)
    - Add large "MASCOT" title with gold glow effect
    - Add subtitle with version info
    - _Requirements: 11.2_
  - [x] 19.2 Implement animated timeline on scroll
    - Timeline line grows/animates as user scrolls
    - Curved connectors draw from timeline to photos
    - Golden dots appear with pop animation
    - Photos alternate left/right along timeline
    - _Requirements: 11.4_
  - [x] 19.3 Add B&W to color hover effect on photos
    - Photos display in grayscale by default
    - Smooth transition to full color on hover
    - _Requirements: 11.1_
  - [x] 19.4 Add vintage tech background
    - Dark background with vintage computer room aesthetic
    - Grayscale filter with gold/orange gradient overlay
    - _Requirements: 11.2_
