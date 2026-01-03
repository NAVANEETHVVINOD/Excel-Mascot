"""
Filter Test Script - Validates all filters work correctly
"""
import cv2
import numpy as np
import sys
import os

# Fix Windows encoding
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from filters import FilterType, apply_filter, get_filter_from_string

def test_all_filters():
    """Test all filters with a sample image."""
    print("=" * 50)
    print("FILTER TEST SUITE")
    print("=" * 50)
    
    # Create a test image (720p like the webcam)
    test_image = np.zeros((720, 1280, 3), dtype=np.uint8)
    
    # Add some color gradients and patterns for testing
    for i in range(720):
        test_image[i, :, 0] = int((i / 720) * 255)  # Blue gradient
        test_image[i, :, 1] = int(((720 - i) / 720) * 180)  # Green gradient
        test_image[i, :, 2] = 128  # Red constant
    
    # Add some rectangles for structure testing
    cv2.rectangle(test_image, (100, 100), (400, 300), (255, 200, 100), -1)
    cv2.rectangle(test_image, (500, 200), (800, 500), (100, 255, 150), -1)
    cv2.circle(test_image, (1000, 400), 150, (255, 255, 255), -1)
    
    # Test each filter
    filters_to_test = [
        ("NORMAL", FilterType.NONE),
        ("GLITCH", FilterType.GLITCH),
        ("NEON", FilterType.NEON),
        ("DREAMY", FilterType.DREAMY),
        ("RETRO", FilterType.RETRO),
        ("NOIR", FilterType.NOIR),
        ("BW", FilterType.BW),
    ]
    
    all_passed = True
    
    for name, filter_type in filters_to_test:
        try:
            print(f"\n[TEST] {name} filter...", end=" ")
            result = apply_filter(test_image.copy(), filter_type)
            
            # Validate result
            if result is None:
                print(f"FAILED - Returned None")
                all_passed = False
            elif not isinstance(result, np.ndarray):
                print(f"FAILED - Not a numpy array")
                all_passed = False
            elif len(result.shape) != 3:
                print(f"FAILED - Wrong dimensions: {result.shape}")
                all_passed = False
            elif result.dtype != np.uint8:
                print(f"FAILED - Wrong dtype: {result.dtype}")
                all_passed = False
            else:
                h, w = result.shape[:2]
                print(f"OK - Output: {result.shape}")
                        
        except Exception as e:
            print(f"FAILED - Exception: {e}")
            all_passed = False
            import traceback
            traceback.print_exc()
    
    # Test string to filter conversion
    print("\n" + "=" * 50)
    print("STRING CONVERSION TEST")
    print("=" * 50)
    
    string_tests = [
        ("NORMAL", FilterType.NONE),
        ("NONE", FilterType.NONE),
        ("GLITCH", FilterType.GLITCH),
        ("NEON", FilterType.NEON),
        ("DREAMY", FilterType.DREAMY),
        ("RETRO", FilterType.RETRO),
        ("NOIR", FilterType.NOIR),
        ("BW", FilterType.BW),
    ]
    
    for string_name, expected_type in string_tests:
        result = get_filter_from_string(string_name)
        status = "OK" if result == expected_type else "FAILED"
        print(f"[STRING] '{string_name}' -> {result.value} {status}")
        if result != expected_type:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("ALL TESTS PASSED!")
    else:
        print("SOME TESTS FAILED!")
    print("=" * 50)
    
    return all_passed

if __name__ == "__main__":
    success = test_all_filters()
    sys.exit(0 if success else 1)
