/**
 * chunk-editor.js
 * Single-file 50×50 prefab chunk editor built on Three.js (CDN imports).
 * Drop into your project and add:
 *   <script type="module" src="chunk-editor.js"></script>
 * in index.html (no build step required).
 */

// ---------------------------------------------------------------------------
// CDN imports – Three r162 + addons
// ---------------------------------------------------------------------------
import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.161.0/build/three.module.js';
import { OrbitControls }  from 'https://cdn.jsdelivr.net/npm/three@0.161.0/examples/jsm/controls/OrbitControls.js';
import { GLTFLoader }     from 'https://cdn.jsdelivr.net/npm/three@0.161.0/examples/jsm/loaders/GLTFLoader.js';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------
const GRID = 50;          // 50×50 cells
const CELL = 1;           // 1 m per cell

/** Built-in tile catalogue. Add more entries as needed. */
const TILE_DEFS = [
  { id: 'empty',       label: 'Empty',        color: '#1a1a2e' },
  { id: 'road_center', label: 'Road Center',  color: '#444455' },
  { id: 'road_dashed', label: 'Road Dashed',  color: '#555566' },
];

/** Asset filenames to load.  Edit this list to match your project. */
const ASSET_FILES = [
  'house_1f.glb',
  'house_2f.glb',
  'store.glb',
  'apartment.glb',
  'fence.glb',
  'tree.glb',
  'tree_large.glb',
  'tree_medium.glb',
  'tree_small.glb',
  'vending.glb',
  'traffic_sign_stop.glb',
  'traffic_sign_triangle.glb',
  'traffic_sign_square.glb',
  'car_sedan_red.glb',
  'car_sedan_mint.glb',
  'car_sedan_lemon.glb',
  'car_truck_red.glb',
  'car_truck_mint.glb',
  'car_truck_lemon.glb',
  'basketball.glb',
  'fruit.glb',
];

const ASSET_BASE = 'assets/';   // resolved relative to index.html
const TEX_BASE   = 'assets/textures/';

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------
let mode          = 'paint';   // 'paint' | 'place' | 'select' | 'rotate'
let activeTileId  = 'road_center';
let activeAsset   = ASSET_FILES[0] || null;

/** 50×50 tile grid – row-major [z][x] */
let tileGrid = Array.from({ length: GRID }, () => Array(GRID).fill('empty'));

/** Placed asset descriptors */
const placedObjects = [];   // { mesh, asset, pos:[x,y,z], rotY, scale }

/** Selected meshes (select mode) */
const selected = new Set();

/** Undo / redo */
const undoStack = [];
const redoStack = [];

// ---------------------------------------------------------------------------
// Loaded asset cache  { filename -> THREE.Group (template) }
// ---------------------------------------------------------------------------
const assetCache = {};

// ---------------------------------------------------------------------------
// Three.js globals
// ---------------------------------------------------------------------------
let renderer, scene, camera, controls;
let tileMeshes = [];          // flat array of 100 plane meshes
let ghostMesh  = null;        // placement preview
let ghostValid = false;
const keyState = new Set();
let isPainting = false;
let paintStroke = [];
const paintVisited = new Set();

const raycaster  = new THREE.Raycaster();
const mouse      = new THREE.Vector2();
const groundPlane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0);

// highlight helpers
let hoverOutline = null;
const selectionOutlines = new Map(); // mesh -> outline mesh

// drag state (move mode)
let isDragging     = false;
let dragStart      = new THREE.Vector3();
let dragOffset     = new THREE.Vector3();
let dragTargets    = [];

// ---------------------------------------------------------------------------
// Texture helpers
// ---------------------------------------------------------------------------
const texLoader = new THREE.TextureLoader();
const tileTexCache = {};

function tileColor(id) {
  const def = TILE_DEFS.find(d => d.id === id);
  return def ? def.color : '#222';
}

function makeTileMaterial(id) {
  const path = `${TEX_BASE}${id}.png`;
  const key  = id;
  if (!tileTexCache[key]) {
    const mat = new THREE.MeshLambertMaterial({ color: tileColor(id) });
    // Attempt texture load; fall back to solid color if missing
    texLoader.load(
      path,
      tex => { mat.map = tex; mat.needsUpdate = true; },
      undefined,
      () => { /* not found – color fallback already set */ }
    );
    tileTexCache[key] = mat;
  }
  return tileTexCache[key];
}

