"""
Generate PWA App Icons for AquaAlert
Uses PIL to create simple gradient icons with the water drop symbol
"""
from PIL import Image, ImageDraw, ImageFont
import os
import math

# Icon sizes needed for PWA
ICON_SIZES = [16, 32, 72, 96, 120, 128, 144, 152, 180, 192, 384, 512]

# Colors (AquaAlert theme)
BG_COLOR_START = (11, 18, 32)  # #0b1220
BG_COLOR_END = (20, 35, 60)    # Slightly lighter
ACCENT_COLOR = (0, 212, 255)   # #00d4ff (cyan)
WHITE = (255, 255, 255)

def create_gradient_background(size):
    """Create a radial gradient background"""
    img = Image.new('RGBA', (size, size), BG_COLOR_START)
    draw = ImageDraw.Draw(img)
    
    center = size // 2
    for y in range(size):
        for x in range(size):
            # Radial gradient
            dist = math.sqrt((x - center)**2 + (y - center)**2)
            max_dist = math.sqrt(2) * center
            ratio = min(dist / max_dist, 1.0)
            
            r = int(BG_COLOR_START[0] * (1 - ratio * 0.3) + BG_COLOR_END[0] * ratio * 0.3)
            g = int(BG_COLOR_START[1] * (1 - ratio * 0.3) + BG_COLOR_END[1] * ratio * 0.3)
            b = int(BG_COLOR_START[2] * (1 - ratio * 0.3) + BG_COLOR_END[2] * ratio * 0.3)
            
            img.putpixel((x, y), (r, g, b, 255))
    
    return img

def draw_water_drop(draw, size, color):
    """Draw a stylized water drop icon"""
    padding = size * 0.15
    drop_width = size - (padding * 2)
    drop_height = size - (padding * 2)
    
    center_x = size // 2
    top_y = padding
    bottom_y = size - padding
    
    # Water drop shape using bezier approximation with polygon
    points = []
    steps = 50
    
    for i in range(steps + 1):
        t = i / steps
        
        if t < 0.5:
            # Top part (pointed)
            local_t = t * 2
            x = center_x
            y = top_y + (local_t * drop_height * 0.4)
            # Widen as we go down
            width_factor = local_t * 0.5
            points.append((x - drop_width * width_factor * 0.5, y))
        else:
            # Bottom part (rounded)
            local_t = (t - 0.5) * 2
            angle = math.pi * (1 - local_t)
            radius = drop_width * 0.5
            center_y = top_y + drop_height * 0.55
            x = center_x + math.cos(angle) * radius
            y = center_y + math.sin(angle) * radius * 0.8
            points.append((x, y))
    
    # Draw the drop outline
    if len(points) >= 3:
        draw.polygon(points, outline=color, fill=None)
        
        # Draw inner highlight
        scale = 0.85
        inner_points = []
        for px, py in points:
            ix = center_x + (px - center_x) * scale
            iy = top_y + drop_height * 0.1 + (py - top_y - drop_height * 0.1) * scale
            inner_points.append((ix, iy))
        
        if len(inner_points) >= 3:
            draw.polygon(inner_points, outline=None, fill=(*color, 30))

def draw_simple_drop(img, size):
    """Draw a simpler, cleaner water drop"""
    draw = ImageDraw.Draw(img, 'RGBA')
    
    # Calculate dimensions
    padding = size * 0.2
    center_x = size // 2
    center_y = size // 2
    
    # Drop dimensions
    drop_height = size * 0.6
    drop_width = size * 0.45
    
    # Top point of drop
    top_y = center_y - drop_height * 0.4
    
    # Draw the main drop shape
    line_width = max(2, int(size * 0.04))
    
    # Create drop path
    points = []
    
    # Top point
    points.append((center_x, top_y))
    
    # Right curve
    for i in range(20):
        t = i / 20
        x = center_x + (drop_width * 0.5) * math.sin(t * math.pi)
        y = top_y + drop_height * t
        points.append((x, y))
    
    # Bottom arc
    bottom_center_y = top_y + drop_height
    for i in range(20):
        angle = -math.pi/2 + (math.pi * i / 20)
        x = center_x + (drop_width * 0.5) * math.cos(angle)
        y = bottom_center_y + (drop_width * 0.3) * math.sin(angle)
        points.append((x, y))
    
    # Left curve (going up)
    for i in range(20, 0, -1):
        t = i / 20
        x = center_x - (drop_width * 0.5) * math.sin(t * math.pi)
        y = top_y + drop_height * t
        points.append((x, y))
    
    # Draw with glow effect
    glow_color = (*ACCENT_COLOR, 100)
    for offset in range(3, 0, -1):
        glow_points = [(p[0], p[1]) for p in points]
        draw.polygon(glow_points, outline=(*ACCENT_COLOR, 50 * offset))
    
    # Main outline
    draw.polygon(points, outline=ACCENT_COLOR, fill=(*ACCENT_COLOR, 20))
    
    # Inner highlight (small arc at bottom)
    highlight_y = bottom_center_y - drop_width * 0.1
    highlight_points = []
    for i in range(15):
        angle = math.pi + (math.pi * 0.6) * (i / 15 - 0.5)
        x = center_x + (drop_width * 0.25) * math.cos(angle)
        y = highlight_y + (drop_width * 0.15) * math.sin(angle)
        highlight_points.append((x, y))
    
    if len(highlight_points) >= 2:
        draw.line(highlight_points, fill=(*ACCENT_COLOR, 180), width=max(1, line_width // 2))
    
    return img

def create_icon(size):
    """Create an icon of the specified size"""
    # Create gradient background
    img = create_gradient_background(size)
    
    # Draw water drop
    img = draw_simple_drop(img, size)
    
    return img

def main():
    # Create icons directory
    icons_dir = os.path.join(os.path.dirname(__file__), 'backend', 'static', 'icons')
    os.makedirs(icons_dir, exist_ok=True)
    
    print("Generating AquaAlert PWA icons...")
    
    for size in ICON_SIZES:
        icon = create_icon(size)
        filename = f"icon-{size}x{size}.png"
        filepath = os.path.join(icons_dir, filename)
        icon.save(filepath, 'PNG')
        print(f"  Created: {filename}")
    
    # Create screenshot placeholders (simple colored rectangles)
    # Wide screenshot (1280x720)
    wide = Image.new('RGB', (1280, 720), BG_COLOR_START)
    wide_draw = ImageDraw.Draw(wide)
    wide_draw.rectangle([100, 100, 1180, 620], outline=ACCENT_COLOR, width=2)
    wide_draw.text((540, 350), "AquaAlert", fill=WHITE)
    wide.save(os.path.join(icons_dir, 'screenshot-wide.png'), 'PNG')
    print("  Created: screenshot-wide.png")
    
    # Narrow screenshot (720x1280)
    narrow = Image.new('RGB', (720, 1280), BG_COLOR_START)
    narrow_draw = ImageDraw.Draw(narrow)
    narrow_draw.rectangle([50, 100, 670, 1180], outline=ACCENT_COLOR, width=2)
    narrow_draw.text((280, 640), "AquaAlert", fill=WHITE)
    narrow.save(os.path.join(icons_dir, 'screenshot-narrow.png'), 'PNG')
    print("  Created: screenshot-narrow.png")
    
    print("\nAll icons generated successfully!")
    print(f"Icons saved to: {icons_dir}")

if __name__ == '__main__':
    main()
