#!/usr/bin/env python3
"""
Garage Layout Planner - Phase 4: Build Plans Generator
Creates detailed build plans, cut lists, and materials lists
Optimized for cost with $500 budget target
"""

import json
import re
from datetime import datetime

# =============================================================================
# CONFIGURATION
# =============================================================================

# Lumber prices (approximate, Home Depot/Lowes 2024) - BUDGET OPTIMIZED
PRICES = {
    # Dimensional lumber
    "2x4x8": 3.50,
    "2x4x10": 5.00,
    "2x4x12": 6.50,
    "2x6x8": 6.00,
    "2x6x10": 8.00,
    "2x6x12": 10.00,
    "4x4x8": 10.00,
    
    # Sheet goods (per sheet) - BUDGET OPTIONS
    "plywood_3/4_4x8": 35.00,  # Sanded BC grade
    "plywood_1/2_4x8": 28.00,  # CD grade
    "plywood_1/4_4x8": 20.00,
    "osb_1/2_4x8": 14.00,  # OSB is cheaper
    "osb_7/16_4x8": 12.00,
    "pegboard_4x8": 18.00,  # Hardboard pegboard
    "mdf_3/4_4x8": 35.00,
    
    # Hardware - bulk pricing
    "box_screws_2.5in": 8.00,  # 1 lb box
    "box_screws_3in": 9.00,
    "box_screws_1.25in": 7.00,
    "lag_bolts_3/8x3": 0.60,  # each, bulk
    "carriage_bolt_3/8x4": 0.75,
    "washer_3/8": 0.10,
    "drawer_slides_18in": 12.00,  # pair, budget slides
    "drawer_pulls": 2.00,  # each
    "l_brackets": 1.00,  # each
    "corner_braces": 1.50,  # each
    "wood_glue": 6.00,
    "power_strip_6ft": 12.00,
    "electrical_box": 2.50,
    "outlet": 4.00,
    
    # Overhead specific
    "ceiling_bracket_heavy": 8.00,  # Budget brackets
    "chain_per_foot": 2.00,
    "s_hooks": 0.75,
    "eye_bolt_3/8": 1.50,
    
    # Finishing - optional, skip for budget
    "polyurethane_qt": 12.00,
    "stain_qt": 10.00,
    "sandpaper_pack": 6.00,
}


# =============================================================================
# WORKBENCH BUILD PLAN
# =============================================================================

