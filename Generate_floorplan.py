#!/usr/bin/env python3
"""
Garage Layout Planner - Visual Floor Plan Generator
Creates a scaled PNG floor plan from the layout recommendation
"""

import json
import re
from PIL import Image, ImageDraw, ImageFont
import os

# =============================================================================
# CONFIGURATION
# =============================================================================

# Image settings
SCALE = 4  # pixels per inch (so 25' = 1200 pixels)
MARGIN = 100  # pixels around the floor plan
TITLE_HEIGHT = 120

# Colors (RGB)
COLORS = {
    'background': (248, 248, 248),
    'floor': (240, 235, 230),
    'walls': (60, 60, 60),
    'vehicle': (100, 149, 237),  # Cornflower blue
    'workbench': (205, 133, 63),  # Peru/wood
    'wall_storage': (144, 238, 144),  # Light green
    'overhead': (255, 218, 185),  # Peach puff
    'door': (139, 69, 19),  # Saddle brown
    'window': (135, 206, 250),  # Light sky blue
    'electrical': (255, 215, 0),  # Gold
    'text': (40, 40, 40),
    'dimension': (100, 100, 100),
    'grid': (220, 220, 220),
}

# =============================================================================
# MEASUREMENT PARSING
# =============================================================================

def measurement_to_inches(measurement: str) -> float:
    """Convert measurement string to inches"""
    if not measurement or measurement == "N/A":
        return 0
    
    total = 0.0
    
    # Feet
    feet_match = re.search(r"(\d+(?:\.\d+)?)'", measurement)
    if feet_match:
        total += float(feet_match.group(1)) * 12
    
    # Inches
    inches_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:(\d+)/(\d+))?\s*"', measurement)
    if inches_match:
        inches = float(inches_match.group(1))
        if inches_match.group(2) and inches_match.group(3):
            inches += float(inches_match.group(2)) / float(inches_match.group(3))
        total += inches
    
    # Plain number
    if not feet_match and not inches_match:
        plain = re.match(r"^(\d+(?:\.\d+)?)$", measurement.strip())
        if plain:
            total = float(plain.group(1))
    
    return total


