# Requirements Document

## Introduction

This document specifies the requirements for Mascot Photo Booth V2 - an enhanced IoT photo booth system that combines gesture-based photo capture with AI-powered object detection (Roboflow Rapid), social sharing capabilities, and an improved web gallery experience. The system upgrades the existing OpenCV/MediaPipe implementation with optional Roboflow integration for custom object detection, adds social sharing features, and introduces new photo booth modes.

**V2.1 Updates**: Added requirements for Excel Techfest themed UI design, improved filter selection feedback, camera window controls, and cloud-only storage mode.

## Glossary

- **Photo_Booth_System**: The complete hardware and software system that captures, processes, and shares photos
- **Gesture_Detector**: The MediaPipe-based component that recognizes hand gestures to trigger actions
- **Roboflow_Detector**: The AI-powered object detection component using Roboflow Rapid API for custom detection
- **Web_Gallery**: The Next.js frontend application that displays photos in realtime
- **Cloud_Storage**: The Supabase storage and database backend
- **Arduino_Mascot**: The physical mascot with LED eyes and servo motor controlled by Arduino
- **Photo_Session**: A single interaction where a user takes one or more photos
- **Detection_Result**: The output from Roboflow containing detected objects, confidence scores, and bounding boxes

## Requirements

### Requirement 1

**User Story:** As a photo booth user, I want to trigger photo capture using hand gestures, so that I can take photos hands-free without touching any buttons.

#### Acceptance Criteria

1. WHEN a user shows a thumbs-up gesture THEN the Photo_Booth_System SHALL capture a photo within 500 milliseconds
2. WHEN a user shows a peace sign gesture THEN the Photo_Booth_System SHALL trigger the love animation on the Arduino_Mascot
3. WHEN a user shows a pointing gesture THEN the Photo_Booth_System SHALL trigger the suspicious animation on the Arduino_Mascot
4. WHEN the Gesture_Detector confidence score falls below 0.7 THEN the Photo_Booth_System SHALL ignore the gesture input
5. WHEN multiple hands appear in frame THEN the Photo_Booth_System SHALL process only the first detected hand

### Requirement 2

**User Story:** As a photo booth operator, I want to integrate Roboflow Rapid for custom object detection, so that I can detect specific props, costumes, or branded items in photos.

#### Acceptance Criteria

1. WHEN the Roboflow_Detector is enabled THEN the Photo_Booth_System SHALL send frames to the Roboflow API endpoint
2. WHEN the Roboflow API returns Detection_Result THEN the Photo_Booth_System SHALL overlay bounding boxes on detected objects
3. WHEN the Roboflow API response time exceeds 2 seconds THEN the Photo_Booth_System SHALL fall back to local MediaPipe detection
4. WHEN the Roboflow API returns an error THEN the Photo_Booth_System SHALL log the error and continue with local detection
5. WHEN a specific prop is detected with confidence above 0.8 THEN the Photo_Booth_System SHALL trigger a custom mascot animation
6. WHEN configuring Roboflow_Detector THEN the Photo_Booth_System SHALL accept API key, model ID, and confidence threshold as parameters

### Requirement 3

**User Story:** As a photo booth user, I want to apply filters to my photos before they are saved, so that I can get creative and fun results.

#### Acceptance Criteria

1. WHEN a user selects the glitch filter THEN the Photo_Booth_System SHALL apply RGB channel shifting and scan line effects to the captured image
2. WHEN a user selects the neon/cyberpunk filter THEN the Photo_Booth_System SHALL apply high contrast with neon color enhancement
3. WHEN a user selects the dreamy/pastel filter THEN the Photo_Booth_System SHALL apply soft blur with pastel color tones
4. WHEN a user selects the retro/polaroid filter THEN the Photo_Booth_System SHALL add a white border frame with timestamp text
5. WHEN a user selects the noir/black-and-white filter THEN the Photo_Booth_System SHALL convert the captured image to high contrast grayscale
6. WHEN no filter is explicitly selected THEN the Photo_Booth_System SHALL save the original unmodified image
7. WHEN a filter is applied THEN the Photo_Booth_System SHALL complete processing within 200 milliseconds

### Requirement 4

**User Story:** As a photo booth user, I want to share my photos on social media, so that I can show my friends the fun photos I took.

#### Acceptance Criteria

