"""Hand-drawn engineering diagrams, one per project, as inline SVG.

Notebook look: graph paper (CSS), wobbly ink from an SVG displacement filter, handwritten notes (Caveat).
Motion (all driven by CSS classes and site.js): every line draws itself in order when the sheet scrolls
into view (`pathLength="1"` + `--d` delay index), notes fade in after their lines, and dots travel along
the signal paths (SMIL, paused off screen and with reduced motion or the pause button).

Only facts stated in the project pages are drawn here; no code, no schematics, no CAD.
"""

from __future__ import annotations

import html
import math

esc = html.escape


class Sheet:
    def __init__(self, key: str, w: int = 960, h: int = 480):
        self.key, self.w, self.h = key, w, h
        self.ink: list[str] = []    # wobbly layer (filtered)
        self.flow: list[str] = []   # moving dots (not filtered, stay crisp)
        self.n = 0

    def _d(self) -> int:
        self.n += 1
        return self.n

    # ---- primitives
    def box(self, x, y, w, h, title, sub="", accent=False, r=8):
        d = self._d()
        cls = "d-line d-acc" if accent else "d-line"
        self.ink.append(f'<rect class="{cls}" x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" pathLength="1" style="--d:{d}"/>')
        cy = y + h / 2 + (-6 if sub else 8)
        self.ink.append(f'<text class="d-txt d-title" x="{x + w / 2}" y="{cy}" text-anchor="middle" style="--d:{d}">{esc(title)}</text>')
        if sub:
            self.ink.append(f'<text class="d-txt d-sub" x="{x + w / 2}" y="{cy + 24}" text-anchor="middle" style="--d:{d}">{esc(sub)}</text>')

    def path(self, d_attr, cls="d-line", accent=False, dashed=False):
        d = self._d()
        c = cls + (" d-acc" if accent else "") + (" d-dash" if dashed else "")
        self.ink.append(f'<path class="{c}" d="{d_attr}" pathLength="1" style="--d:{d}"/>')
        return d

    def circle(self, cx, cy, r, accent=False, cls="d-line"):
        d = self._d()
        c = cls + (" d-acc" if accent else "")
        self.ink.append(f'<circle class="{c}" cx="{cx}" cy="{cy}" r="{r}" pathLength="1" style="--d:{d}"/>')

    def note(self, x, y, text, accent=False, anchor="start", size="", rot=0):
        d = self._d()
        c = "d-txt d-note" + (" d-acc-t" if accent else "") + (f" d-{size}" if size else "")
        tr = f' transform="rotate({rot} {x} {y})"' if rot else ""
        lines = text.split("\n")
        spans = "".join(f'<tspan x="{x}" dy="{0 if i == 0 else 24}">{esc(t)}</tspan>' for i, t in enumerate(lines))
        self.ink.append(f'<text class="{c}" x="{x}" y="{y}" text-anchor="{anchor}"{tr} style="--d:{d}">{spans}</text>')

    def arrow(self, pts, label="", lx=None, ly=None, accent=False, dashed=False, flow=False, dur=2.4, begin=0.0):
        d_attr = "M" + " L".join(f"{x},{y}" for x, y in pts)
        d = self.path(d_attr, accent=accent, dashed=dashed)
        (x1, y1), (x2, y2) = pts[-2], pts[-1]
        a = math.atan2(y2 - y1, x2 - x1)
        s = 11
        p1 = (x2 - s * math.cos(a - 0.45), y2 - s * math.sin(a - 0.45))
        p2 = (x2 - s * math.cos(a + 0.45), y2 - s * math.sin(a + 0.45))
        c = "d-head d-txt" + (" d-acc" if accent else "")
        self.ink.append(f'<path class="{c}" d="M{p1[0]:.1f},{p1[1]:.1f} L{x2},{y2} L{p2[0]:.1f},{p2[1]:.1f}" style="--d:{d}"/>')
        if label:
            if lx is None:
                lx, ly = (pts[0][0] + pts[1][0]) / 2, (pts[0][1] + pts[1][1]) / 2 - 10
            self.ink.append(f'<text class="d-txt d-lbl{" d-acc-t" if accent else ""}" x="{lx}" y="{ly}" text-anchor="middle" style="--d:{d}">{esc(label)}</text>')
        if flow:
            self.dot(d_attr, dur, begin, accent)

    def dot(self, d_attr, dur=2.4, begin=0.0, accent=False):
        self.flow.append(
            f'<circle class="d-dot{" d-dot-acc" if accent else ""}" r="4.5" opacity="0">'
            f'<animateMotion dur="{dur}s" begin="{begin}s" repeatCount="indefinite" path="{d_attr}"/>'
            f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;0.12;0.85;1" dur="{dur}s" begin="{begin}s" repeatCount="indefinite"/>'
            f'</circle>')

    def svg(self, label: str) -> str:
        fid = f"rough-{self.key}"
        return (f'<svg class="sketch-svg" viewBox="0 0 {self.w} {self.h}" role="img" aria-label="{esc(label)}">'
                f'<defs><filter id="{fid}" x="-2%" y="-2%" width="104%" height="104%">'
                f'<feTurbulence type="fractalNoise" baseFrequency="0.022" numOctaves="2" seed="7"/>'
                f'<feDisplacementMap in="SourceGraphic" scale="2.6"/></filter></defs>'
                f'<g class="d-ink" filter="url(#{fid})">{"".join(self.ink)}</g>'
                f'<g class="d-flow" aria-hidden="true">{"".join(self.flow)}</g></svg>')


