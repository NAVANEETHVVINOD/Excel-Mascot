"""
Property-based tests for Capture Modes module.

Tests:
- Property 11: Burst mode photo count
- Property 12: GIF frame count
- Property 13: Collage composition
"""

import pytest
from hypothesis import given, strategies as st, settings
import numpy as np
import tempfile
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from capture_modes import (
    CaptureMode,
    CaptureResult,
    CaptureManager,
    get_gif_frame_count
)
from filters import FilterType


class MockVideoCapture:
    """Mock VideoCapture for testing without real camera."""
    
    def __init__(self, frame_generator=None, width=640, height=480):
        self.width = width
        self.height = height
        self.frame_generator = frame_generator
        self.frame_count = 0
    
    def read(self):
        if self.frame_generator:
            frame = self.frame_generator(self.frame_count)
        else:
            # Generate random frame
            frame = np.random.randint(0, 256, (self.height, self.width, 3), dtype=np.uint8)
        self.frame_count += 1
        return True, frame
    
    def isOpened(self):
        return True
    
    def release(self):
        pass


class TestBurstModePhotoCount:
    """
    **Feature: mascot-photobooth-v2, Property 11: Burst mode photo count**
    **Validates: Requirements 5.1**
    
    For any burst mode capture, the system should produce exactly 4 photos.
    """
    
    def test_burst_produces_exactly_4_photos(self):
        """Burst mode should capture exactly 4 photos."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CaptureManager(photo_dir=tmpdir)
            cap = MockVideoCapture()
            
            result = manager.capture_burst(cap, interval_ms=10)
            
            assert len(result.images) == 4
            assert result.mode == CaptureMode.BURST
    
    @given(count=st.integers(min_value=1, max_value=10))
    @settings(max_examples=20, deadline=None)
    def test_burst_respects_custom_count(self, count):
        """Burst mode should respect custom count parameter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CaptureManager(photo_dir=tmpdir)
            cap = MockVideoCapture()
            
            result = manager.capture_burst(cap, count=count, interval_ms=10)
            
            assert len(result.images) == count
    
    def test_burst_creates_collage(self):
        """Burst mode should create a collage image."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CaptureManager(photo_dir=tmpdir)
            cap = MockVideoCapture()
            
            result = manager.capture_burst(cap, interval_ms=10)
            
            assert result.collage_path is not None
            assert os.path.exists(result.collage_path)
    
    def test_burst_timestamps_are_sequential(self):
        """Burst timestamps should be in sequential order."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CaptureManager(photo_dir=tmpdir)
            cap = MockVideoCapture()
            
            result = manager.capture_burst(cap, interval_ms=10)
            
            for i in range(len(result.timestamps) - 1):
                assert result.timestamps[i] <= result.timestamps[i + 1]


