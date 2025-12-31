"""
Image Filters Module

Provides various photo filters for the Mascot Photo Booth.
Filters: GLITCH, NEON, DREAMY, RETRO, NOIR
"""

import cv2
import numpy as np
from enum import Enum
from typing import Optional


class FilterType(Enum):
    """Available filter types."""
    NONE = "none"
    GLITCH = "glitch"      # RGB channel shifting, scan lines
    NEON = "neon"          # High contrast, neon color enhancement (cyberpunk)
    DREAMY = "dreamy"      # Soft blur, pastel tones
    RETRO = "retro"        # Polaroid border with timestamp
    NOIR = "noir"          # High contrast black and white
    BW = "bw"              # Simple black and white (grayscale)


def apply_filter(image: np.ndarray, filter_type: FilterType, text: str = "EXCEL 2025") -> np.ndarray:
    """
    Apply the specified filter to an image.
    
    Args:
        image: BGR image as numpy array
        filter_type: Type of filter to apply
        text: Text for retro/polaroid filter
        
    Returns:
        Filtered image as numpy array
    """
    if filter_type == FilterType.NONE:
        return image.copy()
    elif filter_type == FilterType.GLITCH:
        return apply_glitch(image)
    elif filter_type == FilterType.NEON:
        return apply_neon(image)
    elif filter_type == FilterType.DREAMY:
        return apply_dreamy(image)
    elif filter_type == FilterType.RETRO:
        return apply_retro(image, text)
    elif filter_type == FilterType.NOIR:
        return apply_noir(image)
    elif filter_type == FilterType.BW:
        return apply_bw(image)
    else:
        return image.copy()


def apply_glitch(image: np.ndarray) -> np.ndarray:
    """
    Apply RGB shift glitch effect with scan lines.
    
    Args:
        image: BGR image as numpy array
        
    Returns:
        Glitched image
    """
    shift = 15
    rows, cols = image.shape[:2]
    
    b, g, r = cv2.split(image)
    
    # Shift Blue left
    b_shifted = np.roll(b, -shift, axis=1)
    
    # Shift Red right
    r_shifted = np.roll(r, shift, axis=1)
    
    glitched = cv2.merge([b_shifted, g, r_shifted])
    
    # Add scan lines
    for i in range(0, rows, 4):
        glitched[i:i+2, :] = (glitched[i:i+2, :] * 0.7).astype(np.uint8)
    
    return glitched


def apply_neon(image: np.ndarray) -> np.ndarray:
    """
    Apply neon/cyberpunk effect with high contrast and color boost.
    
    Args:
        image: BGR image as numpy array
        
    Returns:
        Neon-styled image
    """
    b, g, r = cv2.split(image)
    
    # Boost blue and red for neon look
    b = cv2.convertScaleAbs(b, alpha=1.2, beta=15)
    g = cv2.convertScaleAbs(g, alpha=0.85, beta=0)
    r = cv2.convertScaleAbs(r, alpha=1.3, beta=20)
    
    merged = cv2.merge([b, g, r])
    
    # Increase overall contrast
    neon = cv2.convertScaleAbs(merged, alpha=1.3, beta=15)
    
    return neon


def apply_dreamy(image: np.ndarray) -> np.ndarray:
    """
    Apply soft, dreamy pastel effect.
    
    Args:
        image: BGR image as numpy array
        
    Returns:
        Dreamy pastel image
    """
    # Increase brightness
    bright = cv2.convertScaleAbs(image, alpha=1.1, beta=50)
    
    # Apply soft blur
    blurred = cv2.GaussianBlur(bright, (15, 15), 0)
    
    # Blend original with blur for soft glow
    dreamy = cv2.addWeighted(bright, 0.6, blurred, 0.4, 0)
    
    # Reduce saturation for pastel look
    hsv = cv2.cvtColor(dreamy, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)
    s = (s * 0.6).astype(np.uint8)
    v = np.clip(v.astype(np.int16) + 20, 0, 255).astype(np.uint8)
    
    final_hsv = cv2.merge([h, s, v])
    return cv2.cvtColor(final_hsv, cv2.COLOR_HSV2BGR)


def apply_retro(image: np.ndarray, text: str = "EXCEL 2025") -> np.ndarray:
    """
    Apply retro polaroid frame effect with white border and text.
    
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


def apply_noir(image: np.ndarray) -> np.ndarray:
    """
    Apply high contrast black and white (noir) effect.
    
    Args:
        image: BGR image as numpy array
        
    Returns:
        High contrast grayscale image in BGR format
    """
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Increase contrast
    gray = cv2.convertScaleAbs(gray, alpha=1.3, beta=10)
    
    # Apply slight vignette effect
    rows, cols = gray.shape
    X = cv2.getGaussianKernel(cols, cols * 0.5)
    Y = cv2.getGaussianKernel(rows, rows * 0.5)
    kernel = Y * X.T
    mask = kernel / kernel.max()
    gray = (gray * mask).astype(np.uint8)
    
    # Convert back to BGR so all channels are equal
    noir = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    return noir


def apply_bw(image: np.ndarray) -> np.ndarray:
    """
    Apply simple black and white (grayscale) effect.
    
    Args:
        image: BGR image as numpy array
        
    Returns:
        Grayscale image in BGR format
    """
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Convert back to BGR so all channels are equal
    bw = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    return bw


def get_filter_from_string(filter_name: str) -> FilterType:
    """
    Convert string filter name to FilterType enum.
    
    Args:
        filter_name: String name of filter (case-insensitive)
        
    Returns:
        Corresponding FilterType enum value
    """
    if not filter_name:
        return FilterType.NONE
        
    name_upper = filter_name.upper()
    
    mapping = {
        "NONE": FilterType.NONE,
        "NORMAL": FilterType.NONE,  # Alias for NONE
        "GLITCH": FilterType.GLITCH,
        "NEON": FilterType.NEON,
        "CYBERPUNK": FilterType.NEON,  # Alias
        "DREAMY": FilterType.DREAMY,
        "PASTEL": FilterType.DREAMY,   # Alias
        "RETRO": FilterType.RETRO,
        "POLAROID": FilterType.RETRO,  # Alias
        "NOIR": FilterType.NOIR,
        "BW": FilterType.BW,           # Simple B&W
        "B&W": FilterType.BW,          # Alias
    }
    
    return mapping.get(name_upper, FilterType.NONE)