1. WHEN a photo is displayed in the Web_Gallery THEN the Web_Gallery SHALL display share buttons for common social platforms
2. WHEN a user clicks a share button THEN the Web_Gallery SHALL open the native share dialog with the photo URL
3. WHEN a photo is captured THEN the Photo_Booth_System SHALL generate a unique shareable URL for that photo
4. WHEN a user scans a QR code THEN the Web_Gallery SHALL navigate directly to that specific photo
5. WHEN sharing to social media THEN the Web_Gallery SHALL include customizable caption text and hashtags

### Requirement 5

**User Story:** As a photo booth user, I want different photo capture modes, so that I can choose between single shots, burst mode, or animated GIFs.

#### Acceptance Criteria

1. WHEN burst mode is selected THEN the Photo_Booth_System SHALL display a 4-second countdown timer on the camera display
2. WHEN burst mode countdown completes THEN the Photo_Booth_System SHALL capture 4 photos in rapid succession with 500ms intervals
3. WHEN burst mode captures are complete THEN the Photo_Booth_System SHALL display all 4 photos on the camera screen as a preview
4. WHEN burst mode captures are complete THEN the Photo_Booth_System SHALL create a single collage image combining all 4 photos in a 2x2 grid
5. WHEN burst mode collage is created THEN the Photo_Booth_System SHALL save only the single collage image to Cloud_Storage
6. WHEN GIF mode is selected THEN the Photo_Booth_System SHALL capture 8 frames and combine them into an animated GIF
7. WHEN countdown mode is enabled THEN the Photo_Booth_System SHALL display a visual countdown timer on the camera display before capture

### Requirement 6

**User Story:** As a photo booth operator, I want to view analytics and manage photos through an admin dashboard, so that I can monitor usage and moderate content.

#### Acceptance Criteria

1. WHEN an admin accesses the dashboard THEN the Web_Gallery SHALL display total photo count, photos per day, and peak usage times
2. WHEN an admin selects a photo THEN the Web_Gallery SHALL allow the admin to delete or hide the photo
3. WHEN an admin enables moderation mode THEN the Photo_Booth_System SHALL hold new photos for approval before public display
4. WHEN viewing analytics THEN the Web_Gallery SHALL display filter usage statistics and gesture trigger counts
5. WHEN an admin exports data THEN the Web_Gallery SHALL generate a CSV file with photo metadata and timestamps

### Requirement 7

**User Story:** As a photo booth user, I want the web gallery to update in realtime, so that I can see my photos appear instantly after capture.

#### Acceptance Criteria

1. WHEN a new photo is uploaded to Cloud_Storage THEN the Web_Gallery SHALL display the photo within 2 seconds
2. WHEN viewing the gallery THEN the Web_Gallery SHALL show photos in reverse chronological order
3. WHEN the live view mode is active THEN the Web_Gallery SHALL display only the most recent photo in full screen
4. WHEN the websocket connection is lost THEN the Web_Gallery SHALL attempt reconnection every 5 seconds
5. WHEN reconnection succeeds THEN the Web_Gallery SHALL fetch and display any photos missed during disconnection

### Requirement 8

**User Story:** As a photo booth operator, I want the system to work offline and sync when connectivity returns, so that the booth remains functional during network issues.

#### Acceptance Criteria

1. WHEN network connectivity is lost THEN the Photo_Booth_System SHALL save photos to local storage
2. WHEN network connectivity is restored THEN the Photo_Booth_System SHALL upload all locally stored photos to Cloud_Storage
3. WHEN uploading fails after 3 retry attempts THEN the Photo_Booth_System SHALL mark the photo for manual retry
4. WHEN local storage exceeds 1GB THEN the Photo_Booth_System SHALL alert the operator and pause new captures
5. WHEN syncing queued photos THEN the Photo_Booth_System SHALL preserve original capture timestamps

### Requirement 9

**User Story:** As a photo booth user, I want the Arduino mascot to react to my presence and actions, so that the experience feels interactive and fun.

#### Acceptance Criteria

1. WHEN a user approaches within 1 meter THEN the Arduino_Mascot SHALL trigger a welcome animation with waving hand
2. WHEN a photo is captured THEN the Arduino_Mascot SHALL trigger a flash animation with blinking eyes
3. WHEN the booth is idle for 30 seconds THEN the Arduino_Mascot SHALL trigger a random idle animation
4. WHEN a specific Roboflow detection occurs THEN the Arduino_Mascot SHALL trigger a corresponding custom animation
5. WHEN serial communication fails THEN the Photo_Booth_System SHALL log the error and continue without mascot animations