// ---------------------------------------------------------------------------
// Scene setup
// ---------------------------------------------------------------------------
function initScene() {
  // Renderer
  renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(window.devicePixelRatio);
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type    = THREE.PCFSoftShadowMap;
  renderer.outputColorSpace   = THREE.SRGBColorSpace;
  renderer.domElement.tabIndex = 0;
  renderer.domElement.style.outline = 'none';
  document.getElementById('canvas-container').appendChild(renderer.domElement);

  // Scene
  scene = new THREE.Scene();
  scene.background = new THREE.Color('#e7e5dc');
  scene.fog        = new THREE.Fog('#e7e5dc', 60, 160);

  // Camera
  camera = new THREE.PerspectiveCamera(55, window.innerWidth / window.innerHeight, 0.1, 200);
  camera.position.set(GRID * 0.6, GRID * 0.8, GRID * 1.1);
  camera.lookAt(GRID / 2, 0, GRID / 2);

  // Controls
  controls = new OrbitControls(camera, renderer.domElement);
  controls.target.set(GRID / 2, 0, GRID / 2);
  controls.minDistance = 3;
  controls.maxDistance = 60;
  controls.maxPolarAngle = Math.PI / 2 - 0.05;
  controls.mouseButtons = {
    LEFT: null,
    MIDDLE: THREE.MOUSE.ROTATE,
    RIGHT: THREE.MOUSE.PAN,
  };
  controls.update();

  // Lighting (matches typical viewer.js setup)
  const hemi = new THREE.HemisphereLight('#f6f4ee', '#cfc9b8', 1.4);
  scene.add(hemi);

  const sun = new THREE.DirectionalLight('#ffffff', 2.2);
  sun.position.set(8, 14, 6);
  sun.castShadow = true;
  sun.shadow.mapSize.set(2048, 2048);
  sun.shadow.camera.near = 0.5;
  sun.shadow.camera.far  = 60;
  sun.shadow.camera.left = sun.shadow.camera.bottom = -12;
  sun.shadow.camera.right = sun.shadow.camera.top  =  12;
  scene.add(sun);

  const fill = new THREE.DirectionalLight('#f4f1e8', 0.9);
  fill.position.set(-6, 5, -4);
  scene.add(fill);

  // Grid helper (visual guide only – not interactive)
  const gridHelper = new THREE.GridHelper(GRID, GRID, '#c7c3b8', '#d7d3c8');
  gridHelper.position.set(GRID / 2, 0.002, GRID / 2);
  scene.add(gridHelper);

  // Resize handler
  window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  });
}

// ---------------------------------------------------------------------------
// Tiles
// ---------------------------------------------------------------------------
function buildTileGrid() {
  // Remove old meshes
  tileMeshes.forEach(m => scene.remove(m));
  tileMeshes = [];

  const geo = new THREE.PlaneGeometry(CELL, CELL);
  geo.rotateX(-Math.PI / 2);

  for (let z = 0; z < GRID; z++) {
    for (let x = 0; x < GRID; x++) {
      const id  = tileGrid[z][x];
      const mat = makeTileMaterial(id).clone();
      const mesh = new THREE.Mesh(geo, mat);
      mesh.position.set(x + 0.5, 0, z + 0.5);
      mesh.receiveShadow = true;
      mesh.userData = { type: 'tile', x, z };
      scene.add(mesh);
      tileMeshes.push(mesh);
    }
  }
}

/** Update a single tile cell's material without rebuilding everything */
function updateTileMesh(x, z) {
  const idx  = z * GRID + x;
  const mesh = tileMeshes[idx];
  if (!mesh) return;
  const id   = tileGrid[z][x];
  mesh.material = makeTileMaterial(id).clone();
}

function paintCell(x, z, id, skipUndo = false) {
  const prev = tileGrid[z][x];
  if (prev === id) return;
  if (!skipUndo) pushUndo({ type: 'paint', x, z, prev, next: id });
  tileGrid[z][x] = id;
  updateTileMesh(x, z);
}

// ---------------------------------------------------------------------------
// Asset loading
// ---------------------------------------------------------------------------
const gltfLoader = new GLTFLoader();

function loadAsset(filename) {
  return new Promise((resolve, reject) => {
    if (assetCache[filename]) { resolve(assetCache[filename]); return; }
    gltfLoader.load(
      ASSET_BASE + filename,
      gltf => {
        const group = gltf.scene;
        group.traverse(n => {
          if (n.isMesh) { n.castShadow = true; n.receiveShadow = true; }
        });
        assetCache[filename] = group;
        resolve(group);
      },
      undefined,
      err => {
        // Create a bright placeholder box so we know it loaded
        console.warn(`[chunk-editor] Could not load ${filename}:`, err);
        const box  = new THREE.Mesh(
          new THREE.BoxGeometry(0.8, 1.2, 0.8),
          new THREE.MeshLambertMaterial({ color: '#ff6633' })
        );
        const g = new THREE.Group();
        g.add(box);
        box.position.y = 0.6;
        assetCache[filename] = g;
        resolve(g);
      }
    );
  });
}

function preloadAllAssets() {
  ASSET_FILES.forEach(f => loadAsset(f).catch(() => {}));
}

/** Compute XZ footprint of a scene object via Box3 */
function getFootprint(obj) {
  const box = new THREE.Box3().setFromObject(obj);
  return {
    w: box.max.x - box.min.x,  // X extent
    d: box.max.z - box.min.z,  // Z extent
    offsetX: -box.min.x,       // local offset so mesh origin aligns with min
    offsetZ: -box.min.z,
  };
}

// ---------------------------------------------------------------------------
// Asset placement
// ---------------------------------------------------------------------------
function snapToGrid(worldX, worldZ) {
  return {
    x: Math.floor(worldX) + 0.5,
    z: Math.floor(worldZ) + 0.5,
  };
}