def inches_to_display(inches: float) -> str:
    """Convert inches to readable format"""
    feet = int(inches // 12)
    remaining = inches % 12
    if remaining == 0:
        return f"{feet}'"
    elif feet == 0:
        return f'{remaining:.0f}"'
    else:
        return f"{feet}'{remaining:.0f}\""


# =============================================================================
# LOAD DATA
# =============================================================================

def load_recommendation(filepath: str = "garage_recommendation.txt") -> dict:
    """Parse the recommendation text file"""
    data = {
        'garage_width': 300,  # Default 25'
        'garage_depth': 300,
        'ceiling_height': 120,
        'zones': [],
        'constraints': []
    }
    
    try:
        with open(filepath, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Warning: {filepath} not found")
        return data
    
    # Parse garage dimensions
    dim_match = re.search(r"Garage:\s*(\d+)'?\s*x\s*(\d+)'?", content)
    if dim_match:
        data['garage_width'] = int(dim_match.group(1)) * 12
        data['garage_depth'] = int(dim_match.group(2)) * 12
    
    ceiling_match = re.search(r"Ceiling height:\s*(.+)", content)
    if ceiling_match:
        data['ceiling_height'] = measurement_to_inches(ceiling_match.group(1))
    
    # Parse zones
    zones_section = re.search(r"ZONES PLACED\s*-+\s*(.*?)(?=REASONING|$)", content, re.DOTALL)
    if zones_section:
        zone_text = zones_section.group(1)
        
        # Split into individual zones
        zone_blocks = re.split(r'\n  (?=[A-Z0-9])', zone_text)
        
        for block in zone_blocks:
            if not block.strip():
                continue
            
            zone = {}
            
            # Get zone name (first line)
            lines = block.strip().split('\n')
            zone['name'] = lines[0].strip()
            
            # Determine type from name
            name_lower = zone['name'].lower()
            if 'workbench' in name_lower:
                zone['type'] = 'workbench'
            elif 'overhead' in name_lower:
                zone['type'] = 'overhead'
            elif 'wall storage' in name_lower:
                zone['type'] = 'wall_storage'
            elif any(car in name_lower for car in ['honda', 'toyota', 'ford', 'chevy', 'nissan', 'hyundai', 'kia', 'bmw', 'tesla']):
                zone['type'] = 'vehicle'
            else:
                zone['type'] = 'other'
            
            # Parse position
            pos_match = re.search(r"Position:\s*(.+?)\s*from W,\s*(.+?)\s*from N", block)
            if pos_match:
                zone['x'] = measurement_to_inches(pos_match.group(1))
                zone['y'] = measurement_to_inches(pos_match.group(2))
            
            # Parse size
            size_match = re.search(r"Size:\s*(.+?)\s*x\s*(.+?)(?:\n|$)", block)
            if size_match:
                zone['width'] = measurement_to_inches(size_match.group(1))
                zone['height'] = measurement_to_inches(size_match.group(2))
            
            # Parse wall
            wall_match = re.search(r"Wall:\s*(\w+)", block)
            if wall_match:
                zone['wall'] = wall_match.group(1)
            
            if 'x' in zone and 'width' in zone:
                data['zones'].append(zone)
    
    # Parse constraints
    constraints_section = re.search(r"CONSTRAINTS CONSIDERED\s*-+\s*(.*?)(?=NEXT STEPS|$)", content, re.DOTALL)
    if constraints_section:
        for line in constraints_section.group(1).split('\n'):
            if '*' in line:
                # Parse constraint line
                constraint = {}
                
                if 'door' in line.lower():
                    constraint['type'] = 'door'
                elif 'panel' in line.lower() or 'electrical' in line.lower():
                    constraint['type'] = 'electrical'
                elif 'window' in line.lower():
                    constraint['type'] = 'window'
                else:
                    continue
                
                # Extract position
                pos_match = re.search(r"(\d+)'?\s*(\d+)?\"?\s*from left", line)
                if pos_match:
                    feet = int(pos_match.group(1)) if pos_match.group(1) else 0
                    inches = int(pos_match.group(2)) if pos_match.group(2) else 0
                    constraint['position'] = feet * 12 + inches
                
                # Extract width
                width_match = re.search(r"(\d+)'?\s*(\d+)?\"?\s*wide", line)
                if width_match:
                    feet = int(width_match.group(1)) if width_match.group(1) else 0
                    inches = int(width_match.group(2)) if width_match.group(2) else 0
                    constraint['width'] = feet * 12 + inches
                
                if 'position' in constraint:
                    data['constraints'].append(constraint)
    
    return data


# =============================================================================
# DRAWING FUNCTIONS
# =============================================================================

def draw_floor_plan(data: dict, output_path: str = "garage_floorplan.png"):
    """Generate the floor plan image"""
    
    garage_w = data['garage_width']
    garage_h = data['garage_depth']
    
    # Calculate image size
    img_width = int(garage_w * SCALE) + MARGIN * 2
    img_height = int(garage_h * SCALE) + MARGIN * 2 + TITLE_HEIGHT
    
    # Create image
    img = Image.new('RGB', (img_width, img_height), COLORS['background'])
    draw = ImageDraw.Draw(img)
    
    # Try to load fonts
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
        label_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
        small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        dim_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
    except:
        title_font = ImageFont.load_default()
        label_font = title_font
        small_font = title_font
        dim_font = title_font
    
    # Offsets for floor area
    floor_x = MARGIN
    floor_y = MARGIN + TITLE_HEIGHT
    
    # Draw title
    title = "GARAGE FLOOR PLAN"
    draw.text((img_width // 2, 40), title, font=title_font, fill=COLORS['text'], anchor='mt')
    
    subtitle = f"{inches_to_display(garage_w)} x {inches_to_display(garage_h)} • Ceiling: {inches_to_display(data['ceiling_height'])}"
    draw.text((img_width // 2, 80), subtitle, font=label_font, fill=COLORS['dimension'], anchor='mt')
    
    # Draw floor
    floor_rect = [floor_x, floor_y, floor_x + garage_w * SCALE, floor_y + garage_h * SCALE]
    draw.rectangle(floor_rect, fill=COLORS['floor'])
    
    # Draw grid (every 2 feet)
    grid_spacing = 24 * SCALE  # 2 feet
    for x in range(floor_x, floor_x + int(garage_w * SCALE), grid_spacing):
        draw.line([(x, floor_y), (x, floor_y + garage_h * SCALE)], fill=COLORS['grid'], width=1)
    for y in range(floor_y, floor_y + int(garage_h * SCALE), grid_spacing):
        draw.line([(floor_x, y), (floor_x + garage_w * SCALE, y)], fill=COLORS['grid'], width=1)
    
    # Draw zones (non-overhead first, then overhead with transparency)
    for zone in data['zones']:
        if zone.get('type') == 'overhead':
            continue  # Draw these later
        
        x = floor_x + zone['x'] * SCALE
        y = floor_y + zone['y'] * SCALE
        w = zone['width'] * SCALE
        h = zone['height'] * SCALE
        
        # Get color
        color = COLORS.get(zone.get('type', 'other'), (200, 200, 200))
        
        # Draw filled rectangle
        draw.rectangle([x, y, x + w, y + h], fill=color, outline=COLORS['walls'], width=2)
        
        # Add label
        label = zone['name']
        if zone.get('type') == 'wall_storage':
            # Shorter label for storage
            num_match = re.search(r'\d+', zone['name'])
            label = f"S{num_match.group()}" if num_match else "S"
        elif zone.get('type') == 'vehicle':
            # Just show make/model
            parts = zone['name'].split()
            if len(parts) >= 3:
                label = f"{parts[1]} {parts[2]}"
        
        # Center label in zone
        cx = x + w / 2
        cy = y + h / 2
        
        font_to_use = small_font if zone.get('type') == 'wall_storage' else label_font
        draw.text((cx, cy), label, font=font_to_use, fill=COLORS['text'], anchor='mm')
    
    # Draw overhead zones with hatching pattern
    for zone in data['zones']:
        if zone.get('type') != 'overhead':
            continue
        
        x = floor_x + zone['x'] * SCALE
        y = floor_y + zone['y'] * SCALE
        w = zone['width'] * SCALE
        h = zone['height'] * SCALE
        
        # Draw dashed outline
        draw.rectangle([x, y, x + w, y + h], outline=COLORS['overhead'], width=3)
        
        # Draw diagonal hatching
        spacing = 20
        for i in range(-int(h), int(w), spacing):
            x1 = x + max(0, i)
            y1 = y + max(0, -i)
            x2 = x + min(w, i + h)
            y2 = y + min(h, h - i)
            if x1 < x + w and y1 < y + h:
                draw.line([(x1, y1), (x2, y2)], fill=COLORS['overhead'], width=1)
        
        # Label
        cx = x + w / 2
        cy = y + h / 2
        draw.text((cx, cy), "OVERHEAD", font=small_font, fill=(180, 140, 100), anchor='mm')
    
    # Draw walls (thick border)
    wall_thickness = 4
    draw.rectangle(floor_rect, outline=COLORS['walls'], width=wall_thickness)
    
    # Draw wall labels
    draw.text((floor_x + garage_w * SCALE / 2, floor_y - 30), "NORTH", 
              font=label_font, fill=COLORS['text'], anchor='mm')
    draw.text((floor_x + garage_w * SCALE / 2, floor_y + garage_h * SCALE + 30), "SOUTH (Garage Door)", 
              font=label_font, fill=COLORS['text'], anchor='mm')
    draw.text((floor_x - 30, floor_y + garage_h * SCALE / 2), "WEST", 
              font=label_font, fill=COLORS['text'], anchor='mm', angle=90)
    draw.text((floor_x + garage_w * SCALE + 30, floor_y + garage_h * SCALE / 2), "EAST", 
              font=label_font, fill=COLORS['text'], anchor='mm', angle=90)
    
    # Draw dimension lines
    dim_offset = 50
    
    # Width dimension (top)
    y_dim = floor_y - dim_offset
    draw.line([(floor_x, y_dim), (floor_x + garage_w * SCALE, y_dim)], fill=COLORS['dimension'], width=2)
    draw.line([(floor_x, y_dim - 10), (floor_x, y_dim + 10)], fill=COLORS['dimension'], width=2)
    draw.line([(floor_x + garage_w * SCALE, y_dim - 10), (floor_x + garage_w * SCALE, y_dim + 10)], fill=COLORS['dimension'], width=2)
    draw.text((floor_x + garage_w * SCALE / 2, y_dim - 15), inches_to_display(garage_w), 
              font=dim_font, fill=COLORS['dimension'], anchor='mm')
    
    # Height dimension (right)
    x_dim = floor_x + garage_w * SCALE + dim_offset
    draw.line([(x_dim, floor_y), (x_dim, floor_y + garage_h * SCALE)], fill=COLORS['dimension'], width=2)
    draw.line([(x_dim - 10, floor_y), (x_dim + 10, floor_y)], fill=COLORS['dimension'], width=2)
    draw.line([(x_dim - 10, floor_y + garage_h * SCALE), (x_dim + 10, floor_y + garage_h * SCALE)], fill=COLORS['dimension'], width=2)
    
    # Draw legend
    legend_y = floor_y + garage_h * SCALE + 60
    legend_items = [
        ('vehicle', 'Vehicle'),
        ('workbench', 'Workbench'),
        ('wall_storage', 'Wall Storage'),
        ('overhead', 'Overhead Storage'),
    ]
    
    legend_x = floor_x
    for color_key, label in legend_items:
        # Color swatch
        draw.rectangle([legend_x, legend_y, legend_x + 25, legend_y + 20], 
                      fill=COLORS[color_key], outline=COLORS['walls'])
        # Label
        draw.text((legend_x + 35, legend_y + 10), label, font=small_font, fill=COLORS['text'], anchor='lm')
        legend_x += 150
    
    # Save image
    img.save(output_path, 'PNG', quality=95)
    print(f"Floor plan saved to: {output_path}")
    return output_path


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("Generating garage floor plan...")
    
    # Load data from recommendation
    data = load_recommendation("garage_recommendation.txt")
    
    print(f"  Garage: {inches_to_display(data['garage_width'])} x {inches_to_display(data['garage_depth'])}")
    print(f"  Zones found: {len(data['zones'])}")
    
    # Generate floor plan
    output_path = draw_floor_plan(data)
    
    print("\nDone!")
    return output_path


if __name__ == "__main__":
    main()
