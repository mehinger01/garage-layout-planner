#!/usr/bin/env python3
"""
Garage Layout Planner - 3D Visualization Generator
Reads garage_layout.txt, garage_usage.json, and garage_recommendation.txt
Outputs an interactive 3D HTML visualization

Usage:
    python generate_3d_visualization.py

Output:
    garage_3d_view.html - Interactive 3D visualization
"""

import json
import re
import os
from dataclasses import dataclass, field
from typing import List, Dict, Tuple


# =============================================================================
# PARSING FUNCTIONS
# =============================================================================

def measurement_to_inches(text: str) -> float:
    """Convert various measurement formats to inches"""
    if not text:
        return 0.0
    
    text = str(text).strip().lower()
    
    # Already in inches with quote mark
    if text.endswith('"'):
        text = text[:-1]
        if "'" in text:
            parts = text.split("'")
            feet = float(parts[0]) if parts[0] else 0
            inches = float(parts[1]) if len(parts) > 1 and parts[1] else 0
            return feet * 12 + inches
        else:
            return float(text)
    
    # Feet with apostrophe
    if "'" in text:
        if '"' not in text:
            text = text.replace("'", "")
            return float(text) * 12
        parts = text.replace('"', '').split("'")
        feet = float(parts[0]) if parts[0] else 0
        inches = float(parts[1]) if len(parts) > 1 and parts[1] else 0
        return feet * 12 + inches
    
    # Check for fractions
    if '/' in text:
        parts = text.split()
        total = 0.0
        for part in parts:
            if '/' in part:
                num, denom = part.split('/')
                total += float(num) / float(denom)
            else:
                total += float(part)
        return total
    
    try:
        return float(text)
    except:
        return 0.0


def parse_position(pos_str: str) -> Tuple[float, float]:
    """Parse position string like '2' 6\" from W, 6' 2\" from N'"""
    x, y = 0.0, 0.0
    
    w_match = re.search(r"([\d'\".\s/]+)\s*from\s*W", pos_str, re.IGNORECASE)
    if w_match:
        x = measurement_to_inches(w_match.group(1).strip())
    
    n_match = re.search(r"([\d'\".\s/]+)\s*from\s*N", pos_str, re.IGNORECASE)
    if n_match:
        y = measurement_to_inches(n_match.group(1).strip())
    
    return x, y


def parse_size(size_str: str) -> Tuple[float, float]:
    """Parse size string like '8' 7\" x 18' 10\"'"""
    parts = re.split(r'\s*x\s*', size_str, flags=re.IGNORECASE)
    if len(parts) >= 2:
        width = measurement_to_inches(parts[0].strip())
        depth = measurement_to_inches(parts[1].strip())
        return width, depth
    return 0.0, 0.0


def parse_layout_file(filepath: str) -> Dict:
    """Parse garage_layout.txt"""
    data = {
        'width': 300, 'depth': 300, 'height': 120,
        'windows': [], 'entry_doors': [],
        'garage_door': {}, 'electrical_panel': {}
    }
    
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        dim_match = re.search(r"Dimensions:\s*([\d'\".\s]+)\s*\(E-W\)\s*x\s*([\d'\".\s]+)\s*\(N-S\)", content)
        if dim_match:
            data['width'] = measurement_to_inches(dim_match.group(1))
            data['depth'] = measurement_to_inches(dim_match.group(2))
        
        ceiling_match = re.search(r"Ceiling Height:\s*([\d'\".\s]+)", content)
        if ceiling_match:
            data['height'] = measurement_to_inches(ceiling_match.group(1))
        
        west_section = re.search(r"WEST WALL:(.*?)(?=EAST WALL:|$)", content, re.DOTALL | re.IGNORECASE)
        if west_section:
            windows = re.findall(r"Window at ([\d'\".\s]+)", west_section.group(1))
            for w in windows:
                data['windows'].append({
                    'wall': 'W', 'position': measurement_to_inches(w),
                    'width': 36, 'height': 36, 'fromFloor': 48
                })
        
        south_match = re.search(r"SOUTH WALL:.*?Garage Door at ([\d'\".\s]+)", content, re.DOTALL | re.IGNORECASE)
        if south_match:
            data['garage_door'] = {
                'wall': 'S', 'position': measurement_to_inches(south_match.group(1)),
                'width': 192, 'height': 84
            }
        
        east_section = re.search(r"EAST WALL:(.*?)(?=FLOOR|$)", content, re.DOTALL | re.IGNORECASE)
        if east_section:
            entry_match = re.search(r"Entry Door at ([\d'\".\s]+)", east_section.group(1))
            if entry_match:
                data['entry_doors'].append({
                    'wall': 'E', 'position': measurement_to_inches(entry_match.group(1)),
                    'width': 36, 'height': 80
                })
            
            elec_match = re.search(r"Electrical Panel at ([\d'\".\s]+)", east_section.group(1))
            if elec_match:
                data['electrical_panel'] = {
                    'wall': 'E', 'position': measurement_to_inches(elec_match.group(1)),
                    'width': 24, 'height': 36
                }
        
        north_match = re.search(r"NORTH WALL:.*?Service Door at ([\d'\".\s]+)", content, re.DOTALL | re.IGNORECASE)
        if north_match:
            data['entry_doors'].append({
                'wall': 'N', 'position': measurement_to_inches(north_match.group(1)),
                'width': 36, 'height': 80
            })
        
    except Exception as e:
        print(f"Warning: Could not parse layout file: {e}")
    
    return data


