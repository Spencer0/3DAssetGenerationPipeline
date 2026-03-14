import * as THREE from "https://unpkg.com/three@0.161.0/build/three.module.js";

export const GRID_SIZE = 1;
export const CHUNK_SIZE = 50;

export const TILE_IDS = [
  "empty",
  "road_center",
  "road_dashed"
];

export function createTileMaterials(basePath = "./assets/textures") {
  const loader = new THREE.TextureLoader();
  const materials = new Map();

  for (const id of TILE_IDS) {
    if (id === "empty") continue;
    const tex = loader.load(`${basePath}/${id}.png`);
    tex.wrapS = THREE.ClampToEdgeWrapping;
    tex.wrapT = THREE.ClampToEdgeWrapping;
    tex.magFilter = THREE.NearestFilter;
    tex.minFilter = THREE.NearestMipMapNearestFilter;
    materials.set(id, new THREE.MeshStandardMaterial({ map: tex }));
  }

  return materials;
}

export function computeFootprint(object3d) {
  const box = new THREE.Box3().setFromObject(object3d);
  const size = new THREE.Vector3();
  box.getSize(size);
  return { width: size.x, depth: size.z };
}

export function snapToGrid(value, gridSize = GRID_SIZE) {
  return Math.round(value / gridSize) * gridSize;
}

export function snapVectorToGrid(vec3, gridSize = GRID_SIZE) {
  vec3.x = snapToGrid(vec3.x, gridSize);
  vec3.z = snapToGrid(vec3.z, gridSize);
  return vec3;
}

export function isWithinChunk(pos, footprint, chunkSize = CHUNK_SIZE) {
  const half = chunkSize * 0.5;
  const minX = pos.x - footprint.width * 0.5;
  const maxX = pos.x + footprint.width * 0.5;
  const minZ = pos.z - footprint.depth * 0.5;
  const maxZ = pos.z + footprint.depth * 0.5;
  return minX >= -half && maxX <= half && minZ >= -half && maxZ <= half;
}

export function makeEmptyChunk() {
  const tiles = [];
  for (let z = 0; z < CHUNK_SIZE; z += 1) {
    const row = [];
    for (let x = 0; x < CHUNK_SIZE; x += 1) row.push("empty");
    tiles.push(row);
  }
  return { tiles, objects: [] };
}

// Export the provided group as a GLB. GLTFExporter must be supplied by caller.
export function exportChunkGLB(group, GLTFExporterClass, filename = "chunk.glb") {
  const exporter = new GLTFExporterClass();
  exporter.parse(
    group,
    (result) => {
      const blob = new Blob([result], { type: "model/gltf-binary" });
      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(link.href);
    },
    { binary: true }
  );
}