# ------------------------------------------------------------------ the diagrams

def driver() -> Sheet:
    s = Sheet("driver")
    s.box(20, 40, 130, 72, "Pedal", "throttle")
    s.box(215, 40, 160, 72, "PI control", "Id* = 0 · Iq*", accent=True)
    s.box(440, 40, 150, 72, "inv. Park", "dq → αβ")
    s.box(650, 40, 130, 72, "SVPWM", "duty cycles")
    s.box(810, 40, 140, 104, "Inverter", "6 FETs · 48 V")
    for x in (860, 880, 900):
        s.path(f"M{x},144 L{x},250")
    s.circle(880, 300, 52, accent=True)
    s.note(880, 308, "BLDC", anchor="middle", size="big")
    s.box(640, 352, 150, 72, "Shunts ×3", "INA240 amps")
    s.box(430, 352, 150, 72, "Clarke", "abc → αβ")
    s.box(215, 352, 160, 72, "Park", "αβ → dq")
    s.box(430, 200, 150, 64, "Rotor angle", "Hall + smoothing")
    s.arrow([(150, 76), (215, 76)], "Iq*", flow=True, dur=1.6, accent=True)
    s.arrow([(375, 76), (440, 76)], "Vd Vq", flow=True, dur=1.6, begin=0.4)
    s.arrow([(590, 76), (650, 76)], "Vα Vβ", flow=True, dur=1.6, begin=0.8)
    s.arrow([(780, 76), (810, 76)], flow=True, dur=1.4, begin=1.1)
    s.arrow([(828, 300), (715, 300), (715, 352)], "ia ib ic", 770, 290, flow=True, dur=2.0)
    s.arrow([(640, 388), (580, 388)], flow=True, dur=1.4, begin=0.6)
    s.arrow([(430, 388), (375, 388)], flow=True, dur=1.4, begin=1.0)
    s.arrow([(295, 352), (295, 112)], "Id Iq", 262, 300, accent=True, flow=True, dur=1.8, begin=1.3)
    s.arrow([(842, 266), (760, 266), (760, 232), (580, 232)], "Hall", 800, 256, flow=True, dur=2.2)
    s.arrow([(505, 200), (505, 112)], "θ", 520, 160)
    s.arrow([(430, 232), (340, 232), (340, 352)], "θ", 352, 222)
    s.note(28, 186, "every 100 µs\n(10 kHz loop)")
    s.note(28, 262, "PWM-synced sampling:\n68 µs → 5.4 µs", accent=True)
    s.note(225, 462, "Id = 0: all the current makes torque, none is wasted on flux")
    return s


