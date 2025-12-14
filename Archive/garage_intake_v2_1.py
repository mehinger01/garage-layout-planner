#!/usr/bin/env python3
"""
Garage Layout Planner - Phase 1: Requirements Gathering
Version 2: Bug fixes, data validation, form import, and exit anytime
"""

import re
import sys
from dataclasses import dataclass, field
from typing import Optional, Tuple

@dataclass
class Feature:
    """A permanent/immovable feature in the garage"""
    name: str
    feature_type: str
    position_along_wall: str  # distance from left corner when facing wall
    width: str
    height: str
    notes: str = ""
    sill_height: str = ""     # for windows - height from floor to sill
    header_height: str = ""   # for windows/doors - height from floor to top

@dataclass 
class Wall:
    """One wall of the garage"""
    direction: str  # N, S, E, W
    length: str
    features: list = field(default_factory=list)

@dataclass
class Garage:
    """Complete garage data"""
    width_ew: str = ""  # East-West dimension
    length_ns: str = ""  # North-South dimension  
    ceiling_height: str = ""
    walls: dict = field(default_factory=dict)
    floor_features: list = field(default_factory=list)
    notes: str = ""


def measurement_to_inches(measurement: str) -> Optional[float]:
    """Convert a measurement string to total inches for comparison"""
    if not measurement:
        return None
    
    total_inches = 0.0
    
    # Pattern for feet
    feet_pattern = r"(\d+)'"
    feet_match = re.search(feet_pattern, measurement)
    if feet_match:
        total_inches += float(feet_match.group(1)) * 12
    
    # Pattern for inches with optional fraction
    inches_pattern = r"(\d+)\s*(?:(\d+)/(\d+))?\s*\""
    inches_match = re.search(inches_pattern, measurement)
    if inches_match:
        inches = float(inches_match.group(1))
        if inches_match.group(2) and inches_match.group(3):
            inches += float(inches_match.group(2)) / float(inches_match.group(3))
        total_inches += inches
    
    # Also check for standalone fraction after feet (like 10' 6 3/16")
    standalone_pattern = r"'\s*(\d+)\s+(\d+)/(\d+)"
    standalone_match = re.search(standalone_pattern, measurement)
    if standalone_match:
        inches = float(standalone_match.group(1))
        inches += float(standalone_match.group(2)) / float(standalone_match.group(3))
        total_inches += inches
    elif feet_match and not inches_match:
        # Check for inches without quote mark after feet
        after_feet = r"'\s*(\d+)(?:\s*\")?$"
        after_match = re.search(after_feet, measurement)
        if after_match:
            total_inches += float(after_match.group(1))
    
    return total_inches if total_inches > 0 else None


def parse_measurement(input_str: str) -> Optional[str]:
    """
    Parse various measurement formats and normalize to feet' inches fraction"
    Accepts: 10' 6 3/16", 10'6", 10' 6", 10', 6", 32", etc.
    """
    input_str = input_str.strip()
    if not input_str:
        return None
    
    # Check FIRST if it's just inches (with " symbol) - this must come before feet pattern
    inch_only_pattern = r"^(\d+)\s*(?:(\d+)/(\d+))?\s*\"$"
    match = re.match(inch_only_pattern, input_str)
    if match:
        inches = match.group(1)
        numer = match.group(2)
        denom = match.group(3)
        if numer and denom:
            return f"0' {inches} {numer}/{denom}\""
        else:
            return f"0' {inches}\""
    
    # Check for feet with explicit ' symbol
    feet_pattern = r"^(\d+)'\s*(?:(\d+)\s*(?:(\d+)/(\d+))?\s*\"?)?$"
    match = re.match(feet_pattern, input_str)
    if match:
        feet = match.group(1) or "0"
        inches = match.group(2) or "0"
        numer = match.group(3)
        denom = match.group(4)
        
        if numer and denom:
            return f"{feet}' {inches} {numer}/{denom}\""
        elif inches != "0":
            return f"{feet}' {inches}\""
        else:
            return f"{feet}'"
    
    # Plain number without ' or " - assume feet for larger numbers, inches for smaller
    plain_number = r"^(\d+)$"
    match = re.match(plain_number, input_str)
    if match:
        num = int(match.group(1))
        if num <= 11:
            # Ambiguous - could be feet or inches, assume feet
            return f"{num}'"
        else:
            # Likely inches if over 11 and no unit specified
            return f"0' {num}\""
    
    return input_str  # Return as-is if we can't parse