class TestGIFFrameCount:
    """
    **Feature: mascot-photobooth-v2, Property 12: GIF frame count**
    **Validates: Requirements 5.2**
    
    For any GIF mode capture, the resulting GIF should contain exactly 8 frames.
    """
    
    def test_gif_produces_exactly_8_frames(self):
        """GIF mode should capture exactly 8 frames."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CaptureManager(photo_dir=tmpdir)
            cap = MockVideoCapture()
            
            result = manager.capture_gif(cap, interval_ms=10)
            
            assert len(result.images) == 8
            assert result.mode == CaptureMode.GIF
    
    def test_gif_file_has_8_frames(self):
        """Generated GIF file should have exactly 8 frames."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CaptureManager(photo_dir=tmpdir)
            cap = MockVideoCapture()
            
            result = manager.capture_gif(cap, interval_ms=10)
            
            assert result.gif_path is not None
            assert os.path.exists(result.gif_path)
            
            frame_count = get_gif_frame_count(result.gif_path)
            assert frame_count == 8
    
    @given(frames=st.integers(min_value=2, max_value=15))
    @settings(max_examples=20, deadline=None)
    def test_gif_respects_custom_frame_count(self, frames):
        """GIF mode should respect custom frame count parameter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CaptureManager(photo_dir=tmpdir)
            cap = MockVideoCapture()
            
            result = manager.capture_gif(cap, frames=frames, interval_ms=10)
            
            assert len(result.images) == frames
            
            frame_count = get_gif_frame_count(result.gif_path)
            assert frame_count == frames


class TestCollageComposition:
    """
    **Feature: mascot-photobooth-v2, Property 13: Collage composition**
    **Validates: Requirements 5.5**
    
    For any burst mode result, the collage image should have dimensions 
    that accommodate all 4 source images.
    """
    
    def test_collage_dimensions_accommodate_4_images(self):
        """Collage should be 2x2 grid of source images."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CaptureManager(photo_dir=tmpdir)
            
            # Create 4 test images of same size
            images = [np.random.randint(0, 256, (100, 150, 3), dtype=np.uint8) for _ in range(4)]
            
            collage = manager.create_collage(images)
            
            # Collage should be 2x height and 2x width
            assert collage.shape[0] == 200  # 2 * 100
            assert collage.shape[1] == 300  # 2 * 150
    
    @given(
        h=st.integers(min_value=50, max_value=200),
        w=st.integers(min_value=50, max_value=200)
    )
    @settings(max_examples=50)
    def test_collage_dimensions_scale_with_input(self, h, w):
        """Collage dimensions should scale with input image dimensions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CaptureManager(photo_dir=tmpdir)
            
            images = [np.random.randint(0, 256, (h, w, 3), dtype=np.uint8) for _ in range(4)]
            
            collage = manager.create_collage(images)
            
            assert collage.shape[0] == h * 2
            assert collage.shape[1] == w * 2
    
    def test_collage_handles_fewer_than_4_images(self):
        """Collage should handle fewer than 4 images by duplicating."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CaptureManager(photo_dir=tmpdir)
            
            images = [np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8) for _ in range(2)]
            
            collage = manager.create_collage(images)
            
            # Should still produce 2x2 grid
            assert collage.shape[0] == 200
            assert collage.shape[1] == 200
    
    def test_collage_handles_more_than_4_images(self):
        """Collage should use only first 4 images if more provided."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CaptureManager(photo_dir=tmpdir)
            
            images = [np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8) for _ in range(6)]
            
            collage = manager.create_collage(images)
            
            # Should still produce 2x2 grid
            assert collage.shape[0] == 200
            assert collage.shape[1] == 200


class TestSingleCapture:
    """Tests for single capture mode."""
    
    def test_single_capture_saves_file(self):
        """Single capture should save image to disk."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CaptureManager(photo_dir=tmpdir)
            frame = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
            
            result = manager.capture_single(frame)
            
            assert result.mode == CaptureMode.SINGLE
            assert len(result.images) == 1
            assert os.path.exists(result.output_path)
    
    def test_single_capture_applies_filter(self):
        """Single capture should apply specified filter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CaptureManager(photo_dir=tmpdir)
            frame = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
            
            result = manager.capture_single(frame, filter_type=FilterType.NOIR)
            
            # NOIR filter should make all channels equal (grayscale)
            img = result.images[0]
            assert np.array_equal(img[:, :, 0], img[:, :, 1])


class TestCaptureResult:
    """Tests for CaptureResult dataclass."""
    
    def test_capture_result_creation(self):
        """CaptureResult should store all fields correctly."""
        images = [np.zeros((100, 100, 3), dtype=np.uint8)]
        timestamps = [1234567890.0]
        
        result = CaptureResult(
            mode=CaptureMode.SINGLE,
            images=images,
            timestamps=timestamps,
            output_path="/path/to/photo.jpg"
        )
        
        assert result.mode == CaptureMode.SINGLE
        assert len(result.images) == 1
        assert len(result.timestamps) == 1
        assert result.output_path == "/path/to/photo.jpg"
        assert result.collage_path is None
        assert result.gif_path is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