def telemetry() -> Sheet:
    s = Sheet("telemetry")
    for i, (t, sub) in enumerate((("GPS", "position"), ("IMU", "accel · attitude"), ("Pitot", "air speed"),
                                  ("Motor driver", "V · I · rpm · pedal"))):
        s.box(20, 30 + 80 * i, 170, 58, t, sub)
    s.box(290, 50, 180, 92, "Kalman filter", "6 states · adaptive", accent=True)
    s.box(550, 170, 160, 92, "Live state", "one shared record")
    s.box(790, 40, 150, 62, "microSD", "CSV log")
    s.box(790, 185, 150, 62, "Cockpit", "display over CAN")
    s.box(790, 330, 150, 62, "Pits", "cloud → dashboard")
    s.arrow([(190, 59), (240, 59), (240, 82), (290, 82)], flow=True, dur=1.8)
    s.arrow([(190, 139), (240, 139), (240, 112), (290, 112)], flow=True, dur=1.8, begin=0.5)
    s.arrow([(470, 96), (510, 96), (510, 196), (550, 196)], "fused", 520, 86, accent=True, flow=True, dur=2.0, begin=0.3)
    s.arrow([(190, 219), (550, 219)], flow=True, dur=2.4, begin=0.9)
    s.arrow([(190, 299), (510, 299), (510, 242), (550, 242)], flow=True, dur=2.4, begin=0.2)
    s.arrow([(710, 190), (750, 190), (750, 71), (790, 71)], flow=True, dur=1.8, begin=0.4)
    s.arrow([(710, 216), (790, 216)], "CAN", 772, 240, flow=True, dur=1.4, begin=0.8)
    s.arrow([(710, 242), (750, 242), (750, 361), (790, 361)], "WiFi", 778, 300, flow=True, dur=1.8, begin=1.2)
    s.note(560, 440, "to the pits: ≈ 535 ms → < 1 ms\n(local benchmark)", accent=True)
    s.note(20, 410, "2027: DC-bus energy, wheel speed,\nRTK GNSS, wind and a co-pilot")
    return s


def electronics() -> Sheet:
    s = Sheet("electronics")
    s.box(20, 20, 920, 430, "", r=18)
    for cx, cy in ((44, 44), (916, 44), (44, 426), (916, 426)):
        s.circle(cx, cy, 8)
    s.box(60, 60, 170, 56, "Hall · pedal", "inputs")
    s.box(60, 160, 170, 120, "Teensy 4.1", "600 MHz · FOC", accent=True)
    s.box(300, 180, 130, 80, "Gate", "drivers")
    s.path("M480,80 L900,80")
    s.note(900, 68, "48 V bus · 45 A", anchor="end", accent=True)
    s.path("M480,392 L900,392")
    s.note(900, 418, "GND", anchor="end")
    cols = (500, 640, 780)
    for i, x in enumerate(cols):
        c = x + 35
        s.path(f"M{c},80 L{c},112")
        s.box(x, 112, 70, 52, f"Q{2 * i + 1}")
        s.path(f"M{c},164 L{c},250")
        s.box(x, 250, 70, 52, f"Q{2 * i + 2}")
        s.path(f"M{c},302 L{c},330")
        s.box(x + 12, 330, 46, 26, "", r=3)
        s.path(f"M{c},356 L{c},392")
        s.circle(c, 207, 4)
        s.arrow([(c, 207), (c + 62, 207)])
        s.note(c + 70, 214, "UVW"[i], size="big")
    s.arrow([(145, 116), (145, 160)], flow=True, dur=1.4)
    s.arrow([(230, 220), (300, 220)], "PWM ×6", flow=True, dur=1.4, begin=0.3, accent=True)
    s.arrow([(430, 220), (488, 220)], "gates", flow=True, dur=1.2, begin=0.7)
    s.arrow([(500, 343), (270, 343), (270, 270), (230, 270)], "current sense ×3", 380, 333, dashed=True, accent=True,
            flow=True, dur=2.4, begin=0.5)
    s.dot("M480,80 L535,80 L535,207 L597,207", dur=2.2, begin=0.2)
    s.dot("M480,80 L675,80 L675,207 L737,207", dur=2.6, begin=1.0)
    s.dot("M480,80 L815,80 L815,207 L877,207", dur=3.0, begin=1.7)
    s.note(40, 418, "Motor driver board · 2 layers · KiCad 10, ERC + DRC on every change")
    return s