def parse_usage_file(filepath: str) -> Dict:
    """Parse garage_usage.json"""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Could not parse usage file: {e}")
        return {}


def parse_recommendation_file(filepath: str) -> List[Dict]:
    """Parse garage_recommendation.txt for zone placements"""
    zones = []
    
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        zones_match = re.search(r"ZONES PLACED\s*-+\s*(.*?)(?=REASONING|$)", content, re.DOTALL)
        if not zones_match:
            return zones
        
        zones_text = zones_match.group(1)
        zone_blocks = re.split(r'\n(?=\s{2}[A-Z0-9])', zones_text)
        
        vehicle_count = 0
        
        for block in zone_blocks:
            block = block.strip()
            if not block:
                continue
            
            lines = block.split('\n')
            name = lines[0].strip()
            
            if not name or name.startswith('-'):
                continue
            
            zone = {
                'name': name, 'x': 0, 'y': 0,
                'width': 48, 'depth': 48, 'height': 48,
                'wall': '', 'type': 'unknown'
            }
            
            for line in lines[1:]:
                line = line.strip()
                if line.startswith('Position:'):
                    zone['x'], zone['y'] = parse_position(line.replace('Position:', '').strip())
                elif line.startswith('Size:'):
                    zone['width'], zone['depth'] = parse_size(line.replace('Size:', '').strip())
                elif line.startswith('Wall:'):
                    zone['wall'] = line.replace('Wall:', '').strip()
            
            # Determine type
            name_lower = name.lower()
            if any(brand in name_lower for brand in ['honda', 'nissan', 'toyota', 'ford', 'chevy', 'chevrolet', 'hyundai', 'kia']) or \
               any(str(y) in name for y in range(1990, 2030)):
                zone['type'] = 'vehicle'
                zone['height'] = 69 if any(v in name_lower for v in ['odyssey', 'sienna', 'suv', 'pilot']) else 57
                zone['color'] = '0x3b82f6' if vehicle_count == 0 else '0x6366f1'
                zone['vehicleType'] = 'minivan' if any(v in name_lower for v in ['odyssey', 'sienna']) else 'sedan'
                vehicle_count += 1
            elif 'workbench' in name_lower:
                zone['type'] = 'workbench'
                zone['height'] = 36
                zone['color'] = '0xf59e0b'
            elif 'wall storage' in name_lower:
                zone['type'] = 'wall_storage'
                zone['height'] = 48
                zone['color'] = '0x22c55e'
            elif 'overhead' in name_lower:
                zone['type'] = 'overhead'
                zone['height'] = 12
                zone['heightFromFloor'] = 84
                zone['color'] = '0xa855f7'
            else:
                zone['type'] = 'floor_storage'
                zone['height'] = 36
                zone['color'] = '0x888888'
            
            zones.append(zone)
        
    except Exception as e:
        print(f"Warning: Could not parse recommendation file: {e}")
    
    return zones


# =============================================================================
# HTML GENERATION
# =============================================================================

