import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(window.devicePixelRatio);
document.body.appendChild(renderer.domElement);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0xf0efe9);

const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 200);
camera.position.set(8, 7, 8);

const controls = new OrbitControls(camera, renderer.domElement);
controls.target.set(0, 1, 0);
controls.update();

const hemi = new THREE.HemisphereLight(0xffffff, 0x444444, 0.9);
scene.add(hemi);

const dir = new THREE.DirectionalLight(0xffffff, 0.8);
dir.position.set(5, 10, 7);
scene.add(dir);

const grid = new THREE.GridHelper(40, 40, 0x999999, 0xcccccc);
scene.add(grid);

const loader = new GLTFLoader();
const url = new URLSearchParams(window.location.search).get("asset");

async function loadManifest() {
  const res = await fetch("./manifest.json");
  if (!res.ok) return null;
  return res.json();
}

function placeInGrid(objects, columns = 3, spacing = 4) {
  objects.forEach((obj, i) => {
    const col = i % columns;
    const row = Math.floor(i / columns);
    obj.position.set(col * spacing, 0, row * spacing);
  });
}

async function loadAssets() {
  if (url) {
    loader.load(`./assets/${url}`.replace("./assets/./", "./assets/"), (gltf) => {
      scene.add(gltf.scene);
    });
    return;
  }

  const manifest = await loadManifest();
  if (!manifest || !manifest.assets || manifest.assets.length === 0) {
    console.warn("No manifest or empty assets list.");
    return;
  }

  const loaded = [];
  for (const asset of manifest.assets) {
    await new Promise((resolve) => {
      loader.load(`./assets/${asset}`.replace("./assets/./", "./assets/"), (gltf) => {
        loaded.push(gltf.scene);
        scene.add(gltf.scene);
        resolve();
      }, undefined, () => resolve());
    });
  }

  placeInGrid(loaded, 3, 5);
}

loadAssets();

function onResize() {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
}
window.addEventListener("resize", onResize);

function tick() {
  renderer.render(scene, camera);
  requestAnimationFrame(tick);
}

tick();
