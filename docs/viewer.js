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
camera.position.set(14, 12, 18);

const controls = new OrbitControls(camera, renderer.domElement);
controls.target.set(0, 1, 2);
controls.update();

const hemi = new THREE.HemisphereLight(0xffffff, 0x444444, 0.9);
scene.add(hemi);

const dir = new THREE.DirectionalLight(0xffffff, 0.8);
dir.position.set(5, 10, 7);
scene.add(dir);

const grid = new THREE.GridHelper(80, 80, 0x999999, 0xcccccc);
scene.add(grid);

const loader = new GLTFLoader();
const url = new URLSearchParams(window.location.search).get("asset");

async function loadManifest() {
  const res = await fetch("./manifest.json");
  if (!res.ok) return null;
  return res.json();
}

function placeParkingLot(cars, aptBox) {
  const aptSize = new THREE.Vector3();
  aptBox.getSize(aptSize);
  const aptCenter = new THREE.Vector3();
  aptBox.getCenter(aptCenter);

  const carWidth = 1.7;
  const carDepth = 3.8;
  const gapX = carWidth + 6.0;
  const gapZ = carDepth + 5.0;

  const startX = aptCenter.x - gapX;
  const startZ = aptBox.max.z + 2.0 + carDepth * 0.5;

  cars.forEach((obj, i) => {
    const col = i % 3;
    const row = Math.floor(i / 3);
    obj.position.set(startX + col * gapX, 0, startZ + row * gapZ);
    obj.rotation.y = Math.PI/2; // Face towards apartment
  });
}

function placePark(items) {
  const startX = -5.0;
  const startZ = -8.0;
  const gap = 2.5;
  items.forEach((obj, i) => {
    obj.position.set(startX + (i % 3) * gap, 0, startZ + Math.floor(i / 3) * gap);
  });
}

function cloneFence(fence, count, spacing, rotationY, startX, startZ, axis = "x") {
  const pieces = [];
  for (let i = 0; i < count; i += 1) {
    const piece = fence.clone(true);
    if (axis === "x") piece.position.set(startX + i * spacing, 0, startZ);
    else piece.position.set(startX, 0, startZ + i * spacing);
    piece.rotation.y = rotationY;
    scene.add(piece);
    pieces.push(piece);
  }
  return pieces;
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
  const cars = [];
  const yardItems = [];
  const outsideItems = [];
  let apartment = null;
  let fence = null;
  for (const asset of manifest.assets) {
    await new Promise((resolve) => {
      loader.load(`./assets/${asset}`.replace("./assets/./", "./assets/"), (gltf) => {
        const sceneObj = gltf.scene;
        loaded.push(sceneObj);
        const name = asset.toLowerCase();
        if (name.includes("car_sedan") || name.includes("car_truck")) cars.push(sceneObj);
        else if (name.includes("apartment")) apartment = sceneObj;
        else if (name.includes("fence")) fence = sceneObj;
        else if (name.includes("tree_large")) yardItems.push(sceneObj);
        else if (name.includes("basketball")) yardItems.push(sceneObj);
        else if (name.includes("tree_small") || name.includes("tree_medium") || name.includes("fruit")) outsideItems.push(sceneObj);
        scene.add(gltf.scene);
        resolve();
      }, undefined, () => resolve());
    });
  }

  if (apartment) apartment.position.set(0, 0, 0);

  const aptBox = new THREE.Box3();
  if (apartment) aptBox.setFromObject(apartment);

  // Parking lot behind apartment, 2m offset
  if (apartment) placeParkingLot(cars.map((c) => c), aptBox);

  // Front yard fenced area (front = negative Z)
  if (apartment && fence) {
    const aptWidth = aptBox.max.x - aptBox.min.x;
    const yardWidth = Math.max(aptWidth + 2, 8);
    const yardDepth = 11;

    const frontZ = aptBox.min.z - 2.0;
    const backZ = frontZ - yardDepth;

    const leftX = aptBox.min.x - 1.0;
    const rightX = leftX + yardWidth;

    const fenceSpacing = 2.0;
    const countX = Math.ceil(yardWidth / fenceSpacing);
    const countZ = Math.ceil(yardDepth / fenceSpacing);
    const adjustX = (yardWidth - (countX-1) * fenceSpacing) * 0.5;
    const adjustZ = (yardDepth - (countZ-3) * fenceSpacing) * 0.5;

    // Front fence line
    cloneFence(fence, countX-1, fenceSpacing, 0, leftX + adjustX, backZ, "x");
    // Back fence line (near apartment front)
    cloneFence(fence, countX-1, fenceSpacing, 0, leftX + adjustX, frontZ, "x");
    // Left fence line
    cloneFence(fence, countZ-1, fenceSpacing, Math.PI / 2, leftX, backZ + adjustZ, "z");
    // Right fence line
    cloneFence(fence, countZ-1, fenceSpacing, Math.PI / 2, rightX, backZ + adjustZ, "z");

    // Inside yard: large tree + a few basketballs
    yardItems.forEach((obj, i) => {
      obj.position.set(leftX + 2 + i * 2.0, 0, backZ + 2.5);
    });

    // Outside yard: small + medium trees + apples
    outsideItems.forEach((obj, i) => {
      obj.position.set(leftX - 5 + (i % 3) * 3.0, 0, backZ - 3.0 - Math.floor(i / 3) * 2.5);
    });
  }
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