def mechanics() -> Sheet:
    s = Sheet("mechanics")
    s.note(30, 36, "SIDE", size="big")
    s.path("M30,362 L570,362", cls="d-line d-thin")
    s.path("M46,334 C70,300 150,262 260,246 C370,230 470,232 528,262 C556,278 560,322 540,338 L70,343 C54,343 44,340 46,334 Z", accent=True)
    s.path("M232,250 C262,200 352,192 404,236", cls="d-line d-thin")
    s.circle(130, 330, 32)
    s.circle(470, 330, 32)
    s.circle(470, 330, 11, accent=True)
    s.path("M50,404 L548,404", cls="d-line d-thin")
    s.path("M50,394 L50,414 M548,394 L548,414", cls="d-line d-thin")
    s.note(299, 396, "≈ 2.7 m", anchor="middle")
    s.path("M590,362 L590,196 M580,362 L600,362 M580,196 L600,196", cls="d-line d-thin")
    s.note(604, 282, "≈ 0.8 m")
    s.note(30, 452, "rear hub motor: 350 W, no clutch (2026) → ≈ 500 W, chain + clutch (2027)", accent=True)
    # top view, nose up: trapezoidal steering whose arm lines meet behind the rear wheel (partial Ackermann)
    s.note(690, 36, "TOP", size="big")
    s.path("M790,60 C850,70 905,130 905,220 C905,320 845,410 790,420 C735,410 675,320 675,220 C675,130 730,70 790,60 Z", cls="d-line d-thin")
    kl, kr, t = (720, 140), (860, 140), (790, 470)
    s.path(f"M{kl[0]},{kl[1]} L{kr[0]},{kr[1]}", cls="d-line d-thin")
    ends = []
    for k in (kl, kr):
        dx, dy = t[0] - k[0], t[1] - k[1]
        n = math.hypot(dx, dy)
        e = (k[0] + 46 * dx / n, k[1] + 46 * dy / n)
        ends.append(e)
        s.path(f"M{k[0]},{k[1]} L{e[0]:.1f},{e[1]:.1f}", accent=True)
        s.path(f"M{e[0]:.1f},{e[1]:.1f} L{t[0]},{t[1]}", dashed=True)
    s.path(f"M{ends[0][0]:.1f},{ends[0][1]:.1f} L{ends[1][0]:.1f},{ends[1][1]:.1f}", accent=True)
    s.box(694, 110, 18, 60, "", r=4)
    s.box(868, 110, 18, 60, "", r=4)
    s.box(781, 372, 18, 60, "", r=4)
    s.note(918, 120, "steering\narm", size="small")
    s.note(800, 214, "tie rod", size="small")
    s.note(770, 430, "arm lines meet\nbehind the\nrear wheel", anchor="end", size="small")
    return s