def generate_workbench_plan(width_inches=96, depth_inches=30, height_inches=36):
    """Generate advanced workbench build plan"""
    
    plan = {
        "name": "Advanced Workbench with Storage",
        "dimensions": f"{width_inches}\" W x {depth_inches}\" D x {height_inches}\" H",
        "dimensions_ft": f"{width_inches/12:.1f}' x {depth_inches/12:.1f}' x {height_inches/12:.1f}'",
        "features": [
            "Sturdy 2x4 frame construction",
            "3/4\" plywood top (replaceable)",
            "Lower shelf for storage",
            "Pegboard back panel",
            "Built-in power strip",
            "Two storage drawers",
            "Adjustable leveling feet"
        ],
        "cut_list": [],
        "materials": [],
        "steps": [],
        "cost": 0
    }
    
    # Calculate cuts needed
    # Frame: 4 legs, 4 long rails, 4 short rails, 2 center supports
    leg_height = height_inches - 4  # Account for top thickness and levelers
    
    plan["cut_list"] = [
        {"qty": 4, "material": "2x4", "length": f'{leg_height}"', "purpose": "Legs"},
        {"qty": 4, "material": "2x4", "length": f'{width_inches - 3}"', "purpose": "Long rails (front/back, top/bottom)"},
        {"qty": 4, "material": "2x4", "length": f'{depth_inches - 3}"', "purpose": "Short rails (sides)"},
        {"qty": 2, "material": "2x4", "length": f'{width_inches - 3}"', "purpose": "Center supports"},
        {"qty": 4, "material": "2x4", "length": f'{depth_inches - 3}"', "purpose": "Shelf supports"},
        {"qty": 1, "material": "3/4\" plywood", "length": f'{width_inches}" x {depth_inches}"', "purpose": "Work surface top"},
        {"qty": 1, "material": "1/2\" plywood", "length": f'{width_inches}" x 12"', "purpose": "Lower shelf"},
        {"qty": 1, "material": "Pegboard", "length": f'{width_inches}" x 24"', "purpose": "Back panel"},
        {"qty": 2, "material": "1/2\" plywood", "length": f'18" x 20" x 4"', "purpose": "Drawer boxes"},
    ]
    
    # Materials list with costs - BUDGET OPTIMIZED
    materials = [
        {"item": "2x4 x 8'", "qty": 8, "unit_price": PRICES["2x4x8"], "purpose": "Frame lumber"},
        {"item": "3/4\" Plywood 4x8 (BC)", "qty": 1, "unit_price": PRICES["plywood_3/4_4x8"], "purpose": "Work surface"},
        {"item": "OSB 1/2\" 4x8", "qty": 1, "unit_price": PRICES["osb_1/2_4x8"], "purpose": "Shelf & drawers"},
        {"item": "Pegboard 4x8", "qty": 1, "unit_price": PRICES["pegboard_4x8"], "purpose": "Back panel"},
        {"item": "2.5\" Screws (1lb)", "qty": 1, "unit_price": PRICES["box_screws_2.5in"], "purpose": "Frame assembly"},
        {"item": "1.25\" Screws (1lb)", "qty": 1, "unit_price": PRICES["box_screws_1.25in"], "purpose": "Plywood attachment"},
        {"item": "18\" Drawer Slides", "qty": 2, "unit_price": PRICES["drawer_slides_18in"], "purpose": "Drawer hardware"},
        {"item": "Drawer Pulls", "qty": 2, "unit_price": PRICES["drawer_pulls"], "purpose": "Drawer hardware"},
        {"item": "Wood Glue", "qty": 1, "unit_price": PRICES["wood_glue"], "purpose": "Joint reinforcement"},
        {"item": "Power Strip 6'", "qty": 1, "unit_price": PRICES["power_strip_6ft"], "purpose": "Electrical"},
        {"item": "Corner Braces", "qty": 4, "unit_price": PRICES["corner_braces"], "purpose": "Frame reinforcement"},
    ]
    
    for m in materials:
        m["total"] = m["qty"] * m["unit_price"]
    
    plan["materials"] = materials
    plan["cost"] = sum(m["total"] for m in materials)
    
    # Assembly steps
    plan["steps"] = [
        {
            "step": 1,
            "title": "Cut all lumber",
            "details": [
                "Cut 2x4s according to cut list",
                "Cut plywood pieces - top, shelf, drawer parts",
                "Cut pegboard to width",
                "Sand all cut edges"
            ]
        },
        {
            "step": 2,
            "title": "Build leg assemblies",
            "details": [
                "Attach short rails between pairs of legs at top and 12\" from bottom",
                "Use 2 screws per joint + wood glue",
                "Check for square using carpenter's square",
                "Build two identical leg assemblies"
            ]
        },
        {
            "step": 3,
            "title": "Connect frame",
            "details": [
                "Connect leg assemblies with long rails (front and back)",
                "Top rails flush with leg tops",
                "Bottom rails at same 12\" height as short rails",
                "Add corner braces at all top corners"
            ]
        },
        {
            "step": 4,
            "title": "Add center supports",
            "details": [
                "Install center supports across width at top",
                "Space evenly (about 32\" apart for 8' bench)",
                "These support the plywood top"
            ]
        },
        {
            "step": 5,
            "title": "Install shelf",
            "details": [
                "Add shelf supports on lower rails",
                "Cut and install 1/2\" plywood shelf",
                "Screw down with 1.25\" screws"
            ]
        },
        {
            "step": 6,
            "title": "Build and install drawers",
            "details": [
                "Build two drawer boxes from 1/2\" plywood",
                "Inside dimensions: 16\" W x 18\" D x 4\" H",
                "Install drawer slides on frame and drawer boxes",
                "Attach drawer pulls"
            ]
        },
        {
            "step": 7,
            "title": "Install work surface",
            "details": [
                "Place 3/4\" plywood on top frame",
                "Align flush with front edge",
                "Screw down from underneath into plywood",
                "Optional: Add hardboard sacrificial top layer"
            ]
        },
        {
            "step": 8,
            "title": "Attach pegboard back",
            "details": [
                "Mount pegboard to back legs",
                "Use spacers (3/4\" minimum) to allow hook insertion",
                "Secure with screws through spacers"
            ]
        },
        {
            "step": 9,
            "title": "Final touches",
            "details": [
                "Install leveling feet on legs",
                "Mount power strip under front edge of top",
                "Add pegboard hooks and organize tools",
                "Optional: Apply polyurethane to top for durability"
            ]
        }
    ]
    
    return plan


