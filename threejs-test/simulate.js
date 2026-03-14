// simulate.js - Katamari-style world simulator
// Load via <script type="module" src="./simulate.js"></script> in simulate.html
// Expects importmap with "three" and "three/addons/" mapped to CDN

import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------
const CHUNK_SIZE = 50;        // meters per prefab chunk
const GRID_CHUNKS = 25;       // 10x10 grid of chunks
const WORLD_SIZE = CHUNK_SIZE * GRID_CHUNKS; // 500 m
const CELL_SIZE = 1;          // 1 m per tile
const PLAYER_RADIUS = 1;

const STREAM_RADIUS = 2;      // active chunk radius (1 => 3x3)
const CACHE_LIMIT = 16;       // max cached chunks

const PLAYER_SPEED = 100;      // m/s
const CAMERA_SPEED = 150;      // m/s

const ASSETS_BASE = './assets/';
const PREFABS_BASE = `${ASSETS_BASE}prefabs/`;
const TEXTURES_BASE = `${ASSETS_BASE}textures/`;
const MANIFEST_URL = `${PREFABS_BASE}manifest.json`;

const TILE_COLORS = {
  empty: 0x7caa4f,
  road_center: 0x444444,
  road_dashed: 0x555555,
  grass: 0x5fa832,
  water: 0x2255aa,
  sand: 0xe8d5a3,
  pavement: 0x999977,
};

