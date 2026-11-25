"""Hand-drawn engineering diagrams, one per project, as inline SVG.

Notebook look: graph paper (CSS), ink with a slight hand wobble, handwritten notes (Caveat). The wobble is
geometry, not a filter: every straight stroke becomes a gentle quadratic curve whose bow is seeded per
diagram, so lines stay crisp and antialiased and every build draws the same sheet. (An SVG displacement
filter was tried first: it shifts pixels in whole steps and left visible nicks on long straight edges.)
Motion (all driven by CSS classes and site.js): every line draws itself in order when the sheet scrolls
into view (`pathLength="1"` + `--d` delay index), notes fade in after their lines, and dots travel along
the signal paths (SMIL, paused off screen and with reduced motion or the pause button).

Only facts stated in the project pages are drawn here; no code, no schematics, no CAD files.
"""

from __future__ import annotations

import html
import math
import random
import re

esc = html.escape
_ML = re.compile(r"(?:\s*[ML]\s*-?\d+(?:\.\d+)?[\s,]+-?\d+(?:\.\d+)?)+\s*")
_PT = re.compile(r"([ML])\s*(-?\d+(?:\.\d+)?)[\s,]+(-?\d+(?:\.\d+)?)")


class Sheet:
    def __init__(self, key: str, w: int = 960, h: int = 480):
        self.key, self.w, self.h = key, w, h
        self.ink: list[str] = []    # the drawing
        self.flow: list[str] = []   # moving dots
        self.n = 0
        self.rng = random.Random(key)

    def _d(self) -> int:
        self.n += 1
        return self.n

    # ---- hand wobble
    def _seg(self, x1, y1, x2, y2) -> str:
        """A straight stroke drawn by hand: a quadratic with a small seeded bow."""
        dx, dy = x2 - x1, y2 - y1
        ln = math.hypot(dx, dy)
        if ln < 6:
            return f" L{x2:g},{y2:g}"
        amp = min(1.6, 0.35 + ln * 0.005)
        off = self.rng.uniform(-amp, amp)
        mx = (x1 + x2) / 2 - dy / ln * off
        my = (y1 + y2) / 2 + dx / ln * off
        return f" Q{mx:.1f},{my:.1f} {x2:g},{y2:g}"

    def _wobble(self, d_attr: str) -> str:
        if not _ML.fullmatch(d_attr):
            return d_attr  # curves stay as drawn
        out, cur = [], None
        for cmd, xs, ys in _PT.findall(d_attr):
            x, y = float(xs), float(ys)
            if cmd == "M" or cur is None:
                out.append(f"M{x:g},{y:g}")
            else:
                out.append(self._seg(cur[0], cur[1], x, y))
            cur = (x, y)
        return "".join(out)

    def _rect(self, x, y, w, h, r) -> str:
        r = min(r, w / 2, h / 2)
        s = self._seg
        return (f"M{x + r:g},{y:g}" + s(x + r, y, x + w - r, y) + f" Q{x + w:g},{y:g} {x + w:g},{y + r:g}"
                + s(x + w, y + r, x + w, y + h - r) + f" Q{x + w:g},{y + h:g} {x + w - r:g},{y + h:g}"
                + s(x + w - r, y + h, x + r, y + h) + f" Q{x:g},{y + h:g} {x:g},{y + h - r:g}"
                + s(x, y + h - r, x, y + r) + f" Q{x:g},{y:g} {x + r:g},{y:g}")

    # ---- primitives
    def box(self, x, y, w, h, title, sub="", accent=False, r=8):
        d = self._d()
        cls = "d-line d-acc" if accent else "d-line"
        self.ink.append(f'<path class="{cls}" d="{self._rect(x, y, w, h, r)}" pathLength="1" style="--d:{d}"/>')
        if title:
            cy = y + h / 2 + (-6 if sub else 8)
            self.ink.append(f'<text class="d-txt d-title" x="{x + w / 2}" y="{cy}" text-anchor="middle" style="--d:{d}">{esc(title)}</text>')
            if sub:
                self.ink.append(f'<text class="d-txt d-sub" x="{x + w / 2}" y="{cy + 24}" text-anchor="middle" style="--d:{d}">{esc(sub)}</text>')

    def path(self, d_attr, cls="d-line", accent=False, dashed=False, wobble=True):
        d = self._d()
        c = cls + (" d-acc" if accent else "") + (" d-dash" if dashed else "")
        self.ink.append(f'<path class="{c}" d="{self._wobble(d_attr) if wobble else d_attr}" pathLength="1" style="--d:{d}"/>')
        return d

    def circle(self, cx, cy, r, accent=False, cls="d-line"):
        d = self._d()
        c = cls + (" d-acc" if accent else "")
        self.ink.append(f'<circle class="{c}" cx="{cx}" cy="{cy}" r="{r}" pathLength="1" style="--d:{d}"/>')

    def note(self, x, y, text, accent=False, anchor="start", size="", rot=0, cls="d-note"):
        d = self._d()
        c = f"d-txt {cls}" + (" d-acc-t" if accent else "") + (f" d-{size}" if size else "")
        tr = f' transform="rotate({rot} {x} {y})"' if rot else ""
        lines = text.split("\n")
        spans = "".join(f'<tspan x="{x}" dy="{0 if i == 0 else 24}">{esc(t)}</tspan>' for i, t in enumerate(lines))
        self.ink.append(f'<text class="{c}" x="{x}" y="{y}" text-anchor="{anchor}"{tr} style="--d:{d}">{spans}</text>')

    def head(self, x1, y1, x2, y2, d, accent=False, s=11):
        a = math.atan2(y2 - y1, x2 - x1)
        p1 = (x2 - s * math.cos(a - 0.45), y2 - s * math.sin(a - 0.45))
        p2 = (x2 - s * math.cos(a + 0.45), y2 - s * math.sin(a + 0.45))
        c = "d-head d-txt" + (" d-acc" if accent else "")
        self.ink.append(f'<path class="{c}" d="M{p1[0]:.1f},{p1[1]:.1f} L{x2:g},{y2:g} L{p2[0]:.1f},{p2[1]:.1f}" style="--d:{d}"/>')

    def arrow(self, pts, label="", lx=None, ly=None, accent=False, dashed=False, flow=False, dur=2.4, begin=0.0):
        d_attr = "M" + " L".join(f"{x},{y}" for x, y in pts)
        d = self.path(d_attr, accent=accent, dashed=dashed)
        (x1, y1), (x2, y2) = pts[-2], pts[-1]
        self.head(x1, y1, x2, y2, d, accent)
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

    # ---- drafting conventions (used by the mechanics sheet)
    def center(self, x1, y1, x2, y2):
        """Chain (dash-dot) centre line."""
        d = self._d()
        self.ink.append(f'<path class="d-center" d="M{x1:g},{y1:g} L{x2:g},{y2:g}" style="--d:{d}"/>')

    def dim(self, x1, y1, x2, y2, text, off=0.0, ext_from=None):
        """Dimension: extension lines from the part, a line with arrowheads at both ends and the value."""
        dx, dy = x2 - x1, y2 - y1
        ln = math.hypot(dx, dy)
        nx, ny = -dy / ln, dx / ln
        ax, ay, bx, by = x1 + nx * off, y1 + ny * off, x2 + nx * off, y2 + ny * off
        d = self._d()
        if off:
            for (px, py), (qx, qy) in (((x1, y1), (ax, ay)), ((x2, y2), (bx, by))):
                ex, ey = qx + nx * 6 * math.copysign(1, off), qy + ny * 6 * math.copysign(1, off)
                self.ink.append(f'<path class="d-line d-thin" d="M{px + nx * 4 * math.copysign(1, off):.1f},{py + ny * 4 * math.copysign(1, off):.1f} L{ex:.1f},{ey:.1f}" pathLength="1" style="--d:{d}"/>')
        self.ink.append(f'<path class="d-line d-thin" d="M{ax:.1f},{ay:.1f} L{bx:.1f},{by:.1f}" pathLength="1" style="--d:{d}"/>')
        self.head(bx, by, ax, ay, d, s=9)
        self.head(ax, ay, bx, by, d, s=9)
        mx, my = (ax + bx) / 2, (ay + by) / 2
        ang = math.degrees(math.atan2(dy, dx))
        if ang > 90 or ang < -90:
            ang += 180
        self.ink.append(f'<text class="d-txt d-dim" x="{mx:.1f}" y="{my - 7:.1f}" text-anchor="middle" '
                        f'transform="rotate({ang:.1f} {mx:.1f} {my:.1f})" style="--d:{d}">{esc(text)}</text>')

    def balloon(self, x, y, n, tx, ty):
        """Item balloon with a leader ending in a dot on the part."""
        d = self._d()
        a = math.atan2(ty - y, tx - x)
        sx, sy = x + 13 * math.cos(a), y + 13 * math.sin(a)
        self.ink.append(f'<path class="d-line d-thin" d="M{sx:.1f},{sy:.1f} L{tx:g},{ty:g}" pathLength="1" style="--d:{d}"/>')
        self.ink.append(f'<circle class="d-txt d-pin" cx="{tx}" cy="{ty}" r="2.6" style="--d:{d}"/>')
        self.ink.append(f'<circle class="d-line" cx="{x}" cy="{y}" r="13" pathLength="1" style="--d:{d}"/>')
        self.ink.append(f'<text class="d-txt d-ball" x="{x}" y="{y + 6}" text-anchor="middle" style="--d:{d}">{n}</text>')

    def svg(self, label: str) -> str:
        return (f'<svg class="sketch-svg" viewBox="0 0 {self.w} {self.h}" role="img" aria-label="{esc(label)}">'
                f'<g class="d-ink">{"".join(self.ink)}</g>'
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
    s.note(28, 262, "PWM-synced sampling:\n68 µs → 5.4 µs (bench)", accent=True)
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
    s.note(470, 86, "48 V bus · 45 A", anchor="end", accent=True)
    s.path("M480,392 L900,392")
    s.note(470, 399, "GND", anchor="end")
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
    s.note(480, 434, "Motor driver board · 2 layers · KiCad 10, ERC + DRC on every change", anchor="middle", size="small")
    return s


def mechanics() -> Sheet:
    """A drafting-course sheet: side and top views, centre lines, hidden lines, dimensions in mm taken from the
    CAD assembly's bounding box, item balloons and a parts list. Proportions are the car's; wheel size is schematic."""
    s = Sheet("mechanics", h=576)
    # ---------------- side view (nose left); 2 700 mm over 520 px
    s.note(40, 38, "SIDE VIEW", size="big")
    s.note(40, 60, "dimensions in mm", size="small")
    g = 330                                   # ground
    s.path(f"M40,{g} L604,{g}", cls="d-line d-thin")
    s.path(" ".join(f"M{x},{g} l-10,12" for x in range(52, 604, 16)), cls="d-line d-hair", wobble=False)
    wheels = ((150, 290), (500, 290))
    for cx, cy in wheels:                     # wheels: the part under the shell is visible, the rest hidden
        s.path(f"M{cx + 24},{322} A40,40 0 0,1 {cx - 24},{322}", wobble=False)
        s.path(f"M{cx - 24},{322} A40,40 0 1,1 {cx + 24},{322}", cls="d-line d-thin", dashed=True, wobble=False)
        s.circle(cx, cy, 6, cls="d-line d-thin")
        s.center(cx, 236, cx, 346)
    s.center(96, 290, 556, 290)
    s.circle(500, 290, 13, accent=True)       # rear hub motor
    s.path("M60,300 C64,262 110,232 175,222 C230,213 262,212 290,206 C310,176 360,170 395,186 "
           "C420,196 470,205 520,220 C560,232 582,262 580,292 C578,312 560,320 530,322 L120,322 C84,322 60,314 60,300 Z",
           accent=True, wobble=False)
    s.path("M300,206 C318,186 360,182 388,193", cls="d-line d-thin", wobble=False)       # canopy
    s.dim(60, g, 580, g, "≈ 2 700", off=40)
    s.path(f"M372,177 L626,177 M584,{g} L626,{g}", cls="d-line d-hair")                   # extension lines
    s.dim(618, g, 618, 177, "≈ 820")
    s.balloon(250, 118, 1, 246, 212)
    s.balloon(560, 130, 3, 506, 280)

    # ---------------- top view (nose up), not to the same scale
    s.note(668, 38, "TOP VIEW", size="big")
    s.note(668, 60, "left turn, wheels steered", size="small")
    oy = 34                                   # the whole view sits lower, clear of its title and the width dimension
    body = ("M790,92 C826,94 848,140 848,214 C848,312 830,404 805,452 C800,460 780,460 775,452 "
            "C750,404 732,312 732,214 C732,140 754,94 790,92 Z")
    d = s._d()
    s.ink.append(f'<path class="d-line d-thin" transform="translate(0 {oy})" d="{body}" pathLength="1" style="--d:{d}"/>')
    s.center(790, 80 + oy, 790, 486 + oy)
    kl, kr, t = (754, 186 + oy), (826, 186 + oy), (790, 520 + oy)
    s.path(f"M{kl[0]},{kl[1]} L{kr[0]},{kr[1]}", cls="d-line d-thin")                    # front axle
    ends = []
    for k in (kl, kr):                        # steering arms aimed behind the rear wheel
        dx, dy = t[0] - k[0], t[1] - k[1]
        n = math.hypot(dx, dy)
        e = (k[0] + 30 * dx / n, k[1] + 30 * dy / n)
        ends.append(e)
        s.path(f"M{k[0]},{k[1]} L{e[0]:.1f},{e[1]:.1f}", accent=True)
        s.path(f"M{e[0]:.1f},{e[1]:.1f} L{t[0]},{t[1]}", dashed=True, cls="d-line d-thin")
    s.path(f"M{ends[0][0]:.1f},{ends[0][1]:.1f} L{ends[1][0]:.1f},{ends[1][1]:.1f}", accent=True)   # tie rod
    for (cx, cy), ang in ((kl, -26), (kr, -16)):   # inner wheel turns more than the outer one
        d = s._d()
        s.ink.append(f'<path class="d-line" transform="rotate({ang} {cx} {cy})" d="{s._rect(cx - 6, cy - 24, 12, 48, 3)}" pathLength="1" style="--d:{d}"/>')
        s.path(f"M{cx},{cy - 34} L{cx},{cy - 52}", cls="d-line d-hair", wobble=False)
    s.note(731, 132 + oy, "δi", size="small", anchor="middle")
    s.note(842, 138 + oy, "δo", size="small", anchor="middle")
    d = s._d()
    s.ink.append(f'<path class="d-line" d="{s._rect(784, 396 + oy, 12, 48, 3)}" pathLength="1" style="--d:{d}"/>')  # rear wheel
    s.path(f"M732,{214 + oy} L732,{98} M848,{214 + oy} L848,{98}", cls="d-line d-hair")  # extension lines
    s.dim(732, 106, 848, 106, "≈ 810")
    s.balloon(904, 230 + oy, 2, 808, 208 + oy)
    s.balloon(690, 250 + oy, 4, 748, 196 + oy)
    s.note(904, 566, "δi > δo: partial Ackermann", size="small", anchor="end", accent=True)

    # ---------------- parts list
    x0, x1, x2, x3, y0, rh = 40, 92, 268, 604, 404, 24
    rows = (("ITEM", "PART", "NOTE"), ("1", "Monocoque shell", "closed body over the chassis"),
            ("2", "Steering", "trapezoidal, partial Ackermann"),
            ("3", "Rear wheel", "hub motor 350 W → ≈ 500 W, chain + clutch"),
            ("4", "Brakes", "hydraulic, on all three wheels"))
    ylast = y0 + rh * len(rows)
    s.path(f"M{x0},{y0} L{x3},{y0} L{x3},{ylast} L{x0},{ylast} Z", cls="d-line d-thin")
    s.path(" ".join(f"M{x0},{y0 + rh * i} L{x3},{y0 + rh * i}" for i in range(1, len(rows))), cls="d-line d-hair")
    s.path(f"M{x1},{y0} L{x1},{ylast} M{x2},{y0} L{x2},{ylast}", cls="d-line d-hair")
    for i, (a, b, c) in enumerate(rows):
        y = y0 + rh * i + 17
        cls = "d-th" if i == 0 else "d-tab"
        s.note((x0 + x1) / 2, y, a, anchor="middle", cls=cls)
        s.note(x1 + 10, y, b, cls=cls)
        s.note(x2 + 10, y, c, cls=cls)
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
    s.note(20, 32, "onboard computer · ROS 2 · designed to run 100 % on board (no external process)")
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


def kit() -> Sheet:
    """Where the autonomy kit goes on the car: side view with each part marked in its area, item balloons
    and a parts list saying what each part connects to (from the adc-stack README, without models).
    Positions are indicative; parts still to be chosen are dashed."""
    s = Sheet("kit", h=596)
    sc, tx, ty = 1.55, -11.3, -146.6                      # the mechanics side view, enlarged

    def tf(d: str) -> str:
        return re.sub(r"-?\d+(?:\.\d+)?(?:,| )-?\d+(?:\.\d+)?",
                      lambda m: "{:.1f},{:.1f}".format(*(float(v) * sc + o for v, o in zip(re.split(r"[ ,]", m.group(0)), (tx, ty)))), d)

    s.note(40, 38, "KIT LAYOUT · SIDE VIEW", size="big")
    s.note(40, 62, "positions indicative · dashed: still to choose", size="small")
    g = 365
    s.path(f"M40,{g} L920,{g}", cls="d-line d-thin")
    s.path(" ".join(f"M{x},{g} l-10,12" for x in range(52, 920, 16)), cls="d-line d-hair", wobble=False)
    for cx in (221.2, 763.7):                              # wheels: visible below the shell, hidden above
        s.path(f"M{cx + 37.3:.1f},352.5 A62,62 0 0,1 {cx - 37.3:.1f},352.5", wobble=False)
        s.path(f"M{cx - 37.3:.1f},352.5 A62,62 0 1,1 {cx + 37.3:.1f},352.5", cls="d-line d-thin", dashed=True, wobble=False)
        s.center(cx, 228, cx, 380)
    s.path(tf("M60,300 C64,262 110,232 175,222 C230,213 262,212 290,206 C310,176 360,170 395,186 "
              "C420,196 470,205 520,220 C560,232 582,262 580,292 C578,312 560,320 530,322 L120,322 C84,322 60,314 60,300 Z"),
           cls="d-line d-thin", wobble=False)
    s.path(tf("M300,206 C318,186 360,182 388,193"), cls="d-line d-hair", wobble=False)
    s.circle(540, 176, 15, cls="d-line d-thin")            # the safety driver, under the canopy

    # the parts (small boxes, no text: the balloons and the list name them)
    s.box(290, 166, 46, 20, "", r=3)                       # 1 camera, on top in its pod
    s.path("M313,186 L313,198", cls="d-line d-thin")
    s.box(156, 250, 36, 18, "", r=3)                       # 2 LiDAR, at the front
    s.path("M650,163 L650,138 M640,138 L660,138", cls="d-line")          # 3 GPS antenna
    s.box(462, 292, 26, 18, "", r=3)                       # 4 compass
    s.box(500, 288, 42, 24, "", r=3)                       # 5 telemetry board
    s.box(282, 270, 64, 34, "", r=4, accent=True)          # 6 onboard computer, under the camera
    s.box(664, 288, 42, 24, "", r=3)                       # 7 guard board
    s.circle(763.7, 302.9, 16, accent=True)                # 8 motor driver and hub motor
    s.path(s._rect(205, 300, 38, 22, 3), cls="d-line d-tbd", dashed=True, wobble=False)   # 9 steering actuator (to choose)
    s.path(s._rect(395, 306, 38, 22, 3), cls="d-line d-tbd", dashed=True, wobble=False)   # 10 brake actuator (to choose)
    s.circle(586, 214, 7, accent=True)                     # 11 e-stop, at the driver's hand
    # signal paths, faint: camera and LiDAR into the computer; GPS and compass into the telemetry board;
    # the e-stop into the guard
    for d_ in ("M313,198 L313,270", "M192,259 C230,262 258,272 282,282", "M488,301 L500,301",
               "M650,163 C620,220 560,260 528,288", "M592,219 C628,240 668,262 684,288"):
        s.path(d_, cls="d-line d-hair", dashed=True, wobble=False)
    # the computer talks only to the guard (long CAN run along the floor); the guard fans out to the
    # telemetry board, the motor driver and both actuators
    s.path("M314,304 L314,340 L685,340 L685,312", accent=True)
    s.note(600, 334, "CAN", size="small", anchor="middle", accent=True)
    s.path("M664,296 L542,298", accent=True)                                   # guard → telemetry board
    s.path("M706,300 L748,302", accent=True)                                   # guard → motor driver
    s.note(603, 288, "UART", size="small", anchor="middle", accent=True)       # the guard's links are UART
    s.note(726, 290, "UART", size="small", anchor="middle", accent=True)
    s.path("M685,340 L685,352 L224,352 L224,322", accent=True, dashed=True)    # guard → steering actuator
    s.path("M414,352 L414,328", accent=True, dashed=True)                      # guard → brake actuator

    for n, (bx, by), tgt in ((1, (300, 108), (312, 168)), (2, (110, 150), (170, 252)), (3, (706, 104), (652, 140)),
                             (11, (520, 104), (584, 208)), (9, (220, 404), (224, 322)), (6, (310, 404), (306, 304)),
                             (10, (410, 404), (414, 328)), (4, (480, 404), (475, 310)), (5, (560, 404), (530, 312)),
                             (7, (680, 404), (692, 312)), (8, (790, 404), (770, 318))):
        s.balloon(bx, by, n, *tgt)

    # parts list in two blocks (what goes where, not which model)
    rows = (("1", "Camera", "stereo, on top · to the computer"), ("2", "LiDAR", "2D scanner at the front · to the computer"),
            ("3", "GPS", "position · to the telemetry board"), ("4", "Compass", "orientation · to the telemetry board"),
            ("5", "Telemetry board", "sensors and logging · UART to the guard"), ("6", "Onboard computer", "all autonomy · CAN to the guard only"),
            ("7", "Guard board", "UART · telemetry, driver, actuators"), ("8", "Motor driver", "our FOC driver, rear hub motor"),
            ("9", "Steering actuator", "UART from the guard · to choose"), ("10", "Brake actuator", "UART from the guard · to choose"),
            ("11", "E-stop", "with the safety driver · to the guard"))
    y0, rh = 432, 22
    for block, (x0, xa, xb, x3) in enumerate(((40, 80, 196, 470), (490, 530, 666, 920))):
        part = rows[:6] if block == 0 else rows[6:]
        body = (("ITEM", "PART", "NOTE"),) + part
        ylast = y0 + rh * len(body)
        s.path(f"M{x0},{y0} L{x3},{y0} L{x3},{ylast} L{x0},{ylast} Z", cls="d-line d-thin")
        s.path(" ".join(f"M{x0},{y0 + rh * i} L{x3},{y0 + rh * i}" for i in range(1, len(body))), cls="d-line d-hair")
        s.path(f"M{xa},{y0} L{xa},{ylast} M{xb},{y0} L{xb},{ylast}", cls="d-line d-hair")
        for i, (a, b, c) in enumerate(body):
            y = y0 + rh * i + 16
            cls = "d-th" if i == 0 else "d-tab"
            s.note((x0 + xa) / 2, y, a, anchor="middle", cls=cls)
            s.note(xa + 8, y, b, cls=cls)
            s.note(xb + 8, y, c, cls=cls)
    return s


SHEETS = {"driver": driver, "telemetry": telemetry, "electronics": electronics, "mechanics": mechanics,
          "strategy": strategy, "adc": adc, "kit": kit}

CAPTIONS = {
    "driver": "Field-oriented control, every 100 µs: currents measured, turned into the rotor's frame, corrected and sent back as PWM.",
    "telemetry": "Sensors fused by a Kalman filter into one live state, logged, shown to the driver and sent to the pits.",
    "electronics": "The motor-driver board: a Teensy 4.1 drives three half-bridges on the 48 V bus and reads the current through shunt amplifiers.",
    "mechanics": "Side and top views with overall dimensions in mm, item balloons and parts list. From above, the trapezoidal steering: the arm lines meet behind the rear wheel, so the inner wheel turns more.",
    "strategy": "Pulse and glide: short pushes with the motor at its efficient point, long glides with it off; and what each improvement is worth.",
    "adc": "The autonomy pipeline, entirely on board, and the one-way telemetry to the cloud and the digital twin.",
    "kit": "Where the autonomy kit goes on the car. The onboard computer talks only to the guard board at the back, over a long CAN run; the guard links the telemetry board, the motor driver and the actuators over UART, and takes the e-stop. Positions are indicative.",
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
