"""
Image Filters Module

Provides various photo filters for the Mascot Photo Booth.
"""

import cv2
import numpy as np
from enum import Enum
from typing import Optional


class FilterType(Enum):
    """Available filter types."""
    NONE = "none"
    CARTOON = "cartoon"
    VINTAGE = "vintage"
    BW = "bw"
    POLAROID = "polaroid"
    GLITCH = "glitch"
    CYBERPUNK = "cyberpunk"
    PASTEL = "pastel"


def apply_filter(image: np.ndarray, filter_type: FilterType, text: str = "Mascot 2025") -> np.ndarray:
    """
    Apply the specified filter to an image.
    """
    if filter_type == FilterType.NONE:
        return image.copy()
    elif filter_type == FilterType.CARTOON:
        return apply_cartoon(image)
    elif filter_type == FilterType.VINTAGE:
        return apply_vintage(image)
    elif filter_type == FilterType.BW:
        return apply_bw(image)
    elif filter_type == FilterType.POLAROID:
        return apply_polaroid(image, text)
    elif filter_type == FilterType.GLITCH:
        return apply_glitch(image)
    elif filter_type == FilterType.CYBERPUNK:
        return apply_cyberpunk(image)
    elif filter_type == FilterType.PASTEL:
        return apply_pastel(image)
    else:
        return image.copy()

# ... (Existing implementations: apply_cartoon, apply_vintage, apply_bw, apply_polaroid) ...

def apply_glitch(image: np.ndarray) -> np.ndarray:
    """Simulate RGB shift glitch."""
    shift = 15
    rows, cols, _ = image.shape
    
    b, g, r = cv2.split(image)
    
    # Shift Blue left
    b_shifted = np.roll(b, -shift, axis=1)
    # b_shifted[:, -shift:] = 0 # Optional black bar
    
    # Shift Red right
    r_shifted = np.roll(r, shift, axis=1)
    # r_shifted[:, :shift] = 0
    
    return cv2.merge([b_shifted, g, r_shifted])

def apply_cyberpunk(image: np.ndarray) -> np.ndarray:
    """High contrast, cool tint."""
    # Simple color grading: boost blue/red
    b, g, r = cv2.split(image)
    b = cv2.convertScaleAbs(b, alpha=1.1, beta=10) # More Blue
    g = cv2.convertScaleAbs(g, alpha=0.9, beta=0) 
    r = cv2.convertScaleAbs(r, alpha=1.2, beta=10) # More Red -> Purple
    
    merged = cv2.merge([b, g, r])
    # Increase contrast
    return cv2.convertScaleAbs(merged, alpha=1.2, beta=10)

def apply_pastel(image: np.ndarray) -> np.ndarray:
    """Soft, bright, low saturation."""
    # Increase brightness
    bright = cv2.convertScaleAbs(image, alpha=1.1, beta=40)
    
    # Reduce saturation
    hsv = cv2.cvtColor(bright, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)
    s = cv2.multiply(s, 0.6).astype(np.uint8)
    
    final_hsv = cv2.merge([h, s, v])
    return cv2.cvtColor(final_hsv, cv2.COLOR_HSV2BGR)


def get_filter_from_string(filter_name: str) -> FilterType:
    """
    Convert string filter name to FilterType enum.
    """
    name_upper = filter_name.upper()
    
    mapping = {
        "NONE": FilterType.NONE,
        "CARTOON": FilterType.CARTOON,
        "VINTAGE": FilterType.VINTAGE,
        "BW": FilterType.BW,
        "POLAROID": FilterType.POLAROID,
        "GLITCH": FilterType.GLITCH,
        "CYBERPUNK": FilterType.CYBERPUNK,
        "PASTEL": FilterType.PASTEL,
    }
    
    return mapping.get(name_upper, FilterType.NONE)


def apply_filter(image: np.ndarray, filter_type: FilterType, text: str = "Mascot 2025") -> np.ndarray:
    """
    Apply the specified filter to an image.
    
    Args:
        image: BGR image as numpy array
        filter_type: Type of filter to apply
        text: Text for polaroid filter
        
    Returns:
        Filtered image as numpy array
    """
    if filter_type == FilterType.NONE:
        return image.copy()
    elif filter_type == FilterType.CARTOON:
        return apply_cartoon(image)
    elif filter_type == FilterType.VINTAGE:
        return apply_vintage(image)
    elif filter_type == FilterType.BW:
        return apply_bw(image)
    elif filter_type == FilterType.POLAROID:
        return apply_polaroid(image, text)
    else:
        return image.copy()


def apply_cartoon(image: np.ndarray) -> np.ndarray:
    """
    Apply cartoon effect using edge detection and color quantization.
    
    Args:
        image: BGR image as numpy array
        
    Returns:
        Cartoonized image
    """
    # Edge detection
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 5)
    edges = cv2.adaptiveThreshold(
        gray, 255, 
        cv2.ADAPTIVE_THRESH_MEAN_C, 
        cv2.THRESH_BINARY, 9, 9
    )
    
    # Color smoothing
    color = cv2.bilateralFilter(image, 9, 75, 75)
    
    # Combine edges with color
    cartoon = cv2.bitwise_and(color, color, mask=edges)
    return cartoon


