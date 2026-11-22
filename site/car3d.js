// The 2026 car in x-ray: translucent shell with a blue outline, chassis, steering and wheels inside.
// Loaded by site.js only when the viewer gets near the screen. Renders on demand: it turns slowly on its
// own (unless motion is paused or reduced), can be dragged, and stops drawing when off screen.
import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { MeshoptDecoder } from "three/addons/libs/meshopt_decoder.module.js";
import { RoomEnvironment } from "three/addons/environments/RoomEnvironment.js";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

export async function mount(root, motion) {
  const canvas = root.querySelector("canvas");
  const status = root.querySelector(".viewer-status");
  const dpr = Math.min(window.devicePixelRatio || 1, 1.5);

  const renderer = new THREE.WebGLRenderer({ canvas, antialias: dpr < 1.5, alpha: true, powerPreference: "high-performance" });
  renderer.setPixelRatio(dpr);
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.setClearColor(0x000000, 0);

  const scene = new THREE.Scene();
  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
  pmrem.dispose();
  scene.add(new THREE.HemisphereLight(0xdbe8ff, 0x08202f, 0.5));
  const key = new THREE.DirectionalLight(0xffffff, 1.6);
  key.position.set(4, 8, 5);
  scene.add(key);
  const rim = new THREE.DirectionalLight(0x5e97ff, 1.2);
  rim.position.set(-6, 3, -5);
  scene.add(rim);

  const camera = new THREE.PerspectiveCamera(30, 4 / 3, 0.05, 200);

  // ---- the model
  const gltf = await new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).loadAsync(root.dataset.src, (e) => {
    if (e.total) status.textContent = `Loading the 3D model… ${Math.round((100 * e.loaded) / e.total)}%`;
  });
  const car = gltf.scene;
  const glass = new THREE.MeshPhysicalMaterial({ color: "#cfe0ff", roughness: 0.12, metalness: 0, transparent: true,
    opacity: 0.1, depthWrite: false, side: THREE.DoubleSide });
  const outline = new THREE.LineBasicMaterial({ color: "#5e97ff", transparent: true, opacity: 0.55 });
  // everything inside in one brushed-silver material: the CAD colours (red and blue rims…) fight the x-ray look
  const metal = new THREE.MeshStandardMaterial({ color: "#c3cfda", metalness: 0.55, roughness: 0.38, envMapIntensity: 0.9 });
  car.traverse((o) => {
    if (!o.isMesh) return;
    const m = o.material;
    if (m && (m.transparent || m.opacity < 1)) {  // the body shell is the transparent material of the export
      o.material = glass;
      o.renderOrder = 2;
      o.add(new THREE.LineSegments(new THREE.EdgesGeometry(o.geometry, 35), outline));
    } else {
      o.material = metal;
    }
  });

  // centre it, wheels on y = 0
  const box = new THREE.Box3().setFromObject(car);
  const size = box.getSize(new THREE.Vector3()), centre = box.getCenter(new THREE.Vector3());
  const length = Math.max(size.x, size.z);
  car.position.set(-centre.x, -box.min.y, -centre.z);
  const holder = new THREE.Group();
  holder.add(car);
  scene.add(holder);

  // soft contact shadow
  const sc = document.createElement("canvas"); sc.width = sc.height = 128;
  const g = sc.getContext("2d"), grd = g.createRadialGradient(64, 64, 0, 64, 64, 64);
  grd.addColorStop(0, "rgba(0,0,0,0.55)"); grd.addColorStop(1, "rgba(0,0,0,0)");
  g.fillStyle = grd; g.fillRect(0, 0, 128, 128);
  const shadow = new THREE.Mesh(new THREE.PlaneGeometry(1, 1),
    new THREE.MeshBasicMaterial({ map: new THREE.CanvasTexture(sc), transparent: true, depthWrite: false }));
  shadow.rotation.x = -Math.PI / 2;
  shadow.scale.set(size.x * 1.4, size.z * 1.4, 1);
  shadow.position.y = 0.002;
  scene.add(shadow);

  // floor grid in the scene itself, so it turns with the camera; fog fades it into the background
  const grid = new THREE.GridHelper(Math.max(12, length * 5), Math.round(Math.max(12, length * 5) / 0.25), 0x5e97ff, 0x24506b);
  grid.material.transparent = true;
  grid.material.opacity = 0.55;
  grid.material.depthWrite = false;
  scene.add(grid);
  scene.fog = new THREE.Fog(0x0a2536, length * 2.2, length * 5.5);

  // camera framed on the bounding sphere, three-quarter view from the front
  const longX = size.x >= size.z;                 // which horizontal axis runs nose to tail
  const target = new THREE.Vector3(0, size.y * 0.35, 0);
  let framed = false;
  function frameCamera() {
    // fit the car's length across the view (narrow screens: across the narrower horizontal fov)
    const vfov = THREE.MathUtils.degToRad(camera.fov);
    const hfov = 2 * Math.atan(Math.tan(vfov / 2) * camera.aspect);
    const d = (length * 0.62) / Math.tan(Math.min(vfov, hfov) / 2);
    // first framing: three-quarter view from the front, a little from above; later: keep the user's angle
    const dir = framed ? camera.position.clone().sub(target) : new THREE.Vector3(longX ? 0.6 : 1, 0.42, longX ? 1 : 0.6);
    framed = true;
    camera.position.copy(target).addScaledVector(dir.normalize(), d);
  }

  // ---- controls: drag to turn, no zoom or pan (the page keeps the scroll wheel)
  const controls = new OrbitControls(camera, canvas);
  controls.enableZoom = false;
  controls.enablePan = false;
  controls.enableDamping = true;
  controls.dampingFactor = 0.08;
  controls.rotateSpeed = 0.7;
  controls.minPolarAngle = Math.PI * 0.22;
  controls.maxPolarAngle = Math.PI * 0.48;
  controls.autoRotateSpeed = 0.9;
  controls.target.copy(target);
  canvas.style.touchAction = "pan-y";  // vertical swipes still scroll the page on phones

  // ---- on-demand rendering
  let raf = 0, visible = true, settle = 0, interacting = false;
  function resize() {
    const w = root.clientWidth, h = root.clientHeight;
    if (!w || !h) return;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    frameCamera();
    kick();
  }
  function frame() {
    raf = 0;
    controls.autoRotate = !motion.paused && !interacting;
    controls.update();
    renderer.render(scene, camera);
    if (settle > 0) settle--;
    if (visible && !document.hidden && (controls.autoRotate || interacting || settle > 0)) kick();
  }
  function kick() { if (!raf) raf = requestAnimationFrame(frame); }

  controls.addEventListener("start", () => { interacting = true; root.classList.add("is-touched"); kick(); });
  controls.addEventListener("end", () => { interacting = false; settle = 90; kick(); });
  controls.addEventListener("change", kick);
  motion.subs.add(() => { settle = 30; kick(); });
  new ResizeObserver(resize).observe(root);
  new IntersectionObserver((es) => { visible = es[0].isIntersecting; if (visible) kick(); }).observe(root);
  document.addEventListener("visibilitychange", kick);

  resize();
  if (renderer.compileAsync) await renderer.compileAsync(scene, camera);  // shaders off the main thread where supported
  renderer.render(scene, camera);
  root.classList.add("is-ready");
  status.textContent = "3D model loaded.";
  kick();
}