def strategy() -> Sheet:
    s = Sheet("strategy")
    s.path("M60,40 L60,300 L620,300", cls="d-line d-thin")
    s.note(48, 34, "speed", anchor="end", size="small")
    s.note(620, 326, "distance along the lap →", anchor="end", size="small")
    # pulse (steep, motor on) and glide (shallow, motor off)
    x, v, pts_p, pts_g, trace = 60, 280, [], [], ["M60,280"]
    seq = [(40, 150), (70, 205), (24, 150), (90, 215), (22, 150), (80, 210), (24, 150), (100, 220), (22, 160)]
    for i, (dx, vt) in enumerate(seq):
        seg = f"M{x},{v} L{x + dx},{vt}"
        (pts_p if i % 2 == 0 else pts_g).append(seg)
        if i % 2 == 0:  # a power bar under each pulse, standing on the baseline
            bh = 34 if i else 46
            s.box(x, 382 - bh, dx, bh, "", r=2, accent=True)
        x, v = x + dx, vt
        trace.append(f"L{x},{v}")
    for seg in pts_p:
        s.path(seg, accent=True)
    for seg in pts_g:
        s.path(seg, dashed=True)
    s.dot(" ".join(trace), dur=6, accent=True)
    s.note(110, 130, "pulse: motor on", accent=True, size="small")
    s.note(215, 248, "glide: motor off", size="small")
    s.note(60, 410, "motor power: 150–300 W pulses, zero while gliding", size="small")
    s.path("M60,382 L620,382", cls="d-line d-thin")
    s.note(680, 52, "where the watts go", size="big")
    rows = (("Motor + driver", "chain + clutch ≈ −20 % energy"), ("Rolling", "−0.001 crr ≈ +10 % km/kWh"),
            ("Electronics", "−2 W ≈ +3 %"), ("Aero", "−0.01 m² CdA ≈ +4 %"))
    for i, (t, k) in enumerate(rows):
        y = 80 + 78 * i
        s.box(680, y, 260, 62, t, k, accent=(i == 0))
    s.note(680, 418, "gap to the winner ≈ 22 W\n(≈ 80 W vs ≈ 58 W average)", accent=True)
    return s


def adc() -> Sheet:
    s = Sheet("adc")
    s.note(20, 32, "onboard computer · ROS 2 · runs 100 % on the car")
    labels = (("Sensors", "track · pins"), ("Perception", "cones · stop line"), ("Estimation", "where am I"),
              ("Planning", "energy-aware speed"), ("Control", "steer · brake · torque"))
    xs = (20, 205, 390, 575, 780)
    for i, (x, (t, sub)) in enumerate(zip(xs, labels)):
        s.box(x, 60, 160, 72, t, sub, accent=(t == "Planning"))
        if i:
            s.arrow([(xs[i - 1] + 160, 96), (x, 96)], flow=True, dur=1.4, begin=0.35 * i)
    s.box(800, 200, 140, 70, "Actuators", "steering · brake")
    s.box(575, 200, 170, 70, "Gateway board", "opto-isolated UART")
    s.box(350, 200, 170, 70, "Motor driver", "FOC, same as race")
    s.arrow([(900, 132), (900, 200)], flow=True, dur=1.2, begin=0.2)
    s.arrow([(820, 132), (820, 166), (660, 166), (660, 200)], flow=True, dur=1.6, begin=0.6)
    s.arrow([(575, 235), (520, 235)], flow=True, dur=1.0, begin=1.0)
    s.note(800, 300, "safety driver can\ntake over any time", size="small")
    s.box(20, 360, 150, 60, "Car", "publishes only")
    s.box(300, 360, 170, 60, "Cloud broker", "MQTT")
    s.box(600, 360, 180, 60, "Digital twin", "simulation")
    s.arrow([(170, 390), (300, 390)], flow=True, dur=1.6, accent=True)
    s.arrow([(470, 390), (600, 390)], flow=True, dur=1.6, begin=0.8, accent=True)
    s.path("M690,420 L690,452 L95,452 L95,420", dashed=True)
    s.path("M380,440 L400,464 M400,440 L380,464", accent=True)
    s.note(420, 472, "nothing comes back to the car", size="small", accent=True)
    return s


