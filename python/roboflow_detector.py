"""
Roboflow Rapid Integration Module

Provides AI-powered object detection using Roboflow Rapid API.
Falls back gracefully when API is unavailable or times out.
"""

import cv2
import numpy as np
import requests
import base64
import time
from dataclasses import dataclass
from typing import List, Optional, Tuple
from enum import Enum


class AnimationType(Enum):
    """Animation types that can be triggered by detections."""
    NORMAL = "NORMAL"
    WINK = "WINK"
    FLASH = "FLASH"
    LOVE = "LOVE"
    SUS = "SUS"
    RAINBOW = "RAINBOW"
    WELCOME = "WELCOME"
    CUSTOM = "CUSTOM"


@dataclass
class Detection:
    """Represents a single object detection result."""
    class_name: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # x, y, width, height
    
    def to_dict(self) -> dict:
        return {
            "class_name": self.class_name,
            "confidence": self.confidence,
            "bbox": self.bbox
        }


@dataclass
class DetectionResult:
    """Container for all detections from a single frame."""
    detections: List[Detection]
    inference_time_ms: float
    success: bool
    error_message: Optional[str] = None


class RoboflowDetector:
    """
    Roboflow Rapid object detector with timeout handling.
    
    Falls back gracefully when:
    - API key is not configured
    - API times out (>2 seconds)
    - API returns an error
    """
    
    TIMEOUT_SECONDS = 2.0
    API_URL = "https://detect.roboflow.com"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_id: Optional[str] = None,
        confidence_threshold: float = 0.8,
        animation_mappings: Optional[dict] = None
    ):
        """
        Initialize the Roboflow detector.
        
        Args:
            api_key: Roboflow API key
            model_id: Model ID in format "project/version"
            confidence_threshold: Minimum confidence for detections (0.0-1.0)
            animation_mappings: Dict mapping class names to AnimationType
        """
        self.api_key = api_key
        self.model_id = model_id
        self.confidence_threshold = confidence_threshold
        self.animation_mappings = animation_mappings or {}
        self._enabled = bool(api_key and model_id)
        self._last_error: Optional[str] = None
    
    def is_available(self) -> bool:
        """Check if the detector is configured and available."""
        return self._enabled
    
    def get_last_error(self) -> Optional[str]:
        """Get the last error message, if any."""
        return self._last_error
    
    def detect(self, frame: np.ndarray) -> DetectionResult:
        """
        Run object detection on a frame.
        
        Args:
            frame: BGR image as numpy array
            
        Returns:
            DetectionResult with detections or error info
        """
        if not self._enabled:
            return DetectionResult(
                detections=[],
                inference_time_ms=0,
                success=False,
                error_message="Roboflow detector not configured"
            )
        
        start_time = time.time()
        
        try:
            # Encode frame to base64
            _, buffer = cv2.imencode('.jpg', frame)
            img_base64 = base64.b64encode(buffer).decode('utf-8')
            
            # Make API request
            url = f"{self.API_URL}/{self.model_id}"
            params = {
                "api_key": self.api_key,
                "confidence": self.confidence_threshold
            }
            
            response = requests.post(
                url,
                params=params,
                data=img_base64,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=self.TIMEOUT_SECONDS
            )
            
            inference_time = (time.time() - start_time) * 1000
            
            if response.status_code != 200:
                self._last_error = f"API error: {response.status_code}"
                return DetectionResult(
                    detections=[],
                    inference_time_ms=inference_time,
                    success=False,
                    error_message=self._last_error
                )
            
            # Parse response
            data = response.json()
            detections = []
            
            for pred in data.get("predictions", []):
                detection = Detection(
                    class_name=pred.get("class", "unknown"),
                    confidence=pred.get("confidence", 0.0),
                    bbox=(
                        int(pred.get("x", 0) - pred.get("width", 0) / 2),
                        int(pred.get("y", 0) - pred.get("height", 0) / 2),
                        int(pred.get("width", 0)),
                        int(pred.get("height", 0))
                    )
                )
                detections.append(detection)
            
            self._last_error = None
            return DetectionResult(
                detections=detections,
                inference_time_ms=inference_time,
                success=True
            )
            
        except requests.Timeout:
            inference_time = (time.time() - start_time) * 1000
            self._last_error = "API timeout (>2s)"
            return DetectionResult(
                detections=[],
                inference_time_ms=inference_time,
                success=False,
                error_message=self._last_error
            )
            
        except requests.RequestException as e:
            inference_time = (time.time() - start_time) * 1000
            self._last_error = f"Request error: {str(e)}"
            return DetectionResult(
                detections=[],
                inference_time_ms=inference_time,
                success=False,
                error_message=self._last_error
            )
            
        except Exception as e:
            inference_time = (time.time() - start_time) * 1000
            self._last_error = f"Unexpected error: {str(e)}"
            return DetectionResult(
                detections=[],
                inference_time_ms=inference_time,
                success=False,
                error_message=self._last_error
            )
    
    def draw_detections(
        self,
        frame: np.ndarray,
        detections: List[Detection],
        color: Tuple[int, int, int] = (0, 255, 0),
        thickness: int = 2
    ) -> np.ndarray:
        """
        Draw bounding boxes and labels on frame.
        
        Args:
            frame: BGR image as numpy array
            detections: List of Detection objects
            color: BGR color for boxes
            thickness: Line thickness
            
        Returns:
            Frame with drawn detections
        """
        result = frame.copy()
        
        for det in detections:
            x, y, w, h = det.bbox
            
            # Draw bounding box
            cv2.rectangle(result, (x, y), (x + w, y + h), color, thickness)
            
            # Draw label background
            label = f"{det.class_name}: {det.confidence:.2f}"
            (label_w, label_h), baseline = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1
            )
            cv2.rectangle(
                result,
                (x, y - label_h - 10),
                (x + label_w + 10, y),
                color,
                -1
            )
            
            # Draw label text
            cv2.putText(
                result,
                label,
                (x + 5, y - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 0, 0),
                1
            )
        
        return result
    
    def get_animation_for_detection(
        self,
        detection: Detection
    ) -> Optional[AnimationType]:
        """
        Get the animation type for a detection based on mappings.
        
        Args:
            detection: Detection to check
            
        Returns:
            AnimationType if confidence > threshold and mapping exists
        """
        if detection.confidence < self.confidence_threshold:
            return None
        
        class_name = detection.class_name.lower()
        
        if class_name in self.animation_mappings:
            return self.animation_mappings[class_name]
        
        # Default mappings for common props
        default_mappings = {
            "heart": AnimationType.LOVE,
            "star": AnimationType.RAINBOW,
            "hat": AnimationType.WINK,
            "glasses": AnimationType.SUS,
            "mascot": AnimationType.WELCOME,
        }
        
        for key, animation in default_mappings.items():
            if key in class_name:
                return animation
        
        return AnimationType.CUSTOM
    
    def get_triggered_animations(
        self,
        detections: List[Detection]
    ) -> List[Tuple[Detection, AnimationType]]:
        """
        Get all animations that should be triggered from detections.
        
        Args:
            detections: List of detections to check
            
        Returns:
            List of (detection, animation) tuples for high-confidence detections
        """
        triggered = []
        
        for det in detections:
            if det.confidence >= self.confidence_threshold:
                animation = self.get_animation_for_detection(det)
                if animation:
                    triggered.append((det, animation))
        
        return triggered
