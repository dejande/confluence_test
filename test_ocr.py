#!/usr/bin/env python3

import sys
from PIL import Image
import pytesseract

def test_ocr_setup():
    """Test if OCR is properly set up"""
    try:
        # Test basic OCR functionality
        print("Testing OCR setup...")
        
        # Create a simple test image with text
        from PIL import Image, ImageDraw, ImageFont
        
        # Create a white image
        img = Image.new('RGB', (400, 100), color='white')
        draw = ImageDraw.Draw(img)
        
        # Draw some text
        try:
            # Try to use a default font
            font = ImageFont.load_default()
        except:
            font = None
            
        draw.text((10, 10), "Test Table", fill='black', font=font)
        draw.text((10, 30), "Column1  Column2  Column3", fill='black', font=font)
        draw.text((10, 50), "Value1   Value2   Value3", fill='black', font=font)
        
        # Save test image
        img.save('test_image.png')
        print("Created test image: test_image.png")
        
        # Test OCR on the image
        text = pytesseract.image_to_string(img)
        print(f"OCR Result: '{text.strip()}'")
        
        if text.strip():
            print("✓ OCR is working correctly!")
            return True
        else:
            print("✗ OCR returned empty result")
            return False
            
    except Exception as e:
        print(f"✗ OCR setup failed: {e}")
        print("\nTo fix this:")
        print("1. Install tesseract: brew install tesseract (macOS) or apt-get install tesseract-ocr (Linux)")
        print("2. Install Python package: pip install pytesseract")
        return False

if __name__ == '__main__':
    test_ocr_setup()