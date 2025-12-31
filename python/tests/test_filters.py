"""
Property-based tests for Filters module.

Tests:
- Property 6: Noir filter correctness (black and white)
- Property 7: Retro filter dimension increase (polaroid)
- Property 8: No-filter identity
"""

import pytest
from hypothesis import given, strategies as st, settings
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from filters import (
    FilterType,
    apply_filter,
    apply_noir,
    apply_retro,
    apply_glitch,
    apply_neon,
    apply_dreamy,
    get_filter_from_string
)


# Strategy for generating random BGR images
def image_strategy(min_size=10, max_size=200):
    """Generate random BGR images."""
    return st.builds(
        lambda h, w: np.random.randint(0, 256, (h, w, 3), dtype=np.uint8),
        h=st.integers(min_value=min_size, max_value=max_size),
        w=st.integers(min_value=min_size, max_value=max_size)
    )


class TestNoirFilterCorrectness:
    """
    **Feature: mascot-photobooth-v2, Property 6: Noir filter correctness**
    **Validates: Requirements 3.5**
    
    For any input image, applying the NOIR filter should result in an image 
    where all pixels have equal R, G, and B values (grayscale).
    """
    
    @given(image=image_strategy())
    @settings(max_examples=100)
    def test_noir_filter_equal_rgb_channels(self, image):
        """All pixels in NOIR image should have equal R, G, B values."""
        result = apply_noir(image)
        
        # Check that all three channels are equal for every pixel
        assert np.array_equal(result[:, :, 0], result[:, :, 1])
        assert np.array_equal(result[:, :, 1], result[:, :, 2])
    
    @given(image=image_strategy())
    @settings(max_examples=100)
    def test_noir_filter_preserves_dimensions(self, image):
        """NOIR filter should preserve image dimensions."""
        result = apply_noir(image)
        assert result.shape == image.shape
    
    @given(image=image_strategy())
    @settings(max_examples=100)
    def test_noir_via_apply_filter(self, image):
        """apply_filter with NOIR type should produce same result as apply_noir."""
        direct = apply_noir(image)
        via_apply = apply_filter(image, FilterType.NOIR)
        
        assert np.array_equal(direct, via_apply)


class TestRetroFilterDimensions:
    """
    **Feature: mascot-photobooth-v2, Property 7: Retro filter dimension increase**
    **Validates: Requirements 3.4**
    
    For any input image with dimensions (H, W), applying the RETRO filter 
    should result in an image with dimensions greater than (H, W).
    """
    
    @given(image=image_strategy(min_size=20, max_size=200))
    @settings(max_examples=100)
    def test_retro_increases_dimensions(self, image):
        """RETRO filter should increase both height and width."""
        original_h, original_w = image.shape[:2]
        result = apply_retro(image)
        result_h, result_w = result.shape[:2]
        
        assert result_h > original_h, "Height should increase"
        assert result_w > original_w, "Width should increase"
    
    @given(image=image_strategy(min_size=20, max_size=200))
    @settings(max_examples=100)
    def test_retro_has_white_border(self, image):
        """RETRO filter should add white border pixels."""
        result = apply_retro(image)
        
        # Check top-left corner is white (border area)
        border_size = int(image.shape[1] * 0.05)
        if border_size > 0:
            top_left = result[0, 0]
            assert np.all(top_left == 255), "Border should be white"
    
    @given(image=image_strategy(min_size=20, max_size=200))
    @settings(max_examples=100)
    def test_retro_via_apply_filter(self, image):
        """apply_filter with RETRO type should produce same result as apply_retro."""
        direct = apply_retro(image)
        via_apply = apply_filter(image, FilterType.RETRO)
        
        assert np.array_equal(direct, via_apply)


