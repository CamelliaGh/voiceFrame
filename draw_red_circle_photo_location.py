#!/usr/bin/env python3
"""
Script to draw a red circle where the circle photo is located in the template.
This helps visualize the exact position and size of the photo area.
"""

import json
from PIL import Image, ImageDraw
from pathlib import Path

def draw_red_circle_on_template():
    """Draw a red circle on the template to show where the photo is positioned"""

    # Load template configuration
    template_path = Path("templates/framed/framed_a4_portrait.json")
    with open(template_path, 'r') as f:
        template_config = json.load(f)

    # Load template image
    template_image_path = Path("templates/framed/framed_template_a4_portrait.png")
    if not template_image_path.exists():
        print(f"Template image not found: {template_image_path}")
        return

    # Open the template image
    image = Image.open(template_image_path)
    print(f"Template image loaded: {image.size}")

    # Get photo placeholder coordinates
    photo_placeholder = template_config["placeholders"]["photo"]
    x = photo_placeholder["x"]
    y = photo_placeholder["y"]
    width = photo_placeholder["width"]
    height = photo_placeholder["height"]

    print(f"Photo placeholder: x={x}, y={y}, width={width}, height={height}")

    # Create a drawing context
    draw = ImageDraw.Draw(image)

    # Draw a red rectangle to show the photo area
    draw.rectangle([x, y, x + width, y + height], outline="red", width=5)

    # Draw a red circle in the center of the photo area
    center_x = x + width // 2
    center_y = y + height // 2
    radius = min(width, height) // 4  # Make circle 1/4 of the smaller dimension

    # Draw the circle outline
    draw.ellipse([center_x - radius, center_y - radius, center_x + radius, center_y + radius],
                 outline="red", width=8)

    # Add text label
    draw.text((x, y - 30), "PHOTO AREA", fill="red")
    draw.text((center_x - 50, center_y - 10), "CIRCLE", fill="red")

    # Save the result
    output_path = "template_with_red_circle.png"
    image.save(output_path)
    print(f"Template with red circle saved to: {output_path}")

    # Print coordinates for reference
    print(f"\nPhoto area coordinates:")
    print(f"  Top-left: ({x}, {y})")
    print(f"  Bottom-right: ({x + width}, {y + height})")
    print(f"  Center: ({center_x}, {center_y})")
    print(f"  Circle radius: {radius}")

if __name__ == "__main__":
    draw_red_circle_on_template()
