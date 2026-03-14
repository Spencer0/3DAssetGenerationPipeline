/**
 * simulate.js
 * Basic prefab simulation playground (Katamari-style).
 */

import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.161.0/build/three.module.js';
import { GLTFLoader } from 'https://cdn.jsdelivr.net/npm/three@0.161.0/examples/jsm/loaders/GLTFLoader.js';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------
const GRID_CHUNKS = 10;     // 10x10 chunks
const CHUNK_SIZE = 50;      // 50m per chunk
const CELL = 1;
const WORLD_SIZE = GRID_CHUNKS * CHUNK_SIZE;
const PLAYER_RADIUS = 1;

const ASSET_BASE = 'assets/';
const PREFAB_BASE = 'assets/prefabs/';
const PREFAB_MANIFEST = `${PREFAB_BASE}manifest.json`;
const TEX_BASE = 'assets/textures/';

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------
let scene, camera, renderer;
const keyState = new Set();
const raycaster = new THREE.Raycaster();
const mouse = new THREE.Vector2();

const gltfLoader = new GLTFLoader();
const assetCache = {};
const collidables = []; // { mesh, box: THREE.Box3 }

let playerGroup;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function makeAABBFromCenter(center, size) {
  const half = size * 0.5;
  return new THREE.Box3(
    new THREE.Vector3(center.x - half, center.y - half, center.z - half),
    new THREE.Vector3(center.x + half, center.y + half, center.z + half)
  );
}

function aabbIntersects(a, b) {
  return (
    a.min.x <= b.max.x && a.max.x >= b.min.x &&
    a.min.y <= b.max.y && a.max.y >= b.min.y &&
    a.min.z <= b.max.z && a.max.z >= b.min.z
  );
}

// ---------------------------------------------------------------------------
// UI
// ---------------------------------------------------------------------------
function buildUI() {
  const style = document.createElement('style');
  style.textContent = `
    body { margin: 0; overflow: hidden; background: #ecebe4; font-family: system-ui, -apple-system, Segoe UI, sans-serif; }
    #hud { position: absolute; top: 10px; left: 10px; z-index: 10; background: rgba(20,20,26,.85); color: #eee; padding: 8px 10px; border-radius: 6px; font-size: 12px; }
    #hud a { color: #aee7ff; text-decoration: none; }
    #status { margin-top: 6px; opacity: .8; }
  `;
  document.head.appendChild(style);

  const hud = document.createElement('div');
  hud.id = 'hud';
  hud.innerHTML = `
    <div><strong>Simulate</strong> — WASD to roll, Arrow keys to move camera.</div>
    <div><a href="./index.html">Back to Home</a></div>
    <div id="status">Loading prefabs…</div>
  `;
  document.body.appendChild(hud);
}

function setStatus(text) {
  const el = document.getElementById('status');
  if (el) el.textContent = text;
}

// ---------------------------------------------------------------------------
// Scene setup
// ---------------------------------------------------------------------------
function initScene() {
  renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(window.devicePixelRatio);
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  document.body.appendChild(renderer.domElement);

  scene = new THREE.Scene();
  scene.background = new THREE.Color('#e7e5dc');
  scene.fog = new THREE.Fog('#e7e5dc', 120, 500);

  camera = new THREE.PerspectiveCamera(55, window.innerWidth / window.innerHeight, 0.1, 1000);
  camera.position.set(WORLD_SIZE * 0.5, 35, WORLD_SIZE * 0.5 + 40);

  // Lighting
  const hemi = new THREE.HemisphereLight('#f6f4ee', '#cfc9b8', 1.2);
  scene.add(hemi);

  const sun = new THREE.DirectionalLight('#ffffff', 2.0);
  sun.position.set(20, 40, 10);
  sun.castShadow = true;
  sun.shadow.mapSize.set(2048, 2048);
  sun.shadow.camera.near = 1;
  sun.shadow.camera.far = 200;
  sun.shadow.camera.left = sun.shadow.camera.bottom = -60;
  sun.shadow.camera.right = sun.shadow.camera.top = 60;
  scene.add(sun);

  // Ground
  const groundGeo = new THREE.PlaneGeometry(WORLD_SIZE, WORLD_SIZE);
  groundGeo.rotateX(-Math.PI / 2);
  const groundMat = new THREE.MeshLambertMaterial({ color: '#d9d6cc' });
  const ground = new THREE.Mesh(groundGeo, groundMat);
  ground.receiveShadow = true;
  ground.position.set(WORLD_SIZE / 2, 0, WORLD_SIZE / 2);
  scene.add(ground);

  const gridHelper = new THREE.GridHelper(WORLD_SIZE, GRID_CHUNKS * 5, '#c7c3b8', '#d7d3c8');
  gridHelper.position.set(WORLD_SIZE / 2, 0.002, WORLD_SIZE / 2);
  scene.add(gridHelper);

  window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  });
}

