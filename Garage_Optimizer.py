#!/usr/bin/env python3
"""
Garage Layout Planner - Phase 3: Layout Optimizer
Takes garage constraints + usage profile and recommends zone placements

Input files:
  - garage_layout.txt (or import Garage dataclass)
  - garage_usage.json

Output:
  - Recommended zones with positions
  - Reasoning for each placement
  - ASCII visualization of proposed layout
"""

import json
import re
import sys
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum


# =============================================================================
# DATA STRUCTURES
# =============================================================================

class ZoneType(Enum):
    VEHICLE = "vehicle"
    WORKBENCH = "workbench"
    WALL_STORAGE = "wall_storage"
    OVERHEAD_STORAGE = "overhead_storage"
    FLOOR_STORAGE = "floor_storage"
    CLEARANCE = "clearance"  # Reserved space (door swing, access, etc.)


@dataclass
class Zone:
    """A functional zone in the garage"""
    zone_type: ZoneType
    name: str
    x: float  # Position from west wall (inches)
    y: float  # Position from north wall (inches)
    width: float  # East-west dimension (inches)
    depth: float  # North-south dimension (inches)
    wall: str = ""  # Which wall it's against (N, E, S, W, or "" for floor)
    priority: int = 3  # 1-5, inherited from usage profile
    notes: str = ""


@dataclass
class Constraint:
    """A constraint that affects layout"""
    constraint_type: str  # "door_clearance", "electrical_access", "window", etc.
    x: float
    y: float
    width: float
    depth: float
    wall: str
    description: str


@dataclass
class GarageSpace:
    """Parsed garage dimensions and features"""
    width: float  # East-west (inches)
    depth: float  # North-south (inches)
    ceiling_height: float  # inches
    
    # Features by wall
    north_features: List[Dict] = field(default_factory=list)
    east_features: List[Dict] = field(default_factory=list)
    south_features: List[Dict] = field(default_factory=list)
    west_features: List[Dict] = field(default_factory=list)
    floor_features: List[Dict] = field(default_factory=list)


@dataclass
class UsageProfile:
    """Loaded usage profile"""
    vehicles: List[Dict] = field(default_factory=list)
    storage_categories: List[Dict] = field(default_factory=list)
    work_activities: List[Dict] = field(default_factory=list)
    priorities: Dict = field(default_factory=dict)
    preferences: Dict = field(default_factory=dict)
    notes: str = ""


@dataclass
class LayoutRecommendation:
    """Complete layout recommendation"""
    zones: List[Zone] = field(default_factory=list)
    constraints: List[Constraint] = field(default_factory=list)
    reasoning: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    score: float = 0.0


# =============================================================================
# MEASUREMENT PARSING (reused from intake)
# =============================================================================

def measurement_to_inches(measurement: str) -> Optional[float]:
    """Convert a measurement string to total inches"""
    if not measurement or measurement == "N/A":
        return None
    
    total_inches = 0.0
    
    # Pattern for feet (with optional decimal)
    feet_pattern = r"(\d+(?:\.\d+)?)'"
    feet_match = re.search(feet_pattern, measurement)
    if feet_match:
        total_inches += float(feet_match.group(1)) * 12
    
    # Pattern for inches with optional decimal or fraction (e.g., 184.1" or 6 3/4")
    inches_pattern = r"(\d+(?:\.\d+)?)\s*(?:(\d+)/(\d+))?\s*\""
    inches_match = re.search(inches_pattern, measurement)
    if inches_match:
        inches = float(inches_match.group(1))
        if inches_match.group(2) and inches_match.group(3):
            inches += float(inches_match.group(2)) / float(inches_match.group(3))
        total_inches += inches
    
    # Standalone number with optional decimal (assume inches)
    if not feet_match and not inches_match:
        plain_match = re.match(r"^(\d+(?:\.\d+)?)$", measurement.strip())
        if plain_match:
            total_inches = float(plain_match.group(1))
    
    return total_inches if total_inches > 0 else None


