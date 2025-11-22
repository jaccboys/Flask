from PIL import Image, ImageDraw, ImageFont
import os

# Create icons directory
ICONS_DIR = os.path.join("static", "images")
os.makedirs(ICONS_DIR, exist_ok=True)

# Icon sizes needed for PWA
SIZES = [72, 96, 128, 144, 152, 192, 384, 512]

def create_icon(size):
    # Create a purple gradient background
    img = Image.new('RGB', (size, size), color='#8a63ff')
    draw = ImageDraw.Draw(img)
    
    # Draw a simple vinyl record icon
    # Outer circle (record)
    margin = size // 8
    draw.ellipse([margin, margin, size-margin, size-margin], fill='#1a1a1a', outline='#8a63ff', width=max(2, size//50))
    
    # Inner circle (label)
    inner_margin = size // 3
    draw.ellipse([inner_margin, inner_margin, size-inner_margin, size-inner_margin], fill='#8a63ff')
    
    # Center hole
    center_margin = size // 2 - size // 12
    center_size = size // 6
    draw.ellipse([center_margin, center_margin, center_margin + center_size, center_margin + center_size], fill='#1a1a1a')
    
    # Save
    filename = f"icon-{size}x{size}.png"
    filepath = os.path.join(ICONS_DIR, filename)
    img.save(filepath, 'PNG')
    print(f"Created {filename}")

# Generate all icons
for size in SIZES:
    create_icon(size)

print("All icons generated successfully!")