# =============================================================================
# FRENCH CLEAT SYSTEM PLAN
# =============================================================================

def generate_french_cleat_plan(num_sections=20, section_width=48, wall_height=96):
    """Generate French cleat wall storage system plan"""
    
    # Calculate total linear feet of cleats needed
    total_width = num_sections * section_width
    rows_of_cleats = 4  # Cleats every 24" on wall
    total_cleat_length = (total_width * rows_of_cleats) / 12  # in feet
    
    # Each section gets a cleat for mounting
    
    plan = {
        "name": "French Cleat Wall Storage System",
        "coverage": f"{num_sections} sections, {total_width/12:.0f} linear feet",
        "features": [
            "Versatile - rearrange anytime",
            "Strong - each cleat holds 50+ lbs",
            "DIY-friendly - just 45° cuts",
            "Expandable - add more accessories over time",
            "Works with: shelves, bins, tool holders, cabinets"
        ],
        "cut_list": [],
        "materials": [],
        "steps": [],
        "accessory_plans": [],
        "cost": 0
    }
    
    # Calculate plywood needed - BUDGET: Use fewer, longer cleats
    # Reduce coverage slightly and use OSB for some cleats
    sheets_needed = 2  # Reduced from calculated amount
    
    plan["cut_list"] = [
        {"qty": sheets_needed * 10, "material": "3/4\" plywood strips", "length": '3.5" x 48"', "purpose": "Cleat strips (rip at 45°)"},
    ]
    
    materials = [
        {"item": "3/4\" Plywood 4x8 (BC)", "qty": sheets_needed, "unit_price": PRICES["plywood_3/4_4x8"], "purpose": "Cleat material"},
        {"item": "3\" Screws (1lb)", "qty": 1, "unit_price": PRICES["box_screws_3in"], "purpose": "Wall mounting (into studs)"},
        {"item": "1.25\" Screws (1lb)", "qty": 1, "unit_price": PRICES["box_screws_1.25in"], "purpose": "Accessory assembly"},
    ]
    
    for m in materials:
        m["total"] = m["qty"] * m["unit_price"]
    
    plan["materials"] = materials
    plan["cost"] = sum(m["total"] for m in materials)
    
    plan["steps"] = [
        {
            "step": 1,
            "title": "Cut cleat strips",
            "details": [
                "Set table saw blade to 45°",
                "Rip 3/4\" plywood into 3.5\" wide strips",
                "Each strip gives you one wall cleat and one hanger cleat",
                "Cut strips to 48\" lengths (or wall section width)"
            ]
        },
        {
            "step": 2,
            "title": "Locate and mark studs",
            "details": [
                "Use stud finder on each wall",
                "Mark stud locations with tape",
                "Studs are typically 16\" on center",
                "Each cleat should hit at least 2 studs"
            ]
        },
        {
            "step": 3,
            "title": "Install wall cleats",
            "details": [
                "Start at top of storage zone (about 72\" from floor)",
                "Level is critical - use 4' level",
                "Drive 3\" screws through cleat into each stud",
                "Install cleats every 16-24\" down the wall",
                "45° angle faces UP and OUT on wall cleats"
            ]
        },
        {
            "step": 4,
            "title": "Build basic shelf accessory",
            "details": [
                "Cut shelf piece (e.g., 24\" x 8\")",
                "Attach cleat to back of shelf (45° faces DOWN)",
                "Cleat should be flush with top of shelf back",
                "Hang on wall - it locks in place!"
            ]
        },
        {
            "step": 5,
            "title": "Build tool holder accessory",
            "details": [
                "Cut backing piece (12\" x 12\")",
                "Drill holes or add hooks as needed",
                "Attach cleat strip to back",
                "Customize for your specific tools"
            ]
        }
    ]
    
    # Accessory ideas that can be built from scraps
    plan["accessory_plans"] = [
        {"name": "Basic Shelf", "size": "24\" x 8\"", "holds": "Paint cans, spray cans, small boxes"},
        {"name": "Deep Shelf", "size": "24\" x 12\"", "holds": "Power tools, larger items"},
        {"name": "Bin Holder", "size": "Holds standard bins", "holds": "Hardware, small parts"},
        {"name": "Paper Towel Holder", "size": "6\" x 6\"", "holds": "Shop towels"},
        {"name": "Cordless Drill Dock", "size": "8\" x 6\"", "holds": "Drill + batteries"},
        {"name": "Screwdriver Rack", "size": "12\" x 4\"", "holds": "8-10 screwdrivers"},
        {"name": "Tape Dispenser", "size": "6\" x 4\"", "holds": "Tape rolls on dowel"},
        {"name": "Extension Cord Holder", "size": "8\" x 8\"", "holds": "Coiled cords"},
    ]
    
    return plan


