"""
Capture Modes Module

Provides different photo capture modes: single, burst, and GIF.
"""

import cv2
import numpy as np
import time
import os
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional
import imageio

from filters import FilterType, apply_filter


class CaptureMode(Enum):
    """Available capture modes."""
    SINGLE = "single"
    BURST = "burst"
    GIF = "gif"


@dataclass
class CaptureResult:
    """Result of a capture operation."""
    mode: CaptureMode
    images: List[np.ndarray]
    timestamps: List[float]
    output_path: Optional[str] = None
    collage_path: Optional[str] = None
    gif_path: Optional[str] = None
    collage_image: Optional[np.ndarray] = None
    gif_bytes: Optional[bytes] = None


class CaptureManager:
    """
    Manages different photo capture modes.
    
    Supports:
    - Single: One photo
    - Burst: 4 photos in rapid succession
    - GIF: 8 frames combined into animated GIF
    """
    
    BURST_COUNT = 4
    BURST_INTERVAL_MS = 500
    GIF_FRAME_COUNT = 8
    GIF_INTERVAL_MS = 200
    
    def __init__(self, photo_dir: str = "photos"):
        """
        Initialize the capture manager.
        
        Args:
            photo_dir: Directory to save captured photos
        """
        self.photo_dir = photo_dir
        os.makedirs(photo_dir, exist_ok=True)
    
    def capture_single(
        self,
        frame: np.ndarray,
        filter_type: FilterType = FilterType.NONE,
        text: str = "Mascot 2025",
        save_to_disk: bool = True
    ) -> CaptureResult:
        """
        Capture a single photo.
        
        Args:
            frame: BGR image to capture
            filter_type: Filter to apply
            text: Text for polaroid filter
            
        Returns:
            CaptureResult with single image
        """
        timestamp = time.time()
        filtered = apply_filter(frame, filter_type, text)
        
        filename = f"photo_{int(timestamp)}.jpg"
        filepath = os.path.join(self.photo_dir, filename)
        
        if save_to_disk:
            cv2.imwrite(filepath, filtered)
        else:
            filepath = None # No local file
        
        return CaptureResult(
            mode=CaptureMode.SINGLE,
            images=[filtered],
            timestamps=[timestamp],
            output_path=filepath
        )
    
    def capture_burst(
        self,
        cap: cv2.VideoCapture,
        filter_type: FilterType = FilterType.NONE,
        count: int = None,
        interval_ms: int = None,
        save_to_disk: bool = True,
        window_name: str = "Mascot View"
    ) -> CaptureResult:
        """
        Capture multiple photos in rapid succession with 4-second countdown.
        Shows preview of all 4 photos on camera screen.
        Only saves the collage image (not individual photos).
        
        Args:
            cap: OpenCV VideoCapture object
            filter_type: Filter to apply to all photos
            count: Number of photos (default: 4)
            interval_ms: Interval between captures in ms (default: 500)
            window_name: Name of display window for preview
            
        Returns:
            CaptureResult with burst images and collage
        """
        count = count or self.BURST_COUNT
        interval_ms = interval_ms or self.BURST_INTERVAL_MS
        
        images = []
        timestamps = []
        base_timestamp = int(time.time())
        
        # Capture photos: first one immediately, then countdown between each subsequent photo
        for i in range(count):
            # For photos after the first, show countdown
            if i > 0:
                # Show 4-second countdown before next photo
                self.show_countdown(cap, window_name=window_name, seconds=4)
            
            ret, frame = cap.read()
            if ret:
                # Mirror the frame for selfie-style
                frame = cv2.flip(frame, 1)
                timestamp = time.time()
                filtered = apply_filter(frame, filter_type)
                images.append(filtered)
                timestamps.append(timestamp)
                
                # Show capture flash
                h, w = frame.shape[:2]
                flash_frame = frame.copy()
                cv2.rectangle(flash_frame, (0, 0), (w, h), (255, 255, 255), -1)
                cv2.imshow(window_name, flash_frame)
                cv2.waitKey(50)
                
                # Show captured image briefly with photo number
                display = filtered.copy()
                cv2.putText(display, f"Photo {i+1}/{count} captured!", 
                            (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
                cv2.imshow(window_name, display)
                cv2.waitKey(300)
        
        # Show preview of all 4 photos for 2 seconds
        if images:
            self.show_preview(images, window_name=window_name, duration_ms=2000)
        
        # Create collage (only this gets uploaded)
        collage = self.create_collage(images)
        collage_filename = f"collage_{base_timestamp}.jpg"
        collage_path = os.path.join(self.photo_dir, collage_filename)
        
        if save_to_disk:
            cv2.imwrite(collage_path, collage)
        else:
            collage_path = None

        return CaptureResult(
            mode=CaptureMode.BURST,
            images=images,
            timestamps=timestamps,
            output_path=collage_path,
            collage_path=collage_path,
            collage_image=collage
        )
    
    def capture_gif(
        self,
        cap: cv2.VideoCapture,
        filter_type: FilterType = FilterType.NONE,
        frames: int = None,
        interval_ms: int = None,
        duration_per_frame: float = 0.2,
        save_to_disk: bool = True,
        window_name: str = "Mascot View"
    ) -> CaptureResult:
        """
        Capture frames and combine into animated GIF with smooth live preview.
        
        Args:
            cap: OpenCV VideoCapture object
            filter_type: Filter to apply
            frames: Number of frames (default: 8)
            interval_ms: Interval between captures in ms (default: 200)
            duration_per_frame: Duration of each frame in GIF (seconds)
            window_name: Display window name
            
        Returns:
            CaptureResult with GIF
        """
        frames_count = frames or self.GIF_FRAME_COUNT
        interval_ms = interval_ms or self.GIF_INTERVAL_MS
        
        images = []
        timestamps = []
        base_timestamp = int(time.time())
        
        # Smooth capture with live preview
        for i in range(frames_count):
            ret, frame = cap.read()
            if ret:
                # Mirror the frame for selfie-style
                frame = cv2.flip(frame, 1)
                timestamp = time.time()
                
                # Create display with recording indicator (before filter for speed)
                display = frame.copy()
                h, w = display.shape[:2]
                
                # Add REC indicator
                cv2.circle(display, (30, 30), 12, (0, 0, 255), -1)  # Red dot
                cv2.putText(display, "REC", (50, 38), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                
                # Frame counter
                cv2.putText(display, f"GIF Frame {i+1}/{frames_count}", 
                           (w - 200, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                
                # Progress bar
                progress = (i + 1) / frames_count
                bar_width = 200
                bar_x = (w - bar_width) // 2
                bar_y = h - 40
                cv2.rectangle(display, (bar_x, bar_y), (bar_x + bar_width, bar_y + 10), (50, 50, 50), -1)
                cv2.rectangle(display, (bar_x, bar_y), (bar_x + int(bar_width * progress), bar_y + 10), (0, 255, 0), -1)
                
                # Show live preview (non-blocking)
                cv2.imshow(window_name, display)
                cv2.waitKey(1)  # Minimal wait for responsive display
                
                # Apply filter (do this after display for smoother preview)
                filtered = apply_filter(frame, filter_type)
                
                # Convert BGR to RGB for GIF
                rgb_frame = cv2.cvtColor(filtered, cv2.COLOR_BGR2RGB)
                images.append(rgb_frame)
                timestamps.append(timestamp)
            
            # Wait for next frame (but keep display responsive)
            if i < frames_count - 1:
                wait_start = time.time()
                while (time.time() - wait_start) < (interval_ms / 1000.0):
                    ret, preview = cap.read()
                    if ret:
                        # Mirror the preview
                        preview = cv2.flip(preview, 1)
                        # Show preview with waiting indicator
                        h, w = preview.shape[:2]
                        cv2.circle(preview, (30, 30), 12, (0, 0, 255), -1)
                        cv2.putText(preview, "REC", (50, 38), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                        cv2.putText(preview, f"Next: {i+2}/{frames_count}", 
                                   (w - 180, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                        cv2.imshow(window_name, preview)
                    cv2.waitKey(30)  # ~30fps preview
        
        # Show "Processing..." message
        ret, final_frame = cap.read()
        if ret:
            final_frame = cv2.flip(final_frame, 1)
            h, w = final_frame.shape[:2]
            overlay = final_frame.copy()
            cv2.rectangle(overlay, (w//4, h//2-30), (3*w//4, h//2+30), (0, 0, 0), -1)
            final_frame = cv2.addWeighted(overlay, 0.7, final_frame, 0.3, 0)
            cv2.putText(final_frame, "Creating GIF...", 
                       (w//2 - 100, h//2 + 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
            cv2.imshow(window_name, final_frame)
            cv2.waitKey(100)
        
        # Create GIF
        gif_filename = f"animation_{base_timestamp}.gif"
        gif_path = os.path.join(self.photo_dir, gif_filename)
        gif_bytes_data = None
        
        if save_to_disk:
            imageio.mimsave(
                gif_path,
                images,
                duration=duration_per_frame,
                loop=0
            )
        else:
            # Save to bytes
            import io
            with io.BytesIO() as buf:
                 imageio.mimsave(buf, images, format='GIF', duration=duration_per_frame, loop=0)
                 gif_bytes_data = buf.getvalue()
            gif_path = None
        
        # Convert back to BGR for consistency
        bgr_images = [cv2.cvtColor(img, cv2.COLOR_RGB2BGR) for img in images]
        
        return CaptureResult(
            mode=CaptureMode.GIF,
            images=bgr_images,
            timestamps=timestamps,
            output_path=gif_path,
            gif_path=gif_path,
            gif_bytes=gif_bytes_data
        )
    
    def create_collage(self, images: List[np.ndarray]) -> np.ndarray:
        """
        Create a 2x2 collage from images.
        
        Args:
            images: List of BGR images (should be 4 for 2x2 grid)
            
        Returns:
            Collage image
        """
        if not images:
            raise ValueError("No images provided for collage")
        
        # Work on a copy to avoid mutating the input list
        process_images = images.copy()
        
        # Ensure we have exactly 4 images for 2x2 grid
        while len(process_images) < 4:
            process_images.append(process_images[-1].copy())
        process_images = process_images[:4]
        
        # Resize all images to same size
        target_h = min(img.shape[0] for img in process_images)
        target_w = min(img.shape[1] for img in process_images)
        
        resized = []
        for img in process_images:
            resized.append(cv2.resize(img, (target_w, target_h)))
        
        # Create 2x2 grid
        top_row = np.hstack([resized[0], resized[1]])
        bottom_row = np.hstack([resized[2], resized[3]])
        collage = np.vstack([top_row, bottom_row])
        
        return collage
    
    def show_countdown(
        self,
        cap: cv2.VideoCapture,
        window_name: str = "Mascot View",
        seconds: int = 4
    ) -> None:
        """
        Display countdown on screen before capture.
        
        Args:
            cap: OpenCV VideoCapture object
            window_name: Name of display window
            seconds: Countdown duration (default: 4 for burst mode)
        """
        for i in range(seconds, 0, -1):
            start = time.time()
            while time.time() - start < 1.0:
                ret, frame = cap.read()
                if ret:
                    # Mirror the frame for selfie-style
                    frame = cv2.flip(frame, 1)
                    display = frame.copy()
                    
                    # Draw countdown number
                    h, w = display.shape[:2]
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    text = str(i)
                    font_scale = 5
                    thickness = 10
                    
                    text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
                    text_x = (w - text_size[0]) // 2
                    text_y = (h + text_size[1]) // 2
                    
                    # Draw shadow
                    cv2.putText(display, text, (text_x + 3, text_y + 3),
                                font, font_scale, (0, 0, 0), thickness + 2)
                    # Draw text (gold color)
                    cv2.putText(display, text, (text_x, text_y),
                                font, font_scale, (0, 215, 255), thickness)
                    
                    # Draw "GET READY!" text
                    ready_text = "GET READY!"
                    ready_size = cv2.getTextSize(ready_text, font, 1.5, 3)[0]
                    ready_x = (w - ready_size[0]) // 2
                    cv2.putText(display, ready_text, (ready_x, text_y + 80),
                                font, 1.5, (0, 255, 0), 3)
                    
                    cv2.imshow(window_name, display)
                    cv2.waitKey(1)
    
    def show_preview(
        self,
        images: List[np.ndarray],
        window_name: str = "Mascot View",
        duration_ms: int = 2000
    ) -> None:
        """
        Display preview of captured images as a 2x2 grid.
        
        Args:
            images: List of captured images
            window_name: Name of display window
            duration_ms: How long to show preview
        """
        if not images:
            return
        
        # Create preview collage
        preview = self.create_collage(images)
        
        # Add "PREVIEW" text overlay
        h, w = preview.shape[:2]
        overlay = preview.copy()
        
        # Semi-transparent banner at top
        cv2.rectangle(overlay, (0, 0), (w, 60), (0, 0, 0), -1)
        preview = cv2.addWeighted(overlay, 0.7, preview, 0.3, 0)
        
        # Add text
        cv2.putText(preview, "BURST PREVIEW - Uploading...", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 215, 255), 2)
        
        cv2.imshow(window_name, preview)
        cv2.waitKey(duration_ms)


def get_gif_frame_count(gif_path: str) -> int:
    """
    Get the number of frames in a GIF file.
    
    Args:
        gif_path: Path to GIF file
        
    Returns:
        Number of frames
    """
    reader = imageio.get_reader(gif_path)
    count = len(list(reader))
    reader.close()
    return count
