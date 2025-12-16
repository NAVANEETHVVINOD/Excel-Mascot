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
        save_to_disk: bool = True
    ) -> CaptureResult:
        """
        Capture multiple photos in rapid succession.
        
        Args:
            cap: OpenCV VideoCapture object
            filter_type: Filter to apply to all photos
            count: Number of photos (default: 4)
            interval_ms: Interval between captures in ms (default: 500)
            
        Returns:
            CaptureResult with burst images and collage
        """
        count = count or self.BURST_COUNT
        interval_ms = interval_ms or self.BURST_INTERVAL_MS
        
        images = []
        timestamps = []
        base_timestamp = int(time.time())
        
        for i in range(count):
            ret, frame = cap.read()
            if ret:
                timestamp = time.time()
                filtered = apply_filter(frame, filter_type)
                images.append(filtered)
                timestamps.append(timestamp)
                
                # Save individual photo
                filename = f"burst_{base_timestamp}_{i+1}.jpg"
                filepath = os.path.join(self.photo_dir, filename)
                if save_to_disk:
                    cv2.imwrite(filepath, filtered)
            
            if i < count - 1:
                time.sleep(interval_ms / 1000.0)
        
        # Create collage
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
        save_to_disk: bool = True
    ) -> CaptureResult:
        """
        Capture frames and combine into animated GIF.
        
        Args:
            cap: OpenCV VideoCapture object
            filter_type: Filter to apply
            frames: Number of frames (default: 8)
            interval_ms: Interval between captures in ms (default: 200)
            duration_per_frame: Duration of each frame in GIF (seconds)
            
        Returns:
            CaptureResult with GIF
        """
        frames_count = frames or self.GIF_FRAME_COUNT
        interval_ms = interval_ms or self.GIF_INTERVAL_MS
        
        images = []
        timestamps = []
        base_timestamp = int(time.time())
        
        for i in range(frames_count):
            ret, frame = cap.read()
            if ret:
                timestamp = time.time()
                # Apply filter first
                filtered = apply_filter(frame, filter_type)
                
                # Convert BGR to RGB for GIF
                rgb_frame = cv2.cvtColor(filtered, cv2.COLOR_BGR2RGB)
                images.append(rgb_frame)
                timestamps.append(timestamp)
            
            if i < frames_count - 1:
                time.sleep(interval_ms / 1000.0)
        
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
        seconds: int = 3
    ) -> None:
        """
        Display countdown on screen before capture.
        
        Args:
            cap: OpenCV VideoCapture object
            window_name: Name of display window
            seconds: Countdown duration
        """
        for i in range(seconds, 0, -1):
            start = time.time()
            while time.time() - start < 1.0:
                ret, frame = cap.read()
                if ret:
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
                    # Draw text
                    cv2.putText(display, text, (text_x, text_y),
                                font, font_scale, (0, 255, 255), thickness)
                    
                    cv2.imshow(window_name, display)
                    cv2.waitKey(1)


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