class UserExitException(Exception):
    """Raised when user wants to exit the program"""
    pass


def ask(prompt: str, allow_empty: bool = False) -> str:
    """Ask a question and get input"""
    while True:
        response = input(f"\n{prompt}\n> ").strip()
        if response.lower() in ['quit', 'exit', 'q']:
            raise UserExitException()
        if response or allow_empty:
            return response
        print("Please enter a response.")


def ask_measurement(prompt: str, allow_empty: bool = False) -> str:
    """Ask for a measurement and parse it"""
    while True:
        response = ask(prompt, allow_empty)
        if not response and allow_empty:
            return ""
        parsed = parse_measurement(response)
        if parsed:
            return parsed
        print("Couldn't parse that measurement. Try format like: 10' 6 3/16\"")


def ask_yes_no(prompt: str) -> bool:
    """Ask a yes/no question"""
    while True:
        response = ask(prompt).lower()
        if response in ['y', 'yes']:
            return True
        if response in ['n', 'no']:
            return False
        print("Please enter yes or no (y/n).")


def validate_measurement_against_wall(measurement: str, wall_length: str, description: str) -> bool:
    """
    Check if a measurement makes sense given wall length.
    Returns True if OK to proceed, False if user wants to re-enter.
    """
    meas_inches = measurement_to_inches(measurement)
    wall_inches = measurement_to_inches(wall_length)
    
    if meas_inches is None or wall_inches is None:
        return True  # Can't validate, allow it
    
    if meas_inches > wall_inches:
        print(f"\n⚠️  Warning: {description} ({measurement}) exceeds wall length ({wall_length})")
        return ask_yes_no("Continue anyway?")
    
    return True


def validate_feature_size(width: str, feature_type: str) -> bool:
    """
    Sanity check feature dimensions.
    Returns True if OK to proceed, False if user wants to re-enter.
    """
    width_inches = measurement_to_inches(width)
    if width_inches is None:
        return True
    
    # Reasonable maximums in inches
    max_widths = {
        "entry_door": 48,       # 4 feet
        "service_door": 48,     # 4 feet
        "garage_door": 216,     # 18 feet
        "window": 96,           # 8 feet
        "electrical_panel": 36, # 3 feet
        "outlet": 6,            # 6 inches
        "water_heater": 36,     # 3 feet
        "furnace": 60,          # 5 feet
        "water_line": 12,       # 1 foot
        "drain": 12,            # 1 foot
        "gas_line": 12,         # 1 foot
        "hose_bib": 12,         # 1 foot
        "sump_pump": 24,        # 2 feet
    }
    
    max_width = max_widths.get(feature_type, 120)  # Default 10 feet
    
    if width_inches > max_width:
        max_feet = max_width / 12
        print(f"\n⚠️  Warning: That width ({width}) seems large for this feature type.")
        print(f"   Typical max is around {max_feet:.0f}' for {feature_type}.")
        return ask_yes_no("Continue anyway?")
    
    return True


COMMON_FEATURES = [
    ("entry_door", "Entry Door (to house)"),
    ("garage_door", "Garage Door"),
    ("service_door", "Service Door (to outside)"),
    ("window", "Window"),
    ("electrical_panel", "Electrical Panel"),
    ("outlet", "Electrical Outlet"),
    ("water_heater", "Water Heater"),
    ("furnace", "Furnace/HVAC"),
    ("water_line", "Water Line/Spigot"),
    ("drain", "Floor Drain"),
    ("gas_line", "Gas Line"),
    ("hose_bib", "Hose Bib"),
    ("sump_pump", "Sump Pump"),
    ("stairs", "Stairs"),
    ("attic_access", "Attic Access"),
    ("other", "Other (specify)")
]


