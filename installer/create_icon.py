"""Create a simple icon for Aether installer."""

from PIL import Image, ImageDraw
import sys

def create_icon(size=256):
    """Create a blue circle with 'A' for Aether."""
    # Create image with transparent background
    image = Image.new('RGBA', (size, size), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    # Draw blue circle
    padding = 10
    draw.ellipse(
        [padding, padding, size - padding, size - padding],
        fill=(25, 118, 210, 255)
    )
    
    # Draw 'A' in white
    text_color = (255, 255, 255, 255)
    margin = size // 4
    line_width = max(3, size // 32)
    
    # Left line of A
    draw.line([margin, size - margin, size // 2, margin], fill=text_color, width=line_width)
    # Right line of A
    draw.line([size // 2, margin, size - margin, size - margin], fill=text_color, width=line_width)
    # Crossbar
    crossbar_y = size - size // 3
    draw.line([margin + size//16, crossbar_y, size - margin - size//16, crossbar_y], fill=text_color, width=line_width)
    
    return image

if __name__ == "__main__":
    # Create icon
    icon = create_icon(256)
    
    # Save as PNG (can be converted to .ico with other tools)
    icon.save("aether_icon.png")
    print("Icon saved as aether_icon.png")
    print("Convert to .ico using an online tool or image editor for the installer")