def inches_to_feet_str(inches: float) -> str:
    """Convert inches to readable feet/inches string"""
    feet = int(inches // 12)
    remaining_inches = inches % 12
    if remaining_inches == 0:
        return f"{feet}'"
    elif feet == 0:
        return f'{remaining_inches:.0f}"'
    else:
        return f"{feet}' {remaining_inches:.0f}\""


# =============================================================================
# LAYOUT CONSTANTS
# =============================================================================

# Clearance requirements (inches)
CLEARANCES = {
    "garage_door": 36,      # Clear zone in front of garage door
    "entry_door": 36,       # Door swing + passage
    "service_door": 36,     # Door swing + passage  
    "electrical_panel": 36, # NEC requires 36" clearance
    "water_heater": 24,     # Access for maintenance
    "furnace": 24,          # Access for maintenance
    "window": 6,            # Minimal clearance
    "vehicle_side": 24,     # Space to open car doors
    "vehicle_front": 12,    # Space in front of parked car
    "vehicle_rear": 12,     # Space behind parked car
    "workbench_front": 36,  # Standing/working space
    "walkway": 30,          # Minimum passage width
}

# Standard zone sizes (inches)
ZONE_SIZES = {
    "workbench_small": {"width": 48, "depth": 24},   # 4' x 2'
    "workbench_medium": {"width": 72, "depth": 30},  # 6' x 2.5'
    "workbench_large": {"width": 96, "depth": 30},   # 8' x 2.5'
    "wall_storage_section": {"width": 48, "depth": 18},  # 4' wide, 18" deep
    "overhead_storage": {"width": 48, "depth": 96},  # 4' x 8' platform
}


# =============================================================================
# FILE LOADERS
# =============================================================================

def load_garage_layout(filepath: str = "garage_layout.txt") -> GarageSpace:
    """Parse the ASCII garage layout file to extract dimensions and features"""
    garage = GarageSpace(width=0, depth=0, ceiling_height=0)
    
    try:
        with open(filepath, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Warning: {filepath} not found. Using defaults.")
        return garage
    
    # Parse dimensions from header
    dim_pattern = r"Dimensions:\s*([^(]+)\s*\(E-W\)\s*x\s*([^(]+)\s*\(N-S\)"
    dim_match = re.search(dim_pattern, content)
    if dim_match:
        garage.width = measurement_to_inches(dim_match.group(1).strip()) or 0
        garage.depth = measurement_to_inches(dim_match.group(2).strip()) or 0
    
    ceiling_pattern = r"Ceiling Height:\s*(.+)"
    ceiling_match = re.search(ceiling_pattern, content)
    if ceiling_match:
        garage.ceiling_height = measurement_to_inches(ceiling_match.group(1).strip()) or 0
    
    # Parse wall features
    current_wall = None
    feature_pattern = r"[-•]\s*(.+?)(?:\s+at\s+|\s*@\s*)([^,]+)(?:,\s*w=(.+))?"
    
    for line in content.split('\n'):
        line = line.strip()
        
        # Detect wall sections
        if "NORTH WALL:" in line:
            current_wall = "N"
        elif "EAST WALL:" in line:
            current_wall = "E"
        elif "SOUTH WALL:" in line:
            current_wall = "S"
        elif "WEST WALL:" in line:
            current_wall = "W"
        elif "FLOOR FEATURES:" in line:
            current_wall = "FLOOR"
        
        # Parse feature lines (look for bullet points or dashes)
        if line.startswith(('-', '•', '*')) and current_wall:
            # Simple parsing: extract feature name and position
            parts = line.lstrip('-•* ').split(' at ')
            if len(parts) >= 1:
                feature_name = parts[0].strip()
                position = parts[1].strip() if len(parts) > 1 else "0"
                
                feature = {
                    "name": feature_name,
                    "position": measurement_to_inches(position) or 0,
                    "width": 36,  # Default width
                    "type": feature_name.lower().replace(' ', '_')
                }
                
                # Estimate width based on feature type
                if "garage door" in feature_name.lower():
                    feature["width"] = 192  # 16' default
                elif "door" in feature_name.lower():
                    feature["width"] = 36  # 3' default
                elif "window" in feature_name.lower():
                    feature["width"] = 36  # 3' default
                elif "panel" in feature_name.lower():
                    feature["width"] = 24  # 2' default
                
                if current_wall == "N":
                    garage.north_features.append(feature)
                elif current_wall == "E":
                    garage.east_features.append(feature)
                elif current_wall == "S":
                    garage.south_features.append(feature)
                elif current_wall == "W":
                    garage.west_features.append(feature)
                elif current_wall == "FLOOR":
                    garage.floor_features.append(feature)
    
    return garage


def load_usage_profile(filepath: str = "garage_usage.json") -> UsageProfile:
    """Load the usage profile JSON"""
    profile = UsageProfile()
    
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Warning: {filepath} not found. Using defaults.")
        return profile
    except json.JSONDecodeError:
        print(f"Warning: {filepath} is not valid JSON. Using defaults.")
        return profile
    
    profile.vehicles = data.get("vehicles", [])
    profile.storage_categories = data.get("storage_categories", [])
    profile.work_activities = data.get("work_activities", [])
    profile.priorities = data.get("priorities", {})
    profile.preferences = data.get("preferences", {})
    profile.notes = data.get("notes", "")
    
    return profile


# =============================================================================
# CONSTRAINT GENERATION
# =============================================================================

def generate_constraints(garage: GarageSpace) -> List[Constraint]:
    """Generate constraints from garage features"""
    constraints = []
    
    def add_wall_constraints(features: List[Dict], wall: str, wall_length: float, is_ns: bool):
        """Add constraints for features on a wall"""
        for feature in features:
            pos = feature.get("position", 0)
            width = feature.get("width", 36)
            name = feature.get("name", "Unknown")
            ftype = feature.get("type", "").lower()
            
            # Determine clearance needed
            clearance = CLEARANCES.get(ftype, 24)
            
            # Calculate constraint position based on wall
            if wall == "N":
                x = pos - width / 2
                y = 0
                c_width = width
                c_depth = clearance
            elif wall == "S":
                x = pos - width / 2
                y = garage.depth - clearance
                c_width = width
                c_depth = clearance
            elif wall == "E":
                x = garage.width - clearance
                y = pos - width / 2
                c_width = clearance
                c_depth = width
            elif wall == "W":
                x = 0
                y = pos - width / 2
                c_width = clearance
                c_depth = width
            else:
                continue
            
            # Special handling for garage doors - need full clearance for pulling in
            if "garage_door" in ftype or "garage door" in name.lower():
                if wall == "S":
                    # Garage door on south - clearance extends into garage
                    c_depth = 60  # 5 feet for pulling in
                    y = garage.depth - c_depth
                elif wall == "N":
                    c_depth = 60
                    y = 0
            
            constraints.append(Constraint(
                constraint_type=ftype,
                x=max(0, x),
                y=max(0, y),
                width=c_width,
                depth=c_depth,
                wall=wall,
                description=f"{name} - keep {inches_to_feet_str(clearance)} clear"
            ))
    
    add_wall_constraints(garage.north_features, "N", garage.width, False)
    add_wall_constraints(garage.east_features, "E", garage.depth, True)
    add_wall_constraints(garage.south_features, "S", garage.width, False)
    add_wall_constraints(garage.west_features, "W", garage.depth, True)
    
    return constraints


# =============================================================================
# LAYOUT OPTIMIZATION
# =============================================================================

def optimize_layout(garage: GarageSpace, profile: UsageProfile) -> LayoutRecommendation:
    """Main optimization logic"""
    recommendation = LayoutRecommendation()
    
    # Step 1: Generate constraints from features
    recommendation.constraints = generate_constraints(garage)
    
    # Step 2: Determine what needs to be placed
    zones_needed = []
    
    # Vehicles - count how many must fit to plan side-by-side layout
    vehicles_must_fit = [v for v in profile.vehicles if v.get("must_fit_inside", False)]
    num_vehicles = len(vehicles_must_fit)
    
    for i, vehicle in enumerate(vehicles_must_fit):
        v_length = measurement_to_inches(vehicle.get("length", "180")) or 180
        v_width = measurement_to_inches(vehicle.get("width", "72")) or 72
        
        # Only add door clearance on driver side (left side when pulling in)
        # If multiple cars, only the outermost get extra clearance
        if num_vehicles == 1:
            # Single car - clearance on both sides
            side_clearance = CLEARANCES["vehicle_side"] * 2
        else:
            # Multiple cars - 24" between cars, 24" on outer edge
            side_clearance = CLEARANCES["vehicle_side"]
        
        zones_needed.append({
            "type": ZoneType.VEHICLE,
            "name": f"{vehicle.get('year', '')} {vehicle.get('make', '')} {vehicle.get('model', '')}".strip(),
            "width": v_width + side_clearance,
            "depth": v_length + CLEARANCES["vehicle_front"] + CLEARANCES["vehicle_rear"],
            "priority": profile.priorities.get("vehicle_storage", 3),
            "vehicle_index": i,
            "total_vehicles": num_vehicles
        })
    
    # Workbench (if work activities exist or workspace priority is high)
    if profile.work_activities or profile.priorities.get("workspace", 0) >= 3:
        # Determine workbench size based on activities AND priority
        workspace_priority = profile.priorities.get("workspace", 3)
        needs_large = any(
            a.get("space_needed", "").lower() in ["medium", "large"] 
            for a in profile.work_activities
        )
        
        # Priority 5 = large workbench, priority 4+ with activities = large
        if workspace_priority >= 5 or (workspace_priority >= 4 and needs_large):
            wb_size = ZONE_SIZES["workbench_large"]
        elif needs_large or workspace_priority >= 4:
            wb_size = ZONE_SIZES["workbench_medium"]
        else:
            wb_size = ZONE_SIZES["workbench_small"]
        
        zones_needed.append({
            "type": ZoneType.WORKBENCH,
            "name": "Workbench",
            "width": wb_size["width"],
            "depth": wb_size["depth"] + CLEARANCES["workbench_front"],
            "priority": profile.priorities.get("workspace", 3)
        })
    
    # Wall storage sections
    if profile.preferences.get("wall_storage", True):
        # Estimate wall storage needed based on storage categories
        storage_count = len(profile.storage_categories)
        storage_priority = profile.priorities.get("general_storage", 3)
        
        # Count items by access frequency
        daily_access = sum(1 for s in profile.storage_categories 
                         if s.get("needs_accessibility", "") == "daily")
        weekly_access = sum(1 for s in profile.storage_categories 
                          if s.get("needs_accessibility", "") == "weekly")
        
        # More sections if high storage priority
        # Base: 2 sections, +1 per category, +2 for daily items, +1 for weekly
        # Priority 5 = max it out (20 sections)
        base_sections = 2 + storage_count + (daily_access * 2) + weekly_access
        
        if storage_priority >= 5:
            sections_needed = 20  # Max it out
        elif storage_priority >= 4:
            sections_needed = min(15, int(base_sections * 1.5))
        else:
            sections_needed = min(8, base_sections)
        
        for i in range(sections_needed):
            zones_needed.append({
                "type": ZoneType.WALL_STORAGE,
                "name": f"Wall Storage {i+1}",
                "width": ZONE_SIZES["wall_storage_section"]["width"],
                "depth": ZONE_SIZES["wall_storage_section"]["depth"],
                "priority": profile.priorities.get("general_storage", 3)
            })
    
    # Step 3: Place zones (greedy algorithm - highest priority first)
    zones_needed.sort(key=lambda z: z["priority"], reverse=True)
    
    placed_zones = []
    
    for zone_spec in zones_needed:
        zone = place_zone(
            zone_spec, 
            garage, 
            recommendation.constraints, 
            placed_zones,
            profile.preferences
        )
        if zone:
            placed_zones.append(zone)
            recommendation.zones.append(zone)
            recommendation.reasoning.append(
                f"Placed {zone.name} on {zone.wall or 'floor'} wall at "
                f"({inches_to_feet_str(zone.x)}, {inches_to_feet_str(zone.y)})"
            )
        else:
            recommendation.warnings.append(
                f"Could not place {zone_spec['name']} - insufficient space"
            )
    
    # Step 4: Add overhead storage if preferred and ceiling height allows
    if profile.preferences.get("overhead_storage", False) and garage.ceiling_height >= 96:
        # Place overhead storage platforms over areas that aren't workbench
        # Good locations: over vehicle hood area, along walls above storage
        
        # Calculate usable overhead height (need 7' clearance for walking/car)
        min_clearance = 84  # 7 feet
        overhead_depth = 48  # 4 feet deep platforms
        
        # Try to place 2-3 overhead platforms
        overhead_locations = []
        
        # Location 1: Along north wall (above wall storage, not workbench)
        workbench_zones = [z for z in placed_zones if z.zone_type == ZoneType.WORKBENCH]
        wb_end_x = 0
        if workbench_zones:
            wb = workbench_zones[0]
            wb_end_x = wb.x + wb.width + 24  # Start after workbench + gap
        
        if wb_end_x < garage.width - 96:  # At least 8' of space
            overhead_locations.append({
                "name": "Overhead Storage - North",
                "x": wb_end_x,
                "y": 0,
                "width": min(garage.width - wb_end_x - 24, 144),  # Up to 12'
                "depth": overhead_depth
            })
        
        # Location 2: Along west wall 
        # Check if west wall has space above vehicle area
        vehicle_zones = [z for z in placed_zones if z.zone_type == ZoneType.VEHICLE]
        if vehicle_zones:
            # Place overhead along west wall, spanning from workbench area down
            v = vehicle_zones[0]
            west_overhead_depth = min(v.y - 24, 120)  # Up to 10' long, stop before vehicle
            if west_overhead_depth > 48:  # At least 4' to be useful
                overhead_locations.append({
                    "name": "Overhead Storage - West",
                    "x": 0,
                    "y": 72,  # Start 6' from north wall (below workbench area)
                    "width": overhead_depth,  # 4' out from wall
                    "depth": west_overhead_depth
                })
        
        # Location 3: Along east wall above entry door area
        overhead_locations.append({
            "name": "Overhead Storage - East", 
            "x": garage.width - overhead_depth,
            "y": 48,
            "width": overhead_depth,
            "depth": 96  # 8' section
        })
        
        for loc in overhead_locations:
            if loc["width"] > 36 and loc["depth"] > 36:  # Minimum useful size
                zone = Zone(
                    zone_type=ZoneType.OVERHEAD_STORAGE,
                    name=loc["name"],
                    x=loc["x"],
                    y=loc["y"],
                    width=loc["width"],
                    depth=loc["depth"],
                    wall="ceiling",
                    priority=profile.priorities.get("general_storage", 3),
                    notes=f"Mount at {inches_to_feet_str(min_clearance)} minimum clearance"
                )
                recommendation.zones.append(zone)
                recommendation.reasoning.append(
                    f"Placed {loc['name']} ({inches_to_feet_str(loc['width'])} x {inches_to_feet_str(loc['depth'])}) - ceiling height allows"
                )
    
    # Step 5: Calculate score
    recommendation.score = calculate_layout_score(recommendation, profile)
    
    return recommendation


def place_zone(
    zone_spec: Dict,
    garage: GarageSpace,
    constraints: List[Constraint],
    placed_zones: List[Zone],
    preferences: Dict
) -> Optional[Zone]:
    """Try to place a zone, respecting constraints and existing zones"""
    
    zone_type = zone_spec["type"]
    width = zone_spec["width"]
    depth = zone_spec["depth"]
    name = zone_spec["name"]
    priority = zone_spec.get("priority", 3)
    
    # Strategy depends on zone type
    if zone_type == ZoneType.VEHICLE:
        # Vehicles go in from garage door, typically centered or to one side
        # Assume garage door is on south wall
        best_pos = find_vehicle_position(garage, constraints, placed_zones, width, depth, zone_spec)
        if best_pos:
            return Zone(
                zone_type=zone_type,
                name=name,
                x=best_pos[0],
                y=best_pos[1],
                width=width,
                depth=depth,
                wall="S",
                priority=priority,
                notes="Pull in from garage door"
            )
    
    elif zone_type == ZoneType.WORKBENCH:
        # Workbench goes against a wall, preferably near electrical
        best_wall = find_best_wall_for_workbench(garage, constraints, placed_zones, width, depth)
        if best_wall:
            wall, x, y = best_wall
            return Zone(
                zone_type=zone_type,
                name=name,
                x=x,
                y=y,
                width=width,
                depth=depth,
                wall=wall,
                priority=priority,
                notes="Position for good lighting and electrical access"
            )
    
    elif zone_type == ZoneType.WALL_STORAGE:
        # Wall storage goes on available wall space
        best_spot = find_wall_storage_spot(garage, constraints, placed_zones, width, depth)
        if best_spot:
            wall, x, y = best_spot
            return Zone(
                zone_type=zone_type,
                name=name,
                x=x,
                y=y,
                width=width,
                depth=depth,
                wall=wall,
                priority=priority
            )
    
    return None


def find_vehicle_position(
    garage: GarageSpace,
    constraints: List[Constraint],
    placed_zones: List[Zone],
    width: float,
    depth: float,
    zone_spec: Dict = None
) -> Optional[Tuple[float, float]]:
    """Find position for a vehicle (assumes south-facing garage door)"""
    
    # Check if this is part of a multi-car setup
    vehicle_index = zone_spec.get("vehicle_index", 0) if zone_spec else 0
    total_vehicles = zone_spec.get("total_vehicles", 1) if zone_spec else 1
    
    # Already placed vehicles
    placed_vehicles = [z for z in placed_zones if z.zone_type == ZoneType.VEHICLE]
    
    if total_vehicles == 1:
        # Single car - try centered first, then left, then right
        positions_to_try = [
            ((garage.width - width) / 2, garage.depth - depth),  # Centered
            (CLEARANCES["walkway"], garage.depth - depth),  # Left side
            (garage.width - width - CLEARANCES["walkway"], garage.depth - depth),  # Right side
        ]
    else:
        # Multiple cars - place side by side
        if not placed_vehicles:
            # First car - put on left side
            x = CLEARANCES["walkway"]
            positions_to_try = [(x, garage.depth - depth)]
        else:
            # Subsequent cars - place next to last car with gap
            last_vehicle = placed_vehicles[-1]
            x = last_vehicle.x + last_vehicle.width + 12  # 12" gap between cars
            positions_to_try = [(x, garage.depth - depth)]
    
    for x, y in positions_to_try:
        if x < 0 or y < 0:
            continue
        if x + width > garage.width or y + depth > garage.depth:
            continue
        
        # Check against constraints
        overlaps = False
        for c in constraints:
            if rectangles_overlap(x, y, width, depth, c.x, c.y, c.width, c.depth):
                # Allow overlap with garage door clearance (we're supposed to drive through it)
                if "garage_door" not in c.constraint_type:
                    overlaps = True
                    break
        
        # Check against placed zones
        for z in placed_zones:
            if rectangles_overlap(x, y, width, depth, z.x, z.y, z.width, z.depth):
                overlaps = True
                break
        
        if not overlaps:
            return (x, y)
    
    return None


def find_best_wall_for_workbench(
    garage: GarageSpace,
    constraints: List[Constraint],
    placed_zones: List[Zone],
    width: float,
    depth: float
) -> Optional[Tuple[str, float, float]]:
    """Find best wall position for workbench"""
    
    # Check each wall (prefer walls with electrical, avoid garage door wall)
    walls_to_check = [
        ("N", 0, CLEARANCES["walkway"]),  # North wall
        ("E", garage.width - depth, CLEARANCES["walkway"]),  # East wall (rotated)
        ("W", 0, CLEARANCES["walkway"]),  # West wall
    ]
    
    # Find electrical panel location
    has_electrical = {"N": False, "E": False, "W": False, "S": False}
    for f in garage.east_features:
        if "electrical" in f.get("name", "").lower() or "panel" in f.get("name", "").lower():
            has_electrical["E"] = True
    
    # Sort by preference (electrical first)
    walls_to_check.sort(key=lambda w: has_electrical.get(w[0], False), reverse=True)
    
    for wall, base_x, base_y in walls_to_check:
        # Calculate actual position based on wall
        if wall == "N":
            x = CLEARANCES["walkway"]
            y = 0
            w, d = width, depth
        elif wall == "E":
            x = garage.width - depth
            y = CLEARANCES["walkway"]
            w, d = depth, width
        elif wall == "W":
            x = 0
            y = CLEARANCES["walkway"]
            w, d = depth, width
        else:
            continue
        
        # Check if it fits
        if not position_is_clear(x, y, w, d, garage, constraints, placed_zones):
            continue
        
        return (wall, x, y)
    
    return None


def find_wall_storage_spot(
    garage: GarageSpace,
    constraints: List[Constraint],
    placed_zones: List[Zone],
    width: float,
    depth: float
) -> Optional[Tuple[str, float, float]]:
    """Find available wall space for storage, distributing across walls"""
    
    # Count how many storage sections are on each wall
    wall_counts = {"N": 0, "E": 0, "W": 0}
    for z in placed_zones:
        if z.zone_type == ZoneType.WALL_STORAGE and z.wall in wall_counts:
            wall_counts[z.wall] += 1
    
    # Prioritize walls with fewer sections (distribute evenly)
    walls = sorted(["N", "E", "W"], key=lambda w: wall_counts[w])
    
    for wall in walls:
        # Generate potential positions along the wall
        if wall == "N":
            # North wall - scan left to right
            for x in range(0, int(garage.width - width), 24):
                if position_is_clear(x, 0, width, depth, garage, constraints, placed_zones):
                    return (wall, x, 0)
        elif wall == "E":
            # East wall - scan top to bottom
            for y in range(0, int(garage.depth - width), 24):
                if position_is_clear(garage.width - depth, y, depth, width, garage, constraints, placed_zones):
                    return (wall, garage.width - depth, y)
        elif wall == "W":
            # West wall - scan top to bottom, working around windows
            for y in range(0, int(garage.depth - width), 24):
                if position_is_clear(0, y, depth, width, garage, constraints, placed_zones):
                    return (wall, 0, y)
    
    # If all walls are full, try to squeeze more in anywhere
    for wall in ["N", "E", "W"]:
        if wall == "N":
            for x in range(0, int(garage.width - width), 12):  # Tighter spacing
                if position_is_clear(x, 0, width, depth, garage, constraints, placed_zones):
                    return (wall, x, 0)
        elif wall == "E":
            for y in range(0, int(garage.depth - width), 12):
                if position_is_clear(garage.width - depth, y, depth, width, garage, constraints, placed_zones):
                    return (wall, garage.width - depth, y)
        elif wall == "W":
            for y in range(0, int(garage.depth - width), 12):
                if position_is_clear(0, y, depth, width, garage, constraints, placed_zones):
                    return (wall, 0, y)
    
    return None


def position_is_clear(
    x: float, y: float, width: float, depth: float,
    garage: GarageSpace,
    constraints: List[Constraint],
    placed_zones: List[Zone]
) -> bool:
    """Check if a position is clear of constraints and other zones"""
    
    # Bounds check
    if x < 0 or y < 0:
        return False
    if x + width > garage.width or y + depth > garage.depth:
        return False
    
    # Check constraints
    for c in constraints:
        if rectangles_overlap(x, y, width, depth, c.x, c.y, c.width, c.depth):
            return False
    
    # Check placed zones
    for z in placed_zones:
        if rectangles_overlap(x, y, width, depth, z.x, z.y, z.width, z.depth):
            return False
    
    return True


def rectangles_overlap(
    x1: float, y1: float, w1: float, h1: float,
    x2: float, y2: float, w2: float, h2: float
) -> bool:
    """Check if two rectangles overlap"""
    return not (x1 + w1 <= x2 or x2 + w2 <= x1 or y1 + h1 <= y2 or y2 + h2 <= y1)


def calculate_layout_score(recommendation: LayoutRecommendation, profile: UsageProfile) -> float:
    """Calculate a quality score for the layout (0-100)"""
    score = 100.0
    
    # Deduct for unplaced zones
    score -= len(recommendation.warnings) * 15
    
    # Add points for matching priorities
    vehicle_placed = any(z.zone_type == ZoneType.VEHICLE for z in recommendation.zones)
    if vehicle_placed and profile.priorities.get("vehicle_storage", 0) >= 4:
        score += 10
    
    workbench_placed = any(z.zone_type == ZoneType.WORKBENCH for z in recommendation.zones)
    if workbench_placed and profile.priorities.get("workspace", 0) >= 4:
        score += 10
    
    return max(0, min(100, score))


# =============================================================================
# OUTPUT GENERATION
# =============================================================================

def generate_layout_ascii(garage: GarageSpace, recommendation: LayoutRecommendation) -> str:
    """Generate ASCII representation of the recommended layout"""
    
    # Scale: 1 char = ~6 inches (so 25' = 50 chars)
    scale = 6
    grid_width = int(garage.width / scale) + 2
    grid_height = int(garage.depth / scale) + 2
    
    # Initialize grid
    grid = [[' ' for _ in range(grid_width)] for _ in range(grid_height)]
    
    # Draw borders
    for x in range(grid_width):
        grid[0][x] = '-'
        grid[grid_height-1][x] = '-'
    for y in range(grid_height):
        grid[y][0] = '|'
        grid[y][grid_width-1] = '|'
    grid[0][0] = grid[0][grid_width-1] = grid[grid_height-1][0] = grid[grid_height-1][grid_width-1] = '+'
    
    # Draw zones
    zone_chars = {
        ZoneType.VEHICLE: 'V',
        ZoneType.WORKBENCH: 'W',
        ZoneType.WALL_STORAGE: 'S',
        ZoneType.OVERHEAD_STORAGE: 'O',
        ZoneType.FLOOR_STORAGE: 'F',
        ZoneType.CLEARANCE: '.',
    }
    
    for zone in recommendation.zones:
        char = zone_chars.get(zone.zone_type, '?')
        x_start = int(zone.x / scale) + 1
        y_start = int(zone.y / scale) + 1
        x_end = int((zone.x + zone.width) / scale) + 1
        y_end = int((zone.y + zone.depth) / scale) + 1
        
        for y in range(max(1, y_start), min(grid_height-1, y_end)):
            for x in range(max(1, x_start), min(grid_width-1, x_end)):
                grid[y][x] = char
    
    # Draw constraints (features)
    for constraint in recommendation.constraints:
        x_pos = int((constraint.x + constraint.width/2) / scale) + 1
        y_pos = int((constraint.y + constraint.depth/2) / scale) + 1
        if 0 < x_pos < grid_width - 1 and 0 < y_pos < grid_height - 1:
            if "door" in constraint.constraint_type.lower():
                grid[y_pos][x_pos] = 'D'
            elif "panel" in constraint.constraint_type.lower() or "electrical" in constraint.constraint_type.lower():
                grid[y_pos][x_pos] = 'E'
            elif "window" in constraint.constraint_type.lower():
                grid[y_pos][x_pos] = 'w'
    
    # Build output
    lines = []
    lines.append("=" * 60)
    lines.append("RECOMMENDED GARAGE LAYOUT".center(60))
    lines.append(f"Garage: {inches_to_feet_str(garage.width)} x {inches_to_feet_str(garage.depth)}".center(60))
    lines.append("=" * 60)
    lines.append("")
    lines.append("                    NORTH")
    
    for row in grid:
        lines.append("        " + ''.join(row))
    
    lines.append("                    SOUTH (Garage Door)")
    lines.append("")
    
    # Legend
    lines.append("LEGEND:")
    lines.append("  V = Vehicle parking    W = Workbench      S = Wall storage")
    lines.append("  O = Overhead storage   D = Door           E = Electrical")
    lines.append("  w = Window")
    lines.append("")
    
    return '\n'.join(lines)


def generate_recommendation_report(
    garage: GarageSpace, 
    profile: UsageProfile,
    recommendation: LayoutRecommendation
) -> str:
    """Generate detailed recommendation report"""
    
    lines = []
    lines.append("=" * 60)
    lines.append("GARAGE LAYOUT RECOMMENDATION".center(60))
    lines.append("=" * 60)
    lines.append("")
    
    # Summary
    lines.append("SUMMARY")
    lines.append("-" * 40)
    lines.append(f"Garage size: {inches_to_feet_str(garage.width)} x {inches_to_feet_str(garage.depth)}")
    lines.append(f"Ceiling height: {inches_to_feet_str(garage.ceiling_height)}")
    lines.append(f"Layout score: {recommendation.score:.0f}/100")
    lines.append("")
    
    # Zones placed
    lines.append("ZONES PLACED")
    lines.append("-" * 40)
    for zone in recommendation.zones:
        lines.append(f"  {zone.name}")
        lines.append(f"    Position: {inches_to_feet_str(zone.x)} from W, {inches_to_feet_str(zone.y)} from N")
        lines.append(f"    Size: {inches_to_feet_str(zone.width)} x {inches_to_feet_str(zone.depth)}")
        lines.append(f"    Wall: {zone.wall or 'Floor'}")
        if zone.notes:
            lines.append(f"    Note: {zone.notes}")
    lines.append("")
    
    # Reasoning
    if recommendation.reasoning:
        lines.append("REASONING")
        lines.append("-" * 40)
        for reason in recommendation.reasoning:
            lines.append(f"  * {reason}")
        lines.append("")
    
    # Warnings
    if recommendation.warnings:
        lines.append("WARNINGS")
        lines.append("-" * 40)
        for warning in recommendation.warnings:
            lines.append(f"  ! {warning}")
        lines.append("")
    
    # Constraints considered
    lines.append("CONSTRAINTS CONSIDERED")
    lines.append("-" * 40)
    for constraint in recommendation.constraints:
        lines.append(f"  * {constraint.description}")
    lines.append("")
    
    # Next steps
    lines.append("NEXT STEPS")
    lines.append("-" * 40)
    lines.append("  1. Review this layout and provide feedback")
    lines.append("  2. Adjust priorities if zones are missing")
    lines.append("  3. Generate build plans for approved layout")
    lines.append("")
    
    return '\n'.join(lines)


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Main optimizer flow"""
    
    print("\n" + "=" * 60)
    print("GARAGE LAYOUT OPTIMIZER".center(60))
    print("Phase 3: Layout Recommendations".center(60))
    print("=" * 60)
    
    # Load inputs
    print("\nLoading garage layout...")
    garage = load_garage_layout("garage_layout.txt")
    
    if garage.width == 0 or garage.depth == 0:
        print("Error: Could not load garage dimensions.")
        print("Make sure garage_layout.txt exists from Phase 1.")
        sys.exit(1)
    
    print(f"  Loaded: {inches_to_feet_str(garage.width)} x {inches_to_feet_str(garage.depth)}")
    
    print("\nLoading usage profile...")
    profile = load_usage_profile("garage_usage.json")
    print(f"  Vehicles: {len(profile.vehicles)}")
    print(f"  Storage categories: {len(profile.storage_categories)}")
    print(f"  Work activities: {len(profile.work_activities)}")
    
    # Optimize
    print("\nOptimizing layout...")
    recommendation = optimize_layout(garage, profile)
    
    # Generate outputs
    print("\n")
    ascii_layout = generate_layout_ascii(garage, recommendation)
    print(ascii_layout)
    
    report = generate_recommendation_report(garage, profile, recommendation)
    print(report)
    
    # Save outputs
    with open("garage_recommendation.txt", "w") as f:
        f.write(ascii_layout)
        f.write("\n\n")
        f.write(report)
    print("Saved to garage_recommendation.txt")
    
    print("\n" + "=" * 60)
    print("Layout optimization complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