def gather_wall_features(wall_direction: str, wall_length: str) -> list:
    """Interactively gather features on a wall"""
    features = []
    
    print(f"\n--- Features on {wall_direction} Wall ({wall_length} long) ---")
    print("Let's identify any permanent features on this wall.")
    print("(These are things that can't be moved and we'll need to work around)")
    
    while True:
        print("\nCommon features:")
        for i, (code, name) in enumerate(COMMON_FEATURES, 1):
            print(f"  {i}. {name}")
        print("  0. Done with this wall")
        
        choice = ask("Enter number or feature name (0 when done):")
        
        if choice == "0":
            # Confirmation if no features entered
            if not features:
                if ask_yes_no(f"No features on {wall_direction} wall - is that correct?"):
                    break
                else:
                    continue
            break
            
        # Parse choice
        feature_type = None
        feature_name = None
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(COMMON_FEATURES):
                feature_type, feature_name = COMMON_FEATURES[idx]
        except ValueError:
            feature_type = "other"
            feature_name = choice
        
        if feature_type == "other":
            feature_name = ask("What is this feature?")
        
        if feature_type and feature_name:
            print(f"\nAdding: {feature_name}")
            
            # Get position with validation
            while True:
                position = ask_measurement(
                    f"Position along wall from left corner (when facing wall)?\n"
                    f"(Wall is {wall_length} long, measuring to center of feature)"
                )
                if validate_measurement_against_wall(position, wall_length, "Position"):
                    break
            
            # Get width with validation
            while True:
                width = ask_measurement("Width of feature?")
                if validate_measurement_against_wall(width, wall_length, "Width"):
                    if validate_feature_size(width, feature_type):
                        break
            
            height = ask_measurement("Height of feature? (or floor-to-ceiling, etc.)", allow_empty=True)
            
            notes_input = ask("Any notes about this feature? (press Enter to skip)", allow_empty=True)
            notes = notes_input if notes_input.lower() not in ['no', 'n', ''] else ""
            
            features.append(Feature(
                name=feature_name,
                feature_type=feature_type,
                position_along_wall=position,
                width=width,
                height=height or "N/A",
                notes=notes
            ))
            
            print(f"✓ Added {feature_name}")
    
    return features


def gather_floor_features(garage_width: str, garage_length: str) -> list:
    """Gather features on the floor (drains, sump pumps, etc.)"""
    features = []
    
    print("\n--- Floor Features ---")
    print("Any permanent features on the floor we need to work around?")
    print("(drains, sump pumps, support posts, etc.)")
    
    if not ask_yes_no("Are there any floor features to capture?"):
        return features
    
    floor_feature_types = [
        ("drain", "Floor Drain"),
        ("sump_pump", "Sump Pump"),
        ("post", "Support Post"),
        ("other", "Other (specify)")
    ]
    
    while True:
        print("\nFloor feature types:")
        for i, (code, name) in enumerate(floor_feature_types, 1):
            print(f"  {i}. {name}")
        print("  0. Done with floor features")
        
        choice = ask("Enter number (0 when done):")
        
        if choice == "0":
            break
        
        feature_type = None
        feature_name = None
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(floor_feature_types):
                feature_type, feature_name = floor_feature_types[idx]
        except ValueError:
            continue
        
        if feature_type == "other":
            feature_name = ask("What is this feature?")
        
        if feature_type and feature_name:
            print(f"\nAdding: {feature_name}")
            
            # Get position with validation
            while True:
                pos_ns = ask_measurement("Position from North wall?")
                if validate_measurement_against_wall(pos_ns, garage_length, "Position from North"):
                    break
            
            while True:
                pos_ew = ask_measurement("Position from West wall?")
                if validate_measurement_against_wall(pos_ew, garage_width, "Position from West"):
                    break
            
            size = ask_measurement("Size/diameter?", allow_empty=True)
            notes_input = ask("Notes? (press Enter to skip)", allow_empty=True)
            notes = notes_input if notes_input.lower() not in ['no', 'n', ''] else ""
            
            features.append({
                "name": feature_name,
                "feature_type": feature_type,
                "pos_ns": pos_ns,
                "pos_ew": pos_ew,
                "size": size or "N/A",
                "notes": notes
            })
            print(f"✓ Added {feature_name}")
    
    return features


