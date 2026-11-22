// 3D hero: the 2026 car in x-ray, parked on the start line; scrolling first orbits it and then follows it
// around the course (Indianapolis on the home page, Silesia Ring on the ADC page).
// Falls back to the static course outline without WebGL, and holds still with reduced motion or the pause button.
import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { MeshoptDecoder } from "three/addons/libs/meshopt_decoder.module.js";
import { RoomEnvironment } from "three/addons/environments/RoomEnvironment.js";

const root = document.querySelector("[data-hero3d]");
const base = root ? root.dataset.base || "" : "";
const reduce = window.matchMedia("(prefers-reduced-motion: reduce)");
const PAUSE_KEY = "elyos-motion-paused";

function webglOK() {
  try { const c = document.createElement("canvas"); return !!(c.getContext("webgl2") || c.getContext("webgl")); }
  catch (e) { return false; }
}

if (root && webglOK()) start().catch((e) => console.warn("hero3d:", e));

async function start() {
  const trackKey = root.dataset.track;
  const tracks = await (await fetch(base + "tracks.json")).json();
  const T = tracks[trackKey].path3d;
  const closed = tracks[trackKey].closed;

  // ---- course in three.js coordinates: X = east, Y = up, Z = -north
  const n = T.x.length;
  const P = [];
  for (let i = 0; i < n; i++) P.push(new THREE.Vector3(T.x[i], T.z[i], -T.y[i]));
  const s = [0];
  for (let i = 1; i < n; i++) s.push(s[i - 1] + P[i].distanceTo(P[i - 1]));
  const L = s[n - 1] + (closed ? P[0].distanceTo(P[n - 1]) : 0);

  // time warp from a simple curvature-limited speed (a_lat = 2 m/s², v ≤ 9 m/s): slower through corners
  const t = [0];
  for (let i = 1; i < n; i++) {
    const k = Math.abs(T.k[i]);
    const v = Math.max(3, Math.min(9, Math.sqrt(2 / Math.max(k, 1e-6))));
    t.push(t[i - 1] + (s[i] - s[i - 1]) / v);
  }
  const tEnd = t[n - 1];

  function sample(frac) {  // position and heading at a fraction of the run, in time
    const tt = Math.min(Math.max(frac, 0), 1) * tEnd;
    let i = 1;
    while (i < n - 1 && t[i] < tt) i++;
    const a = (tt - t[i - 1]) / Math.max(t[i] - t[i - 1], 1e-9);
    const pos = P[i - 1].clone().lerp(P[i], a);
    const dir = P[Math.min(i + 2, n - 1)].clone().sub(P[Math.max(i - 2, 0)]).setY(0).normalize();
    return { pos, dir, dist: s[i - 1] + a * (s[i] - s[i - 1]) };
  }

  // ---- renderer and scene
  const canvas = root.querySelector("canvas");
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false, powerPreference: "high-performance" });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.75));
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  const scene = new THREE.Scene();
  const deep = new THREE.Color("#08202f");
  scene.background = deep;
  scene.fog = new THREE.Fog(deep, 40, 320);
  scene.environment = new THREE.PMREMGenerator(renderer).fromScene(new RoomEnvironment(), 0.04).texture;
  scene.add(new THREE.HemisphereLight(0xdbe8ff, 0x08202f, 0.25));
  const sun = new THREE.DirectionalLight(0xffffff, 1.4);
  sun.position.set(30, 60, 20);
  scene.add(sun);
  const camera = new THREE.PerspectiveCamera(40, 1, 0.05, 2000);

  // ground, asphalt ribbon, signal-blue edges, checkered line
  const ground = new THREE.Mesh(new THREE.PlaneGeometry(6000, 6000), new THREE.MeshStandardMaterial({ color: "#081c29", roughness: 1, envMapIntensity: 0.2 }));
  ground.rotation.x = -Math.PI / 2;
  ground.position.y = -0.05;
  scene.add(ground);

  const W = 4;  // half width of the course (m), assumed
  const ribbon = [], left = [], right = [];
  const loopIdx = closed ? [...Array(n).keys(), 0] : [...Array(n).keys()];
  loopIdx.forEach((i, j) => {
    const prev = P[loopIdx[Math.max(j - 1, 0)]], next = P[loopIdx[Math.min(j + 1, loopIdx.length - 1)]];
    const tan = next.clone().sub(prev).setY(0).normalize();
    const nor = new THREE.Vector3(-tan.z, 0, tan.x);
    const l = P[i].clone().addScaledVector(nor, W), r = P[i].clone().addScaledVector(nor, -W);
    left.push(l.clone().setY(l.y + 0.03)); right.push(r.clone().setY(r.y + 0.03));
    ribbon.push(l, r);
  });
  const g = new THREE.BufferGeometry().setFromPoints(ribbon);
  const idx = [];
  for (let j = 0; j < loopIdx.length - 1; j++) { const a = 2 * j; idx.push(a, a + 1, a + 2, a + 1, a + 3, a + 2); }
  g.setIndex(idx); g.computeVertexNormals();
  scene.add(new THREE.Mesh(g, new THREE.MeshStandardMaterial({ color: "#123044", roughness: 0.95, envMapIntensity: 0.25, side: THREE.DoubleSide })));
  const edgeMat = new THREE.LineBasicMaterial({ color: "#5e97ff" });
  scene.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(left), edgeMat));
  scene.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(right), edgeMat));

  function checkered(at, dir) {
    const c = document.createElement("canvas"); c.width = 256; c.height = 32;
    const x = c.getContext("2d");
    for (let i = 0; i < 16; i++) for (let j = 0; j < 2; j++) { x.fillStyle = (i + j) % 2 ? "#ffffff" : "#000000"; x.fillRect(i * 16, j * 16, 16, 16); }
    const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace;
    const m = new THREE.Mesh(new THREE.PlaneGeometry(2 * W, 0.6), new THREE.MeshBasicMaterial({ map: tex }));
    m.rotation.x = -Math.PI / 2;
    m.rotation.z = Math.atan2(dir.x, dir.z) + Math.PI / 2;
    m.position.copy(at).setY(at.y + 0.04);
    scene.add(m);
  }
  const startS = sample(0), endS = sample(1);
  checkered(closed ? startS.pos : endS.pos, closed ? startS.dir : endS.dir);

  // ---- the car, in x-ray
  const gltf = await new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).loadAsync(base + "assets/car.glb");
  const car = gltf.scene;
  const glass = new THREE.MeshPhysicalMaterial({ color: "#cfe0ff", roughness: 0.15, metalness: 0, transparent: true,
    opacity: 0.12, depthWrite: false, side: THREE.DoubleSide });
  const outline = new THREE.LineBasicMaterial({ color: "#5e97ff", transparent: true, opacity: 0.45 });
  car.traverse((o) => {
    if (!o.isMesh) return;
    const m = o.material;
    if (m && (m.transparent || m.opacity < 1)) {  // the body shell is the transparent material of the export
      o.material = glass;
      o.renderOrder = 2;
      const e = new THREE.LineSegments(new THREE.EdgesGeometry(o.geometry, 35), outline);
      o.add(e);
    }
  });
  const box = new THREE.Box3().setFromObject(car);
  const holder = new THREE.Group();
  car.position.y = -box.min.y;  // wheels on the ground
  holder.add(car);
  scene.add(holder);

  // ---- motion state
  const btn = root.querySelector(".motion-toggle");
  let paused = reduce.matches || localStorage.getItem(PAUSE_KEY) === "1";
  function syncBtn() { if (btn) { btn.setAttribute("aria-pressed", String(paused)); btn.textContent = paused ? "Play motion" : "Pause motion"; } }
  syncBtn();
  if (btn) btn.addEventListener("click", () => { paused = !paused; localStorage.setItem(PAUSE_KEY, paused ? "1" : "0"); syncBtn(); kick(); });
  reduce.addEventListener("change", () => { paused = reduce.matches; syncBtn(); kick(); });
  const readout = root.querySelector(".readout");

  const forced = new URLSearchParams(location.search).get("hero");  // ?hero=0.5 pins the scroll progress (QA)
  function progress() {
    if (forced !== null) return Math.min(Math.max(parseFloat(forced) || 0, 0), 1);
    const r = root.getBoundingClientRect();
    const span = Math.max(root.offsetHeight - window.innerHeight, 1);
    return Math.min(Math.max(-r.top / span, 0), 1);
  }

  function resize() {
    const w = canvas.clientWidth, h = canvas.clientHeight;
    if (canvas.width !== Math.round(w * renderer.getPixelRatio()) || canvas.height !== Math.round(h * renderer.getPixelRatio())) {
      renderer.setSize(w, h, false);
      camera.aspect = w / h; camera.updateProjectionMatrix();
    }
  }

  const ORBIT_END = 0.22, BLEND_END = 0.32;
  let idle = 0, last = performance.now(), visible = true, raf = 0;
  const camPos = new THREE.Vector3(), look = new THREE.Vector3();

  function frame(now) {
    raf = 0;
    resize();
    const dt = Math.min((now - last) / 1000, 0.1); last = now;
    const p = paused && forced === null ? 0 : progress();
    if (!paused && p === 0 && forced === null) idle += dt * 0.25;  // slow turntable while waiting at the top

    const runFrac = p <= BLEND_END ? 0 : (p - BLEND_END) / (1 - BLEND_END);
    const st = sample(runFrac);
    holder.position.copy(st.pos);
    holder.rotation.y = Math.atan2(st.dir.x, st.dir.z);

    // orbit camera around the parked car
    const ang = 0.9 + idle + (Math.min(p, ORBIT_END) / ORBIT_END) * Math.PI * 1.15;
    const R = 5.2 * Math.max(1, 1.1 / camera.aspect);  // portrait screens: step back so the whole car fits
    const orbit = new THREE.Vector3(Math.sin(ang) * R, 1.9 * Math.min(R / 5.2, 1.6), Math.cos(ang) * R).add(st.pos);
    // chase camera behind and above
    const chase = st.pos.clone().addScaledVector(st.dir, -9).setY(st.pos.y + 1.7);
    const b = p <= ORBIT_END ? 0 : Math.min((p - ORBIT_END) / (BLEND_END - ORBIT_END), 1);
    const e = b * b * (3 - 2 * b);
    camPos.copy(orbit).lerp(chase, e);
    look.copy(st.pos).setY(st.pos.y + 0.6).addScaledVector(st.dir, e * 18);
    camera.position.copy(camPos);
    camera.lookAt(look);
    renderer.render(scene, camera);

    if (readout) {
      const d = Math.round(runFrac === 0 ? 0 : st.dist);
      readout.textContent = closed
        ? `Lap distance ${d.toLocaleString("en-US")} m of ${Math.round(L).toLocaleString("en-US")} m`
        : `Distance ${d.toLocaleString("en-US")} m of ${Math.round(L).toLocaleString("en-US")} m`;
    }
    if (visible && !paused && p === 0) kick();  // keep the turntable going only while idle at the top
  }
  function kick() { if (!raf) raf = requestAnimationFrame(frame); }

  window.addEventListener("scroll", kick, { passive: true });
  window.addEventListener("resize", kick);
  new IntersectionObserver((es) => { visible = es[0].isIntersecting; if (visible) kick(); }).observe(root);
  root.classList.add("is-3d");
  kick();
}