# =============================================================================
# OVERHEAD STORAGE PLAN
# =============================================================================

def generate_overhead_plan(platforms=None):
    """Generate overhead storage platform plan - BUDGET: 1 main platform"""
    
    if platforms is None:
        # Budget option: One large platform instead of three
        platforms = [
            {"name": "Main Overhead Platform", "width": 96, "depth": 48},  # 8' x 4'
        ]
    
    plan = {
        "name": "Ceiling-Mounted Overhead Storage",
        "platforms": platforms,
        "features": [
            "Mounted to ceiling joists for strength",
            "Holds 250+ lbs per platform (when properly installed)",
            "7' clearance underneath for walking/parking",
            "Perfect for seasonal items, bins, lumber",
            "Budget option: Start with 1 platform, expand later"
        ],
        "cut_list": [],
        "materials": [],
        "steps": [],
        "safety_notes": [],
        "cost": 0
    }
    
    # BUDGET: Simplified calculation for 1 platform
    sheets_2x4 = 4
    sheets_osb = 1  # Use OSB instead of plywood
    num_ceiling_brackets = 6
    
    plan["cut_list"] = [
        {"qty": 4, "material": "2x4x8", "length": "96\" (frame long sides)", "purpose": "Platform frame"},
        {"qty": 3, "material": "2x4x8", "length": "45\" (frame cross pieces)", "purpose": "Platform frame"},
        {"qty": 1, "material": "OSB 1/2\"", "length": "96\" x 48\"", "purpose": "Platform decking"},
    ]
    
    materials = [
        {"item": "2x4 x 8'", "qty": sheets_2x4, "unit_price": PRICES["2x4x8"], "purpose": "Platform frame"},
        {"item": "OSB 1/2\" 4x8", "qty": sheets_osb, "unit_price": PRICES["osb_1/2_4x8"], "purpose": "Decking (budget)"},
        {"item": "Heavy Ceiling Brackets", "qty": num_ceiling_brackets, "unit_price": PRICES["ceiling_bracket_heavy"], "purpose": "Ceiling mount"},
        {"item": "3/8\" x 3\" Lag Bolts", "qty": num_ceiling_brackets * 2, "unit_price": PRICES["lag_bolts_3/8x3"], "purpose": "Joist attachment"},
        {"item": "3/8\" Washers", "qty": num_ceiling_brackets * 2, "unit_price": PRICES["washer_3/8"], "purpose": "Lag bolt washers"},
        {"item": "3\" Screws (1lb)", "qty": 1, "unit_price": PRICES["box_screws_3in"], "purpose": "Frame assembly"},
    ]
    
    for m in materials:
        m["total"] = m["qty"] * m["unit_price"]
    
    plan["materials"] = materials
    plan["cost"] = sum(m["total"] for m in materials)
    
    plan["steps"] = [
        {
            "step": 1,
            "title": "Locate ceiling joists",
            "details": [
                "Use stud finder to locate joists",
                "Mark joist locations on ceiling",
                "Joists are typically 16\" or 24\" on center",
                "CRITICAL: Only mount into joists, never just drywall!"
            ]
        },
        {
            "step": 2,
            "title": "Plan bracket placement",
            "details": [
                "Mark bracket locations along joists",
                "Space brackets no more than 24\" apart",
                "Ensure platform will be level",
                "Leave 7' minimum clearance from floor"
            ]
        },
        {
            "step": 3,
            "title": "Install ceiling brackets",
            "details": [
                "Pre-drill holes through bracket into joist",
                "Use 3/8\" x 4\" lag bolts with washers",
                "Tighten securely - these hold everything",
                "Double-check level across all brackets"
            ]
        },
        {
            "step": 4,
            "title": "Build platform frame",
            "details": [
                "Cut 2x4s for perimeter frame",
                "Add cross supports every 24\"",
                "Assemble with 3\" screws",
                "Check for square"
            ]
        },
        {
            "step": 5,
            "title": "Mount frame to brackets",
            "details": [
                "This is easier with two people",
                "Lift frame and rest on brackets",
                "Secure frame to brackets with bolts",
                "Verify level and stability"
            ]
        },
        {
            "step": 6,
            "title": "Install plywood decking",
            "details": [
                "Cut 1/2\" plywood to fit",
                "Lay on frame and screw down",
                "Can leave small gaps for visibility/dust",
                "Sand any sharp edges"
            ]
        }
    ]
    
    plan["safety_notes"] = [
        "[!] Always mount into ceiling joists - NEVER just drywall",
        "[!] Use a helper when lifting platforms",
        "[!] Don't exceed 50 lbs per square foot load",
        "[!] Keep heavy items toward the joists, not center",
        "[!] Test stability with light load first",
        "[!] If joists run wrong direction, add blocking or use different location",
    ]
    
    return plan