function withinBounds(snappedX, snappedZ, footW, footD) {
  const minX = snappedX - footW / 2;
  const maxX = snappedX + footW / 2;
  const minZ = snappedZ - footD / 2;
  const maxZ = snappedZ + footD / 2;
  return minX >= 0 && maxX <= GRID && minZ >= 0 && maxZ <= GRID;
}

async function placeAsset(worldX, worldZ, filename, rotY = 0, scale = 1, skipUndo = false) {
  const { x: sx, z: sz } = snapToGrid(worldX, worldZ);
  const template = await loadAsset(filename);
  const instance = template.clone(true);
  instance.scale.setScalar(scale);
  instance.rotation.y = rotY;

  // Check bounds using footprint of a temporary positioned clone
  const fp = getFootprint(instance);
  if (!withinBounds(sx, sz, fp.w, fp.d)) {
    showToast('⚠ Placement exceeds chunk bounds!', 'warn');
    return null;
  }

  instance.position.set(sx, 0, sz);
  instance.userData = { type: 'placed', asset: filename, rotY, scale };
  scene.add(instance);

  const descriptor = { mesh: instance, asset: filename, pos: [sx, 0, sz], rotY, scale };
  placedObjects.push(descriptor);

  if (!skipUndo) pushUndo({ type: 'place', descriptor });

  return instance;
}

function removeObject(descriptor, skipUndo = false) {
  scene.remove(descriptor.mesh);
  const idx = placedObjects.indexOf(descriptor);
  if (idx !== -1) placedObjects.splice(idx, 1);
  selected.delete(descriptor.mesh);
  removeOutline(descriptor.mesh);
  if (!skipUndo) pushUndo({ type: 'remove', descriptor });
}

// ---------------------------------------------------------------------------
// Ghost / preview mesh
// ---------------------------------------------------------------------------
async function updateGhost(worldX, worldZ) {
  if (mode !== 'place' || !activeAsset) {
    if (ghostMesh) { scene.remove(ghostMesh); ghostMesh = null; }
    return;
  }
  const { x: sx, z: sz } = snapToGrid(worldX, worldZ);

  if (ghostMesh && ghostMesh.userData.asset !== activeAsset) {
    scene.remove(ghostMesh);
    ghostMesh = null;
  }

  if (!ghostMesh) {
    const template = await loadAsset(activeAsset);
    ghostMesh = template.clone(true);
    ghostMesh.traverse(n => {
      if (n.isMesh) {
        n.material = n.material.clone();
        n.material.transparent = true;
        n.material.opacity = 0.45;
      }
    });
    ghostMesh.userData.type = 'ghost';
    ghostMesh.userData.asset = activeAsset;
    scene.add(ghostMesh);
  }

  ghostMesh.position.set(sx, 0, sz);
  const fp = getFootprint(ghostMesh);
  ghostValid = withinBounds(sx, sz, fp.w, fp.d);

  ghostMesh.traverse(n => {
    if (n.isMesh) {
      n.material.color.set(ghostValid ? '#88ff88' : '#ff4444');
    }
  });
}

// ---------------------------------------------------------------------------
// Selection & outline
// ---------------------------------------------------------------------------
function makeOutlineMesh(mesh) {
  const box  = new THREE.Box3().setFromObject(mesh);
  const size = new THREE.Vector3();
  box.getSize(size);
  const center = new THREE.Vector3();
  box.getCenter(center);

  const geo = new THREE.BoxGeometry(size.x + 0.08, size.y + 0.08, size.z + 0.08);
  const mat = new THREE.MeshBasicMaterial({
    color: '#00e5ff', wireframe: true, depthTest: false,
  });
  const outline = new THREE.Mesh(geo, mat);
  outline.position.copy(center);
  return outline;
}

function addOutline(mesh) {
  if (selectionOutlines.has(mesh)) return;
  const o = makeOutlineMesh(mesh);
  scene.add(o);
  selectionOutlines.set(mesh, o);
}

function removeOutline(mesh) {
  const o = selectionOutlines.get(mesh);
  if (o) { scene.remove(o); selectionOutlines.delete(mesh); }
}

function syncOutline(mesh) {
  removeOutline(mesh);
  addOutline(mesh);
}

function clearSelection() {
  selected.forEach(m => removeOutline(m));
  selected.clear();
}

function selectObject(mesh, additive = false) {
  if (!additive) clearSelection();
  if (selected.has(mesh)) {
    selected.delete(mesh);
    removeOutline(mesh);
  } else {
    selected.add(mesh);
    addOutline(mesh);
  }
}

// ---------------------------------------------------------------------------
// Undo / redo
// ---------------------------------------------------------------------------
function pushUndo(action) {
  undoStack.push(action);
  redoStack.length = 0;  // clear redo on new action
  updateUndoButtons();
}