### Requirement 10

**User Story:** As a developer, I want the system configuration to be centralized and validated, so that deployment and maintenance are straightforward.

#### Acceptance Criteria

1. WHEN the Photo_Booth_System starts THEN the system SHALL validate all required configuration parameters
2. WHEN a required configuration parameter is missing THEN the Photo_Booth_System SHALL display a clear error message and exit
3. WHEN environment variables are provided THEN the Photo_Booth_System SHALL use them over default configuration values
4. WHEN serializing configuration to disk THEN the Photo_Booth_System SHALL encode using JSON format
5. WHEN parsing configuration from disk THEN the Photo_Booth_System SHALL validate against the configuration schema



### Requirement 11

**User Story:** As a photo booth user, I want the web gallery to match the Excel Techfest 2025 design theme, so that the experience feels cohesive with the event branding.

#### Acceptance Criteria

1. WHEN viewing the Web_Gallery THEN the system SHALL display photos in a polaroid-style card format with pin decorations at the top
2. WHEN viewing the Web_Gallery THEN the system SHALL use a dark background with the Excel 2025 gold/orange color scheme
3. WHEN viewing a photo card THEN the system SHALL display metadata including "REC_DATE" and "LOC" fields in monospace font
4. WHEN viewing the Web_Gallery THEN the system SHALL display a vertical timeline connector between photo cards
5. WHEN viewing the Web_Gallery THEN the system SHALL include the Excel 2025 logo and navigation header matching the main event site

### Requirement 12

**User Story:** As a photo booth user, I want clear visual feedback on which filter is currently selected, so that I know what effect will be applied to my photo.

#### Acceptance Criteria

1. WHEN a filter button is clicked THEN the Web_Gallery SHALL highlight the selected filter button with a distinct active state matching the capture mode button styling
2. WHEN viewing the filter controls THEN the Web_Gallery SHALL NOT display a reset/none option as a separate button
3. WHEN the Photo_Booth_System receives a filter command THEN the system SHALL display the current filter name on the camera preview
4. WHEN the last selected filter is clicked again THEN the Web_Gallery SHALL deselect it and return to no filter mode

### Requirement 13

**User Story:** As a photo booth operator, I want the camera window to have standard window controls, so that I can minimize or close the application easily.

#### Acceptance Criteria

1. WHEN the camera window is displayed THEN the Photo_Booth_System SHALL provide a close button to exit the application
2. WHEN the camera window is displayed THEN the Photo_Booth_System SHALL provide a minimize button to minimize the window
3. WHEN the user presses the Escape key THEN the Photo_Booth_System SHALL exit fullscreen mode
4. WHEN the user presses 'Q' key THEN the Photo_Booth_System SHALL close the application gracefully

### Requirement 14

**User Story:** As a photo booth operator, I want photos to only be saved to Supabase cloud storage, so that I don't have to manage local storage and offline queues.

#### Acceptance Criteria

1. WHEN a photo is captured THEN the Photo_Booth_System SHALL upload directly to Cloud_Storage without saving locally
2. WHEN the upload fails THEN the Photo_Booth_System SHALL display an error message and discard the photo
3. WHEN cloud-only mode is enabled THEN the Photo_Booth_System SHALL NOT create local photo files or offline cache

### Requirement 15

**User Story:** As a photo booth user, I want my photo to appear on the website immediately after capture, so that I can see and share it right away.

#### Acceptance Criteria

1. WHEN a photo is successfully uploaded THEN the Web_Gallery SHALL display the new photo within 2 seconds via realtime subscription
2. WHEN viewing the gallery THEN the Web_Gallery SHALL show a loading indicator while photos are being fetched
3. WHEN a new photo appears THEN the Web_Gallery SHALL animate the photo card entrance for visual feedback

### Requirement 16

**User Story:** As a photo booth user, I want photos to only be captured when I show a thumbs up gesture, so that accidental captures don't occur.

#### Acceptance Criteria

1. WHEN a thumbs-up gesture is detected THEN the Photo_Booth_System SHALL trigger photo capture
2. WHEN any other gesture is detected THEN the Photo_Booth_System SHALL NOT trigger photo capture
3. WHEN peace or pointing gestures are detected THEN the Photo_Booth_System SHALL only trigger mascot animations without capturing photos
