import React, { useRef, useEffect, useState, useCallback } from 'react';
import * as THREE from 'three';

// Garage data from Mike's recommendation
const GARAGE = {
  width: 25 * 12,   // 25' in inches
  depth: 25 * 12,   // 25' in inches  
  height: 146,      // 12'2" in inches
  
  features: {
    garageDoor: { wall: 'S', position: 150, width: 192, height: 84 },
    serviceDoor: { wall: 'N', position: 150, width: 36, height: 80 },
    entryDoor: { wall: 'E', position: 72, width: 36, height: 80 },
    windows: [
      { wall: 'W', position: 62, width: 36, height: 36, fromFloor: 48 },
      { wall: 'W', position: 158, width: 36, height: 36, fromFloor: 48 }
    ],
    electricalPanel: { wall: 'E', position: 240, width: 24, height: 36 }
  },
  
  zones: [
    // Vehicles
    { type: 'vehicle', name: '2009 Honda Odyssey', x: 30, y: 74, width: 103, depth: 226, height: 69, color: 0x3b82f6, vehicleType: 'minivan' },
    { type: 'vehicle', name: '2018 Nissan Altima', x: 145, y: 84, width: 96, depth: 216, height: 57, color: 0x6366f1, vehicleType: 'sedan' },
    
    // Workbench
    { type: 'workbench', name: 'Workbench (8ft)', x: 30, y: 0, width: 96, depth: 66, height: 36, color: 0xf59e0b },
    
    // Wall Storage - North wall
    { type: 'wall_storage', name: 'Wall Storage N1', x: 144, y: 0, width: 48, depth: 18, height: 48, color: 0x22c55e, wall: 'N' },
    { type: 'wall_storage', name: 'Wall Storage N2', x: 192, y: 0, width: 48, depth: 18, height: 48, color: 0x22c55e, wall: 'N' },
    
    // Wall Storage - East wall
    { type: 'wall_storage', name: 'Wall Storage E1', x: 282, y: 0, width: 18, depth: 48, height: 48, color: 0x22c55e, wall: 'E' },
    { type: 'wall_storage', name: 'Wall Storage E2', x: 282, y: 96, width: 18, depth: 48, height: 48, color: 0x22c55e, wall: 'E' },
    { type: 'wall_storage', name: 'Wall Storage E3', x: 282, y: 120, width: 18, depth: 48, height: 48, color: 0x22c55e, wall: 'E' },
    { type: 'wall_storage', name: 'Wall Storage E4', x: 282, y: 144, width: 18, depth: 48, height: 48, color: 0x22c55e, wall: 'E' },
    { type: 'wall_storage', name: 'Wall Storage E5', x: 282, y: 168, width: 18, depth: 48, height: 48, color: 0x22c55e, wall: 'E' },
    
    // Wall Storage - West wall
    { type: 'wall_storage', name: 'Wall Storage W1', x: 0, y: 84, width: 18, depth: 48, height: 48, color: 0x22c55e, wall: 'W' },
    { type: 'wall_storage', name: 'Wall Storage W2', x: 0, y: 192, width: 18, depth: 48, height: 48, color: 0x22c55e, wall: 'W' },
    { type: 'wall_storage', name: 'Wall Storage W3', x: 0, y: 216, width: 18, depth: 48, height: 48, color: 0x22c55e, wall: 'W' },
    { type: 'wall_storage', name: 'Wall Storage W4', x: 0, y: 240, width: 18, depth: 48, height: 48, color: 0x22c55e, wall: 'W' },
    
    // Overhead Storage
    { type: 'overhead', name: 'Overhead - North', x: 150, y: 0, width: 126, depth: 48, height: 12, heightFromFloor: 84, color: 0xa855f7 },
    { type: 'overhead', name: 'Overhead - West', x: 0, y: 72, width: 48, depth: 50, height: 12, heightFromFloor: 84, color: 0xa855f7 },
    { type: 'overhead', name: 'Overhead - East', x: 252, y: 48, width: 48, depth: 96, height: 12, heightFromFloor: 84, color: 0xa855f7 },
  ]
};

const SCALE = 0.02;

// Texture generators
function createConcreteTexture() {
  const canvas = document.createElement('canvas');
  canvas.width = 256;
  canvas.height = 256;
  const ctx = canvas.getContext('2d');
  
  ctx.fillStyle = '#4a4a4a';
  ctx.fillRect(0, 0, 256, 256);
  
  // Add noise
  for (let i = 0; i < 5000; i++) {
    const x = Math.random() * 256;
    const y = Math.random() * 256;
    const gray = 60 + Math.random() * 30;
    ctx.fillStyle = `rgb(${gray}, ${gray}, ${gray})`;
    ctx.fillRect(x, y, 2, 2);
  }
  
  // Add cracks
  ctx.strokeStyle = '#3a3a3a';
  ctx.lineWidth = 1;
  for (let i = 0; i < 3; i++) {
    ctx.beginPath();
    ctx.moveTo(Math.random() * 256, Math.random() * 256);
    for (let j = 0; j < 5; j++) {
      ctx.lineTo(Math.random() * 256, Math.random() * 256);
    }
    ctx.stroke();
  }
  
  return new THREE.CanvasTexture(canvas);
}

function createWoodTexture() {
  const canvas = document.createElement('canvas');
  canvas.width = 128;
  canvas.height = 128;
  const ctx = canvas.getContext('2d');
  
  ctx.fillStyle = '#8B4513';
  ctx.fillRect(0, 0, 128, 128);
  
  // Wood grain
  ctx.strokeStyle = '#6B3510';
  ctx.lineWidth = 2;
  for (let i = 0; i < 20; i++) {
    ctx.beginPath();
    ctx.moveTo(0, i * 7 + Math.random() * 3);
    ctx.bezierCurveTo(40, i * 7 + Math.random() * 5, 80, i * 7 - Math.random() * 5, 128, i * 7 + Math.random() * 3);
    ctx.stroke();
  }
  
  return new THREE.CanvasTexture(canvas);
}

function createPegboardTexture() {
  const canvas = document.createElement('canvas');
  canvas.width = 128;
  canvas.height = 128;
  const ctx = canvas.getContext('2d');
  
  ctx.fillStyle = '#c4a574';
  ctx.fillRect(0, 0, 128, 128);
  
  // Holes
  ctx.fillStyle = '#2a2a2a';
  for (let x = 8; x < 128; x += 16) {
    for (let y = 8; y < 128; y += 16) {
      ctx.beginPath();
      ctx.arc(x, y, 3, 0, Math.PI * 2);
      ctx.fill();
    }
  }
  
  return new THREE.CanvasTexture(canvas);
}