// ---------------------------------------------------------------------------
// HUD / UI
// ---------------------------------------------------------------------------
function buildHUD() {
  const style = document.createElement('style');
  style.textContent = `
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { overflow: hidden; background: #000; font-family: system-ui, -apple-system, Segoe UI, sans-serif; }
    #hud {
      position: fixed; top: 0; left: 0; width: 100%; height: 100%;
      pointer-events: none; z-index: 10;
    }
    #status {
      position: absolute; top: 16px; left: 50%; transform: translateX(-50%);
      background: rgba(0,0,0,0.72); color: #7fff7f;
      padding: 8px 22px; border-radius: 4px; font-size: 13px;
      letter-spacing: 0.06em; border: 1px solid #2a2a2a;
      transition: opacity 0.4s;
    }
    #controls {
      position: absolute; bottom: 16px; left: 16px;
      background: rgba(0,0,0,0.65); color: #aaa;
      padding: 10px 16px; border-radius: 4px; font-size: 12px;
      line-height: 1.7; border: 1px solid #2a2a2a;
    }
    #controls span { color: #fff; }
    #score {
      position: absolute; top: 16px; right: 16px;
      background: rgba(0,0,0,0.65); color: #ffdd55;
      padding: 8px 18px; border-radius: 4px; font-size: 14px;
      letter-spacing: 0.08em; border: 1px solid #2a2a2a;
    }
    #home-link {
      position: absolute; bottom: 16px; right: 16px;
      pointer-events: all;
      background: rgba(0,0,0,0.72); color: #7fa8ff;
      padding: 8px 18px; border-radius: 4px; font-size: 12px;
      border: 1px solid #2a2a2a; text-decoration: none;
      transition: background 0.2s, color 0.2s;
    }
    #home-link:hover { background: #1a2a4a; color: #fff; }
  `;
  document.head.appendChild(style);

  const hud = document.createElement('div');
  hud.id = 'hud';
  hud.innerHTML = `
    <div id="status">Loading world...</div>
    <div id="controls">
      <span>WASD</span> Move &nbsp;|&nbsp; <span>Arrows</span> Camera &nbsp;|&nbsp; Roll into objects to collect
    </div>
    <div id="score">Collected: <span id="score-val">0</span></div>
    <a id="home-link" href="./index.html">Back to Home</a>
  `;
  document.body.appendChild(hud);

  return {
    setStatus(msg) { document.getElementById('status').textContent = msg; },
    hideStatus() { document.getElementById('status').style.opacity = '0'; },
    setScore(n) { document.getElementById('score-val').textContent = n; },
  };
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------
async function main() {
  const hud = buildHUD();

  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  document.body.appendChild(renderer.domElement);

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x87ceeb);
  scene.fog = new THREE.Fog(0x87ceeb, 80, 300);

  const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 800);
  const camOffset = new THREE.Vector3(0, 18, 22);
  camera.position.copy(camOffset);

  const hemiLight = new THREE.HemisphereLight(0xaaddff, 0x447722, 0.9);
  scene.add(hemiLight);

  const dirLight = new THREE.DirectionalLight(0xffffff, 1.2);
  dirLight.position.set(120, 200, 80);
  dirLight.castShadow = true;
  dirLight.shadow.mapSize.set(2048, 2048);
  dirLight.shadow.camera.near = 1;
  dirLight.shadow.camera.far = 600;
  dirLight.shadow.camera.left = -250;
  dirLight.shadow.camera.right = 250;
  dirLight.shadow.camera.top = 250;
  dirLight.shadow.camera.bottom = -250;
  scene.add(dirLight);

  const ambLight = new THREE.AmbientLight(0xffffff, 0.3);
  scene.add(ambLight);

  const groundGeo = new THREE.PlaneGeometry(WORLD_SIZE, WORLD_SIZE);
  const groundMat = new THREE.MeshLambertMaterial({ color: 0x6aaa42 });
  const ground = new THREE.Mesh(groundGeo, groundMat);
  ground.rotation.x = -Math.PI / 2;
  ground.position.set(WORLD_SIZE / 2, 0, WORLD_SIZE / 2);
  ground.receiveShadow = true;
  scene.add(ground);

  const gridHelper = new THREE.GridHelper(WORLD_SIZE, GRID_CHUNKS * 5, 0x333333, 0x222222);
  gridHelper.position.set(WORLD_SIZE / 2, 0.01, WORLD_SIZE / 2);
  gridHelper.material.opacity = 0.18;
  gridHelper.material.transparent = true;
  scene.add(gridHelper);

  window.addEventListener('resize', () => {
    renderer.setSize(window.innerWidth, window.innerHeight);
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
  });

  const texLoader = new THREE.TextureLoader();
  const texCache = {};
  async function loadTexture(name) {
    if (texCache[name]) return texCache[name];
    return new Promise(resolve => {
      texLoader.load(
        `${TEXTURES_BASE}${name}`,
        tex => { texCache[name] = tex; resolve(tex); },
        undefined,
        () => resolve(null)
      );
    });
  }

  const gltfLoader = new GLTFLoader();
  const modelCache = {};
  function loadModel(assetName) {
    if (modelCache[assetName]) return Promise.resolve(modelCache[assetName]);
    return new Promise(resolve => {
      gltfLoader.load(
        `${ASSETS_BASE}${assetName}`,
        gltf => { modelCache[assetName] = gltf; resolve(gltf); },
        undefined,
        err => { console.warn(`GLB load failed: ${assetName}`, err); resolve(null); }
      );
    });
  }

  // Load manifest
  hud.setStatus('Loading manifest...');
  let prefabFiles = ['suburb.json'];
  try {
    const mRes = await fetch(MANIFEST_URL);
    if (mRes.ok) {
      const mData = await mRes.json();
      if (Array.isArray(mData.prefabs) && mData.prefabs.length) {
        prefabFiles = mData.prefabs;
      }
    }
  } catch (e) {
    console.warn('Manifest missing, using fallback.', e);
  }

  // Load prefabs
  hud.setStatus(`Loading ${prefabFiles.length} prefab(s)...`);
  const prefabDefs = [];
  for (const pf of prefabFiles) {
    try {
      const res = await fetch(`${PREFABS_BASE}${pf}`);
      if (res.ok) prefabDefs.push(await res.json());
    } catch (e) {
      console.warn(`Prefab load failed: ${pf}`, e);
    }
  }
  if (!prefabDefs.length) {
    hud.setStatus('No prefabs loaded.');
    return;
  }

  // Tile batching
  const tileGeo = new THREE.PlaneGeometry(CELL_SIZE, CELL_SIZE);
  tileGeo.rotateX(-Math.PI / 2);
  const tilePadY = 0.005;
  const tileMatCache = {};
  let roadCenterTex = null;
  let roadDashedTex = null;
  let tileTexturesReady = false;

  async function ensureTileTextures() {
    if (tileTexturesReady) return;
    roadCenterTex = await loadTexture('road_center.png');
    roadDashedTex = await loadTexture('road_dashed.png');
    tileTexturesReady = true;
  }

  function getTileMaterial(type) {
    if (tileMatCache[type]) return tileMatCache[type];
    let mat;
    if (type === 'road_center' && roadCenterTex) {
      mat = new THREE.MeshLambertMaterial({ map: roadCenterTex });
    } else if (type === 'road_dashed' && roadDashedTex) {
      mat = new THREE.MeshLambertMaterial({ map: roadDashedTex });
    } else {
      mat = new THREE.MeshLambertMaterial({ color: TILE_COLORS[type] ?? 0x888888 });
    }
    tileMatCache[type] = mat;
    return mat;
  }

  function buildTileInstances(tiles, originX, originZ) {
    const typePositions = new Map();
    for (let z = 0; z < tiles.length; z++) {
      const row = tiles[z];
      for (let x = 0; x < row.length; x++) {
        const type = row[x];
        if (!type || type === 'empty') continue;
        if (!typePositions.has(type)) typePositions.set(type, []);
        typePositions.get(type).push({ x, z });
      }
    }

    const meshes = [];
    const tmp = new THREE.Object3D();
    typePositions.forEach((positions, type) => {
      const mat = getTileMaterial(type);
      const inst = new THREE.InstancedMesh(tileGeo, mat, positions.length);
      inst.receiveShadow = false;
      for (let i = 0; i < positions.length; i++) {
        const p = positions[i];
        tmp.position.set(
          originX + p.x * CELL_SIZE + CELL_SIZE / 2,
          tilePadY,
          originZ + p.z * CELL_SIZE + CELL_SIZE / 2
        );
        tmp.rotation.set(0, 0, 0);
        tmp.updateMatrix();
        inst.setMatrixAt(i, tmp.matrix);
      }
      inst.instanceMatrix.needsUpdate = true;
      meshes.push(inst);
    });
    return meshes;
  }

  // Chunk manager (streaming + cache)
  const chunkMap = new Map();
  const chunkCache = new Map();
  const cacheOrder = [];
  const loadingChunks = new Set();
  let activeChunkKeys = new Set();

  function chunkKey(cx, cz) { return `${cx},${cz}`; }
  function parseChunkKey(key) { return key.split(',').map(n => parseInt(n, 10)); }
  function inBounds(cx, cz) {
    return cx >= 0 && cz >= 0 && cx < GRID_CHUNKS && cz < GRID_CHUNKS;
  }

  function cachePush(key, record) {
    chunkCache.set(key, record);
    cacheOrder.push(key);
    if (cacheOrder.length > CACHE_LIMIT) {
      const evictKey = cacheOrder.shift();
      if (evictKey) chunkCache.delete(evictKey);
    }
  }

  function cachePop(key) {
    const rec = chunkCache.get(key);
    if (!rec) return null;
    chunkCache.delete(key);
    const idx = cacheOrder.indexOf(key);
    if (idx >= 0) cacheOrder.splice(idx, 1);
    return rec;
  }

  async function buildChunk(cx, cz) {
    const key = chunkKey(cx, cz);
    const group = new THREE.Group();
    group.name = `chunk-${key}`;

    const idx = (cz * GRID_CHUNKS + cx) % prefabDefs.length;
    const def = prefabDefs[idx] || {};
    const originX = cx * CHUNK_SIZE;
    const originZ = cz * CHUNK_SIZE;

    const collidables = [];

    if (Array.isArray(def.tiles)) {
      await ensureTileTextures();
      const tiles = buildTileInstances(def.tiles, originX, originZ);
      tiles.forEach(m => group.add(m));
    }

    if (Array.isArray(def.objects)) {
      for (const obj of def.objects) {
        const gltf = await loadModel(obj.asset);
        if (!gltf) continue;

        const mesh = gltf.scene.clone(true);
        mesh.position.set(
          originX + (obj.pos[0] ?? 0),
          obj.pos[1] ?? 0,
          originZ + (obj.pos[2] ?? 0)
        );
        mesh.rotation.y = obj.rotY ?? 0;
        const s = obj.scale ?? 1;
        mesh.scale.set(s, s, s);

        mesh.traverse(child => {
          if (child.isMesh) {
            child.castShadow = false;
            child.receiveShadow = false;
          }
        });
        group.add(mesh);

        const box = new THREE.Box3().setFromObject(mesh);
        collidables.push({ box, mesh });
      }
    }

    return { key, cx, cz, group, collidables, lastUsed: performance.now() };
  }

  async function ensureChunk(cx, cz) {
    if (!inBounds(cx, cz)) return;
    const key = chunkKey(cx, cz);
    if (chunkMap.has(key)) return;

    const cached = cachePop(key);
    if (cached) {
      chunkMap.set(key, cached);
      scene.add(cached.group);
      return;
    }

    if (loadingChunks.has(key)) return;
    loadingChunks.add(key);
    try {
      const rec = await buildChunk(cx, cz);
      chunkMap.set(key, rec);
      scene.add(rec.group);
    } catch (e) {
      console.warn('Chunk load failed', key, e);
    } finally {
      loadingChunks.delete(key);
    }
  }

  function unloadChunk(key) {
    const rec = chunkMap.get(key);
    if (!rec) return;
    scene.remove(rec.group);
    chunkMap.delete(key);
    rec.lastUsed = performance.now();
    cachePush(key, rec);
  }

  function computeActiveKeys(cx, cz) {
    const set = new Set();
    for (let dz = -STREAM_RADIUS; dz <= STREAM_RADIUS; dz++) {
      for (let dx = -STREAM_RADIUS; dx <= STREAM_RADIUS; dx++) {
        const nx = cx + dx;
        const nz = cz + dz;
        if (inBounds(nx, nz)) set.add(chunkKey(nx, nz));
      }
    }
    return set;
  }

  function syncActiveChunks(cx, cz) {
    const desired = computeActiveKeys(cx, cz);
    desired.forEach(key => {
      if (!activeChunkKeys.has(key)) {
        const [x, z] = parseChunkKey(key);
        ensureChunk(x, z);
      }
    });
    activeChunkKeys.forEach(key => {
      if (!desired.has(key)) unloadChunk(key);
    });
    activeChunkKeys = desired;
  }

  // Player
  const playerGroup = new THREE.Group();
  const playerGeo = new THREE.SphereGeometry(PLAYER_RADIUS, 20, 20);
  const playerMat = new THREE.MeshStandardMaterial({ color: 0xff4422, roughness: 0.5, metalness: 0.1 });
  const player = new THREE.Mesh(playerGeo, playerMat);
  player.castShadow = true;
  playerGroup.add(player);

  const spawnX = WORLD_SIZE / 2;
  const spawnZ = WORLD_SIZE / 2;
  playerGroup.position.set(spawnX, PLAYER_RADIUS, spawnZ);
  scene.add(playerGroup);

  const cameraAnchor = new THREE.Vector3(spawnX, 0, spawnZ);

  // Input state
  const keys = {};
  window.addEventListener('keydown', e => { keys[e.code] = true; });
  window.addEventListener('keyup', e => { keys[e.code] = false; });

  // Player AABB helper
  const playerBox = new THREE.Box3();

  let pickedCount = 0;
  let lastChunkX = -1;
  let lastChunkZ = -1;

  hud.setStatus('Streaming chunks...');

  function update(dt) {
    // Player movement (WASD)
    const moveDir = new THREE.Vector3();
    if (keys['KeyW']) moveDir.z -= 1;
    if (keys['KeyS']) moveDir.z += 1;
    if (keys['KeyA']) moveDir.x -= 1;
    if (keys['KeyD']) moveDir.x += 1;
    if (moveDir.lengthSq() > 0) {
      moveDir.normalize().multiplyScalar(PLAYER_SPEED * dt);
      playerGroup.position.add(moveDir);

      const rollAxis = new THREE.Vector3(moveDir.z, 0, -moveDir.x).normalize();
      const rollAngle = moveDir.length() / PLAYER_RADIUS;
      player.rotateOnWorldAxis(rollAxis, rollAngle);
    }

    // Clamp player within world
    const minB = PLAYER_RADIUS;
    const maxB = WORLD_SIZE - PLAYER_RADIUS;
    playerGroup.position.x = Math.max(minB, Math.min(maxB, playerGroup.position.x));
    playerGroup.position.z = Math.max(minB, Math.min(maxB, playerGroup.position.z));
    playerGroup.position.y = PLAYER_RADIUS;

    // Chunk streaming
    const cx = Math.floor(playerGroup.position.x / CHUNK_SIZE);
    const cz = Math.floor(playerGroup.position.z / CHUNK_SIZE);
    if (cx !== lastChunkX || cz !== lastChunkZ) {
      syncActiveChunks(cx, cz);
      lastChunkX = cx;
      lastChunkZ = cz;
    }

    // Camera movement (Arrow keys)
    if (keys['ArrowLeft']) cameraAnchor.x -= CAMERA_SPEED * dt;
    if (keys['ArrowRight']) cameraAnchor.x += CAMERA_SPEED * dt;
    if (keys['ArrowUp']) cameraAnchor.z -= CAMERA_SPEED * dt;
    if (keys['ArrowDown']) cameraAnchor.z += CAMERA_SPEED * dt;

    cameraAnchor.x = Math.max(0, Math.min(WORLD_SIZE, cameraAnchor.x));
    cameraAnchor.z = Math.max(0, Math.min(WORLD_SIZE, cameraAnchor.z));

    camera.position.set(
      playerGroup.position.x + (cameraAnchor.x - WORLD_SIZE / 2) * 0.3,
      camOffset.y,
      playerGroup.position.z + camOffset.z + (cameraAnchor.z - WORLD_SIZE / 2) * 0.3
    );
    camera.lookAt(playerGroup.position);

    // Collision detection (active chunks only)
    playerBox.setFromCenterAndSize(
      playerGroup.position,
      new THREE.Vector3(PLAYER_RADIUS * 2, PLAYER_RADIUS * 2, PLAYER_RADIUS * 2)
    );

    activeChunkKeys.forEach(key => {
      const rec = chunkMap.get(key);
      if (!rec) return;
      for (let i = rec.collidables.length - 1; i >= 0; i--) {
        const c = rec.collidables[i];
        if (playerBox.intersectsBox(c.box)) {
          playerGroup.attach(c.mesh);
          rec.collidables.splice(i, 1);
          pickedCount += 1;
          hud.setScore(pickedCount);
        }
      }
    });
  }

  const clock = new THREE.Clock();
  renderer.setAnimationLoop(() => {
    const dt = Math.min(clock.getDelta(), 0.1);
    update(dt);
    renderer.render(scene, camera);
  });

  // Initial chunk load
  syncActiveChunks(Math.floor(spawnX / CHUNK_SIZE), Math.floor(spawnZ / CHUNK_SIZE));
  hud.setStatus('World ready. Roll around to collect objects.');
  setTimeout(() => hud.hideStatus(), 3000);
}

main().catch(err => {
  console.error('Simulator error:', err);
  const statusEl = document.getElementById('status');
  if (statusEl) statusEl.textContent = `Error: ${err.message}`;
});