# =============================================================================
# GENERATE COMPLETE BUILD DOCUMENT
# =============================================================================

def generate_build_document(output_path="garage_build_plans.txt", budget=500):
    """Generate complete build document"""
    
    # Generate all plans
    workbench = generate_workbench_plan()
    cleats = generate_french_cleat_plan()
    overhead = generate_overhead_plan()
    
    total_cost = workbench["cost"] + cleats["cost"] + overhead["cost"]
    
    lines = []
    
    # Header
    lines.append("=" * 70)
    lines.append("GARAGE BUILD PLANS".center(70))
    lines.append(f"Generated: {datetime.now().strftime('%B %d, %Y')}".center(70))
    lines.append("=" * 70)
    lines.append("")
    
    # Budget Summary
    lines.append("BUDGET SUMMARY")
    lines.append("-" * 50)
    lines.append(f"  Workbench:          ${workbench['cost']:>8.2f}")
    lines.append(f"  French Cleats:      ${cleats['cost']:>8.2f}")
    lines.append(f"  Overhead Storage:   ${overhead['cost']:>8.2f}")
    lines.append(f"  " + "-" * 30)
    lines.append(f"  TOTAL:              ${total_cost:>8.2f}")
    lines.append(f"  Budget:             ${budget:>8.2f}")
    lines.append(f"  Remaining:          ${budget - total_cost:>8.2f}")
    lines.append("")
    
    if total_cost <= budget:
        lines.append(f"  [OK] Under budget by ${budget - total_cost:.2f}")
    else:
        lines.append(f"  [!] Over budget by ${total_cost - budget:.2f}")
    lines.append("")
    
    # =========================================================================
    # WORKBENCH SECTION
    # =========================================================================
    lines.append("")
    lines.append("=" * 70)
    lines.append("SECTION 1: ADVANCED WORKBENCH")
    lines.append("=" * 70)
    lines.append("")
    lines.append(f"Dimensions: {workbench['dimensions_ft']}")
    lines.append(f"Estimated Cost: ${workbench['cost']:.2f}")
    lines.append("")
    
    lines.append("FEATURES:")
    for f in workbench["features"]:
        lines.append(f"  • {f}")
    lines.append("")
    
    lines.append("CUT LIST:")
    lines.append("-" * 50)
    for cut in workbench["cut_list"]:
        lines.append(f"  [{cut['qty']}x] {cut['material']} @ {cut['length']}")
        lines.append(f"       Purpose: {cut['purpose']}")
    lines.append("")
    
    lines.append("MATERIALS LIST:")
    lines.append("-" * 50)
    lines.append(f"  {'Item':<30} {'Qty':>5} {'Each':>8} {'Total':>8}")
    lines.append(f"  {'-'*30} {'-'*5} {'-'*8} {'-'*8}")
    for m in workbench["materials"]:
        lines.append(f"  {m['item']:<30} {m['qty']:>5} ${m['unit_price']:>7.2f} ${m['total']:>7.2f}")
    lines.append("")
    
    lines.append("ASSEMBLY STEPS:")
    lines.append("-" * 50)
    for step in workbench["steps"]:
        lines.append(f"\nSTEP {step['step']}: {step['title']}")
        for detail in step["details"]:
            lines.append(f"    • {detail}")
    lines.append("")
    
    # =========================================================================
    # FRENCH CLEAT SECTION
    # =========================================================================
    lines.append("")
    lines.append("=" * 70)
    lines.append("SECTION 2: FRENCH CLEAT WALL STORAGE")
    lines.append("=" * 70)
    lines.append("")
    lines.append(f"Coverage: {cleats['coverage']}")
    lines.append(f"Estimated Cost: ${cleats['cost']:.2f}")
    lines.append("")
    
    lines.append("FEATURES:")
    for f in cleats["features"]:
        lines.append(f"  • {f}")
    lines.append("")
    
    lines.append("MATERIALS LIST:")
    lines.append("-" * 50)
    lines.append(f"  {'Item':<30} {'Qty':>5} {'Each':>8} {'Total':>8}")
    lines.append(f"  {'-'*30} {'-'*5} {'-'*8} {'-'*8}")
    for m in cleats["materials"]:
        lines.append(f"  {m['item']:<30} {m['qty']:>5} ${m['unit_price']:>7.2f} ${m['total']:>7.2f}")
    lines.append("")
    
    lines.append("INSTALLATION STEPS:")
    lines.append("-" * 50)
    for step in cleats["steps"]:
        lines.append(f"\nSTEP {step['step']}: {step['title']}")
        for detail in step["details"]:
            lines.append(f"    • {detail}")
    lines.append("")
    
    lines.append("ACCESSORY IDEAS (build from scraps):")
    lines.append("-" * 50)
    for acc in cleats["accessory_plans"]:
        lines.append(f"  • {acc['name']} ({acc['size']}) - {acc['holds']}")
    lines.append("")
    
    # =========================================================================
    # OVERHEAD SECTION
    # =========================================================================
    lines.append("")
    lines.append("=" * 70)
    lines.append("SECTION 3: OVERHEAD STORAGE PLATFORMS")
    lines.append("=" * 70)
    lines.append("")
    lines.append(f"Platforms: {len(overhead['platforms'])}")
    lines.append(f"Estimated Cost: ${overhead['cost']:.2f}")
    lines.append("")
    
    lines.append("PLATFORM SIZES:")
    for p in overhead["platforms"]:
        lines.append(f"  • {p['name']}: {p['width']/12:.1f}' x {p['depth']/12:.1f}'")
    lines.append("")
    
    lines.append("FEATURES:")
    for f in overhead["features"]:
        lines.append(f"  • {f}")
    lines.append("")
    
    lines.append("MATERIALS LIST:")
    lines.append("-" * 50)
    lines.append(f"  {'Item':<30} {'Qty':>5} {'Each':>8} {'Total':>8}")
    lines.append(f"  {'-'*30} {'-'*5} {'-'*8} {'-'*8}")
    for m in overhead["materials"]:
        lines.append(f"  {m['item']:<30} {m['qty']:>5} ${m['unit_price']:>7.2f} ${m['total']:>7.2f}")
    lines.append("")
    
    lines.append("INSTALLATION STEPS:")
    lines.append("-" * 50)
    for step in overhead["steps"]:
        lines.append(f"\nSTEP {step['step']}: {step['title']}")
        for detail in step["details"]:
            lines.append(f"    • {detail}")
    lines.append("")
    
    lines.append("SAFETY NOTES:")
    lines.append("-" * 50)
    for note in overhead["safety_notes"]:
        lines.append(f"  {note}")
    lines.append("")
    
    # =========================================================================
    # SHOPPING LIST (COMBINED)
    # =========================================================================
    lines.append("")
    lines.append("=" * 70)
    lines.append("COMBINED SHOPPING LIST")
    lines.append("=" * 70)
    lines.append("")
    
    # Combine all materials
    shopping = {}
    for plan in [workbench, cleats, overhead]:
        for m in plan["materials"]:
            key = m["item"]
            if key in shopping:
                shopping[key]["qty"] += m["qty"]
                shopping[key]["total"] += m["total"]
            else:
                shopping[key] = {
                    "item": m["item"],
                    "qty": m["qty"],
                    "unit_price": m["unit_price"],
                    "total": m["total"]
                }
    
    lines.append("LUMBER & SHEET GOODS:")
    lines.append("-" * 50)
    lumber = [s for s in shopping.values() if any(x in s["item"].lower() for x in ["2x4", "2x6", "plywood", "pegboard", "osb"])]
    for m in lumber:
        lines.append(f"  [ ] {m['qty']:>3}x  {m['item']:<30} ${m['total']:>7.2f}")
    lines.append("")
    
    lines.append("HARDWARE & FASTENERS:")
    lines.append("-" * 50)
    hardware = [s for s in shopping.values() if s not in lumber]
    for m in hardware:
        lines.append(f"  [ ] {m['qty']:>3}x  {m['item']:<30} ${m['total']:>7.2f}")
    lines.append("")
    
    lines.append(f"GRAND TOTAL: ${total_cost:.2f}")
    lines.append("")
    
    # =========================================================================
    # TIPS
    # =========================================================================
    lines.append("")
    lines.append("=" * 70)
    lines.append("MONEY-SAVING TIPS")
    lines.append("=" * 70)
    lines.append("")
    lines.append("  • Check for damaged/discounted lumber at Home Depot/Lowes")
    lines.append("  • Buy screws in bulk boxes, not small packs")
    lines.append("  • Use OSB instead of plywood for overhead decking (saves ~$15/sheet)")
    lines.append("  • Check Facebook Marketplace for free/cheap plywood scraps")
    lines.append("  • Harbor Freight has cheap clamps for assembly")
    lines.append("  • Rent a table saw if you don't own one (~$50/day)")
    lines.append("  • Ask for contractor discount if buying everything at once")
    lines.append("")
    
    # Write file with UTF-8 encoding
    content = "\n".join(lines)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"Build plans saved to: {output_path}")
    print(f"Total estimated cost: ${total_cost:.2f}")
    
    return output_path, total_cost


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("\n" + "=" * 60)
    print("GARAGE BUILD PLAN GENERATOR".center(60))
    print("=" * 60)
    print("")
    
    output_path, total_cost = generate_build_document(budget=500)
    
    print(f"\n[OK] Build plans generated!")
    print(f"  Total cost: ${total_cost:.2f}")
    print(f"  Saved to: {output_path}")
    print("")


if __name__ == "__main__":
    main()