def generate_html(garage_data: Dict, zones: List[Dict], usage_data: Dict) -> str:
    """Generate complete HTML file with embedded Three.js visualization"""
    
    zones_js = json.dumps(zones, indent=2)
    
    features = {
        'garageDoor': garage_data.get('garage_door', {'wall': 'S', 'position': 150, 'width': 192, 'height': 84}),
        'entryDoors': garage_data.get('entry_doors', []),
        'windows': garage_data.get('windows', []),
        'electricalPanel': garage_data.get('electrical_panel', {'wall': 'E', 'position': 240, 'width': 24, 'height': 36})
    }
    features_js = json.dumps(features, indent=2)
    
    vehicles = usage_data.get('vehicles', [])
    vehicle_names = [f"{v.get('year', '')} {v.get('make', '')} {v.get('model', '')}" for v in vehicles if v.get('must_fit_inside', True)]
    vehicle_str = ' + '.join(vehicle_names) if vehicle_names else 'No vehicles'
    
    width_ft = int(garage_data.get('width', 300) / 12)
    depth_ft = int(garage_data.get('depth', 300) / 12)
    height_ft = int(garage_data.get('height', 120) / 12)
    
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Garage 3D Layout</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #1a1a2e; color: white; overflow: hidden; }}
        .container {{ display: flex; flex-direction: column; height: 100vh; }}
        header {{ background: linear-gradient(to right, #1e293b, #0f172a); padding: 1rem 1.5rem; border-bottom: 1px solid #334155; display: flex; justify-content: space-between; align-items: center; }}
        header h1 {{ font-size: 1.5rem; display: flex; align-items: center; gap: 0.5rem; }}
        header h1 span {{ font-size: 0.9rem; font-weight: normal; color: #94a3b8; }}
        header p {{ color: #94a3b8; font-size: 0.85rem; }}
        .score {{ text-align: right; }}
        .score-label {{ font-size: 0.8rem; color: #94a3b8; }}
        .score-value {{ font-size: 1.5rem; font-weight: bold; color: #4ade80; }}
        .main {{ flex: 1; display: flex; overflow: hidden; }}
        #canvas-container {{ flex: 1; cursor: grab; position: relative; }}
        #canvas-container:active {{ cursor: grabbing; }}
        .tooltip {{ position: absolute; top: 1rem; left: 1rem; background: rgba(0,0,0,0.85); padding: 0.5rem 1rem; border-radius: 0.5rem; pointer-events: none; display: none; }}
        .tooltip.visible {{ display: block; }}
        .tooltip .name {{ font-weight: 600; }}
        .tooltip .hint {{ font-size: 0.75rem; color: #94a3b8; }}
        .sidebar {{ width: 320px; background: #1e293b; border-left: 1px solid #334155; display: flex; flex-direction: column; overflow: hidden; }}
        .sidebar-section {{ padding: 1rem; border-bottom: 1px solid #334155; }}
        .sidebar-section h3 {{ font-size: 0.95rem; margin-bottom: 0.75rem; display: flex; align-items: center; gap: 0.5rem; }}
        .view-buttons {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.5rem; }}
        .view-btn {{ padding: 0.5rem; border: none; border-radius: 0.375rem; font-size: 0.75rem; font-weight: 500; cursor: pointer; transition: all 0.2s; background: #334155; color: #e2e8f0; }}
        .view-btn:hover {{ background: #475569; }}
        .view-btn.active {{ background: #2563eb; color: white; }}
        .hint-text {{ font-size: 0.7rem; color: #64748b; margin-top: 0.5rem; }}
        .filter-list {{ display: flex; flex-direction: column; gap: 0.5rem; }}
        .filter-btn {{ display: flex; align-items: center; gap: 0.75rem; padding: 0.5rem 0.75rem; background: #334155; border: none; border-radius: 0.375rem; color: white; cursor: pointer; transition: all 0.2s; text-align: left; }}
        .filter-btn:hover {{ background: #475569; }}
        .filter-btn.hidden {{ background: #0f172a; color: #64748b; }}
        .filter-dot {{ width: 1rem; height: 1rem; border-radius: 0.25rem; }}
        .filter-btn.hidden .filter-dot {{ background: #475569 !important; }}
        .filter-label {{ flex: 1; font-size: 0.875rem; }}
        .filter-check {{ font-size: 0.75rem; }}
        .detail-box {{ background: #334155; border-radius: 0.5rem; padding: 1rem; }}
        .detail-box .name {{ font-size: 1.1rem; font-weight: 600; }}
        .detail-box .type {{ font-size: 0.85rem; color: #94a3b8; margin-top: 0.25rem; }}
        .detail-box .divider {{ border-top: 1px solid #475569; margin: 0.75rem 0; }}
        .detail-row {{ display: flex; justify-content: space-between; font-size: 0.85rem; margin-bottom: 0.25rem; }}
        .detail-row .label {{ color: #94a3b8; }}
        .detail-placeholder {{ background: rgba(15,23,42,0.5); border-radius: 0.5rem; padding: 1rem; text-align: center; color: #64748b; font-size: 0.875rem; }}
        .zone-list {{ flex: 1; overflow-y: auto; padding: 1rem; }}
        .zone-list h3 {{ margin-bottom: 0.75rem; }}
        .zone-list-items {{ display: flex; flex-direction: column; gap: 0.25rem; }}
        .zone-item {{ display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem 0.75rem; border-radius: 0.375rem; font-size: 0.85rem; color: #94a3b8; cursor: pointer; transition: all 0.2s; border: none; background: transparent; text-align: left; width: 100%; }}
        .zone-item:hover {{ background: #334155; color: white; }}
        .zone-item.selected {{ background: #2563eb; color: white; }}
        .zone-item .icon {{ flex-shrink: 0; }}
        .zone-item .name {{ flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
        footer {{ background: #1e293b; padding: 0.5rem 1rem; border-top: 1px solid #334155; display: flex; justify-content: space-between; font-size: 0.75rem; color: #64748b; }}
        .footer-stats {{ display: flex; gap: 1rem; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div>
                <h1>🏠 Garage Layout <span>3D View</span></h1>
                <p>{width_ft}' × {depth_ft}' × {height_ft}' ceiling • {vehicle_str}</p>
            </div>
            <div class="score">
                <div class="score-label">Layout Score</div>
                <div class="score-value">60/100</div>
            </div>
        </header>
        <div class="main">
            <div id="canvas-container">
                <div class="tooltip" id="tooltip">
                    <div class="name" id="tooltip-name"></div>
                    <div class="hint">Click to select</div>
                </div>
            </div>
            <div class="sidebar">
                <div class="sidebar-section">
                    <h3>🎥 Camera View</h3>
                    <div class="view-buttons">
                        <button class="view-btn active" data-view="corner">Corner</button>
                        <button class="view-btn" data-view="top">Top</button>
                        <button class="view-btn" data-view="front">Front</button>
                        <button class="view-btn" data-view="side">Side</button>
                    </div>
                    <p class="hint-text">🖱️ Drag to rotate • Scroll to zoom • Click to select</p>
                </div>
                <div class="sidebar-section">
                    <h3>👁️ Show/Hide</h3>
                    <div class="filter-list" id="filter-list"></div>
                </div>
                <div class="sidebar-section">
                    <h3>📍 Selected Zone</h3>
                    <div id="detail-container">
                        <div class="detail-placeholder">Click on any zone to see details</div>
                    </div>
                </div>
                <div class="zone-list">
                    <h3>📋 All Zones (<span id="zone-count">0</span>)</h3>
                    <div class="zone-list-items" id="zone-list"></div>
                </div>
            </div>
        </div>
        <footer>
            <div class="footer-stats" id="footer-stats"></div>
            <div>Garage Layout Planner v1.0</div>
        </footer>
    </div>
    <script>
const GARAGE = {{ width: {garage_data.get('width', 300)}, depth: {garage_data.get('depth', 300)}, height: {garage_data.get('height', 120)}, features: {features_js}, zones: {zones_js} }};
const SCALE = 0.02;
const ZONE_TYPES = {{ vehicle: {{ color: '#3b82f6', label: 'Vehicles', icon: '🚗' }}, workbench: {{ color: '#f59e0b', label: 'Workbench', icon: '🔧' }}, wall_storage: {{ color: '#22c55e', label: 'Wall Storage', icon: '📦' }}, overhead: {{ color: '#a855f7', label: 'Overhead', icon: '⬆️' }}, floor_storage: {{ color: '#888888', label: 'Floor Storage', icon: '📦' }} }};
let scene, camera, renderer, selectedZone = null, hoveredZone = null, zoneMeshes = [];
let visibleTypes = {{ vehicle: true, workbench: true, wall_storage: true, overhead: true, floor_storage: true }};
let cameraAngle = {{ theta: Math.PI/4, phi: Math.PI/4, distance: 15 }};
let mouse = {{ isDown: false, lastX: 0, lastY: 0 }};
const raycaster = new THREE.Raycaster(), mouseVec = new THREE.Vector2();

function init() {{
    const container = document.getElementById('canvas-container');
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x1e1e2e);
    scene.fog = new THREE.Fog(0x1e1e2e, 20, 40);
    camera = new THREE.PerspectiveCamera(50, container.clientWidth / container.clientHeight, 0.1, 1000);
    updateCameraPosition();
    renderer = new THREE.WebGLRenderer({{ antialias: true }});
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.shadowMap.enabled = true;
    container.appendChild(renderer.domElement);
    scene.add(new THREE.AmbientLight(0xffffff, 0.3));
    const mainLight = new THREE.PointLight(0xfff5e6, 1, 20);
    mainLight.position.set(GARAGE.width * SCALE / 2, GARAGE.height * SCALE - 0.5, GARAGE.depth * SCALE / 2);
    scene.add(mainLight);
    scene.add(new THREE.DirectionalLight(0xffffff, 0.4).translateX(10).translateY(10).translateZ(10));
    buildGarage();
    setupUI();
    container.addEventListener('mousedown', e => {{ if (e.button === 0) {{ mouse.isDown = true; mouse.lastX = e.clientX; mouse.lastY = e.clientY; }} }});
    container.addEventListener('mouseup', () => mouse.isDown = false);
    container.addEventListener('mouseleave', () => mouse.isDown = false);
    container.addEventListener('mousemove', onMouseMove);
    container.addEventListener('click', onClick);
    container.addEventListener('wheel', e => {{ e.preventDefault(); cameraAngle.distance = Math.max(5, Math.min(30, cameraAngle.distance + e.deltaY * 0.01)); updateCameraPosition(); }}, {{ passive: false }});
    window.addEventListener('resize', () => {{ camera.aspect = container.clientWidth / container.clientHeight; camera.updateProjectionMatrix(); renderer.setSize(container.clientWidth, container.clientHeight); }});
    (function animate() {{ requestAnimationFrame(animate); renderer.render(scene, camera); }})();
}}

function updateCameraPosition() {{
    const {{ theta, phi, distance }} = cameraAngle;
    const cx = GARAGE.width * SCALE / 2, cz = GARAGE.depth * SCALE / 2, cy = GARAGE.height * SCALE / 2;
    camera.position.set(cx + distance * Math.sin(phi) * Math.cos(theta), cy + distance * Math.cos(phi), cz + distance * Math.sin(phi) * Math.sin(theta));
    camera.lookAt(cx, cy * 0.3, cz);
}}

function buildGarage() {{
    const W = GARAGE.width * SCALE, D = GARAGE.depth * SCALE, H = GARAGE.height * SCALE;
    const floor = new THREE.Mesh(new THREE.PlaneGeometry(W, D), new THREE.MeshStandardMaterial({{ color: 0x404040, roughness: 0.9 }}));
    floor.rotation.x = -Math.PI / 2; floor.position.set(W/2, 0, D/2); floor.receiveShadow = true; scene.add(floor);
    const grid = new THREE.GridHelper(Math.max(W, D), 50, 0x333333, 0x282828); grid.position.set(W/2, 0.005, D/2); scene.add(grid);
    const wallMat = new THREE.MeshStandardMaterial({{ color: 0x909090, transparent: true, opacity: 0.12, side: THREE.DoubleSide }});
    [[W/2, H/2, 0, 0], [W/2, H/2, D, Math.PI], [W, H/2, D/2, -Math.PI/2], [0, H/2, D/2, Math.PI/2]].forEach(([x, y, z, ry], i) => {{
        const isNS = i < 2;
        const wall = new THREE.Mesh(new THREE.PlaneGeometry(isNS ? W : D, H), wallMat);
        wall.position.set(x, y, z); wall.rotation.y = ry; scene.add(wall);
    }});
    const edgeMat = new THREE.LineBasicMaterial({{ color: 0x666666 }});
    [[[0,0,0],[W,0,0]],[[W,0,0],[W,0,D]],[[W,0,D],[0,0,D]],[[0,0,D],[0,0,0]],[[0,H,0],[W,H,0]],[[W,H,0],[W,H,D]],[[W,H,D],[0,H,D]],[[0,H,D],[0,H,0]],[[0,0,0],[0,H,0]],[[W,0,0],[W,H,0]],[[W,0,D],[W,H,D]],[[0,0,D],[0,H,D]]].forEach(([s, e]) => {{
        scene.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(...s), new THREE.Vector3(...e)]), edgeMat));
    }});
    if (GARAGE.features.garageDoor) {{
        const gd = GARAGE.features.garageDoor, gdW = (gd.width || 192) * SCALE, gdH = (gd.height || 84) * SCALE, gdX = (GARAGE.width/2 - (gd.width||192)/2) * SCALE;
        const gdMesh = new THREE.Mesh(new THREE.BoxGeometry(gdW, gdH, 0.08), new THREE.MeshStandardMaterial({{ color: 0xf5f5f5 }}));
        gdMesh.position.set(gdX + gdW/2, gdH/2, D - 0.04); scene.add(gdMesh);
    }}
    (GARAGE.features.windows || []).forEach(win => {{
        const glass = new THREE.Mesh(new THREE.PlaneGeometry((win.height||36)*SCALE, (win.width||36)*SCALE), new THREE.MeshStandardMaterial({{ color: 0x87ceeb, transparent: true, opacity: 0.5 }}));
        glass.rotation.y = Math.PI/2; glass.rotation.z = Math.PI/2; glass.position.set(0.02, (win.fromFloor||48)*SCALE + (win.height||36)*SCALE/2, (win.position||0)*SCALE); scene.add(glass);
    }});
    ['N','S','E','W'].forEach((dir, i) => {{
        const canvas = document.createElement('canvas'); canvas.width = 128; canvas.height = 128;
        const ctx = canvas.getContext('2d'); ctx.beginPath(); ctx.arc(64,64,50,0,Math.PI*2); ctx.fillStyle = 'rgba(0,0,0,0.5)'; ctx.fill();
        ctx.fillStyle = ['#ff6b6b','#4ecdc4','#ffe66d','#95e1d3'][i]; ctx.font = 'bold 64px Arial'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(dir, 64, 64);
        const sprite = new THREE.Sprite(new THREE.SpriteMaterial({{ map: new THREE.CanvasTexture(canvas) }}));
        sprite.position.set(...[[W/2,H+0.4,-0.6],[W/2,H+0.4,D+0.6],[W+0.6,H+0.4,D/2],[-0.6,H+0.4,D/2]][i]); sprite.scale.set(0.6,0.6,0.6); scene.add(sprite);
    }});
    GARAGE.zones.forEach(zone => {{ const mesh = createZoneMesh(zone); scene.add(mesh); zoneMeshes.push({{ mesh, data: zone }}); }});
}}

function createZoneMesh(zone) {{
    const w = (zone.width||48)*SCALE, d = (zone.depth||48)*SCALE, h = (zone.height||48)*SCALE;
    const x = (zone.x||0)*SCALE, z = (zone.y||0)*SCALE, y = (zone.heightFromFloor||0)*SCALE;
    const color = parseInt(zone.color || '0x888888');
    const group = new THREE.Group();
    
    if (zone.type === 'vehicle') {{
        const isMinivan = zone.vehicleType === 'minivan';
        const body = new THREE.Mesh(new THREE.BoxGeometry(w, h*0.4, d*0.92), new THREE.MeshStandardMaterial({{ color, metalness: 0.8, roughness: 0.3 }}));
        body.position.y = h*0.2; body.castShadow = true; group.add(body);
        const cabinH = isMinivan ? h*0.55 : h*0.4, cabinD = isMinivan ? d*0.7 : d*0.5;
        const cabin = new THREE.Mesh(new THREE.BoxGeometry(w*0.9, cabinH, cabinD), new THREE.MeshStandardMaterial({{ color: 0x1a1a1a, transparent: true, opacity: 0.85 }}));
        cabin.position.set(0, h*0.4 + cabinH/2, isMinivan ? -d*0.05 : -d*0.1); group.add(cabin);
        const wheelGeom = new THREE.CylinderGeometry(h*0.22, h*0.22, w*0.08, 16), wheelMat = new THREE.MeshStandardMaterial({{ color: 0x1a1a1a }});
        [[-w/2,d*0.32],[w/2,d*0.32],[-w/2,-d*0.32],[w/2,-d*0.32]].forEach(([wx,wz]) => {{
            const wheel = new THREE.Mesh(wheelGeom, wheelMat); wheel.rotation.z = Math.PI/2; wheel.position.set(wx*0.95, h*0.22, wz); group.add(wheel);
        }});
        const hlGeom = new THREE.CircleGeometry(h*0.1, 16), hlMat = new THREE.MeshStandardMaterial({{ color: 0xffffcc, emissive: 0xffffcc, emissiveIntensity: 0.3 }});
        [[-w*0.35,d/2-0.01],[w*0.35,d/2-0.01]].forEach(([hx,hz]) => {{ const hl = new THREE.Mesh(hlGeom, hlMat); hl.position.set(hx, h*0.25, hz); group.add(hl); }});
        group.position.set(x + w/2, 0, z + d/2);
    }} else if (zone.type === 'workbench') {{
        const top = new THREE.Mesh(new THREE.BoxGeometry(w, 0.06, d), new THREE.MeshStandardMaterial({{ color }})); top.position.y = h; top.castShadow = true; group.add(top);
        const legGeom = new THREE.BoxGeometry(0.06, h, 0.06), legMat = new THREE.MeshStandardMaterial({{ color: 0x333333 }});
        [[-w/2+0.05,-d/2+0.05],[w/2-0.05,-d/2+0.05],[-w/2+0.05,d/2-0.05],[w/2-0.05,d/2-0.05]].forEach(([lx,lz]) => {{ const leg = new THREE.Mesh(legGeom, legMat); leg.position.set(lx, h/2, lz); group.add(leg); }});
        const peg = new THREE.Mesh(new THREE.BoxGeometry(w, h*0.8, 0.03), new THREE.MeshStandardMaterial({{ color: 0xc4a574 }})); peg.position.set(0, h*1.4, -d/2+0.02); group.add(peg);
        group.position.set(x + w/2, 0, z + d/2);
    }} else if (zone.type === 'overhead') {{
        const plat = new THREE.Mesh(new THREE.BoxGeometry(w, 0.05, d), new THREE.MeshStandardMaterial({{ color, transparent: true, opacity: 0.85 }})); plat.castShadow = true; group.add(plat);
        const chainH = GARAGE.height*SCALE - y - h/2, chainGeom = new THREE.CylinderGeometry(0.015,0.015,chainH), chainMat = new THREE.MeshStandardMaterial({{ color: 0x555555 }});
        [[-w/2+0.1,-d/2+0.1],[w/2-0.1,-d/2+0.1],[-w/2+0.1,d/2-0.1],[w/2-0.1,d/2-0.1]].forEach(([cx,cz]) => {{ const chain = new THREE.Mesh(chainGeom, chainMat); chain.position.set(cx, chainH/2, cz); group.add(chain); }});
        const binColors = [0x3b82f6, 0xef4444, 0x22c55e], binCount = Math.min(3, Math.floor(w/0.4));
        for (let i = 0; i < binCount; i++) {{ const bin = new THREE.Mesh(new THREE.BoxGeometry(w/binCount*0.7, 0.15, d*0.6), new THREE.MeshStandardMaterial({{ color: binColors[i%3] }})); bin.position.set(-w/2 + w/binCount*(i+0.5), 0.1, 0); group.add(bin); }}
        group.position.set(x + w/2, y + h/2, z + d/2);
    }} else {{
        const mesh = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), new THREE.MeshStandardMaterial({{ color, transparent: true, opacity: 0.8 }})); mesh.castShadow = true; group.add(mesh);
        const heightOffset = zone.type === 'wall_storage' ? 24*SCALE : 0;
        group.position.set(x + w/2, heightOffset + h/2, z + d/2);
    }}
    group.userData = {{ zone }};
    return group;
}}

function setupUI() {{
    const filterList = document.getElementById('filter-list');
    Object.entries(ZONE_TYPES).forEach(([type, info]) => {{
        if (!GARAGE.zones.some(z => z.type === type)) return;
        const btn = document.createElement('button'); btn.className = 'filter-btn'; btn.dataset.type = type;
        btn.innerHTML = `<div class="filter-dot" style="background: ${{info.color}}"></div><span class="filter-label">${{info.icon}} ${{info.label}}</span><span class="filter-check">✓</span>`;
        btn.onclick = () => toggleType(type); filterList.appendChild(btn);
    }});
    updateZoneList(); updateFooterStats();
    document.querySelectorAll('.view-btn').forEach(btn => {{ btn.onclick = () => setView(btn.dataset.view); }});
}}

function updateZoneList() {{
    const list = document.getElementById('zone-list'); list.innerHTML = '';
    const visibleZones = GARAGE.zones.filter(z => visibleTypes[z.type]);
    document.getElementById('zone-count').textContent = visibleZones.length;
    visibleZones.forEach(zone => {{
        const info = ZONE_TYPES[zone.type] || {{ icon: '📦' }};
        const btn = document.createElement('button'); btn.className = 'zone-item' + (selectedZone?.name === zone.name ? ' selected' : '');
        btn.innerHTML = `<span class="icon">${{info.icon}}</span><span class="name">${{zone.name}}</span>`;
        btn.onclick = () => selectZone(zone); list.appendChild(btn);
    }});
}}

function updateFooterStats() {{
    const stats = document.getElementById('footer-stats'), counts = {{}};
    GARAGE.zones.forEach(z => {{ counts[z.type] = (counts[z.type] || 0) + 1; }});
    stats.innerHTML = Object.entries(counts).map(([type, count]) => {{ const info = ZONE_TYPES[type] || {{ icon: '📦', label: type }}; return `<span>${{info.icon}} ${{count}} ${{info.label}}</span>`; }}).join('');
}}

function toggleType(type) {{
    visibleTypes[type] = !visibleTypes[type];
    zoneMeshes.forEach(({{ mesh, data }}) => {{ mesh.visible = visibleTypes[data.type]; }});
    document.querySelectorAll('.filter-btn').forEach(btn => {{ if (btn.dataset.type === type) btn.classList.toggle('hidden', !visibleTypes[type]); }});
    updateZoneList();
}}

function setView(view) {{
    const views = {{ corner: {{ theta: Math.PI/4, phi: Math.PI/4, distance: 15 }}, top: {{ theta: 0, phi: 0.1, distance: 15 }}, front: {{ theta: 0, phi: Math.PI/2-0.1, distance: 15 }}, side: {{ theta: Math.PI/2, phi: Math.PI/3, distance: 15 }} }};
    cameraAngle = views[view] || views.corner; updateCameraPosition();
    document.querySelectorAll('.view-btn').forEach(btn => {{ btn.classList.toggle('active', btn.dataset.view === view); }});
}}

function selectZone(zone) {{ selectedZone = zone; updateDetailPanel(); updateZoneList(); }}

function updateDetailPanel() {{
    const container = document.getElementById('detail-container');
    if (!selectedZone) {{ container.innerHTML = '<div class="detail-placeholder">Click on any zone to see details</div>'; return; }}
    const info = ZONE_TYPES[selectedZone.type] || {{ icon: '📦', label: selectedZone.type }};
    const fmt = (inches) => {{ const f = Math.floor(inches/12), r = Math.round(inches%12); return r === 0 ? `${{f}}'` : `${{f}}'${{r}}"`; }};
    container.innerHTML = `<div class="detail-box"><div class="name">${{selectedZone.name}}</div><div class="type">${{info.icon}} ${{info.label}}</div><div class="divider"></div>
    <div class="detail-row"><span class="label">Width:</span><span>${{fmt(selectedZone.width||0)}}</span></div>
    <div class="detail-row"><span class="label">Depth:</span><span>${{fmt(selectedZone.depth||0)}}</span></div>
    ${{selectedZone.height ? `<div class="detail-row"><span class="label">Height:</span><span>${{fmt(selectedZone.height)}}</span></div>` : ''}}
    <div class="detail-row"><span class="label">Position:</span><span>${{fmt(selectedZone.x||0)}} from W, ${{fmt(selectedZone.y||0)}} from N</span></div></div>`;
}}

function onMouseMove(e) {{
    const container = document.getElementById('canvas-container'), rect = container.getBoundingClientRect();
    mouseVec.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
    mouseVec.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
    raycaster.setFromCamera(mouseVec, camera);
    let found = null;
    for (const hit of raycaster.intersectObjects(scene.children, true)) {{
        let obj = hit.object;
        while (obj) {{ if (obj.userData?.zone) {{ found = obj.userData.zone; break; }} obj = obj.parent; }}
        if (found) break;
    }}
    const tooltip = document.getElementById('tooltip');
    if (found && !selectedZone) {{ document.getElementById('tooltip-name').textContent = found.name; tooltip.classList.add('visible'); }} else {{ tooltip.classList.remove('visible'); }}
    hoveredZone = found;
    if (mouse.isDown) {{
        cameraAngle.theta += (e.clientX - mouse.lastX) * 0.01;
        cameraAngle.phi = Math.max(0.1, Math.min(Math.PI/2 - 0.1, cameraAngle.phi + (e.clientY - mouse.lastY) * 0.01));
        mouse.lastX = e.clientX; mouse.lastY = e.clientY; updateCameraPosition();
    }}
}}

function onClick() {{ if (hoveredZone) selectZone(hoveredZone); else selectZone(null); }}

init();
    </script>
</body>
</html>'''


# =============================================================================
# MAIN
# =============================================================================

def main():
    layout_file = 'garage_layout.txt'
    usage_file = 'garage_usage.json'
    recommendation_file = 'garage_recommendation.txt'
    output_file = 'garage_3d_view.html'
    
    print("=" * 60)
    print("     GARAGE 3D VISUALIZATION GENERATOR")
    print("=" * 60)
    print()
    
    if not os.path.exists(layout_file):
        print(f"Warning: {layout_file} not found. Using defaults.")
        garage_data = {'width': 300, 'depth': 300, 'height': 120}
    else:
        print(f"Reading {layout_file}...")
        garage_data = parse_layout_file(layout_file)
    
    if not os.path.exists(usage_file):
        print(f"Warning: {usage_file} not found.")
        usage_data = {}
    else:
        print(f"Reading {usage_file}...")
        usage_data = parse_usage_file(usage_file)
    
    if not os.path.exists(recommendation_file):
        print(f"Warning: {recommendation_file} not found.")
        zones = []
    else:
        print(f"Reading {recommendation_file}...")
        zones = parse_recommendation_file(recommendation_file)
    
    print()
    print(f"Garage: {int(garage_data.get('width', 300)/12)}' x {int(garage_data.get('depth', 300)/12)}' x {int(garage_data.get('height', 120)/12)}' ceiling")
    print(f"Zones found: {len(zones)}")
    
    type_counts = {}
    for z in zones:
        t = z.get('type', 'unknown')
        type_counts[t] = type_counts.get(t, 0) + 1
    
    for t, count in sorted(type_counts.items()):
        print(f"  - {t}: {count}")
    
    print()
    print(f"Generating {output_file}...")
    
    html = generate_html(garage_data, zones, usage_data)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print()
    print("=" * 60)
    print(f"  ✓ 3D visualization saved to: {output_file}")
    print("  Open in a web browser to view your garage layout!")
    print("=" * 60)


if __name__ == '__main__':
    main()