// ---------------------------------------------------------------------------
// Tile materials
// ---------------------------------------------------------------------------
const tileTexCache = {};
function tileColor(id) {
  if (id === 'road_center') return '#444455';
  if (id === 'road_dashed') return '#555566';
  return '#1a1a2e';
}

function makeTileMaterial(id) {
  if (!tileTexCache[id]) {
    const mat = new THREE.MeshLambertMaterial({ color: tileColor(id) });
    const texLoader = new THREE.TextureLoader();
    texLoader.load(
      `${TEX_BASE}${id}.png`,
      tex => { mat.map = tex; mat.needsUpdate = true; },
      undefined,
      () => { /* fallback */ }
    );
    tileTexCache[id] = mat;
  }
  return tileTexCache[id];
}

// ---------------------------------------------------------------------------
// Assets & prefabs
// ---------------------------------------------------------------------------
function loadAsset(filename) {
  return new Promise((resolve, reject) => {
    if (assetCache[filename]) { resolve(assetCache[filename]); return; }
    gltfLoader.load(
      ASSET_BASE + filename,
      gltf => {
        const group = gltf.scene;
        group.traverse(n => {
          if (n.isMesh) {
            n.castShadow = true;
            n.receiveShadow = true;
          }
        });
        assetCache[filename] = group;
        resolve(group);
      },
      undefined,
      err => reject(err)
    );
  });
}

async function loadPrefabList() {
  try {
    const res = await fetch(PREFAB_MANIFEST, { cache: 'no-store' });
    if (!res.ok) throw new Error('manifest not found');
    const data = await res.json();
    if (Array.isArray(data.prefabs) && data.prefabs.length > 0) return data.prefabs;
  } catch (err) {
    console.warn('[simulate] Prefab manifest missing, using default list.');
  }
  return ['suburb.json'];
}

async function loadPrefab(path) {
  const res = await fetch(`${PREFAB_BASE}${path}`, { cache: 'no-store' });
  if (!res.ok) throw new Error(`Failed to load prefab ${path}`);
  return res.json();
}

function addTileMesh(x, z, id) {
  if (id === 'empty') return;
  const geo = new THREE.PlaneGeometry(CELL, CELL);
  geo.rotateX(-Math.PI / 2);
  const mat = makeTileMaterial(id).clone();
  const mesh = new THREE.Mesh(geo, mat);
  mesh.position.set(x + 0.5, 0, z + 0.5);
  mesh.receiveShadow = true;
  scene.add(mesh);
}

async function addPrefabAt(prefab, offsetX, offsetZ) {
  // Tiles
  if (Array.isArray(prefab.tiles)) {
    for (let z = 0; z < prefab.tiles.length; z++) {
      const row = prefab.tiles[z];
      if (!Array.isArray(row)) continue;
      for (let x = 0; x < row.length; x++) {
        addTileMesh(offsetX + x, offsetZ + z, row[x]);
      }
    }
  }

  // Objects
  if (Array.isArray(prefab.objects)) {
    for (const obj of prefab.objects) {
      if (!obj || !obj.asset || !Array.isArray(obj.pos)) continue;
      try {
        const template = await loadAsset(obj.asset);
        const inst = template.clone(true);
        inst.position.set(obj.pos[0] + offsetX, obj.pos[1] || 0, obj.pos[2] + offsetZ);
        inst.rotation.y = obj.rotY || 0;
        const scale = obj.scale || 1;
        inst.scale.setScalar(scale);
        scene.add(inst);

        const box = new THREE.Box3().setFromObject(inst);
        collidables.push({ mesh: inst, box });
      } catch (err) {
        console.warn('[simulate] failed to load asset', obj.asset, err);
      }
    }
  }
}