SHEETS = {"driver": driver, "telemetry": telemetry, "electronics": electronics, "mechanics": mechanics,
          "strategy": strategy, "adc": adc}

CAPTIONS = {
    "driver": "Field-oriented control, every 100 µs: currents measured, turned into the rotor's frame, corrected and sent back as PWM.",
    "telemetry": "Sensors fused by a Kalman filter into one live state, logged, shown to the driver and sent to the pits.",
    "electronics": "The motor-driver board: a Teensy 4.1 drives three half-bridges on the 48 V bus and reads the current through shunt amplifiers.",
    "mechanics": "Side view with overall size, and the trapezoidal steering seen from above: the arm lines meet behind the rear wheel, so the inner wheel turns more.",
    "strategy": "Pulse and glide: short pushes with the motor at its efficient point, long glides with it off; and what each improvement is worth.",
    "adc": "The autonomy pipeline, entirely on board, and the one-way telemetry to the cloud and the digital twin.",
}


def sheet(key: str, fig: int, title: str) -> str:
    """Full figure: graph-paper sheet with the drawing, a CAD-style title block and a caption."""
    if key not in SHEETS:
        return ""
    cap = CAPTIONS[key]
    return f"""<figure class="sketch" data-reveal data-sketch>
<div class="sketch-scroll" tabindex="0" role="group" aria-label="{esc(title)} diagram, scrolls sideways on small screens">{SHEETS[key]().svg(f"Diagram: {cap}")}</div>
<figcaption><span class="tb"><span class="tb-k">Fig.</span> {fig:02d}</span><span class="tb"><span class="tb-k">Title</span> {esc(title)}</span><span class="tb tb-wide">{esc(cap)}</span><span class="tb"><span class="tb-k">Scale</span> NTS</span><span class="tb tb-hint" aria-hidden="true">Swipe sideways to see the whole drawing →</span></figcaption>
</figure>"""


# small glyphs for the home cards (64 × 64)
GLYPHS = {
    "mechanics": '<circle cx="32" cy="34" r="20"/><circle cx="32" cy="34" r="4"/><path d="M32 14v16M32 38v16M12 34h16M36 34h16"/><path d="M14 18a26 26 0 0 1 14-8" class="g-acc"/>',
    "electronics": '<rect x="16" y="16" width="32" height="32" rx="3"/><path d="M22 10v6M32 10v6M42 10v6M22 48v6M32 48v6M42 48v6M10 22h6M10 32h6M10 42h6M48 22h6M48 32h6M48 42h6"/><rect x="25" y="25" width="14" height="14" class="g-acc"/>',
    "driver": '<path d="M6 32c5-16 10-16 15 0s10 16 15 0 10-16 15 0 5 8 7 4"/><path d="M6 32c5 12 10 12 15 0s10-12 15 0" class="g-acc"/>',
    "telemetry": '<path d="M32 54V26"/><circle cx="32" cy="22" r="4" class="g-acc"/><path d="M22 14a14 14 0 0 0 0 16M42 14a14 14 0 0 1 0 16M15 8a24 24 0 0 0 0 28M49 8a24 24 0 0 1 0 28"/><path d="M24 54h16"/>',
    "strategy": '<path d="M8 54h50M8 54V8"/><path d="M10 48l8-20 10 6 6-16 12 8 8-14" class="g-acc"/>',
    "adc": '<path d="M8 50c12-4 10-24 24-26s14-14 24-16"/><path d="M18 52l4-8 4 8zM40 26l4-8 4 8z" class="g-acc"/><circle cx="32" cy="24" r="4"/>',
}


def glyph(key: str) -> str:
    return (f'<svg class="glyph" viewBox="0 0 64 64" aria-hidden="true" focusable="false">'
            f'<g fill="none" stroke-linecap="round" stroke-linejoin="round">{GLYPHS.get(key, "")}</g></svg>')