async function applyUndo(action) {
  switch (action.type) {
    case 'paint':
      tileGrid[action.z][action.x] = action.prev;
      updateTileMesh(action.x, action.z);
      break;
    case 'paint-stroke':
      for (let i = action.cells.length - 1; i >= 0; i -= 1) {
        const c = action.cells[i];
        tileGrid[c.z][c.x] = c.prev;
        updateTileMesh(c.x, c.z);
      }
      break;
    case 'place':
      removeObject(action.descriptor, true);
      break;
    case 'remove':
      // Re-place
      const d = action.descriptor;
      const m = await loadAsset(d.asset);
      const inst = m.clone(true);
      inst.position.set(...d.pos);
      inst.rotation.y = d.rotY;
      inst.scale.setScalar(d.scale);
      inst.userData = { type: 'placed', asset: d.asset, rotY: d.rotY, scale: d.scale };
      scene.add(inst);
      d.mesh = inst;
      placedObjects.push(d);
      break;
    case 'rotate':
      action.descriptor.mesh.rotation.y -= Math.PI / 2;
      action.descriptor.rotY -= Math.PI / 2;
      syncOutline(action.descriptor.mesh);
      break;
    case 'move':
      action.descriptor.mesh.position.copy(action.from);
      action.descriptor.pos = [action.from.x, action.from.y, action.from.z];
      syncOutline(action.descriptor.mesh);
      break;
  }
}

async function applyRedo(action) {
  switch (action.type) {
    case 'paint':
      tileGrid[action.z][action.x] = action.next;
      updateTileMesh(action.x, action.z);
      break;
    case 'paint-stroke':
      for (let i = 0; i < action.cells.length; i += 1) {
        const c = action.cells[i];
        tileGrid[c.z][c.x] = c.next;
        updateTileMesh(c.x, c.z);
      }
      break;
    case 'place':
      // Re-place
      const d2 = action.descriptor;
      const m2 = await loadAsset(d2.asset);
      const inst2 = m2.clone(true);
      inst2.position.set(...d2.pos);
      inst2.rotation.y = d2.rotY;
      inst2.scale.setScalar(d2.scale);
      inst2.userData = { type: 'placed', asset: d2.asset, rotY: d2.rotY, scale: d2.scale };
      scene.add(inst2);
      d2.mesh = inst2;
      placedObjects.push(d2);
      break;
    case 'remove':
      removeObject(action.descriptor, true);
      break;
    case 'rotate':
      action.descriptor.mesh.rotation.y += Math.PI / 2;
      action.descriptor.rotY += Math.PI / 2;
      syncOutline(action.descriptor.mesh);
      break;
    case 'move':
      action.descriptor.mesh.position.copy(action.to);
      action.descriptor.pos = [action.to.x, action.to.y, action.to.z];
      syncOutline(action.descriptor.mesh);
      break;
  }
}

async function undo() {
  if (!undoStack.length) return;
  const action = undoStack.pop();
  await applyUndo(action);
  redoStack.push(action);
  updateUndoButtons();
}

async function redo() {
  if (!redoStack.length) return;
  const action = redoStack.pop();
  await applyRedo(action);
  undoStack.push(action);
  updateUndoButtons();
}

function updateUndoButtons() {
  const u = document.getElementById('btn-undo');
  const r = document.getElementById('btn-redo');
  if (u) u.disabled = undoStack.length === 0;
  if (r) r.disabled = redoStack.length === 0;
}

// ---------------------------------------------------------------------------
// Keyboard shortcuts
// ---------------------------------------------------------------------------
window.addEventListener('keydown', e => {
  const tag = document.activeElement.tagName;
  if (tag === 'INPUT' || tag === 'SELECT' || tag === 'TEXTAREA') return;

  if ((e.ctrlKey || e.metaKey) && e.key === 'z') { e.preventDefault(); undo(); return; }
  if ((e.ctrlKey || e.metaKey) && e.key === 'y') { e.preventDefault(); redo(); return; }
  if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'Z') { e.preventDefault(); redo(); return; }

  if (e.key === 'Delete' || e.key === 'Backspace') {
    if (mode === 'select') deleteSelected();
  }
  if (e.key === 'r' || e.key === 'R') {
    if (mode === 'select') rotateSelected();
  }

  // Mode hotkeys
  const modeKeys = { 'p': 'paint', 'a': 'place', 's': 'select', 'v': 'rotate' };
  if (modeKeys[e.key]) setMode(modeKeys[e.key]);
});

// ---------------------------------------------------------------------------
// Pointer / raycasting
// ---------------------------------------------------------------------------
function getIntersects(event, targets) {
  const rect = renderer.domElement.getBoundingClientRect();
  mouse.x =  ((event.clientX - rect.left) / rect.width)  * 2 - 1;
  mouse.y = -((event.clientY - rect.top)  / rect.height) * 2 + 1;
  raycaster.setFromCamera(mouse, camera);
  return raycaster.intersectObjects(targets, true);
}

function getWorldFromGround(event) {
  const rect = renderer.domElement.getBoundingClientRect();
  mouse.x =  ((event.clientX - rect.left) / rect.width)  * 2 - 1;
  mouse.y = -((event.clientY - rect.top)  / rect.height) * 2 + 1;
  raycaster.setFromCamera(mouse, camera);
  const pt = new THREE.Vector3();
  raycaster.ray.intersectPlane(groundPlane, pt);
  return pt;
}