async function buildWorld() {
  const prefabList = await loadPrefabList();
  setStatus(`Loading prefabs (${prefabList.length})…`);

  const prefabs = [];
  for (const p of prefabList) {
    try {
      const data = await loadPrefab(p);
      prefabs.push({ name: p, data });
    } catch (err) {
      console.warn('[simulate] prefab load failed', p, err);
    }
  }

  if (!prefabs.length) {
    setStatus('No prefabs found.');
    return;
  }

  setStatus('Spawning world…');
  let idx = 0;
  for (let gz = 0; gz < GRID_CHUNKS; gz++) {
    for (let gx = 0; gx < GRID_CHUNKS; gx++) {
      const prefab = prefabs[idx % prefabs.length].data;
      const offsetX = gx * CHUNK_SIZE;
      const offsetZ = gz * CHUNK_SIZE;
      await addPrefabAt(prefab, offsetX, offsetZ);
      idx += 1;
    }
  }
  setStatus(`World ready: ${GRID_CHUNKS}x${GRID_CHUNKS} chunks.`);
}

// ---------------------------------------------------------------------------
// Player
// ---------------------------------------------------------------------------
function spawnPlayer() {
  playerGroup = new THREE.Group();
  const geo = new THREE.SphereGeometry(PLAYER_RADIUS, 24, 18);
  const mat = new THREE.MeshStandardMaterial({ color: '#a2d9ff', roughness: 0.35, metalness: 0.1 });
  const sphere = new THREE.Mesh(geo, mat);
  sphere.castShadow = true;
  sphere.receiveShadow = true;
  playerGroup.add(sphere);
  playerGroup.position.set(WORLD_SIZE / 2, PLAYER_RADIUS, WORLD_SIZE / 2);
  scene.add(playerGroup);
}

// ---------------------------------------------------------------------------
// Input
// ---------------------------------------------------------------------------
function bindInput() {
  window.addEventListener('keydown', e => {
    keyState.add(e.key);
    if (['ArrowUp','ArrowDown','ArrowLeft','ArrowRight'].includes(e.key)) e.preventDefault();
  });
  window.addEventListener('keyup', e => keyState.delete(e.key));
}

// ---------------------------------------------------------------------------
// Update loop
// ---------------------------------------------------------------------------
function updatePlayer(dt) {
  const speed = 8; // meters per second
  const dx = (keyState.has('d') || keyState.has('D')) ? 1 : (keyState.has('a') || keyState.has('A')) ? -1 : 0;
  const dz = (keyState.has('s') || keyState.has('S')) ? 1 : (keyState.has('w') || keyState.has('W')) ? -1 : 0;

  if (dx === 0 && dz === 0) return;
  const dir = new THREE.Vector3(dx, 0, dz).normalize();
  const delta = dir.multiplyScalar(speed * dt);

  const next = playerGroup.position.clone().add(delta);
  next.x = clamp(next.x, PLAYER_RADIUS, WORLD_SIZE - PLAYER_RADIUS);
  next.z = clamp(next.z, PLAYER_RADIUS, WORLD_SIZE - PLAYER_RADIUS);

  // Roll the sphere
  const moveVec = next.clone().sub(playerGroup.position);
  if (moveVec.lengthSq() > 0) {
    const axis = new THREE.Vector3(moveVec.z, 0, -moveVec.x).normalize();
    const angle = moveVec.length() / PLAYER_RADIUS;
    playerGroup.children[0].rotateOnAxis(axis, angle);
  }
  playerGroup.position.copy(next);
}

function updateCamera(dt) {
  const camSpeed = 20;
  let dx = 0;
  let dz = 0;
  if (keyState.has('ArrowUp')) dz -= 1;
  if (keyState.has('ArrowDown')) dz += 1;
  if (keyState.has('ArrowLeft')) dx -= 1;
  if (keyState.has('ArrowRight')) dx += 1;
  if (dx !== 0 || dz !== 0) {
    const delta = new THREE.Vector3(dx, 0, dz).normalize().multiplyScalar(camSpeed * dt);
    camera.position.add(delta);
  }
  camera.lookAt(playerGroup.position);
}

function updateCollisions() {
  const playerBox = makeAABBFromCenter(playerGroup.position, PLAYER_RADIUS * 2);
  for (let i = collidables.length - 1; i >= 0; i--) {
    const item = collidables[i];
    if (aabbIntersects(playerBox, item.box)) {
      playerGroup.attach(item.mesh);
      collidables.splice(i, 1);
    }
  }
}

let lastTime = performance.now();
function animate() {
  requestAnimationFrame(animate);
  const now = performance.now();
  const dt = Math.min(0.05, (now - lastTime) / 1000);
  lastTime = now;

  updatePlayer(dt);
  updateCamera(dt);
  updateCollisions();

  renderer.render(scene, camera);
}

// ---------------------------------------------------------------------------
// Bootstrap
// ---------------------------------------------------------------------------
async function main() {
  buildUI();
  initScene();
  bindInput();
  spawnPlayer();
  await buildWorld();
  animate();
}

main();
