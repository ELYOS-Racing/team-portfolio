// Elyos Racing Team site: entrance gate, scroll reveals, counters, the circuit hero and the lazy 3D car.
// Everything is progressive: without this file the pages are complete and static.
(() => {
  "use strict";
  const doc = document.documentElement;
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)");
  const PAUSE_KEY = "elyos-motion-paused";
  const SCRIPT_URL = document.currentScript ? document.currentScript.src : location.href;

  // ------------------------------------------------------------ entrance gate
  // The hero copy waits for Archivo (max 800 ms) so it never appears in the fallback face and then jumps.
  const gate = new Promise((resolve) => {
    setTimeout(resolve, 800);
    if (document.fonts && document.fonts.load) {
      Promise.all([document.fonts.load('850 1em "Archivo"'), document.fonts.load('400 1em "Archivo"')])
        .then(() => document.fonts.ready).then(resolve, resolve);
    } else resolve();
  });
  gate.then(() => requestAnimationFrame(() => doc.classList.add("is-ready")));

  // ------------------------------------------------------------ scroll reveals (+ counters)
  const revealables = document.querySelectorAll("[data-reveal]");
  revealables.forEach((el) => {  // stagger siblings that reveal together
    const sibs = [...el.parentElement.children].filter((c) => c.hasAttribute("data-reveal"));
    if (sibs.length > 1) el.style.setProperty("--i", Math.min(sibs.indexOf(el), 6));
  });
  const counters = new Map();
  if (!reduce.matches) document.querySelectorAll("[data-count]").forEach((el) => {
    counters.set(el.closest("[data-reveal]") || el, el);
    el.textContent = "0";
  });
  function countUp(el) {
    const target = +el.dataset.count, t0 = performance.now(), dur = 1300;
    const step = (now) => {
      const x = Math.min((now - t0) / dur, 1);
      el.textContent = Math.round(target * (1 - Math.pow(2, -10 * x))).toLocaleString("en-US");
      if (x < 1) requestAnimationFrame(step); else el.textContent = target.toLocaleString("en-US");
    };
    requestAnimationFrame(step);
  }
  function reveal(el) {
    el.classList.add("is-in");
    const c = counters.get(el);
    if (c) { counters.delete(el); setTimeout(() => countUp(c), 150); }
  }
  if ("IntersectionObserver" in window) {
    const io = new IntersectionObserver((entries) => entries.forEach((e) => {
      if (e.isIntersecting) { reveal(e.target); io.unobserve(e.target); }
    }), { rootMargin: "0px 0px -8% 0px", threshold: 0.12 });
    revealables.forEach((el) => io.observe(el));
  } else revealables.forEach(reveal);

  // ------------------------------------------------------------ motion preference (shared by hero and car)
  const motion = {
    paused: reduce.matches || localStorage.getItem(PAUSE_KEY) === "1",
    subs: new Set(),
    set(p, remember) {
      this.paused = p;
      if (remember) try { localStorage.setItem(PAUSE_KEY, p ? "1" : "0"); } catch (e) { /* private mode */ }
      this.subs.forEach((f) => f(p));
    },
  };
  reduce.addEventListener("change", () => motion.set(reduce.matches, false));
  window.elyosMotion = motion;

  // ------------------------------------------------------------ circuit hero
  const hero = document.querySelector("[data-circuit]");
  if (hero) circuit(hero);

  function circuit(root) {
    const svg = root.querySelector(".hero-svg");
    const lap = svg.querySelector(".lap"), trail = svg.querySelector(".trail"), car = svg.querySelector(".car");
    const btn = root.querySelector(".motion-toggle");
    const ds = root.dataset, laps = mode() === "laps";
    function mode() { return ds.mode; }
    const LAPS = +ds.laps || 1, TOTAL_KM = +ds.totalKm || 0, LEN_M = +ds.lengthM, VMAX = (+ds.vmax || 30) / 3.6;
    const hud = {};
    root.querySelectorAll("[data-hud]").forEach((el) => { hud[el.dataset.hud] = el; });

    // --- the course: the path is a polyline, read its vertices and resample them evenly by arc length
    const raw = (lap.getAttribute("d").match(/-?\d+(?:\.\d+)?/g) || []).map(Number);
    const vx = [], vy = [];
    for (let i = 0; i + 1 < raw.length; i += 2) { vx.push(raw[i]); vy.push(raw[i + 1]); }
    if (laps) { vx.push(vx[0]); vy.push(vy[0]); }
    const cum = [0];
    for (let i = 1; i < vx.length; i++) cum.push(cum[i - 1] + Math.hypot(vx[i] - vx[i - 1], vy[i] - vy[i - 1]));
    const total = cum[cum.length - 1];
    const N = 1200, X = new Float32Array(N + 1), Y = new Float32Array(N + 1);
    for (let i = 0, j = 1; i <= N; i++) {
      const s = (total * i) / N;
      while (j < cum.length - 1 && cum[j] < s) j++;
      const a = (s - cum[j - 1]) / Math.max(cum[j] - cum[j - 1], 1e-9);
      X[i] = vx[j - 1] + a * (vx[j] - vx[j - 1]);
      Y[i] = vy[j - 1] + a * (vy[j] - vy[j - 1]);
    }

    // --- speed from curvature (lateral grip limit), smoothed, then time along the course
    const seg = LEN_M / N, W = 6, idx = (i) => (laps ? (i + N) % N : Math.min(Math.max(i, 0), N));
    const head = new Float32Array(N + 1);
    for (let i = 0; i <= N; i++) head[i] = Math.atan2(Y[idx(i + W)] - Y[idx(i - W)], X[idx(i + W)] - X[idx(i - W)]);
    let v = new Float32Array(N + 1);
    for (let i = 0; i <= N; i++) {
      let d = head[idx(i + 1)] - head[idx(i - 1)];
      d = Math.atan2(Math.sin(d), Math.cos(d));
      const k = Math.abs(d) / (2 * seg);
      v[i] = Math.max(3, Math.min(VMAX, Math.sqrt(1.6 / Math.max(k, 1e-6))));
    }
    for (let pass = 0; pass < 3; pass++) {
      const o = new Float32Array(N + 1);
      for (let i = 0; i <= N; i++) { let s = 0; for (let j = -15; j <= 15; j++) s += v[idx(i + j)]; o[i] = s / 31; }
      v = o;
    }
    if (!laps) { for (let i = 0; i < 40; i++) { const r = (i + 1) / 41; v[i] *= 0.25 + 0.75 * r; v[N - i] *= 0.25 + 0.75 * r; } }  // launch and stop
    const T = new Float32Array(N + 1);
    for (let i = 1; i <= N; i++) T[i] = T[i - 1] + seg / ((v[i] + v[i - 1]) / 2);
    const tLap = T[N];

    function at(q) {  // q: fraction of the lap in time → arc fraction, position, speed
      const tt = Math.min(Math.max(q, 0), 1) * tLap;
      let lo = 0, hi = N;
      while (hi - lo > 1) { const m = (lo + hi) >> 1; if (T[m] < tt) lo = m; else hi = m; }
      const a = (tt - T[lo]) / Math.max(T[hi] - T[lo], 1e-9);
      const h = head[lo] + a * Math.atan2(Math.sin(head[hi] - head[lo]), Math.cos(head[hi] - head[lo]));
      return { f: (lo + a) / N, x: X[lo] + a * (X[hi] - X[lo]), y: Y[lo] + a * (Y[hi] - Y[lo]), v: v[lo] + a * (v[hi] - v[lo]), h };
    }

    // --- timeline. Laps: a time-lapse, the first lap at a readable pace and each one faster, until the
    // kilowatt-hour runs out; open course: one run to the finish. Then a hold, and it starts again.
    const lapDur = (n) => (laps ? Math.max(1.15, 7.5 * Math.pow(0.8, n - 1)) : 13);
    const HOLD = 5;
    let lapN = 1, q = 0, hold = 0, finished = false, live = false, raf = 0, last = 0, visible = true, hudAt = 0;

    function draw(force) {
      const p = finished ? at(laps ? 0 : 1) : at(q);
      car.setAttribute("transform", `translate(${p.x.toFixed(1)} ${p.y.toFixed(1)}) rotate(${(p.h * 180 / Math.PI).toFixed(1)})`);
      const speedup = laps ? 7.5 / lapDur(lapN) : 1;
      const len = finished ? 0 : Math.min(260, (laps ? 26 : 70) * (p.v / VMAX) * Math.sqrt(speedup));
      const head = p.f * 1000;
      trail.style.strokeDasharray = `${len.toFixed(1)} ${(1000 - len).toFixed(1)}`;
      trail.style.strokeDashoffset = (len - head).toFixed(1);
      const now = performance.now();
      if (!force && now - hudAt < 90) return;
      hudAt = now;
      const kmh = finished ? 0 : Math.round(p.v * 3.6);
      if (hud.status) {
        hud.status.textContent = finished ? ds.finish
          : laps ? `Time-lapse ×${Math.round(tLap / lapDur(lapN))}` : ds.running || "Running";
      }
      if (hud.speed) hud.speed.firstChild.nodeValue = String(kmh);
      if (laps) {
        const done = finished ? LAPS : lapN - 1 + p.f;
        hud.lap.firstChild.nodeValue = String(finished ? LAPS : lapN);
        hud.dist.firstChild.nodeValue = ((done / LAPS) * TOTAL_KM).toFixed(1);  // the official total, spread over the laps
        const left = Math.max(0, 1 - done / LAPS);
        hud.energy.firstChild.nodeValue = Math.round(1000 * left).toLocaleString("en-US");
        hud.bar.parentElement.style.setProperty("--p", left.toFixed(4));
      } else {
        const f = finished ? 1 : p.f;
        hud.dist.firstChild.nodeValue = Math.round(f * LEN_M).toLocaleString("en-US");
        hud.bar.parentElement.style.setProperty("--p", f.toFixed(4));
      }
    }

    function finish() {
      finished = true; hold = 0;
      root.classList.add("is-finished");
    }
    function restart() {
      finished = false; lapN = 1; q = 0;
      root.classList.remove("is-finished");
    }

    function frame(now) {
      raf = 0;
      const dt = Math.min((now - last) / 1000, 0.05); last = now;
      if (finished) {
        hold += dt;
        if (hold > HOLD) restart();
      } else {
        q += dt / lapDur(lapN);
        while (q >= 1 && !finished) {
          if (laps && lapN < LAPS) { q -= 1; lapN++; } else { q = 1; finish(); }
        }
      }
      draw(false);
      loop();
    }
    function loop() { if (!raf && live && visible && !motion.paused && !document.hidden) raf = requestAnimationFrame(frame); }
    function wake() { last = performance.now(); loop(); }

    function syncBtn() {
      root.classList.toggle("is-paused", motion.paused);
      if (!btn) return;
      btn.setAttribute("aria-pressed", String(motion.paused));
      btn.querySelector(".lbl").textContent = motion.paused ? "Play motion" : "Pause motion";
    }
    motion.subs.add(() => {
      syncBtn();
      if (motion.paused) { draw(true); return; }
      if (finished && !root.classList.contains("is-finished")) restart();  // leaving the still state
      wake();
    });
    if (btn) btn.addEventListener("click", () => motion.set(!motion.paused, true));
    syncBtn();

    document.addEventListener("visibilitychange", wake);
    if ("IntersectionObserver" in window) {
      new IntersectionObserver((es) => { visible = es[0].isIntersecting; wake(); }).observe(root);
    }

    // start once the outline has drawn itself (or right away with reduced motion)
    const go = () => {
      if (live) return;
      live = true;
      if (motion.paused) { finish(); root.classList.remove("is-finished"); }  // still: show the finished readout
      draw(true);
      root.classList.add("is-live");
      wake();
    };
    gate.then(() => {
      if (reduce.matches) return go();
      lap.addEventListener("animationend", go, { once: true });
      setTimeout(go, 2600);  // in case the animation never fires (hidden tab, forced colours…)
    });
  }

  // ------------------------------------------------------------ hand-drawn diagrams: dots move only while seen
  const sketches = document.querySelectorAll(".sketch-svg");
  if (sketches.length) {
    const seen = new Set();
    const sync = (svg) => {
      if (!svg.pauseAnimations) return;
      if (seen.has(svg) && !motion.paused && !document.hidden) svg.unpauseAnimations(); else svg.pauseAnimations();
    };
    sketches.forEach((svg) => sync(svg));
    if ("IntersectionObserver" in window) {
      const io = new IntersectionObserver((es) => es.forEach((e) => {
        if (e.isIntersecting) seen.add(e.target); else seen.delete(e.target);
        sync(e.target);
      }), { threshold: 0.05 });
      sketches.forEach((svg) => io.observe(svg));
    }
    motion.subs.add(() => sketches.forEach(sync));
    document.addEventListener("visibilitychange", () => sketches.forEach(sync));
  }

  // ------------------------------------------------------------ chapter rail: highlight the section in view
  const rail = document.querySelector(".rail");
  if (rail && "IntersectionObserver" in window) {
    const links = new Map();
    rail.querySelectorAll("a").forEach((a) => {
      const t = document.getElementById(a.getAttribute("href").slice(1));
      if (t) links.set(t.matches("main, section") ? t : t.closest("section") || t, a);  // a heading id maps to its section
    });
    const visible = new Map();
    const pick = () => {
      let best = null, top = Infinity;
      visible.forEach((r, el) => { if (r < top) { top = r; best = el; } });
      links.forEach((a, el) => { if (el === best) a.setAttribute("aria-current", "location"); else a.removeAttribute("aria-current"); });
    };
    const io = new IntersectionObserver((es) => {
      es.forEach((e) => { if (e.isIntersecting) visible.set(e.target, e.target.getBoundingClientRect().top); else visible.delete(e.target); });
      visible.forEach((_, el) => visible.set(el, Math.abs(el.getBoundingClientRect().top)));
      pick();
    }, { rootMargin: "-35% 0px -55% 0px" });
    links.forEach((_, el) => io.observe(el));
  }

  // ------------------------------------------------------------ divider tabs: keep the open one in view on narrow screens
  const tabCur = document.querySelector(".sheet-tabs [aria-current]");
  if (tabCur) {
    const strip = tabCur.closest("ol");
    strip.scrollLeft = tabCur.offsetLeft - (strip.clientWidth - tabCur.offsetWidth) / 2;
  }

  // ------------------------------------------------------------ 3D car, loaded only when it is near
  const viewer = document.querySelector("[data-car3d]");
  if (viewer) {
    const status = viewer.querySelector(".viewer-status");
    let gl = false;
    try { const c = document.createElement("canvas"); gl = !!(c.getContext("webgl2") || c.getContext("webgl")); } catch (e) { /* no GL */ }
    if (!gl) {
      status.textContent = "The 3D model needs WebGL, which this browser has turned off.";
    } else {
      const load = () => {
        status.textContent = "Loading the 3D model…";
        import(new URL("car3d.js", SCRIPT_URL).href)
          .then((m) => m.mount(viewer, motion))
          .catch((e) => { console.warn("car3d:", e); status.textContent = "The 3D model could not load. Reload the page to try again."; });
      };
      const saveData = navigator.connection && navigator.connection.saveData;
      if (saveData) {  // data saver on: load only on request
        status.innerHTML = '<button class="btn btn-ghost" type="button">Load the 3D model (0.8 MB)</button>';
        status.querySelector("button").addEventListener("click", load, { once: true });
      } else if ("IntersectionObserver" in window) {
        const io = new IntersectionObserver((es) => {
          if (es[0].isIntersecting) { io.disconnect(); load(); }
        }, { rootMargin: "500px 0px" });
        io.observe(viewer);
      } else load();
    }
  }
})();