function clampToGrid(x, z) {
  return {
    x: Math.max(0.5, Math.min(GRID - 0.5, x)),
    z: Math.max(0.5, Math.min(GRID - 0.5, z)),
  };
}

function bindPointerEvents() {
  renderer.domElement.addEventListener('pointermove', async e => {
    if (mode === 'place') {
      const pt = getWorldFromGround(e);
      if (pt) await updateGhost(pt.x, pt.z);
    }

    if (mode === 'paint' && isPainting) {
      const hits = getIntersects(e, tileMeshes);
      if (hits.length > 0) {
        const { x, z } = hits[0].object.userData;
        paintCellStroke(x, z);
      }
    }

    if (isDragging && dragTargets.length > 0) {
      const pt = getWorldFromGround(e);
      if (!pt) return;
      const dx = pt.x - dragStart.x;
      const dz = pt.z - dragStart.z;
      dragTargets.forEach(desc => {
        const { x: sx, z: sz } = snapToGrid(desc._dragOrigin.x + dx, desc._dragOrigin.z + dz);
        const clamped = clampToGrid(sx, sz);
        desc.mesh.position.set(clamped.x, 0, clamped.z);
        syncOutline(desc.mesh);
      });
    }
  });

  renderer.domElement.addEventListener('pointerdown', e => {
    renderer.domElement.focus();
    if (e.button !== 0) return;

    if (mode === 'paint') {
      const hits = getIntersects(e, tileMeshes);
      isPainting = true;
      paintStroke = [];
      paintVisited.clear();
      if (hits.length > 0) {
        const { x, z } = hits[0].object.userData;
        paintCellStroke(x, z);
      }
      return;
    }

    if (mode === 'select') {
      const pt = getWorldFromGround(e);
      if (!pt) return;

      // Check placed objects first
      const placedMeshes = placedObjects.map(d => d.mesh);
      const hits = getIntersects(e, placedMeshes);
      if (hits.length > 0) {
        // Find root placed mesh
        let obj = hits[0].object;
        while (obj.parent && !placedObjects.find(d => d.mesh === obj)) obj = obj.parent;
        selectObject(obj, e.shiftKey);

        // Prepare drag
        isDragging    = true;
        dragStart.copy(pt);
        dragTargets = [...selected].map(m => {
          const desc = placedObjects.find(d => d.mesh === m);
          if (desc) { desc._dragOrigin = m.position.clone(); }
          return desc;
        }).filter(Boolean);
      } else {
        if (!e.shiftKey) clearSelection();
      }
    }
  });

  renderer.domElement.addEventListener('pointerup', async e => {
    if (e.button !== 0) return;

    if (mode === 'paint' && isPainting) {
      endPaintStroke();
      return;
    }

    if (isDragging) {
      // Commit drag positions
      dragTargets.forEach(desc => {
        const from = desc._dragOrigin;
        const to   = desc.mesh.position.clone();
        if (!from.equals(to)) {
          pushUndo({ type: 'move', descriptor: desc, from: from.clone(), to: to.clone() });
          desc.pos = [to.x, to.y, to.z];
        }
        delete desc._dragOrigin;
      });
      isDragging  = false;
      dragTargets = [];
      return;
    }

    if (mode === 'place') {
      if (!activeAsset) { showToast('No asset selected', 'warn'); return; }
      const pt = getWorldFromGround(e);
      if (pt) {
        controls.enabled = false;  // prevent orbit on click
        await placeAsset(pt.x, pt.z, activeAsset);
        setTimeout(() => { controls.enabled = true; }, 50);
      }
      return;
    }

    if (mode === 'rotate') {
      const placedMeshes = placedObjects.map(d => d.mesh);
      const hits = getIntersects(e, placedMeshes);
      if (hits.length > 0) {
        let obj = hits[0].object;
        while (obj.parent && !placedObjects.find(d => d.mesh === obj)) obj = obj.parent;
        const desc = placedObjects.find(d => d.mesh === obj);
        if (desc) rotateDescriptor(desc);
      }
    }
  });

  // Disable controls while interacting with UI
  renderer.domElement.addEventListener('contextmenu', e => e.preventDefault());
  renderer.domElement.addEventListener('pointerleave', () => {
    if (mode === 'paint' && isPainting) endPaintStroke();
  });
}

function paintCellStroke(x, z) {
  const key = `${x},${z}`;
  if (paintVisited.has(key)) return;
  const prev = tileGrid[z][x];
  if (prev === activeTileId) {
    paintVisited.add(key);
    return;
  }
  paintVisited.add(key);
  paintStroke.push({ x, z, prev, next: activeTileId });
  tileGrid[z][x] = activeTileId;
  updateTileMesh(x, z);
}

function endPaintStroke() {
  isPainting = false;
  if (paintStroke.length > 0) {
    pushUndo({ type: 'paint-stroke', cells: paintStroke });
  }
  paintStroke = [];
  paintVisited.clear();
}

