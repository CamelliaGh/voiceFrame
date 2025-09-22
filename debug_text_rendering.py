#!/usr/bin/env python3
"""
Debug script to test text rendering on a template image
"""
import sys
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Add the backend directory to the path
sys.path.append(str(Path(__file__).parent / 'backend'))

def test_text_rendering():
    """Test text rendering on the framed template"""
    
    # Load the template image
    template_path = Path(__file__).parent / 'templates' / 'framed' / 'framed_template.png'
    if not template_path.exists():
        print(f"Template not found: {template_path}")
        return
    
    # Load template configuration
    config_path = Path(__file__).parent / 'templates' / 'framed' / 'framed_template.json'
    if not config_path.exists():
        print(f"Config not found: {config_path}")
        return
    
    import json
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    print(f"Template config: {config}")
    
    # Load the template image
    image = Image.open(template_path)
    print(f"Template image size: {image.size}")
    print(f"Template image mode: {image.mode}")
    
    # Get text placeholder
    text_placeholder = config['placeholders']['text']
    print(f"Text placeholder: {text_placeholder}")
    
    # Create drawing context
    draw = ImageDraw.Draw(image)
    
    # Try to load a font
    font_size = text_placeholder.get('font_size', 32)
    try:
        # Try to load a system font
        font = ImageFont.truetype("Arial", font_size)
        print(f"Loaded Arial font at size {font_size}")
    except:
        try:
            font = ImageFont.truetype("Helvetica", font_size)
            print(f"Loaded Helvetica font at size {font_size}")
        except:
            font = ImageFont.load_default()
            print(f"Using default font")
    
    # Test text
    test_text = "TEST TEXT - DEBUG"
    
    # Calculate position
    x = text_placeholder['x']
    y = text_placeholder['y']
    
    # Draw text in bright red for visibility
    draw.text((x, y), test_text, font=font, fill='#FF0000')
    print(f"Drew text '{test_text}' at position ({x}, {y}) in red")
    
    # Save the result
    output_path = Path(__file__).parent / 'debug_text_output.png'
    image.save(output_path)
    print(f"Saved debug image to: {output_path}")
    
    # Also try drawing at different positions to see if it's a positioning issue
    draw.text((100, 100), "TOP LEFT", font=font, fill='#00FF00')
    draw.text((image.width - 200, 100), "TOP RIGHT", font=font, fill='#0000FF')
    draw.text((100, image.height - 100), "BOTTOM LEFT", font=font, fill='#FFFF00')
    draw.text((image.width - 200, image.height - 100), "BOTTOM RIGHT", font=font, fill='#FF00FF')
    
    image.save(output_path)
    print(f"Added test text at corners and saved to: {output_path}")

if __name__ == "__main__":
    test_text_rendering()