def generate_ascii_diagram(garage: Garage) -> str:
    """Generate a simple ASCII top-down diagram of the garage"""
    
    width = 60  # characters wide
    
    lines = []
    
    # Title
    lines.append("=" * width)
    lines.append("GARAGE FLOOR PLAN (Top-Down View)".center(width))
    lines.append(f"Dimensions: {garage.width_ew} (E-W) x {garage.length_ns} (N-S)".center(width))
    lines.append(f"Ceiling Height: {garage.ceiling_height}".center(width))
    lines.append("=" * width)
    lines.append("")
    
    # North wall label
    n_wall = garage.walls.get('N')
    n_features = ", ".join([f.name for f in n_wall.features]) if n_wall and n_wall.features else "(none)"
    lines.append(f"NORTH WALL: {n_features}".center(width))
    
    # Top border
    lines.append("+" + "-" * (width - 2) + "+")
    
    # West and East walls with interior
    w_wall = garage.walls.get('W')
    e_wall = garage.walls.get('E')
    w_features = [f.name for f in w_wall.features] if w_wall and w_wall.features else []
    e_features = [f.name for f in e_wall.features] if e_wall and e_wall.features else []
    
    # Calculate how many lines we need
    max_side_features = max(len(w_features), len(e_features), 1)
    interior_height = max(15, max_side_features + 4)
    
    for i in range(interior_height):
        left_label = w_features[i] if i < len(w_features) else ""
        right_label = e_features[i] if i < len(e_features) else ""
        
        # Create interior line
        interior = " " * (width - 2)
        
        # Add floor features in middle area
        if i == interior_height // 2 and garage.floor_features:
            floor_text = "Floor: " + ", ".join([f["name"] for f in garage.floor_features])
            interior = floor_text.center(width - 2)
        
        line = "|" + interior + "|"
        
        # Build the full line with side labels
        if left_label and right_label:
            lines.append(f"{left_label:>15} {line} {right_label}")
        elif left_label:
            lines.append(f"{left_label:>15} {line}")
        elif right_label:
            lines.append(f"{'':>15} {line} {right_label}")
        else:
            lines.append(f"{'':>15} {line}")
    
    # Bottom border  
    lines.append("+" + "-" * (width - 2) + "+")
    
    # South wall label
    s_wall = garage.walls.get('S')
    s_features = ", ".join([f.name for f in s_wall.features]) if s_wall and s_wall.features else "(none)"
    lines.append(f"SOUTH WALL: {s_features}".center(width))
    
    # Legend
    lines.append("")
    lines.append("=" * width)
    lines.append("FEATURE DETAILS:")
    lines.append("=" * width)
    
    wall_names = {'N': 'North', 'E': 'East', 'S': 'South', 'W': 'West'}
    
    for direction in ['N', 'E', 'S', 'W']:
        wall = garage.walls.get(direction)
        if wall and wall.features:
            lines.append(f"\n{wall_names[direction]} Wall ({wall.length}):")
            for f in wall.features:
                lines.append(f"  • {f.name}: {f.width} wide, {f.position_along_wall} from left")
                if f.notes:
                    lines.append(f"    Note: {f.notes}")
        elif wall:
            lines.append(f"\n{wall_names[direction]} Wall ({wall.length}): (no features)")
    
    if garage.floor_features:
        lines.append(f"\nFloor Features:")
        for f in garage.floor_features:
            lines.append(f"  • {f['name']}: {f['pos_ns']} from N wall, {f['pos_ew']} from W wall")
            if f.get('notes'):
                lines.append(f"    Note: {f['notes']}")
    else:
        lines.append(f"\nFloor Features: (none)")
    
    if garage.notes:
        lines.append(f"\nAdditional Notes:")
        lines.append(f"  {garage.notes}")
    
    return "\n".join(lines)


