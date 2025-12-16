"""
Property-based tests for Roboflow Detector module.

Tests Property 5: Detection confidence animation trigger
"""

import pytest
from hypothesis import given, strategies as st, settings
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from roboflow_detector import (
    RoboflowDetector,
    Detection,
    DetectionResult,
    AnimationType
)


# Strategies for generating test data
confidence_strategy = st.floats(min_value=0.0, max_value=1.0, allow_nan=False)
class_name_strategy = st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'N')))
bbox_strategy = st.tuples(
    st.integers(min_value=0, max_value=1920),
    st.integers(min_value=0, max_value=1080),
    st.integers(min_value=1, max_value=500),
    st.integers(min_value=1, max_value=500)
)

detection_strategy = st.builds(
    Detection,
    class_name=class_name_strategy,
    confidence=confidence_strategy,
    bbox=bbox_strategy
)


class TestDetectionConfidenceThreshold:
    """
    **Feature: mascot-photobooth-v2, Property 5: Detection confidence animation trigger**
    **Validates: Requirements 2.5**
    
    For any Roboflow detection with confidence above 0.8, 
    the system should trigger the corresponding custom animation.
    """
    
    @given(confidence=st.floats(min_value=0.81, max_value=1.0, allow_nan=False))
    @settings(max_examples=100)
    def test_high_confidence_triggers_animation(self, confidence):
        """Detections with confidence > 0.8 should trigger animations."""
        detector = RoboflowDetector(
            api_key="test",
            model_id="test/1",
            confidence_threshold=0.8
        )
        
        detection = Detection(
            class_name="test_object",
            confidence=confidence,
            bbox=(100, 100, 50, 50)
        )
        
        animation = detector.get_animation_for_detection(detection)
        assert animation is not None, f"Expected animation for confidence {confidence}"
    
    @given(confidence=st.floats(min_value=0.0, max_value=0.79, allow_nan=False))
    @settings(max_examples=100)
    def test_low_confidence_no_animation(self, confidence):
        """Detections with confidence <= 0.8 should not trigger animations."""
        detector = RoboflowDetector(
            api_key="test",
            model_id="test/1",
            confidence_threshold=0.8
        )
        
        detection = Detection(
            class_name="test_object",
            confidence=confidence,
            bbox=(100, 100, 50, 50)
        )
        
        animation = detector.get_animation_for_detection(detection)
        assert animation is None, f"Expected no animation for confidence {confidence}"
    
    @given(
        threshold=st.floats(min_value=0.1, max_value=0.9, allow_nan=False),
        confidence=st.floats(min_value=0.0, max_value=1.0, allow_nan=False)
    )
    @settings(max_examples=100)
    def test_configurable_threshold(self, threshold, confidence):
        """Animation trigger respects configurable threshold."""
        detector = RoboflowDetector(
            api_key="test",
            model_id="test/1",
            confidence_threshold=threshold
        )
        
        detection = Detection(
            class_name="test_object",
            confidence=confidence,
            bbox=(100, 100, 50, 50)
        )
        
        animation = detector.get_animation_for_detection(detection)
        
        if confidence >= threshold:
            assert animation is not None
        else:
            assert animation is None
    
    @given(detections=st.lists(detection_strategy, min_size=0, max_size=10))
    @settings(max_examples=100)
    def test_triggered_animations_only_high_confidence(self, detections):
        """get_triggered_animations only returns high-confidence detections."""
        threshold = 0.8
        detector = RoboflowDetector(
            api_key="test",
            model_id="test/1",
            confidence_threshold=threshold
        )
        
        triggered = detector.get_triggered_animations(detections)
        
        # All triggered detections should have confidence >= threshold
        for det, anim in triggered:
            assert det.confidence >= threshold
        
        # Count should match high-confidence detections
        high_conf_count = sum(1 for d in detections if d.confidence >= threshold)
        assert len(triggered) == high_conf_count


class TestDetectionDataIntegrity:
    """Tests for Detection data class integrity."""
    
    @given(detection=detection_strategy)
    @settings(max_examples=100)
    def test_detection_to_dict_roundtrip(self, detection):
        """Detection.to_dict() preserves all data."""
        d = detection.to_dict()
        
        assert d["class_name"] == detection.class_name
        assert d["confidence"] == detection.confidence
        assert d["bbox"] == detection.bbox
    
    @given(
        class_name=class_name_strategy,
        confidence=confidence_strategy,
        bbox=bbox_strategy
    )
    @settings(max_examples=100)
    def test_detection_creation(self, class_name, confidence, bbox):
        """Detection can be created with any valid inputs."""
        detection = Detection(
            class_name=class_name,
            confidence=confidence,
            bbox=bbox
        )
        
        assert detection.class_name == class_name
        assert detection.confidence == confidence
        assert detection.bbox == bbox


class TestAnimationMappings:
    """Tests for animation mapping functionality."""
    
    def test_default_heart_mapping(self):
        """Heart class maps to LOVE animation."""
        detector = RoboflowDetector(api_key="test", model_id="test/1")
        detection = Detection(class_name="heart", confidence=0.9, bbox=(0, 0, 10, 10))
        
        animation = detector.get_animation_for_detection(detection)
        assert animation == AnimationType.LOVE
    
    def test_default_star_mapping(self):
        """Star class maps to RAINBOW animation."""
        detector = RoboflowDetector(api_key="test", model_id="test/1")
        detection = Detection(class_name="star", confidence=0.9, bbox=(0, 0, 10, 10))
        
        animation = detector.get_animation_for_detection(detection)
        assert animation == AnimationType.RAINBOW
    
    def test_custom_mapping_override(self):
        """Custom mappings override defaults."""
        custom_mappings = {"heart": AnimationType.WINK}
        detector = RoboflowDetector(
            api_key="test",
            model_id="test/1",
            animation_mappings=custom_mappings
        )
        detection = Detection(class_name="heart", confidence=0.9, bbox=(0, 0, 10, 10))
        
        animation = detector.get_animation_for_detection(detection)
        assert animation == AnimationType.WINK


class TestDetectorAvailability:
    """Tests for detector availability checks."""
    
    def test_not_available_without_api_key(self):
        """Detector is not available without API key."""
        detector = RoboflowDetector(api_key=None, model_id="test/1")
        assert not detector.is_available()
    
    def test_not_available_without_model_id(self):
        """Detector is not available without model ID."""
        detector = RoboflowDetector(api_key="test", model_id=None)
        assert not detector.is_available()
    
    def test_available_with_both(self):
        """Detector is available with both API key and model ID."""
        detector = RoboflowDetector(api_key="test", model_id="test/1")
        assert detector.is_available()
    
    def test_detect_returns_error_when_not_configured(self):
        """detect() returns error result when not configured."""
        import numpy as np
        detector = RoboflowDetector(api_key=None, model_id=None)
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        
        result = detector.detect(frame)
        
        assert not result.success
        assert "not configured" in result.error_message


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