function createFrenchCleatTexture() {
  const canvas = document.createElement('canvas');
  canvas.width = 64;
  canvas.height = 128;
  const ctx = canvas.getContext('2d');
  
  ctx.fillStyle = '#deb887';
  ctx.fillRect(0, 0, 64, 128);
  
  // Angled slats
  ctx.fillStyle = '#c4a060';
  for (let y = 0; y < 128; y += 24) {
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(64, y);
    ctx.lineTo(64, y + 12);
    ctx.lineTo(0, y + 8);
    ctx.closePath();
    ctx.fill();
  }
  
  return new THREE.CanvasTexture(canvas);
}

function createGarageDoorTexture() {
  const canvas = document.createElement('canvas');
  canvas.width = 256;
  canvas.height = 128;
  const ctx = canvas.getContext('2d');
  
  ctx.fillStyle = '#f5f5f5';
  ctx.fillRect(0, 0, 256, 128);
  
  // Panels
  ctx.strokeStyle = '#ccc';
  ctx.lineWidth = 3;
  for (let y = 0; y < 128; y += 32) {
    ctx.strokeRect(4, y + 4, 120, 24);
    ctx.strokeRect(132, y + 4, 120, 24);
  }
  
  // Windows on top panel
  ctx.fillStyle = '#87ceeb';
  ctx.fillRect(20, 8, 30, 16);
  ctx.fillRect(60, 8, 30, 16);
  ctx.fillRect(166, 8, 30, 16);
  ctx.fillRect(206, 8, 30, 16);
  
  return new THREE.CanvasTexture(canvas);
}