// ---------------------------------------------------------------------------
// Rotate & Delete helpers
// ---------------------------------------------------------------------------
function rotateDescriptor(desc) {
  desc.mesh.rotation.y += Math.PI / 2;
  desc.rotY = desc.mesh.rotation.y;
  syncOutline(desc.mesh);
  pushUndo({ type: 'rotate', descriptor: desc });
}

function rotateSelected() {
  selected.forEach(m => {
    const desc = placedObjects.find(d => d.mesh === m);
    if (desc) rotateDescriptor(desc);
  });
}

function deleteSelected() {
  selected.forEach(m => {
    const desc = placedObjects.find(d => d.mesh === m);
    if (desc) removeObject(desc);
  });
}

// ---------------------------------------------------------------------------
// UI / Save + Load
// ---------------------------------------------------------------------------
function setMode(next) {
  if (mode === next) return;
  mode = next;
  if (mode !== 'place' && ghostMesh) {
    scene.remove(ghostMesh);
    ghostMesh = null;
    ghostValid = false;
  }
  if (mode !== 'select') clearSelection();
  updateHint();

  const ids = ['btn-mode-paint', 'btn-mode-place', 'btn-mode-select', 'btn-mode-rotate'];
  ids.forEach(id => {
    const b = document.getElementById(id);
    if (b) b.classList.toggle('ce-btn--active', id === `btn-mode-${mode}`);
  });
}

function updateHint() {
  const hint = document.getElementById('ce-hint');
  if (!hint) return;
  switch (mode) {
    case 'paint':
      hint.textContent = 'Paint mode: click or drag to paint tiles.';
      break;
    case 'place':
      hint.textContent = 'Place mode: hover to preview, click to place asset.';
      break;
    case 'select':
      hint.textContent = 'Select mode: click to select; drag to move; Del to delete.';
      break;
    case 'rotate':
      hint.textContent = 'Rotate mode: click an object to rotate 90�.';
      break;
    default:
      hint.textContent = '';
  }
}

function showToast(msg, type = 'info') {
  const el = document.getElementById('ce-toast');
  if (!el) return;
  el.textContent = msg;
  el.className = `ce-toast ce-toast--${type} ce-toast--visible`;
  clearTimeout(el._timer);
  el._timer = setTimeout(() => {
    el.className = `ce-toast ce-toast--${type}`;
  }, 2000);
}

function makeChunkData(name) {
  return {
    name,
    tiles: tileGrid,
    objects: placedObjects.map(d => ({
      asset: d.asset,
      pos: d.pos,
      rotY: d.rotY,
      scale: d.scale,
    })),
  };
}

function sanitizeName(raw) {
  const trimmed = (raw || '').trim();
  const safe = trimmed.replace(/[^a-zA-Z0-9_-]+/g, '-').replace(/^-+|-+$/g, '');
  return safe || 'chunk';
}

function saveJSON() {
  const nameInput = document.getElementById('ce-chunk-name');
  const name = sanitizeName(nameInput ? nameInput.value : '');
  if (nameInput) nameInput.value = name;
  const data = makeChunkData(name);
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  downloadBlob(blob, `${name}.json`);
}

function resetEditorState() {
  placedObjects.forEach(d => scene.remove(d.mesh));
  placedObjects.length = 0;
  clearSelection();
  selectionOutlines.clear();
  if (ghostMesh) { scene.remove(ghostMesh); ghostMesh = null; }
  ghostValid = false;

  isDragging = false;
  dragTargets = [];
  dragStart.set(0, 0, 0);

  isPainting = false;
  paintStroke = [];
  paintVisited.clear();

  undoStack.length = 0;
  redoStack.length = 0;
  updateUndoButtons();
}

