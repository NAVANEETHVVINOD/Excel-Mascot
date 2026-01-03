"""
Image Filters Module - Enhanced Cinematic Quality

Provides professional photo filters for the Mascot Photo Booth.
Filters: NOIR, RETRO, GLITCH, NEON, DREAMY, BW
"""

import cv2
import numpy as np
from enum import Enum
from typing import Optional


class FilterType(Enum):
    """Available filter types."""
    NONE = "none"
    GLITCH = "glitch"      # RGB channel shifting, scan lines, chromatic aberration
    NEON = "neon"          # Cyan + Magenta pops, cyberpunk vibe
    DREAMY = "dreamy"      # Pastel tones, soft glow, film-like
    RETRO = "retro"        # Warm polaroid, sepia tint, matte blacks
    NOIR = "noir"          # Deep B&W, high contrast, vignette, film grain
    BW = "bw"              # Clean grayscale, timeless look


def enhance_sharpness(image: np.ndarray, strength: float = 1.0) -> np.ndarray:
    """
    Enhance image sharpness for 720p webcam quality improvement.
    
    Args:
        image: BGR image
        strength: Sharpening strength (0.5-2.0)
    
    Returns:
        Sharpened image
    """
    # Unsharp mask technique for natural sharpening
    gaussian = cv2.GaussianBlur(image, (0, 0), 3)
    sharpened = cv2.addWeighted(image, 1.0 + strength, gaussian, -strength, 0)
    return sharpened


def denoise_image(image: np.ndarray, strength: int = 5) -> np.ndarray:
    """
    Apply fast denoising for cleaner photos.
    
    Args:
        image: BGR image
        strength: Denoising strength (3-10)
    
    Returns:
        Denoised image
    """
    # Fast bilateral filter for edge-preserving smoothing
    return cv2.bilateralFilter(image, d=5, sigmaColor=strength*10, sigmaSpace=strength*10)


def add_vignette(image: np.ndarray, strength: float = 0.5) -> np.ndarray:
    """
    Add subtle vignette effect (darkened corners).
    
    Args:
        image: BGR image
        strength: Vignette intensity (0.3-1.0)
    
    Returns:
        Image with vignette
    """
    rows, cols = image.shape[:2]
    
    # Create radial gradient mask
    X = cv2.getGaussianKernel(cols, cols * 0.6)
    Y = cv2.getGaussianKernel(rows, rows * 0.6)
    kernel = Y * X.T
    
    # Normalize and adjust strength
    mask = kernel / kernel.max()
    mask = mask * (1 - strength) + strength
    
    # Apply to all channels
    result = image.copy().astype(np.float32)
    for i in range(3):
        result[:, :, i] = result[:, :, i] * mask
    
    return np.clip(result, 0, 255).astype(np.uint8)


def add_film_grain(image: np.ndarray, intensity: float = 0.15) -> np.ndarray:
    """
    Add subtle film grain texture.
    
    Args:
        image: BGR image
        intensity: Grain intensity (0.1-0.3)
    
    Returns:
        Image with film grain
    """
    rows, cols = image.shape[:2]
    
    # Generate noise
    noise = np.random.randn(rows, cols, 3) * 25 * intensity
    
    # Add noise to image
    grainy = image.astype(np.float32) + noise
    return np.clip(grainy, 0, 255).astype(np.uint8)


def apply_filter(image: np.ndarray, filter_type: FilterType, text: str = "EXCEL 2025") -> np.ndarray:
    """
    Apply the specified filter to an image with quality enhancement.
    
    Args:
        image: BGR image as numpy array
        filter_type: Type of filter to apply
        text: Text for retro/polaroid filter
        
    Returns:
        Filtered image as numpy array
    """
    # First, enhance base quality for 720p webcam
    enhanced = enhance_sharpness(image, strength=0.5)
    
    if filter_type == FilterType.NONE:
        # Even NONE filter gets basic enhancement
        return denoise_image(enhanced, strength=3)
    elif filter_type == FilterType.GLITCH:
        return apply_glitch(enhanced)
    elif filter_type == FilterType.NEON:
        return apply_neon(enhanced)
    elif filter_type == FilterType.DREAMY:
        return apply_dreamy(enhanced)
    elif filter_type == FilterType.RETRO:
        return apply_retro(enhanced, text)
    elif filter_type == FilterType.NOIR:
        return apply_noir(enhanced)
    elif filter_type == FilterType.BW:
        return apply_bw(enhanced)
    else:
        return enhanced