def import_from_form(filepath: str) -> Garage:
    """Import garage data from a filled-out form template"""
    
    garage = Garage()
    current_section = None
    current_feature = {}
    current_wall_features = []
    
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    def save_current_feature():
        nonlocal current_feature, current_wall_features
        if current_feature.get('feature') and current_feature['feature'] != '___':
            # Convert to Feature object
            feat = Feature(
                name=current_feature.get('feature', ''),
                feature_type=current_feature.get('feature', '').lower().replace(' ', '_'),
                position_along_wall=current_feature.get('position', 'N/A'),
                width=current_feature.get('width', 'N/A'),
                height=current_feature.get('height', 'N/A'),
                sill_height=current_feature.get('sill_height', ''),
                header_height=current_feature.get('header_height', ''),
                notes=current_feature.get('notes', '')
            )
            current_wall_features.append(feat)
        current_feature = {}
    
    def save_current_wall(direction):
        nonlocal current_wall_features
        save_current_feature()
        if direction == 'N':
            length = garage.width_ew
        elif direction == 'S':
            length = garage.width_ew
        else:
            length = garage.length_ns
        garage.walls[direction] = Wall(
            direction=direction,
            length=length,
            features=current_wall_features
        )
        current_wall_features = []
    
    for line in lines:
        line = line.strip()
        
        # Skip comments and empty lines
        if not line or line.startswith('#'):
            continue
        
        # Check for section headers
        if line.startswith('[') and line.endswith(']'):
            # Save previous section data
            if current_section == 'NORTH WALL':
                save_current_wall('N')
            elif current_section == 'EAST WALL':
                save_current_wall('E')
            elif current_section == 'SOUTH WALL':
                save_current_wall('S')
            elif current_section == 'WEST WALL':
                save_current_wall('W')
            elif current_section == 'FLOOR FEATURES':
                # Save any pending floor feature
                if current_feature.get('feature') and current_feature['feature'] != '___':
                    garage.floor_features.append({
                        'name': current_feature.get('feature', ''),
                        'feature_type': current_feature.get('feature', '').lower().replace(' ', '_'),
                        'pos_ns': current_feature.get('pos_from_north', 'N/A'),
                        'pos_ew': current_feature.get('pos_from_west', 'N/A'),
                        'size': current_feature.get('size', 'N/A'),
                        'notes': current_feature.get('notes', '')
                    })
                current_feature = {}
            
            current_section = line[1:-1]
            continue
        
        # Parse key: value pairs
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip().lower()
            value = value.strip()
            
            # Skip unfilled values
            if value == '___' or value == '':
                continue
            
            # Parse measurement if applicable
            if key in ['width_ew', 'length_ns', 'ceiling_height', 'position', 'width', 'height', 
                       'sill_height', 'header_height', 'size', 'pos_from_north', 'pos_from_west']:
                parsed = parse_measurement(value)
                if parsed:
                    value = parsed
            
            # Handle based on section
            if current_section == 'GARAGE DIMENSIONS':
                if key == 'width_ew':
                    garage.width_ew = value
                elif key == 'length_ns':
                    garage.length_ns = value
                elif key == 'ceiling_height':
                    garage.ceiling_height = value
            
            elif current_section in ['NORTH WALL', 'EAST WALL', 'SOUTH WALL', 'WEST WALL']:
                if key == 'feature':
                    save_current_feature()
                    current_feature = {'feature': value}
                else:
                    current_feature[key] = value
            
            elif current_section == 'FLOOR FEATURES':
                if key == 'feature':
                    # Save previous floor feature
                    if current_feature.get('feature'):
                        garage.floor_features.append({
                            'name': current_feature.get('feature', ''),
                            'feature_type': current_feature.get('feature', '').lower().replace(' ', '_'),
                            'pos_ns': current_feature.get('pos_from_north', 'N/A'),
                            'pos_ew': current_feature.get('pos_from_west', 'N/A'),
                            'size': current_feature.get('size', 'N/A'),
                            'notes': current_feature.get('notes', '')
                        })
                    current_feature = {'feature': value}
                else:
                    current_feature[key] = value
            
            elif current_section == 'NOTES':
                if key == 'notes':
                    garage.notes = value
    
    # Save final section
    if current_section == 'NORTH WALL':
        save_current_wall('N')
    elif current_section == 'EAST WALL':
        save_current_wall('E')
    elif current_section == 'SOUTH WALL':
        save_current_wall('S')
    elif current_section == 'WEST WALL':
        save_current_wall('W')
    elif current_section == 'FLOOR FEATURES' and current_feature.get('feature'):
        garage.floor_features.append({
            'name': current_feature.get('feature', ''),
            'feature_type': current_feature.get('feature', '').lower().replace(' ', '_'),
            'pos_ns': current_feature.get('pos_from_north', 'N/A'),
            'pos_ew': current_feature.get('pos_from_west', 'N/A'),
            'size': current_feature.get('size', 'N/A'),
            'notes': current_feature.get('notes', '')
        })
    
    # Ensure all walls exist
    for direction, length in [('N', garage.width_ew), ('E', garage.length_ns), 
                               ('S', garage.width_ew), ('W', garage.length_ns)]:
        if direction not in garage.walls:
            garage.walls[direction] = Wall(direction=direction, length=length, features=[])
    
    return garage