class TestNoFilterIdentity:
    """
    **Feature: mascot-photobooth-v2, Property 8: No-filter identity**
    **Validates: Requirements 3.6**
    
    For any input image, when no filter is selected, 
    the output image should be byte-identical to the input.
    """
    
    @given(image=image_strategy())
    @settings(max_examples=100)
    def test_no_filter_returns_copy(self, image):
        """NONE filter should return identical copy of image."""
        result = apply_filter(image, FilterType.NONE)
        
        assert np.array_equal(result, image)
    
    @given(image=image_strategy())
    @settings(max_examples=100)
    def test_no_filter_is_copy_not_reference(self, image):
        """NONE filter should return a copy, not the same object."""
        result = apply_filter(image, FilterType.NONE)
        
        # Modify result and verify original is unchanged
        original_copy = image.copy()
        result[0, 0] = [0, 0, 0]
        
        assert np.array_equal(image, original_copy)


class TestFilterTypeConversion:
    """Tests for filter type string conversion."""
    
    def test_get_filter_from_string_none(self):
        assert get_filter_from_string("none") == FilterType.NONE
        assert get_filter_from_string("NONE") == FilterType.NONE
    
    def test_get_filter_from_string_glitch(self):
        assert get_filter_from_string("glitch") == FilterType.GLITCH
        assert get_filter_from_string("GLITCH") == FilterType.GLITCH
    
    def test_get_filter_from_string_neon(self):
        assert get_filter_from_string("neon") == FilterType.NEON
        assert get_filter_from_string("CYBERPUNK") == FilterType.NEON  # Alias
    
    def test_get_filter_from_string_dreamy(self):
        assert get_filter_from_string("dreamy") == FilterType.DREAMY
        assert get_filter_from_string("PASTEL") == FilterType.DREAMY  # Alias
    
    def test_get_filter_from_string_retro(self):
        assert get_filter_from_string("retro") == FilterType.RETRO
        assert get_filter_from_string("POLAROID") == FilterType.RETRO  # Alias
    
    def test_get_filter_from_string_noir(self):
        assert get_filter_from_string("noir") == FilterType.NOIR
        assert get_filter_from_string("BW") == FilterType.NOIR  # Alias
    
    def test_get_filter_from_string_unknown(self):
        """Unknown filter names should default to NONE."""
        assert get_filter_from_string("unknown") == FilterType.NONE
        assert get_filter_from_string("") == FilterType.NONE


class TestGlitchFilter:
    """Tests for glitch filter."""
    
    @given(image=image_strategy(min_size=20, max_size=100))
    @settings(max_examples=50)
    def test_glitch_preserves_dimensions(self, image):
        """Glitch filter should preserve image dimensions."""
        result = apply_glitch(image)
        assert result.shape == image.shape
    
    @given(image=image_strategy(min_size=20, max_size=100))
    @settings(max_examples=50)
    def test_glitch_returns_valid_image(self, image):
        """Glitch filter should return valid BGR image."""
        result = apply_glitch(image)
        
        assert result.dtype == np.uint8
        assert len(result.shape) == 3
        assert result.shape[2] == 3


class TestNeonFilter:
    """Tests for neon filter."""
    
    @given(image=image_strategy(min_size=20, max_size=100))
    @settings(max_examples=50)
    def test_neon_preserves_dimensions(self, image):
        """Neon filter should preserve image dimensions."""
        result = apply_neon(image)
        assert result.shape == image.shape
    
    @given(image=image_strategy(min_size=20, max_size=100))
    @settings(max_examples=50)
    def test_neon_returns_valid_image(self, image):
        """Neon filter should return valid BGR image."""
        result = apply_neon(image)
        
        assert result.dtype == np.uint8
        assert len(result.shape) == 3
        assert result.shape[2] == 3


class TestDreamyFilter:
    """Tests for dreamy filter."""
    
    @given(image=image_strategy(min_size=20, max_size=100))
    @settings(max_examples=50)
    def test_dreamy_preserves_dimensions(self, image):
        """Dreamy filter should preserve image dimensions."""
        result = apply_dreamy(image)
        assert result.shape == image.shape
    
    @given(image=image_strategy(min_size=20, max_size=100))
    @settings(max_examples=50)
    def test_dreamy_returns_valid_image(self, image):
        """Dreamy filter should return valid BGR image."""
        result = apply_dreamy(image)
        
        assert result.dtype == np.uint8
        assert len(result.shape) == 3
        assert result.shape[2] == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
