# Garage Layout Planner - Project Handoff Document
## Created: December 13, 2025

---

## PROJECT OVERVIEW

Building a garage layout optimization tool that:
1. Captures garage dimensions and constraints (doors, windows, electrical, etc.)
2. Captures usage requirements (vehicles, storage, work activities)
3. Optimizes layout with blueprints, renderings, and build plans

**Target users:** Homeowners planning garage organization
**Target platform:** Initially Python CLI, eventually mobile app

---

## CURRENT STATE (MVP Progress)

### Completed Components:

**1. Garage Intake (v2)** - `garage_intake_v2.py`
- Conversational wall-by-wall data capture
- Form-based import from text file
- Measurement validation (warns if dimensions exceed wall length)
- Feature size sanity checks
- Exit anytime with 'quit' or 'exit'
- Outputs ASCII diagram + saves to `garage_layout.txt`

**2. Usage Questionnaire** - `garage_usage.py`
- Captures vehicles (year/make/model with auto-dimension lookup)
- Captures storage needs (categories, quantity, access frequency)
- Captures work activities (type, frequency, space needed, power requirements)
- Priority rankings (1-5 scale for vehicles, workspace, storage, accessibility)
- Preferences (wall storage, overhead storage, clear floor)
- Outputs to `garage_usage.json` and `garage_usage.txt`

**3. Vehicle Database** - `vehicle_database.py`
- 191 vehicles, 34 makes
- 18KB total size (mobile-friendly)
- Dimensions in inches (length, width, height)
- Fuzzy matching for typos ("altimia" → "Altima")
- Common aliases ("chevy" → Chevrolet, "f150" → F-150)
- Approximate year matching (within 5 years if exact not found)

**4. Form Template** - `garage_form_template.txt`
- Fill-in-the-blank text file for garage measurements
- Supports sill height, header height for windows
- Import via: `py garage_intake_v2.py --import <filename>`

### Mike's Test Data:
- `mikes_garage.txt` - 25' x 25' garage, 12'2" ceiling
  - North: Service door (centered)
  - East: Entry door to house, electrical panel
  - South: 16' garage door (centered)
  - West: Two windows (62" from left, 8' apart)

---

## FILE STRUCTURE

```
Garage_Designer/
├── garage_intake_v2.py    # Phase 1: Dimension capture
├── garage_usage.py        # Phase 2: Usage questionnaire  
├── vehicle_database.py    # Vehicle dimensions lookup
├── garage_form_template.txt  # Blank intake form
├── mikes_garage.txt       # Mike's filled-in form
├── garage_layout.txt      # Output: ASCII diagram
├── garage_usage.json      # Output: Usage data (structured)
└── garage_usage.txt       # Output: Usage data (readable)
```

---

## HOW TO RUN

```bash
# Navigate to project folder
cd Documents\Garage_Designer

# Phase 1: Capture garage dimensions
py garage_intake_v2.py                          # Interactive mode
py garage_intake_v2.py --import mikes_garage.txt  # Import from file

# Phase 2: Capture usage requirements
py garage_usage.py
```

---

## WHAT'S NEXT (Build Order)

1. **Layout Optimization Logic** - The brain that suggests placements
   - Input: garage constraints + usage profile
   - Output: Recommended zones (vehicle, workbench, storage areas)
   - Consider: door swing clearance, electrical access, workflow

2. **Visual Output (PNG/SVG)** - Proper scaled diagrams
   - Top-down floor plan with features positioned
   - Wall elevations showing vertical space
   - Build this AFTER optimization logic is stable

3. **Build Plans & Parts Lists** - Final deliverable
   - Cut lists for workbenches/shelving
   - Hardware/materials list
   - Step-by-step instructions

---

## PARKING LOT (Future Features)

### High Priority:
- [ ] Rolling/scrollable menu for vehicle selection (instead of typing)
- [ ] Load existing `garage_usage.json` to avoid re-entry
- [ ] Image upload: AI analyzes garage photos for dimensions
- [ ] 3D rendering of proposed layout

### Medium Priority:
- [ ] Multiple layout options with trade-off comparison
- [ ] Cost estimation for recommended storage solutions
- [ ] Integration with common storage products (Gladiator, Husky, etc.)
- [ ] Export to PDF for printing

### Lower Priority:
- [ ] Web/mobile app version
- [ ] Sharing/collaboration features
- [ ] Before/after visualization
- [ ] AR preview (see layout in actual garage via phone camera)

### Technical Debt:
- [ ] Consolidate measurement parsing across all modules
- [ ] Add unit tests
- [ ] Standardize data model between intake and usage modules
- [ ] Add logging for debugging

---

## KEY DESIGN DECISIONS

1. **Offline-first vehicle database** - Poor garage signal; 18KB is negligible
2. **Fuzzy matching over strict input** - Users will typo; be forgiving
3. **Warn but allow override** - User might know something we don't
4. **ASCII before graphics** - Validate data model before investing in visuals
5. **JSON for data, TXT for humans** - Structured for code, readable for users

---

## KNOWN ISSUES / BUGS FIXED

- [x] Floor drain captured menu number instead of name
- [x] Inch-only input (32") parsed as feet (32')
- [x] Unicode stars (★☆) caused Windows encoding error
- [x] Empty notes displayed as "Note: no"
- [x] No confirmation when skipping walls with no features
- [x] Exact year match only (now allows ±5 years)
- [x] No typo tolerance (now has fuzzy matching)

---

## CONTEXT FOR NEW CHAT

When starting a new chat, paste this prompt:

```
I'm building a Garage Layout Planner with Claude. Here's where we left off:

**Completed:**
- Garage dimension intake (wall-by-wall, form import, validation)
- Usage questionnaire (vehicles, storage, activities, priorities)
- Vehicle database (191 cars, fuzzy matching, 18KB)

**Next step:** Layout optimization logic - the brain that takes constraints + usage and suggests where to place workbenches, storage zones, vehicle parking.

**Files:** I have garage_intake_v2.py, garage_usage.py, vehicle_database.py

**My garage:** 25' x 25', 12'2" ceiling, garage door on south, entry door + electrical panel on east, service door on north, two windows on west.

**My usage:** [summarize your garage_usage.json here]

Let's build the optimizer.
```

---

## MIKE'S CONTEXT

- Senior Domain Expert at Mercor Intelligence (AI training)
- Former K-12 superintendent and COO
- Hands-on with garage/woodworking/automotive projects
- Building custom workbench, organizing garage
- 2009 Honda Odyssey + 2018 Nissan Altima
- Prefers: wall storage, overhead storage, doesn't need floor completely clear
- Priorities: all rated 4/5 (balanced across vehicle/workspace/storage/accessibility)

---

*Document generated during vibe coding session - December 13, 2025*