export default function Garage3DViewer() {
  const containerRef = useRef(null);
  const sceneRef = useRef(null);
  const rendererRef = useRef(null);
  const cameraRef = useRef(null);
  const [selectedZone, setSelectedZone] = useState(null);
  const [hoveredZone, setHoveredZone] = useState(null);
  const [viewMode, setViewMode] = useState('corner');
  const [visibleTypes, setVisibleTypes] = useState({
    vehicle: true,
    workbench: true,
    wall_storage: true,
    overhead: true
  });
  const mouseRef = useRef({ isDown: false, lastX: 0, lastY: 0 });
  const cameraAngleRef = useRef({ theta: Math.PI / 4, phi: Math.PI / 4, distance: 15 });
  const raycasterRef = useRef(new THREE.Raycaster());
  const mouseVecRef = useRef(new THREE.Vector2());
  const zoneMeshesRef = useRef([]);
  const outlineMeshRef = useRef(null);

  const updateCameraPosition = useCallback(() => {
    if (!cameraRef.current) return;
    const { theta, phi, distance } = cameraAngleRef.current;
    const camera = cameraRef.current;
    
    const centerX = (GARAGE.width * SCALE) / 2;
    const centerZ = (GARAGE.depth * SCALE) / 2;
    const centerY = (GARAGE.height * SCALE) / 2;
    
    camera.position.x = centerX + distance * Math.sin(phi) * Math.cos(theta);
    camera.position.y = centerY + distance * Math.cos(phi);
    camera.position.z = centerZ + distance * Math.sin(phi) * Math.sin(theta);
    camera.lookAt(centerX, centerY * 0.3, centerZ);
  }, []);

  useEffect(() => {
    if (!containerRef.current) return;
    
    // Scene setup
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x1e1e2e);
    scene.fog = new THREE.Fog(0x1e1e2e, 20, 40);
    sceneRef.current = scene;
    
    // Camera
    const camera = new THREE.PerspectiveCamera(50, containerRef.current.clientWidth / containerRef.current.clientHeight, 0.1, 1000);
    cameraRef.current = camera;
    updateCameraPosition();
    
    // Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(containerRef.current.clientWidth, containerRef.current.clientHeight);
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.2;
    containerRef.current.appendChild(renderer.domElement);
    rendererRef.current = renderer;
    
    // Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.3);
    scene.add(ambientLight);
    
    // Main light (simulating garage light)
    const mainLight = new THREE.PointLight(0xfff5e6, 1, 20);
    mainLight.position.set(GARAGE.width * SCALE / 2, GARAGE.height * SCALE - 0.5, GARAGE.depth * SCALE / 2);
    mainLight.castShadow = true;
    scene.add(mainLight);
    
    // Secondary lights
    const fillLight1 = new THREE.DirectionalLight(0xffffff, 0.4);
    fillLight1.position.set(10, 10, 10);
    fillLight1.castShadow = true;
    scene.add(fillLight1);
    
    const fillLight2 = new THREE.DirectionalLight(0x8888ff, 0.2);
    fillLight2.position.set(-5, 5, -5);
    scene.add(fillLight2);
    
    // Build garage
    buildGarage(scene);
    
    // Animation loop
    let animationId;
    function animate() {
      animationId = requestAnimationFrame(animate);
      renderer.render(scene, camera);
    }
    animate();
    
    // Handle resize
    const handleResize = () => {
      if (!containerRef.current) return;
      camera.aspect = containerRef.current.clientWidth / containerRef.current.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(containerRef.current.clientWidth, containerRef.current.clientHeight);
    };
    window.addEventListener('resize', handleResize);
    
    return () => {
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(animationId);
      if (containerRef.current && renderer.domElement) {
        containerRef.current.removeChild(renderer.domElement);
      }
      renderer.dispose();
    };
  }, [updateCameraPosition]);

  // Update zone visibility when filter changes
  useEffect(() => {
    zoneMeshesRef.current.forEach(({ mesh, data }) => {
      mesh.visible = visibleTypes[data.type];
    });
  }, [visibleTypes]);

  function buildGarage(scene) {
    const W = GARAGE.width * SCALE;
    const D = GARAGE.depth * SCALE;
    const H = GARAGE.height * SCALE;
    
    // Floor with concrete texture
    const floorTexture = createConcreteTexture();
    floorTexture.wrapS = THREE.RepeatWrapping;
    floorTexture.wrapT = THREE.RepeatWrapping;
    floorTexture.repeat.set(4, 4);
    
    const floorGeom = new THREE.PlaneGeometry(W, D);
    const floorMat = new THREE.MeshStandardMaterial({ 
      map: floorTexture,
      roughness: 0.9,
      metalness: 0.1
    });
    const floor = new THREE.Mesh(floorGeom, floorMat);
    floor.rotation.x = -Math.PI / 2;
    floor.position.set(W/2, 0, D/2);
    floor.receiveShadow = true;
    scene.add(floor);
    
    // Floor markings (parking lines)
    const lineMat = new THREE.MeshBasicMaterial({ color: 0xffff00 });
    const lineGeom = new THREE.PlaneGeometry(0.02, D * 0.7);
    
    // Center dividing line
    const centerLine = new THREE.Mesh(lineGeom, lineMat);
    centerLine.rotation.x = -Math.PI / 2;
    centerLine.position.set(W/2, 0.01, D * 0.65);
    scene.add(centerLine);
    
    // Grid (subtle)
    const gridHelper = new THREE.GridHelper(Math.max(W, D), 50, 0x333333, 0x282828);
    gridHelper.position.set(W/2, 0.005, D/2);
    scene.add(gridHelper);
    
    // Walls
    const wallMat = new THREE.MeshStandardMaterial({ 
      color: 0x909090,
      transparent: true,
      opacity: 0.12,
      side: THREE.DoubleSide
    });
    
    // North wall
    const northWall = new THREE.Mesh(new THREE.PlaneGeometry(W, H), wallMat);
    northWall.position.set(W/2, H/2, 0);
    scene.add(northWall);
    
    // South wall
    const southWall = new THREE.Mesh(new THREE.PlaneGeometry(W, H), wallMat);
    southWall.position.set(W/2, H/2, D);
    southWall.rotation.y = Math.PI;
    scene.add(southWall);
    
    // East wall
    const eastWall = new THREE.Mesh(new THREE.PlaneGeometry(D, H), wallMat);
    eastWall.position.set(W, H/2, D/2);
    eastWall.rotation.y = -Math.PI/2;
    scene.add(eastWall);
    
    // West wall
    const westWall = new THREE.Mesh(new THREE.PlaneGeometry(D, H), wallMat);
    westWall.position.set(0, H/2, D/2);
    westWall.rotation.y = Math.PI/2;
    scene.add(westWall);
    
    // Wall frame edges
    const edgeMat = new THREE.LineBasicMaterial({ color: 0x666666 });
    const corners = [
      [[0, 0, 0], [W, 0, 0]], [[W, 0, 0], [W, 0, D]], [[W, 0, D], [0, 0, D]], [[0, 0, D], [0, 0, 0]],
      [[0, H, 0], [W, H, 0]], [[W, H, 0], [W, H, D]], [[W, H, D], [0, H, D]], [[0, H, D], [0, H, 0]],
      [[0, 0, 0], [0, H, 0]], [[W, 0, 0], [W, H, 0]], [[W, 0, D], [W, H, D]], [[0, 0, D], [0, H, D]]
    ];
    
    corners.forEach(([start, end]) => {
      const points = [new THREE.Vector3(...start), new THREE.Vector3(...end)];
      const geom = new THREE.BufferGeometry().setFromPoints(points);
      scene.add(new THREE.Line(geom, edgeMat));
    });
    
    // Ceiling beams
    const beamMat = new THREE.MeshStandardMaterial({ color: 0x4a4a4a });
    for (let i = 1; i < 5; i++) {
      const beamGeom = new THREE.BoxGeometry(W, 0.08, 0.15);
      const beam = new THREE.Mesh(beamGeom, beamMat);
      beam.position.set(W/2, H - 0.04, D * i / 5);
      scene.add(beam);
    }
    
    // Garage door with texture
    const gdTexture = createGarageDoorTexture();
    const gd = GARAGE.features.garageDoor;
    const gdWidth = gd.width * SCALE;
    const gdHeight = gd.height * SCALE;
    const gdX = (GARAGE.width/2 - gd.width/2) * SCALE;
    
    const garageDoorGeom = new THREE.BoxGeometry(gdWidth, gdHeight, 0.08);
    const garageDoorMat = new THREE.MeshStandardMaterial({ 
      map: gdTexture,
      roughness: 0.6
    });
    const garageDoor = new THREE.Mesh(garageDoorGeom, garageDoorMat);
    garageDoor.position.set(gdX + gdWidth/2, gdHeight/2, D - 0.04);
    garageDoor.castShadow = true;
    scene.add(garageDoor);
    
    // Windows with frame
    GARAGE.features.windows.forEach(win => {
      // Frame
      const frameGeom = new THREE.BoxGeometry(0.08, win.height * SCALE + 0.1, win.width * SCALE + 0.1);
      const frameMat = new THREE.MeshStandardMaterial({ color: 0xffffff });
      const frame = new THREE.Mesh(frameGeom, frameMat);
      frame.position.set(0.04, win.fromFloor * SCALE + win.height * SCALE / 2, win.position * SCALE);
      scene.add(frame);
      
      // Glass
      const glassGeom = new THREE.PlaneGeometry(win.height * SCALE, win.width * SCALE);
      const glassMat = new THREE.MeshStandardMaterial({ 
        color: 0x87ceeb,
        transparent: true,
        opacity: 0.4,
        roughness: 0.1,
        metalness: 0.1
      });
      const glass = new THREE.Mesh(glassGeom, glassMat);
      glass.rotation.y = Math.PI/2;
      glass.rotation.z = Math.PI/2;
      glass.position.set(0.06, win.fromFloor * SCALE + win.height * SCALE / 2, win.position * SCALE);
      scene.add(glass);
    });
    
    // Entry door with detail
    const ed = GARAGE.features.entryDoor;
    const doorGroup = new THREE.Group();
    
    // Door frame
    const doorFrameGeom = new THREE.BoxGeometry(0.1, ed.height * SCALE + 0.1, ed.width * SCALE + 0.1);
    const doorFrameMat = new THREE.MeshStandardMaterial({ color: 0xffffff });
    const doorFrame = new THREE.Mesh(doorFrameGeom, doorFrameMat);
    doorGroup.add(doorFrame);
    
    // Door panel
    const doorPanelGeom = new THREE.BoxGeometry(0.06, ed.height * SCALE, ed.width * SCALE);
    const doorPanelMat = new THREE.MeshStandardMaterial({ color: 0x654321 });
    const doorPanel = new THREE.Mesh(doorPanelGeom, doorPanelMat);
    doorPanel.position.x = 0.02;
    doorGroup.add(doorPanel);
    
    // Door handle
    const handleGeom = new THREE.SphereGeometry(0.03, 8, 8);
    const handleMat = new THREE.MeshStandardMaterial({ color: 0xc0c0c0, metalness: 0.8 });
    const handle = new THREE.Mesh(handleGeom, handleMat);
    handle.position.set(0.08, 0, ed.width * SCALE * 0.35);
    doorGroup.add(handle);
    
    doorGroup.position.set(W - 0.05, ed.height * SCALE / 2, ed.position * SCALE);
    scene.add(doorGroup);
    
    // Electrical panel
    const ep = GARAGE.features.electricalPanel;
    const epGroup = new THREE.Group();
    
    const epBoxGeom = new THREE.BoxGeometry(0.08, ep.height * SCALE, ep.width * SCALE);
    const epBoxMat = new THREE.MeshStandardMaterial({ color: 0x2a2a2a, metalness: 0.5 });
    const epBox = new THREE.Mesh(epBoxGeom, epBoxMat);
    epGroup.add(epBox);
    
    // Warning label
    const labelGeom = new THREE.PlaneGeometry(ep.width * SCALE * 0.6, ep.height * SCALE * 0.2);
    const labelCanvas = document.createElement('canvas');
    labelCanvas.width = 64;
    labelCanvas.height = 32;
    const labelCtx = labelCanvas.getContext('2d');
    labelCtx.fillStyle = '#ffcc00';
    labelCtx.fillRect(0, 0, 64, 32);
    labelCtx.fillStyle = '#000';
    labelCtx.font = 'bold 10px Arial';
    labelCtx.textAlign = 'center';
    labelCtx.fillText('⚡ DANGER', 32, 20);
    const labelTexture = new THREE.CanvasTexture(labelCanvas);
    const labelMat = new THREE.MeshBasicMaterial({ map: labelTexture });
    const label = new THREE.Mesh(labelGeom, labelMat);
    label.position.set(0.05, ep.height * SCALE * 0.3, 0);
    label.rotation.y = -Math.PI/2;
    epGroup.add(label);
    
    epGroup.position.set(W - 0.04, 48 * SCALE + ep.height * SCALE / 2, ep.position * SCALE);
    scene.add(epGroup);
    
    // Ceiling light fixture
    const lightFixtureGeom = new THREE.CylinderGeometry(0.15, 0.15, 0.05, 16);
    const lightFixtureMat = new THREE.MeshStandardMaterial({ color: 0xffffff, emissive: 0xffffee, emissiveIntensity: 0.5 });
    const lightFixture = new THREE.Mesh(lightFixtureGeom, lightFixtureMat);
    lightFixture.position.set(W/2, H - 0.05, D/2);
    scene.add(lightFixture);
    
    // Add zones
    zoneMeshesRef.current = [];
    GARAGE.zones.forEach(zone => {
      const zoneObj = createZone(zone, scene);
      scene.add(zoneObj);
      zoneMeshesRef.current.push({ mesh: zoneObj, data: zone });
    });
    
    // Compass labels
    addCompass(scene, W, D, H);
  }

  function createZone(zone, scene) {
    const w = zone.width * SCALE;
    const d = zone.depth * SCALE;
    const h = zone.height * SCALE;
    const x = zone.x * SCALE;
    const z = zone.y * SCALE;
    const y = (zone.heightFromFloor || 0) * SCALE;
    
    if (zone.type === 'vehicle') {
      return createDetailedCar(zone, x, z, w, d, h);
    }
    
    if (zone.type === 'workbench') {
      return createDetailedWorkbench(zone, x, z, w, d, h);
    }
    
    if (zone.type === 'wall_storage') {
      return createWallStorage(zone, x, z, w, d, h);
    }
    
    if (zone.type === 'overhead') {
      return createOverheadStorage(zone, x, z, w, d, h, y);
    }
    
    // Default
    const geometry = new THREE.BoxGeometry(w, h, d);
    const material = new THREE.MeshStandardMaterial({ color: zone.color });
    const mesh = new THREE.Mesh(geometry, material);
    mesh.position.set(x + w/2, y + h/2, z + d/2);
    mesh.userData = { zone };
    return mesh;
  }

  function createDetailedCar(zone, x, z, w, d, h) {
    const group = new THREE.Group();
    const isMinivan = zone.vehicleType === 'minivan';
    
    // Car body (lower)
    const bodyGeom = new THREE.BoxGeometry(w, h * 0.4, d * 0.92);
    const bodyMat = new THREE.MeshStandardMaterial({ 
      color: zone.color,
      metalness: 0.8,
      roughness: 0.3
    });
    const body = new THREE.Mesh(bodyGeom, bodyMat);
    body.position.set(0, h * 0.2, 0);
    body.castShadow = true;
    group.add(body);
    
    // Cabin
    const cabinWidth = w * 0.9;
    const cabinHeight = isMinivan ? h * 0.55 : h * 0.4;
    const cabinDepth = isMinivan ? d * 0.7 : d * 0.5;
    const cabinZ = isMinivan ? -d * 0.05 : -d * 0.1;
    
    const cabinGeom = new THREE.BoxGeometry(cabinWidth, cabinHeight, cabinDepth);
    const cabinMat = new THREE.MeshStandardMaterial({ 
      color: 0x1a1a1a,
      transparent: true,
      opacity: 0.85,
      metalness: 0.1,
      roughness: 0.5
    });
    const cabin = new THREE.Mesh(cabinGeom, cabinMat);
    cabin.position.set(0, h * 0.4 + cabinHeight/2, cabinZ);
    cabin.castShadow = true;
    group.add(cabin);
    
    // Windshield (angled)
    const wsGeom = new THREE.PlaneGeometry(cabinWidth * 0.95, cabinHeight * 0.9);
    const wsMat = new THREE.MeshStandardMaterial({ 
      color: 0x6699cc,
      transparent: true,
      opacity: 0.6,
      side: THREE.DoubleSide
    });
    const windshield = new THREE.Mesh(wsGeom, wsMat);
    windshield.rotation.x = isMinivan ? -0.3 : -0.4;
    windshield.position.set(0, h * 0.65, cabinZ + cabinDepth/2 + 0.05);
    group.add(windshield);
    
    // Rear window
    const rwGeom = new THREE.PlaneGeometry(cabinWidth * 0.9, cabinHeight * 0.7);
    const rearWindow = new THREE.Mesh(rwGeom, wsMat);
    rearWindow.rotation.x = isMinivan ? 0.2 : 0.35;
    rearWindow.position.set(0, h * 0.6, cabinZ - cabinDepth/2 - 0.03);
    group.add(rearWindow);
    
    // Wheels
    const wheelRadius = h * 0.22;
    const wheelWidth = w * 0.08;
    const wheelGeom = new THREE.CylinderGeometry(wheelRadius, wheelRadius, wheelWidth, 24);
    const wheelMat = new THREE.MeshStandardMaterial({ color: 0x1a1a1a, roughness: 0.8 });
    const hubMat = new THREE.MeshStandardMaterial({ color: 0xcccccc, metalness: 0.7 });
    
    const wheelPositions = [
      [-w/2 + wheelWidth/2, d * 0.32],
      [w/2 - wheelWidth/2, d * 0.32],
      [-w/2 + wheelWidth/2, -d * 0.32],
      [w/2 - wheelWidth/2, -d * 0.32]
    ];
    
    wheelPositions.forEach(([wx, wz]) => {
      const wheel = new THREE.Mesh(wheelGeom, wheelMat);
      wheel.rotation.z = Math.PI / 2;
      wheel.position.set(wx, wheelRadius, wz);
      group.add(wheel);
      
      // Hub cap
      const hubGeom = new THREE.CylinderGeometry(wheelRadius * 0.6, wheelRadius * 0.6, wheelWidth + 0.01, 16);
      const hub = new THREE.Mesh(hubGeom, hubMat);
      hub.rotation.z = Math.PI / 2;
      hub.position.set(wx * 1.01, wheelRadius, wz);
      group.add(hub);
    });
    
    // Headlights
    const hlGeom = new THREE.CircleGeometry(h * 0.1, 16);
    const hlMat = new THREE.MeshStandardMaterial({ color: 0xffffcc, emissive: 0xffffcc, emissiveIntensity: 0.3 });
    [[-w * 0.35, d/2 - 0.01], [w * 0.35, d/2 - 0.01]].forEach(([hx, hz]) => {
      const hl = new THREE.Mesh(hlGeom, hlMat);
      hl.position.set(hx, h * 0.25, hz);
      group.add(hl);
    });
    
    // Taillights
    const tlMat = new THREE.MeshStandardMaterial({ color: 0xff3333, emissive: 0xff0000, emissiveIntensity: 0.2 });
    [[-w * 0.35, -d/2 + 0.01], [w * 0.35, -d/2 + 0.01]].forEach(([tx, tz]) => {
      const tl = new THREE.Mesh(hlGeom, tlMat);
      tl.rotation.y = Math.PI;
      tl.position.set(tx, h * 0.25, tz);
      group.add(tl);
    });
    
    // License plate
    const lpGeom = new THREE.PlaneGeometry(w * 0.25, h * 0.08);
    const lpCanvas = document.createElement('canvas');
    lpCanvas.width = 64;
    lpCanvas.height = 24;
    const lpCtx = lpCanvas.getContext('2d');
    lpCtx.fillStyle = '#fff';
    lpCtx.fillRect(0, 0, 64, 24);
    lpCtx.strokeStyle = '#000';
    lpCtx.strokeRect(1, 1, 62, 22);
    lpCtx.fillStyle = '#000';
    lpCtx.font = 'bold 12px monospace';
    lpCtx.textAlign = 'center';
    lpCtx.fillText('GARAGE', 32, 16);
    const lpTexture = new THREE.CanvasTexture(lpCanvas);
    const lpMat = new THREE.MeshBasicMaterial({ map: lpTexture });
    const licensePlate = new THREE.Mesh(lpGeom, lpMat);
    licensePlate.rotation.y = Math.PI;
    licensePlate.position.set(0, h * 0.12, -d/2 + 0.01);
    group.add(licensePlate);
    
    group.position.set(x + w/2, 0, z + d/2);
    group.userData = { zone };
    return group;
  }

  function createDetailedWorkbench(zone, x, z, w, d, h) {
    const group = new THREE.Group();
    
    // Workbench top with wood texture
    const woodTexture = createWoodTexture();
    woodTexture.wrapS = THREE.RepeatWrapping;
    woodTexture.wrapT = THREE.RepeatWrapping;
    woodTexture.repeat.set(2, 1);
    
    const topGeom = new THREE.BoxGeometry(w, 0.06, d);
    const topMat = new THREE.MeshStandardMaterial({ 
      map: woodTexture,
      roughness: 0.7
    });
    const top = new THREE.Mesh(topGeom, topMat);
    top.position.y = h;
    top.castShadow = true;
    top.receiveShadow = true;
    group.add(top);
    
    // Frame
    const frameMat = new THREE.MeshStandardMaterial({ color: 0x333333, metalness: 0.5 });
    
    // Legs
    const legGeom = new THREE.BoxGeometry(0.06, h, 0.06);
    [[-w/2 + 0.06, -d/2 + 0.06], [w/2 - 0.06, -d/2 + 0.06], 
     [-w/2 + 0.06, d/2 - 0.06], [w/2 - 0.06, d/2 - 0.06]].forEach(([lx, lz]) => {
      const leg = new THREE.Mesh(legGeom, frameMat);
      leg.position.set(lx, h/2, lz);
      leg.castShadow = true;
      group.add(leg);
    });
    
    // Crossbars
    const crossGeom = new THREE.BoxGeometry(w - 0.1, 0.04, 0.04);
    const crossbar1 = new THREE.Mesh(crossGeom, frameMat);
    crossbar1.position.set(0, h * 0.3, -d/2 + 0.06);
    group.add(crossbar1);
    const crossbar2 = new THREE.Mesh(crossGeom, frameMat);
    crossbar2.position.set(0, h * 0.3, d/2 - 0.06);
    group.add(crossbar2);
    
    // Lower shelf
    const shelfGeom = new THREE.BoxGeometry(w - 0.15, 0.03, d - 0.15);
    const shelfMat = new THREE.MeshStandardMaterial({ color: 0x666666 });
    const shelf = new THREE.Mesh(shelfGeom, shelfMat);
    shelf.position.set(0, h * 0.15, 0);
    group.add(shelf);
    
    // Pegboard with texture
    const pegTexture = createPegboardTexture();
    pegTexture.wrapS = THREE.RepeatWrapping;
    pegTexture.wrapT = THREE.RepeatWrapping;
    pegTexture.repeat.set(3, 2);
    
    const pegGeom = new THREE.BoxGeometry(w, h * 0.9, 0.03);
    const pegMat = new THREE.MeshStandardMaterial({ map: pegTexture });
    const pegboard = new THREE.Mesh(pegGeom, pegMat);
    pegboard.position.set(0, h * 1.5, -d/2 + 0.02);
    group.add(pegboard);
    
    // Tools on pegboard
    addToolSilhouettes(group, w, h, d);
    
    // Vise
    const viseGroup = new THREE.Group();
    const viseBaseGeom = new THREE.BoxGeometry(0.15, 0.08, 0.12);
    const viseMat = new THREE.MeshStandardMaterial({ color: 0x444444, metalness: 0.6 });
    const viseBase = new THREE.Mesh(viseBaseGeom, viseMat);
    viseGroup.add(viseBase);
    
    const viseJawGeom = new THREE.BoxGeometry(0.15, 0.12, 0.03);
    const viseJaw1 = new THREE.Mesh(viseJawGeom, viseMat);
    viseJaw1.position.set(0, 0.08, 0.04);
    viseGroup.add(viseJaw1);
    const viseJaw2 = new THREE.Mesh(viseJawGeom, viseMat);
    viseJaw2.position.set(0, 0.08, -0.04);
    viseGroup.add(viseJaw2);
    
    viseGroup.position.set(w/2 - 0.15, h + 0.04, 0);
    group.add(viseGroup);
    
    // Power strip
    const stripGeom = new THREE.BoxGeometry(0.4, 0.03, 0.06);
    const stripMat = new THREE.MeshStandardMaterial({ color: 0xffa500 });
    const powerStrip = new THREE.Mesh(stripGeom, stripMat);
    powerStrip.position.set(0, h + 0.02, d/2 - 0.05);
    group.add(powerStrip);
    
    // Drawers
    const drawerMat = new THREE.MeshStandardMaterial({ color: 0x555555, metalness: 0.3 });
    for (let i = 0; i < 3; i++) {
      const drawerGeom = new THREE.BoxGeometry(w/3 - 0.05, h * 0.25, d - 0.1);
      const drawer = new THREE.Mesh(drawerGeom, drawerMat);
      drawer.position.set(-w/3 + i * w/3, h * 0.65, 0);
      group.add(drawer);
      
      // Handle
      const handleGeom = new THREE.BoxGeometry(0.08, 0.02, 0.02);
      const handleMat = new THREE.MeshStandardMaterial({ color: 0xcccccc, metalness: 0.7 });
      const handle = new THREE.Mesh(handleGeom, handleMat);
      handle.position.set(-w/3 + i * w/3, h * 0.68, d/2 - 0.03);
      group.add(handle);
    }
    
    group.position.set(x + w/2, 0, z + d/2);
    group.userData = { zone };
    return group;
  }

  function addToolSilhouettes(group, w, h, d) {
    const toolMat = new THREE.MeshStandardMaterial({ color: 0x333333 });
    
    // Hammer
    const hammerHandle = new THREE.Mesh(new THREE.CylinderGeometry(0.01, 0.01, 0.2), toolMat);
    hammerHandle.rotation.z = Math.PI / 6;
    hammerHandle.position.set(-w/3, h * 1.4, -d/2 + 0.05);
    group.add(hammerHandle);
    
    const hammerHead = new THREE.Mesh(new THREE.BoxGeometry(0.06, 0.03, 0.03), toolMat);
    hammerHead.position.set(-w/3 + 0.05, h * 1.5, -d/2 + 0.05);
    group.add(hammerHead);
    
    // Screwdrivers
    for (let i = 0; i < 4; i++) {
      const sdHandle = new THREE.Mesh(new THREE.CylinderGeometry(0.015, 0.015, 0.08), 
        new THREE.MeshStandardMaterial({ color: [0xff0000, 0x0000ff, 0xffff00, 0x00ff00][i] }));
      sdHandle.position.set(-w/6 + i * 0.06, h * 1.55, -d/2 + 0.05);
      group.add(sdHandle);
      
      const sdShaft = new THREE.Mesh(new THREE.CylinderGeometry(0.005, 0.005, 0.1), toolMat);
      sdShaft.position.set(-w/6 + i * 0.06, h * 1.4, -d/2 + 0.05);
      group.add(sdShaft);
    }
    
    // Wrench
    const wrenchGeom = new THREE.BoxGeometry(0.15, 0.03, 0.01);
    const wrench = new THREE.Mesh(wrenchGeom, new THREE.MeshStandardMaterial({ color: 0x888888, metalness: 0.8 }));
    wrench.rotation.z = 0.2;
    wrench.position.set(w/4, h * 1.35, -d/2 + 0.05);
    group.add(wrench);
    
    // Pliers
    const pliersGeom = new THREE.BoxGeometry(0.03, 0.12, 0.02);
    const pliers = new THREE.Mesh(pliersGeom, new THREE.MeshStandardMaterial({ color: 0xcc0000 }));
    pliers.position.set(w/3, h * 1.45, -d/2 + 0.05);
    group.add(pliers);
    
    // Tape measure
    const tapeGeom = new THREE.CylinderGeometry(0.03, 0.03, 0.02, 16);
    const tapeMat = new THREE.MeshStandardMaterial({ color: 0xffcc00 });
    const tape = new THREE.Mesh(tapeGeom, tapeMat);
    tape.rotation.x = Math.PI / 2;
    tape.position.set(w/6, h * 1.3, -d/2 + 0.05);
    group.add(tape);
  }

  function createWallStorage(zone, x, z, w, d, h) {
    const group = new THREE.Group();
    
    // French cleat backing
    const cleatTexture = createFrenchCleatTexture();
    cleatTexture.wrapS = THREE.RepeatWrapping;
    cleatTexture.wrapT = THREE.RepeatWrapping;
    
    const isVertical = zone.wall === 'E' || zone.wall === 'W';
    const backW = isVertical ? d : w;
    const backD = isVertical ? w : d;
    
    const backGeom = new THREE.BoxGeometry(backW, h, 0.03);
    const backMat = new THREE.MeshStandardMaterial({ 
      map: cleatTexture,
      color: 0x22c55e
    });
    const back = new THREE.Mesh(backGeom, backMat);
    back.castShadow = true;
    group.add(back);
    
    // Shelves
    const shelfMat = new THREE.MeshStandardMaterial({ color: 0x1a8f3c });
    for (let i = 0; i < 2; i++) {
      const shelfGeom = new THREE.BoxGeometry(backW * 0.9, 0.02, backD * 0.8);
      const shelf = new THREE.Mesh(shelfGeom, shelfMat);
      shelf.position.set(0, -h/3 + i * h/2, backD/2);
      shelf.castShadow = true;
      group.add(shelf);
    }
    
    // Some items on shelves (boxes)
    const boxMat = new THREE.MeshStandardMaterial({ color: 0x8B4513 });
    const box1 = new THREE.Mesh(new THREE.BoxGeometry(backW * 0.3, h * 0.2, backD * 0.5), boxMat);
    box1.position.set(-backW * 0.25, -h/3 + h * 0.12, backD/2);
    group.add(box1);
    
    const box2 = new THREE.Mesh(new THREE.BoxGeometry(backW * 0.25, h * 0.15, backD * 0.4), 
      new THREE.MeshStandardMaterial({ color: 0x4169E1 }));
    box2.position.set(backW * 0.2, h/6 + h * 0.1, backD/2);
    group.add(box2);
    
    // Position based on wall
    const heightFromFloor = 24 * SCALE;
    if (zone.wall === 'E') {
      group.rotation.y = -Math.PI/2;
      group.position.set(x + w/2, heightFromFloor + h/2, z + d/2);
    } else if (zone.wall === 'W') {
      group.rotation.y = Math.PI/2;
      group.position.set(x + w/2, heightFromFloor + h/2, z + d/2);
    } else {
      group.position.set(x + w/2, heightFromFloor + h/2, z + d/2);
    }
    
    group.userData = { zone };
    return group;
  }

  function createOverheadStorage(zone, x, z, w, d, h, y) {
    const group = new THREE.Group();
    
    // Platform frame
    const frameMat = new THREE.MeshStandardMaterial({ color: 0x666666, metalness: 0.5 });
    
    // Main platform
    const platGeom = new THREE.BoxGeometry(w, 0.05, d);
    const platMat = new THREE.MeshStandardMaterial({ 
      color: zone.color,
      transparent: true,
      opacity: 0.85
    });
    const platform = new THREE.Mesh(platGeom, platMat);
    platform.castShadow = true;
    platform.receiveShadow = true;
    group.add(platform);
    
    // Wire mesh texture effect
    const meshGeom = new THREE.PlaneGeometry(w - 0.05, d - 0.05);
    const meshMat = new THREE.MeshStandardMaterial({ 
      color: 0x888888,
      wireframe: true,
      transparent: true,
      opacity: 0.3
    });
    const wireMesh = new THREE.Mesh(meshGeom, meshMat);
    wireMesh.rotation.x = -Math.PI/2;
    wireMesh.position.y = 0.03;
    group.add(wireMesh);
    
    // Frame edges
    const edgeGeom = new THREE.BoxGeometry(w, 0.04, 0.04);
    const edge1 = new THREE.Mesh(edgeGeom, frameMat);
    edge1.position.set(0, 0, -d/2 + 0.02);
    group.add(edge1);
    const edge2 = new THREE.Mesh(edgeGeom, frameMat);
    edge2.position.set(0, 0, d/2 - 0.02);
    group.add(edge2);
    
    const sideEdgeGeom = new THREE.BoxGeometry(0.04, 0.04, d);
    const edge3 = new THREE.Mesh(sideEdgeGeom, frameMat);
    edge3.position.set(-w/2 + 0.02, 0, 0);
    group.add(edge3);
    const edge4 = new THREE.Mesh(sideEdgeGeom, frameMat);
    edge4.position.set(w/2 - 0.02, 0, 0);
    group.add(edge4);
    
    // Ceiling mount chains
    const ceilingHeight = GARAGE.height * SCALE;
    const chainHeight = ceilingHeight - y - h/2;
    const chainGeom = new THREE.CylinderGeometry(0.015, 0.015, chainHeight);
    const chainMat = new THREE.MeshStandardMaterial({ color: 0x555555, metalness: 0.6 });
    
    [[-w/2 + 0.1, -d/2 + 0.1], [w/2 - 0.1, -d/2 + 0.1], 
     [-w/2 + 0.1, d/2 - 0.1], [w/2 - 0.1, d/2 - 0.1]].forEach(([cx, cz]) => {
      const chain = new THREE.Mesh(chainGeom, chainMat);
      chain.position.set(cx, chainHeight/2, cz);
      group.add(chain);
      
      // Ceiling bracket
      const bracketGeom = new THREE.BoxGeometry(0.08, 0.03, 0.08);
      const bracket = new THREE.Mesh(bracketGeom, chainMat);
      bracket.position.set(cx, chainHeight, cz);
      group.add(bracket);
    });
    
    // Storage bins on platform
    const binColors = [0x3b82f6, 0xef4444, 0x22c55e, 0xf59e0b];
    const binCount = Math.min(3, Math.floor(w / 0.4));
    for (let i = 0; i < binCount; i++) {
      const binGeom = new THREE.BoxGeometry(w/binCount * 0.7, 0.15, d * 0.6);
      const binMat = new THREE.MeshStandardMaterial({ color: binColors[i % binColors.length] });
      const bin = new THREE.Mesh(binGeom, binMat);
      bin.position.set(-w/2 + w/binCount * (i + 0.5), 0.1, 0);
      group.add(bin);
    }
    
    group.position.set(x + w/2, y + h/2, z + d/2);
    group.userData = { zone };
    return group;
  }

  function addCompass(scene, W, D, H) {
    const createLabel = (text, x, y, z, color = '#ffffff') => {
      const canvas = document.createElement('canvas');
      canvas.width = 128;
      canvas.height = 128;
      const ctx = canvas.getContext('2d');
      
      // Background circle
      ctx.beginPath();
      ctx.arc(64, 64, 50, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(0,0,0,0.5)';
      ctx.fill();
      
      ctx.fillStyle = color;
      ctx.font = 'bold 64px Arial';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(text, 64, 64);
      
      const texture = new THREE.CanvasTexture(canvas);
      const spriteMat = new THREE.SpriteMaterial({ map: texture });
      const sprite = new THREE.Sprite(spriteMat);
      sprite.position.set(x, y, z);
      sprite.scale.set(0.6, 0.6, 0.6);
      scene.add(sprite);
    };
    
    createLabel('N', W/2, H + 0.4, -0.6, '#ff6b6b');
    createLabel('S', W/2, H + 0.4, D + 0.6, '#4ecdc4');
    createLabel('E', W + 0.6, H + 0.4, D/2, '#ffe66d');
    createLabel('W', -0.6, H + 0.4, D/2, '#95e1d3');
  }

  // Event handlers
  const handleMouseDown = (e) => {
    if (e.button === 0) {
      mouseRef.current.isDown = true;
      mouseRef.current.lastX = e.clientX;
      mouseRef.current.lastY = e.clientY;
    }
  };

  const handleMouseUp = () => {
    mouseRef.current.isDown = false;
  };

  const handleClick = (e) => {
    if (!containerRef.current || !cameraRef.current || !sceneRef.current) return;
    
    const rect = containerRef.current.getBoundingClientRect();
    mouseVecRef.current.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
    mouseVecRef.current.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
    
    raycasterRef.current.setFromCamera(mouseVecRef.current, cameraRef.current);
    const intersects = raycasterRef.current.intersectObjects(sceneRef.current.children, true);
    
    let found = null;
    for (const intersect of intersects) {
      let obj = intersect.object;
      while (obj) {
        if (obj.userData?.zone) {
          found = obj.userData.zone;
          break;
        }
        obj = obj.parent;
      }
      if (found) break;
    }
    
    setSelectedZone(found);
  };

  const handleMouseMove = (e) => {
    if (!containerRef.current) return;
    
    const rect = containerRef.current.getBoundingClientRect();
    mouseVecRef.current.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
    mouseVecRef.current.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
    
    // Raycasting for hover
    if (cameraRef.current && sceneRef.current) {
      raycasterRef.current.setFromCamera(mouseVecRef.current, cameraRef.current);
      const intersects = raycasterRef.current.intersectObjects(sceneRef.current.children, true);
      
      let found = null;
      for (const intersect of intersects) {
        let obj = intersect.object;
        while (obj) {
          if (obj.userData?.zone) {
            found = obj.userData.zone;
            break;
          }
          obj = obj.parent;
        }
        if (found) break;
      }
      setHoveredZone(found);
    }
    
    // Camera rotation
    if (mouseRef.current.isDown) {
      const dx = e.clientX - mouseRef.current.lastX;
      const dy = e.clientY - mouseRef.current.lastY;
      
      cameraAngleRef.current.theta += dx * 0.01;
      cameraAngleRef.current.phi = Math.max(0.1, Math.min(Math.PI/2 - 0.1, cameraAngleRef.current.phi + dy * 0.01));
      
      mouseRef.current.lastX = e.clientX;
      mouseRef.current.lastY = e.clientY;
      
      updateCameraPosition();
    }
  };

  const handleWheel = (e) => {
    e.preventDefault();
    cameraAngleRef.current.distance = Math.max(5, Math.min(30, cameraAngleRef.current.distance + e.deltaY * 0.01));
    updateCameraPosition();
  };

  const setPresetView = (view) => {
    switch(view) {
      case 'top':
        cameraAngleRef.current = { theta: 0, phi: 0.1, distance: 15 };
        break;
      case 'front':
        cameraAngleRef.current = { theta: 0, phi: Math.PI/2 - 0.1, distance: 15 };
        break;
      case 'side':
        cameraAngleRef.current = { theta: Math.PI/2, phi: Math.PI/3, distance: 15 };
        break;
      case 'corner':
      default:
        cameraAngleRef.current = { theta: Math.PI/4, phi: Math.PI/4, distance: 15 };
    }
    updateCameraPosition();
    setViewMode(view);
  };

  const toggleType = (type) => {
    setVisibleTypes(prev => ({ ...prev, [type]: !prev[type] }));
  };

  const zoneTypeInfo = {
    vehicle: { color: 'bg-blue-500', label: 'Vehicles', icon: '🚗' },
    workbench: { color: 'bg-amber-500', label: 'Workbench', icon: '🔧' },
    wall_storage: { color: 'bg-green-500', label: 'Wall Storage', icon: '📦' },
    overhead: { color: 'bg-purple-500', label: 'Overhead', icon: '⬆️' }
  };

  const formatDimension = (inches) => {
    const feet = Math.floor(inches / 12);
    const remainingInches = Math.round(inches % 12);
    if (remainingInches === 0) return `${feet}'`;
    return `${feet}'${remainingInches}"`;
  };

  return (
    <div className="w-full h-screen bg-gray-900 flex flex-col">
      {/* Header */}
      <div className="bg-gradient-to-r from-gray-800 to-gray-900 p-4 border-b border-gray-700">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white flex items-center gap-2">
              🏠 Mike's Garage <span className="text-sm font-normal text-gray-400">3D Layout</span>
            </h1>
            <p className="text-gray-400 text-sm">25' × 25' × 12'2" ceiling • Honda Odyssey + Nissan Altima</p>
          </div>
          <div className="text-right">
            <div className="text-sm text-gray-400">Layout Score</div>
            <div className="text-2xl font-bold text-green-400">60/100</div>
          </div>
        </div>
      </div>
      
      {/* Main content */}
      <div className="flex-1 flex overflow-hidden">
        {/* 3D Viewer */}
        <div 
          ref={containerRef} 
          className="flex-1 cursor-grab active:cursor-grabbing relative"
          onMouseDown={handleMouseDown}
          onMouseUp={handleMouseUp}
          onMouseMove={handleMouseMove}
          onMouseLeave={handleMouseUp}
          onClick={handleClick}
          onWheel={handleWheel}
        >
          {/* Hover tooltip */}
          {hoveredZone && !selectedZone && (
            <div className="absolute top-4 left-4 bg-black/80 text-white px-3 py-2 rounded-lg pointer-events-none">
              <div className="font-medium">{hoveredZone.name}</div>
              <div className="text-xs text-gray-400">Click to select</div>
            </div>
          )}
        </div>
        
        {/* Sidebar */}
        <div className="w-80 bg-gray-800 border-l border-gray-700 flex flex-col">
          {/* View Controls */}
          <div className="p-4 border-b border-gray-700">
            <h3 className="text-white font-semibold mb-3 flex items-center gap-2">
              <span>🎥</span> Camera View
            </h3>
            <div className="grid grid-cols-4 gap-2">
              {['corner', 'top', 'front', 'side'].map(view => (
                <button
                  key={view}
                  onClick={() => setPresetView(view)}
                  className={`px-2 py-2 rounded text-xs font-medium transition ${
                    viewMode === view 
                      ? 'bg-blue-600 text-white' 
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                >
                  {view.charAt(0).toUpperCase() + view.slice(1)}
                </button>
              ))}
            </div>
            <p className="text-gray-500 text-xs mt-2">🖱️ Drag to rotate • Scroll to zoom • Click to select</p>
          </div>
          
          {/* Filter Controls */}
          <div className="p-4 border-b border-gray-700">
            <h3 className="text-white font-semibold mb-3 flex items-center gap-2">
              <span>👁️</span> Show/Hide
            </h3>
            <div className="space-y-2">
              {Object.entries(zoneTypeInfo).map(([type, { color, label, icon }]) => (
                <button
                  key={type}
                  onClick={() => toggleType(type)}
                  className={`w-full flex items-center gap-3 px-3 py-2 rounded transition ${
                    visibleTypes[type] 
                      ? 'bg-gray-700 text-white' 
                      : 'bg-gray-900 text-gray-500'
                  }`}
                >
                  <div className={`w-4 h-4 rounded ${visibleTypes[type] ? color : 'bg-gray-600'}`}></div>
                  <span className="flex-1 text-left text-sm">{icon} {label}</span>
                  <span className="text-xs">{visibleTypes[type] ? '✓' : '○'}</span>
                </button>
              ))}
            </div>
          </div>
          
          {/* Selected Zone Detail */}
          <div className="p-4 border-b border-gray-700">
            <h3 className="text-white font-semibold mb-3 flex items-center gap-2">
              <span>📍</span> Selected Zone
            </h3>
            {selectedZone ? (
              <div className="bg-gray-700 rounded-lg p-4">
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <p className="text-white font-medium text-lg">{selectedZone.name}</p>
                    <p className="text-gray-400 text-sm capitalize flex items-center gap-1">
                      {zoneTypeInfo[selectedZone.type]?.icon} {selectedZone.type.replace('_', ' ')}
                    </p>
                  </div>
                  <button 
                    onClick={() => setSelectedZone(null)}
                    className="text-gray-500 hover:text-white"
                  >✕</button>
                </div>
                <div className="mt-3 pt-3 border-t border-gray-600 space-y-1">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-400">Width:</span>
                    <span className="text-white">{formatDimension(selectedZone.width)}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-400">Depth:</span>
                    <span className="text-white">{formatDimension(selectedZone.depth)}</span>
                  </div>
                  {selectedZone.height && (
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-400">Height:</span>
                      <span className="text-white">{formatDimension(selectedZone.height)}</span>
                    </div>
                  )}
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-400">Position:</span>
                    <span className="text-white">{formatDimension(selectedZone.x)} from W, {formatDimension(selectedZone.y)} from N</span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-gray-500 text-sm bg-gray-900/50 rounded-lg p-4 text-center">
                Click on any zone to see details
              </div>
            )}
          </div>
          
          {/* Zone List */}
          <div className="flex-1 overflow-y-auto p-4">
            <h3 className="text-white font-semibold mb-3 flex items-center gap-2">
              <span>📋</span> All Zones ({GARAGE.zones.filter(z => visibleTypes[z.type]).length})
            </h3>
            <div className="space-y-1">
              {GARAGE.zones.filter(z => visibleTypes[z.type]).map((zone, i) => (
                <button 
                  key={i}
                  onClick={() => setSelectedZone(zone)}
                  className={`w-full text-left text-sm px-3 py-2 rounded flex items-center gap-2 transition ${
                    selectedZone?.name === zone.name 
                      ? 'bg-blue-600 text-white' 
                      : hoveredZone?.name === zone.name
                        ? 'bg-gray-600 text-white'
                        : 'text-gray-400 hover:bg-gray-700 hover:text-white'
                  }`}
                >
                  <span>{zoneTypeInfo[zone.type]?.icon}</span>
                  <span className="flex-1 truncate">{zone.name}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
      
      {/* Footer */}
      <div className="bg-gray-800 px-4 py-2 border-t border-gray-700">
        <div className="flex justify-between items-center text-xs text-gray-500">
          <div className="flex gap-4">
            <span>🚗 2 Vehicles</span>
            <span>🔧 1 Workbench</span>
            <span>📦 11 Wall Storage</span>
            <span>⬆️ 3 Overhead</span>
          </div>
          <div>Garage Layout Planner v1.0</div>
        </div>
      </div>
    </div>
  );
}