def apply_vintage(image: np.ndarray) -> np.ndarray:
    """
    Apply vintage/sepia effect with noise grain.
    
    Args:
        image: BGR image as numpy array
        
    Returns:
        Vintage-styled image
    """
    # Sepia transformation matrix
    kernel = np.array([
        [0.272, 0.534, 0.131],
        [0.349, 0.686, 0.168],
        [0.393, 0.769, 0.189]
    ])
    
    sepia = cv2.transform(image, kernel)
    sepia = np.clip(sepia, 0, 255).astype(np.uint8)
    
    # Add film grain noise
    noise = np.random.normal(0, 15, sepia.shape).astype(np.int16)
    vintage = np.clip(sepia.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    
    return vintage


def apply_bw(image: np.ndarray) -> np.ndarray:
    """
    Convert image to black and white (grayscale).
    
    Args:
        image: BGR image as numpy array
        
    Returns:
        Grayscale image in BGR format (all channels equal)
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Convert back to BGR so all channels are equal
    bw = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    return bw


def apply_polaroid(image: np.ndarray, text: str = "Mascot 2025") -> np.ndarray:
    """
    Apply polaroid frame effect with white border and text.
    
    Args:
        image: BGR image as numpy array
        text: Text to display at bottom of frame
        
    Returns:
        Image with polaroid frame (larger dimensions)
    """
    row, col = image.shape[:2]
    
    # Calculate border sizes
    bottom = int(row * 0.25)  # 25% of height for bottom
    border = int(col * 0.05)  # 5% for sides and top
    
    # White color
    white = [255, 255, 255]
    
    # Add white border
    polaroid = cv2.copyMakeBorder(
        image, 
        border, bottom, border, border, 
        cv2.BORDER_CONSTANT, 
        value=white
    )
    
    # Add text
    font = cv2.FONT_HERSHEY_SCRIPT_SIMPLEX
    font_scale = 1.5
    thickness = 2
    text_color = (50, 50, 50)
    
    # Calculate centered text position
    text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
    text_x = (polaroid.shape[1] - text_size[0]) // 2
    text_y = polaroid.shape[0] - (bottom // 2) + (text_size[1] // 2)
    
    cv2.putText(
        polaroid, text, (text_x, text_y), 
        font, font_scale, text_color, thickness
    )
    
    return polaroid


def apply_glitch(image: np.ndarray) -> np.ndarray:
    """Simulate RGB shift glitch."""
    shift = 15
    rows, cols, _ = image.shape
    
    b, g, r = cv2.split(image)
    
    # Shift Blue left
    b_shifted = np.roll(b, -shift, axis=1)
    # b_shifted[:, -shift:] = 0 # Optional black bar
    
    # Shift Red right
    r_shifted = np.roll(r, shift, axis=1)
    # r_shifted[:, :shift] = 0
    
    return cv2.merge([b_shifted, g, r_shifted])

def apply_cyberpunk(image: np.ndarray) -> np.ndarray:
    """High contrast, cool tint."""
    # Simple color grading: boost blue/red
    b, g, r = cv2.split(image)
    b = cv2.convertScaleAbs(b, alpha=1.1, beta=10) # More Blue
    g = cv2.convertScaleAbs(g, alpha=0.9, beta=0) 
    r = cv2.convertScaleAbs(r, alpha=1.2, beta=10) # More Red -> Purple
    
    merged = cv2.merge([b, g, r])
    # Increase contrast
    return cv2.convertScaleAbs(merged, alpha=1.2, beta=10)

def apply_pastel(image: np.ndarray) -> np.ndarray:
    """Soft, bright, low saturation."""
    # Increase brightness
    bright = cv2.convertScaleAbs(image, alpha=1.1, beta=40)
    
    # Reduce saturation
    hsv = cv2.cvtColor(bright, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)
    s = cv2.multiply(s, 0.6).astype(np.uint8)
    
    final_hsv = cv2.merge([h, s, v])
    return cv2.cvtColor(final_hsv, cv2.COLOR_HSV2BGR)


def get_filter_from_string(filter_name: str) -> FilterType:
    """
    Convert string filter name to FilterType enum.
    
    Args:
        filter_name: String name of filter (case-insensitive)
        
    Returns:
        Corresponding FilterType enum value
    """
    name_upper = filter_name.upper()
    
    mapping = {
        "NONE": FilterType.NONE,
        "CARTOON": FilterType.CARTOON,
        "VINTAGE": FilterType.VINTAGE,
        "BW": FilterType.BW,
        "POLAROID": FilterType.POLAROID,
    }
    
    return mapping.get(name_upper, FilterType.NONE)