async function loadJSONFile(file) {
  try {
    const text = await file.text();
    const data = JSON.parse(text);
    if (!data || !Array.isArray(data.tiles) || data.tiles.length !== GRID) {
      showToast('Invalid JSON: tiles must be 50x50', 'error');
      return;
    }
    if (!Array.isArray(data.objects)) {
      showToast('Invalid JSON: objects must be array', 'error');
      return;
    }
    for (let z = 0; z < GRID; z++) {
      if (!Array.isArray(data.tiles[z]) || data.tiles[z].length !== GRID) {
        showToast('Invalid JSON: tiles must be 50x50', 'error');
        return;
      }
    }

    resetEditorState();

    for (let z = 0; z < GRID; z++) {
      for (let x = 0; x < GRID; x++) {
        tileGrid[z][x] = data.tiles[z][x];
      }
    }
    buildTileGrid();

    for (const d of data.objects) {
      if (!d || !d.asset || !Array.isArray(d.pos)) continue;
      await placeAsset(d.pos[0], d.pos[2], d.asset, d.rotY || 0, d.scale || 1, true);
    }

    const nameInput = document.getElementById('ce-chunk-name');
    if (nameInput && data.name) nameInput.value = data.name;
    showToast('Loaded chunk', 'success');
  } catch (err) {
    console.error('[chunk-editor] load JSON error:', err);
    showToast('Failed to load JSON', 'error');
  }
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function buildUI() {
  const style = document.createElement('style');
  style.textContent = `
    body { margin: 0; overflow: hidden; font-family: system-ui, -apple-system, Segoe UI, sans-serif; }
    #ce-root { position: relative; width: 100vw; height: 100vh; }
    #canvas-container { position: absolute; inset: 0; }
    .ce-toolbar { position: absolute; top: 10px; left: 10px; z-index: 10; display: flex; flex-wrap: wrap; gap: 6px; align-items: center; padding: 8px 10px; background: rgba(18, 18, 28, 0.9); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; color: #e6e6e6; }
    .ce-label { font-size: 11px; letter-spacing: .04em; opacity: .8; }
    .ce-sep { width: 1px; height: 18px; background: rgba(255,255,255,0.12); margin: 0 4px; }
    .ce-btn { background: #1b1b2f; color: #e6e6e6; border: 1px solid #2c2c48; padding: 4px 8px; border-radius: 4px; cursor: pointer; font-size: 12px; }
    .ce-btn--active { background: #00bcd4; color: #081018; border-color: #00bcd4; }
    .ce-btn--export { background: rgba(0,229,255,.08); border-color: rgba(0,229,255,.4); }
    .ce-btn--danger { background: rgba(255,68,102,.08); border-color: rgba(255,68,102,.4); }
    .ce-select { background: #1b1b2f; color: #e6e6e6; border: 1px solid #2c2c48; padding: 4px 6px; border-radius: 4px; font-size: 12px; }
    #ce-hint { position: absolute; left: 10px; bottom: 10px; z-index: 10; background: rgba(18, 18, 28, 0.9); color: #e6e6e6; padding: 6px 10px; border-radius: 6px; font-size: 12px; }
    .ce-toast { position: absolute; right: 10px; top: 10px; z-index: 12; opacity: 0; transition: opacity .2s ease; background: rgba(18, 18, 28, 0.9); color: #e6e6e6; padding: 6px 10px; border-radius: 6px; font-size: 12px; }
    .ce-toast--visible { opacity: 1; }
    .ce-toast--error { background: rgba(120, 16, 24, 0.9); }
    .ce-toast--warn { background: rgba(120, 90, 16, 0.9); }
    .ce-toast--success { background: rgba(16, 110, 60, 0.9); }
  `;
  document.head.appendChild(style);

  const root = document.createElement('div');
  root.id = 'ce-root';
  document.body.appendChild(root);

  const canvasContainer = document.createElement('div');
  canvasContainer.id = 'canvas-container';
  root.appendChild(canvasContainer);

  const toolbar = document.createElement('div');
  toolbar.className = 'ce-toolbar';
  root.appendChild(toolbar);

  // Mode buttons
  toolbar.appendChild(makeLabel('MODE'));
  const btnPaint  = makeBtn('Paint',  'btn-mode-paint',  () => setMode('paint'));
  const btnPlace  = makeBtn('Place',  'btn-mode-place',  () => setMode('place'));
  const btnSelect = makeBtn('Select', 'btn-mode-select', () => setMode('select'));
  const btnRotate = makeBtn('Rotate', 'btn-mode-rotate', () => setMode('rotate'));
  toolbar.appendChild(btnPaint);
  toolbar.appendChild(btnPlace);
  toolbar.appendChild(btnSelect);
  toolbar.appendChild(btnRotate);

  toolbar.appendChild(makeSep());

  // Tile selector
  toolbar.appendChild(makeLabel('TILE'));
  const tileSelect = document.createElement('select');
  tileSelect.id = 'ce-tile-select';
  tileSelect.className = 'ce-select';
  TILE_DEFS.forEach(t => {
    const opt = document.createElement('option');
    opt.value = t.id;
    opt.textContent = t.label;
    tileSelect.appendChild(opt);
  });
  tileSelect.value = activeTileId;
  tileSelect.addEventListener('change', e => {
    activeTileId = e.target.value;
    if (mode !== 'paint') setMode('paint');
    else updateHint();
  });
  toolbar.appendChild(tileSelect);

  toolbar.appendChild(makeSep());

  // Asset selector
  toolbar.appendChild(makeLabel('ASSET'));
  const assetSelect = document.createElement('select');
  assetSelect.id = 'ce-asset-select';
  assetSelect.className = 'ce-select';
  if (ASSET_FILES.length === 0) {
    const opt = document.createElement('option');
    opt.value = '';
    opt.textContent = '(no assets)';
    assetSelect.appendChild(opt);
  } else {
    ASSET_FILES.forEach(f => {
      const opt = document.createElement('option');
      opt.value = f;
      opt.textContent = f;
      assetSelect.appendChild(opt);
    });
  }
  activeAsset = ASSET_FILES[0] || null;
  assetSelect.addEventListener('change', e => {
    activeAsset = e.target.value || null;
    if (mode !== 'place') {
      setMode('place');
    } else {
      if (ghostMesh) {
        scene.remove(ghostMesh);
        ghostMesh = null;
        ghostValid = false;
      }
      updateHint();
    }
  });
  toolbar.appendChild(assetSelect);

  toolbar.appendChild(makeSep());

  // Undo / redo
  toolbar.appendChild(makeLabel('HISTORY'));
  const btnUndo = makeBtn('Undo', 'btn-undo', async () => await undo());
  const btnRedo = makeBtn('Redo', 'btn-redo', async () => await redo());
  btnUndo.disabled = true;
  btnRedo.disabled = true;
  toolbar.appendChild(btnUndo);
  toolbar.appendChild(btnRedo);

  toolbar.appendChild(makeSep());

  // Selection helpers
  toolbar.appendChild(makeLabel('SELECTION'));
  const btnDel = makeBtn('Delete', null, deleteSelected, 'ce-btn ce-btn--danger');
  const btnRot = makeBtn('Rotate 90', null, rotateSelected);
  toolbar.appendChild(btnDel);
  toolbar.appendChild(btnRot);

  toolbar.appendChild(makeSep());

  // Save / Load
  toolbar.appendChild(makeLabel('CHUNK'));
  const nameInput = document.createElement('input');
  nameInput.id = 'ce-chunk-name';
  nameInput.className = 'ce-select';
  nameInput.placeholder = 'chunk-name';
  toolbar.appendChild(nameInput);

  const btnSave = makeBtn('Save', null, saveJSON, 'ce-btn ce-btn--export');
  toolbar.appendChild(btnSave);

  const fileInput = document.createElement('input');
  fileInput.type = 'file';
  fileInput.accept = '.json,application/json';
  fileInput.style.display = 'none';
  fileInput.addEventListener('change', e => {
    const file = e.target.files && e.target.files[0];
    if (file) loadJSONFile(file);
    e.target.value = '';
  });
  document.body.appendChild(fileInput);

  const btnLoad = makeBtn('Load', null, () => fileInput.click(), 'ce-btn ce-btn--export');
  toolbar.appendChild(btnLoad);

  const hint = document.createElement('div');
  hint.id = 'ce-hint';
  document.body.appendChild(hint);

  const toast = document.createElement('div');
  toast.id = 'ce-toast';
  toast.className = 'ce-toast';
  document.body.appendChild(toast);
}

// UI helpers
function makeSep() {
  const s = document.createElement('div');
  s.className = 'ce-sep';
  return s;
}

function makeLabel(text) {
  const l = document.createElement('span');
  l.className = 'ce-label';
  l.textContent = text;
  return l;
}

function makeBtn(label, id, onClick, cls = 'ce-btn') {
  const b = document.createElement('button');
  b.className = cls;
  if (id) b.id = id;
  b.textContent = label;
  b.addEventListener('click', onClick);
  return b;
}

// ---------------------------------------------------------------------------
// Render loop
// ---------------------------------------------------------------------------
function animate() {
  requestAnimationFrame(animate);

  // Arrow-key camera movement (ground plane)
  const moveSpeed = 0.12;
  if (keyState.size) {
    const forward = new THREE.Vector3();
    camera.getWorldDirection(forward);
    forward.y = 0;
    forward.normalize();
    const right = new THREE.Vector3().crossVectors(forward, new THREE.Vector3(0, 1, 0)).normalize();
    const delta = new THREE.Vector3();
    if (keyState.has('ArrowUp')) delta.add(forward);
    if (keyState.has('ArrowDown')) delta.addScaledVector(forward, -1);
    if (keyState.has('ArrowRight')) delta.add(right);
    if (keyState.has('ArrowLeft')) delta.addScaledVector(right, -1);
    if (delta.lengthSq() > 0) {
      delta.normalize().multiplyScalar(moveSpeed);
      camera.position.add(delta);
      controls.target.add(delta);
    }
  }

  // Sync outline positions (objects may drift due to orbit)
  selectionOutlines.forEach((outline, mesh) => {
    const box = new THREE.Box3().setFromObject(mesh);
    const center = new THREE.Vector3();
    box.getCenter(center);
    outline.position.copy(center);
  });

  controls.update();
  renderer.render(scene, camera);
}

// ---------------------------------------------------------------------------
// Bootstrap
// ---------------------------------------------------------------------------
async function main() {
  buildUI();
  initScene();
  bindPointerEvents();
  bindKeyControls();
  buildTileGrid();
  preloadAllAssets();
  setMode('paint');
  animate();
  showToast('Chunk editor ready - P/A/S/V to switch modes', 'info');
}

main();

// Keyboard WASD controls
function bindKeyControls() {
  window.addEventListener('keydown', e => {
    const tag = document.activeElement.tagName;
    if (tag === 'INPUT' || tag === 'SELECT' || tag === 'TEXTAREA') return;
    if (e.key === 'ArrowUp' || e.key === 'ArrowDown' || e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
      e.preventDefault();
      keyState.add(e.key);
    }
  });
  window.addEventListener('keyup', e => {
    if (keyState.has(e.key)) keyState.delete(e.key);
  });
}