def apply_glitch(image: np.ndarray) -> np.ndarray:
    """
    GLITCH ARCHIVE MODE - RGB shift, scan lines, chromatic aberration.
    
    Look: RGB channel shift, digital scan lines, slight distortion
    Mood: Corrupted hardware archive, system decoding
    """
    result = image.copy()
    rows, cols = result.shape[:2]
    
    # Split channels
    b, g, r = cv2.split(result)
    
    # Chromatic aberration - shift red and blue channels
    shift_amount = max(8, cols // 80)  # Dynamic shift based on image size
    
    # Shift Blue left
    b_shifted = np.roll(b, -shift_amount, axis=1)
    b_shifted[:, -shift_amount:] = b[:, -shift_amount:]
    
    # Shift Red right  
    r_shifted = np.roll(r, shift_amount, axis=1)
    r_shifted[:, :shift_amount] = r[:, :shift_amount]
    
    # Merge shifted channels
    glitched = cv2.merge([b_shifted, g, r_shifted])
    
    # Add horizontal scan lines
    line_interval = 3
    for i in range(0, rows, line_interval):
        if i + 1 < rows:
            glitched[i, :] = (glitched[i, :].astype(np.float32) * 0.7).astype(np.uint8)
    
    # Add random horizontal band distortion (subtle)
    num_bands = 3
    for _ in range(num_bands):
        band_y = np.random.randint(0, rows - 20)
        band_height = np.random.randint(2, 8)
        shift = np.random.randint(-15, 15)
        
        band = glitched[band_y:band_y + band_height, :].copy()
        band = np.roll(band, shift, axis=1)
        glitched[band_y:band_y + band_height, :] = band
    
    # Slight contrast boost
    glitched = cv2.convertScaleAbs(glitched, alpha=1.1, beta=5)
    
    return glitched


def apply_neon(image: np.ndarray) -> np.ndarray:
    """
    NEON CYBERCORE - Cyan + Magenta pops, clean contrast, tech-festival vibe.
    
    Look: Cyan + Magenta color pops, clean contrast
    Mood: Modern cyberpunk, neon energy
    """
    result = image.copy()
    
    # Convert to LAB for better color manipulation
    lab = cv2.cvtColor(result, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    
    # Boost contrast in luminance
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    l = clahe.apply(l)
    
    # Boost color channels (a=green-magenta, b=blue-yellow)
    a = cv2.convertScaleAbs(a, alpha=1.2, beta=0)  # Push magenta
    b = cv2.convertScaleAbs(b, alpha=0.9, beta=-10)  # Push cyan/blue
    
    lab = cv2.merge([l, a, b])
    result = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    
    # Boost blue and red channels for neon glow
    bgr = cv2.split(result)
    bgr[0] = cv2.convertScaleAbs(bgr[0], alpha=1.15, beta=10)  # Blue boost
    bgr[2] = cv2.convertScaleAbs(bgr[2], alpha=1.1, beta=8)    # Red boost
    result = cv2.merge(bgr)
    
    # Add subtle bloom/glow
    blurred = cv2.GaussianBlur(result, (0, 0), 8)
    result = cv2.addWeighted(result, 0.85, blurred, 0.15, 0)
    
    # Sharpen edges
    result = enhance_sharpness(result, strength=0.3)
    
    return result


def apply_dreamy(image: np.ndarray) -> np.ndarray:
    """
    DREAMY SOFTLIGHT - Pastel tones, soft focus, gentle glow.
    
    Look: Pastel tone, soft focus, gentle glow
    Mood: Aesthetic, peaceful, film-like
    """
    result = image.copy()
    
    # Lift shadows - brighten dark areas
    lab = cv2.cvtColor(result, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    
    # Apply gamma correction to lift shadows
    l_float = l.astype(np.float32) / 255.0
    l_lifted = np.power(l_float, 0.85) * 255
    l = np.clip(l_lifted, 0, 255).astype(np.uint8)
    
    # Reduce saturation for pastel look
    a = cv2.convertScaleAbs(a, alpha=0.7, beta=30)  # Towards neutral
    b = cv2.convertScaleAbs(b, alpha=0.75, beta=20)  # Towards neutral
    
    lab = cv2.merge([l, a, b])
    result = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    
    # Add soft glow (bloom effect)
    blurred = cv2.GaussianBlur(result, (0, 0), 25)
    result = cv2.addWeighted(result, 0.55, blurred, 0.45, 0)
    
    # Warm up highlights slightly
    result = cv2.convertScaleAbs(result, alpha=1.05, beta=15)
    
    # Add very subtle vignette
    result = add_vignette(result, strength=0.2)
    
    return result


def apply_retro(image: np.ndarray, text: str = "EXCEL 2025") -> np.ndarray:
    """
    RETRO POLAROID - Warm cream tones, slight fading, nostalgic 90s feel.
    
    Look: Warm cream color tone, slight fading, soft highlights
    Mood: Old printed memory, nostalgic festival
    """
    result = image.copy()
    
    # Apply warm sepia-like tone
    # Create sepia transformation matrix
    sepia_filter = np.array([
        [0.272, 0.534, 0.131],
        [0.349, 0.686, 0.168],
        [0.393, 0.769, 0.189]
    ])
    
    # Apply sepia transform
    sepia = cv2.transform(result, sepia_filter)
    sepia = np.clip(sepia, 0, 255).astype(np.uint8)
    
    # Blend with original for less intense effect
    result = cv2.addWeighted(result, 0.35, sepia, 0.65, 0)
    
    # Matte blacks - lift shadows
    lab = cv2.cvtColor(result, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    
    # Lift blacks (matte look)
    l = np.clip(l.astype(np.float32) + 15, 0, 255).astype(np.uint8)
    
    lab = cv2.merge([l, a, b])
    result = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    
    # Add warm cast
    bgr = cv2.split(result)
    bgr[2] = cv2.convertScaleAbs(bgr[2], alpha=1.08, beta=8)   # Red warmth
    bgr[1] = cv2.convertScaleAbs(bgr[1], alpha=1.02, beta=3)   # Slight green
    bgr[0] = cv2.convertScaleAbs(bgr[0], alpha=0.95, beta=-5)  # Reduce blue
    result = cv2.merge(bgr)
    
    # Add subtle vignette
    result = add_vignette(result, strength=0.25)
    
    # Add polaroid frame
    row, col = result.shape[:2]
    bottom_border = int(row * 0.20)
    side_border = int(col * 0.04)
    
    # Cream white color for frame
    cream = [240, 248, 255]  # Slightly warm white
    
    polaroid = cv2.copyMakeBorder(
        result,
        side_border, bottom_border, side_border, side_border,
        cv2.BORDER_CONSTANT,
        value=cream
    )
    
    # Add text
    font = cv2.FONT_HERSHEY_SCRIPT_SIMPLEX
    font_scale = min(1.5, col / 400)
    thickness = 2
    text_color = (60, 60, 80)  # Dark warm gray
    
    text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
    text_x = (polaroid.shape[1] - text_size[0]) // 2
    text_y = polaroid.shape[0] - (bottom_border // 2) + (text_size[1] // 2)
    
    cv2.putText(polaroid, text, (text_x, text_y), font, font_scale, text_color, thickness)
    
    return polaroid


def apply_noir(image: np.ndarray) -> np.ndarray:
    """
    NOIR TERMINAL MONOCHROME - Deep B&W, high contrast, vignette, film grain.
    
    Look: Deep black + white, high contrast, subtle vignette, slight film grain
    Mood: Classified document, retro sci-fi detective, Blade Runner feed
    """
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Apply CLAHE for dramatic contrast
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    contrasted = clahe.apply(gray)
    
    # Additional contrast boost
    contrasted = cv2.convertScaleAbs(contrasted, alpha=1.25, beta=-10)
    
    # Convert back to BGR
    noir = cv2.cvtColor(contrasted, cv2.COLOR_GRAY2BGR)
    
    # Add vignette for dramatic effect
    noir = add_vignette(noir, strength=0.4)
    
    # Add subtle film grain
    noir = add_film_grain(noir, intensity=0.12)
    
    return noir


def apply_bw(image: np.ndarray) -> np.ndarray:
    """
    B&W CLASSIC - Clean grayscale, smooth tones, timeless documentary look.
    
    Look: Clean grayscale, no grain, smooth tones
    Mood: Timeless, documentary log
    """
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Gentle contrast enhancement
    clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    
    # Smooth out noise for clean look
    enhanced = cv2.bilateralFilter(enhanced, d=5, sigmaColor=40, sigmaSpace=40)
    
    # Convert back to BGR
    bw = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)
    
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
        "NORMAL": FilterType.NONE,
        "GLITCH": FilterType.GLITCH,
        "NEON": FilterType.NEON,
        "CYBERPUNK": FilterType.NEON,
        "DREAMY": FilterType.DREAMY,
        "PASTEL": FilterType.DREAMY,
        "RETRO": FilterType.RETRO,
        "POLAROID": FilterType.RETRO,
        "NOIR": FilterType.NOIR,
        "BW": FilterType.BW,
        "B&W": FilterType.BW,
    }
    
    return mapping.get(name_upper, FilterType.NONE)