def main():
    """Main conversation flow"""
    print("\n" + "=" * 60)
    print("GARAGE LAYOUT PLANNER".center(60))
    print("Phase 1: Requirements Gathering (v2)".center(60))
    print("=" * 60)
    
    print("\nHi! I'm going to walk you through capturing your garage")
    print("dimensions and permanent features. This will help us plan")
    print("an optimal layout that works around what can't be moved.")
    print("\nFor measurements, use formats like: 10' 6 3/16\"")
    print("I'll warn you if something seems off, but you can override.")
    
    garage = Garage()
    
    # Overall dimensions
    print("\n--- OVERALL DIMENSIONS ---")
    
    garage.width_ew = ask_measurement(
        "What's the total WIDTH of your garage? (East to West dimension)"
    )
    
    garage.length_ns = ask_measurement(
        "What's the total LENGTH of your garage? (North to South dimension)"
    )
    
    garage.ceiling_height = ask_measurement(
        "What's the ceiling height?"
    )
    
    print(f"\n✓ Got it: {garage.width_ew} wide x {garage.length_ns} deep, {garage.ceiling_height} ceiling")
    
    # Walk through each wall
    print("\n--- WALL-BY-WALL WALKTHROUGH ---")
    print("Now let's go wall by wall, starting with North and going clockwise.")
    
    wall_info = {
        'N': ('North', garage.width_ew),
        'E': ('East', garage.length_ns),
        'S': ('South', garage.width_ew),
        'W': ('West', garage.length_ns)
    }
    
    for direction in ['N', 'E', 'S', 'W']:
        name, length = wall_info[direction]
        print(f"\n{'=' * 40}")
        print(f"Standing at the {name} wall, facing it...")
        print(f"This wall is {length} long.")
        
        features = gather_wall_features(direction, length)
        garage.walls[direction] = Wall(
            direction=direction,
            length=length,
            features=features
        )
        
        feature_count = len(features)
        print(f"\n✓ {name} wall complete: {feature_count} feature{'s' if feature_count != 1 else ''} captured")
    
    # Floor features
    garage.floor_features = gather_floor_features(garage.width_ew, garage.length_ns)
    
    # Any notes
    print("\n--- FINAL NOTES ---")
    notes_input = ask(
        "Any other notes about the garage? (existing layout, goals, constraints, etc.)\n"
        "(Press Enter to skip)",
        allow_empty=True
    )
    garage.notes = notes_input if notes_input.lower() not in ['no', 'n'] else ""
    
    # Generate output
    print("\n" + "=" * 60)
    print("GENERATING DIAGRAM...")
    print("=" * 60)
    
    diagram = generate_ascii_diagram(garage)
    print("\n" + diagram)
    
    # Save to file
    with open("garage_layout.txt", "w") as f:
        f.write(diagram)
    print("\n✓ Diagram saved to garage_layout.txt")
    
    print("\n" + "=" * 60)
    print("Requirements gathering complete!")
    print("Next steps: We'll use this data to generate layout options.")
    print("=" * 60)


if __name__ == "__main__":
    try:
        # Check for import argument
        if len(sys.argv) >= 3 and sys.argv[1] == '--import':
            filepath = sys.argv[2]
            print(f"\nImporting from: {filepath}")
            garage = import_from_form(filepath)
            print(f"✓ Imported garage: {garage.width_ew} x {garage.length_ns}, {garage.ceiling_height} ceiling")
            
            # Generate diagram
            diagram = generate_ascii_diagram(garage)
            print("\n" + diagram)
            
            with open("garage_layout.txt", "w") as f:
                f.write(diagram)
            print("\n✓ Diagram saved to garage_layout.txt")
        
        elif len(sys.argv) >= 2 and sys.argv[1] == '--template':
            # Generate a fresh template
            print("\nGenerating blank form template...")
            print("Use: py garage_intake_v2.py --import <your_filled_form.txt>")
            print("Template saved to: garage_form_template.txt")
        
        else:
            # Run interactive mode
            print("\nTip: Type 'quit' or 'exit' at any prompt to exit.")
            print("     Use --import <file> to import from a form template.")
            print("     Use --template to generate a blank form.\n")
            main()
    
    except UserExitException:
        print("\n\nExiting... Goodbye!")
    except KeyboardInterrupt:
        print("\n\nExiting... Goodbye!")
    except FileNotFoundError as e:
        print(f"\nError: Could not find file: {e.filename}")
    except Exception as e:
        print(f"\nError: {e}")
