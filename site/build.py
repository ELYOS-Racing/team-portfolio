"""Builds the static portfolio site into _site/ from site/data.yaml and the Markdown pages.

    pip install markdown pyyaml
    python site/build.py                 # → _site/
    python site/build.py --write-readme  # rewrites the results table of README.md from data.yaml
    python site/build.py --check-readme  # CI: fails if README.md and data.yaml disagree
"""

from __future__ import annotations

import argparse
import html
import json
import math
import re
import shutil
import sys
from pathlib import Path

import markdown
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import diagrams  # noqa: E402  (site/diagrams.py)

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
OUT = ROOT / "_site"
REPO = "https://github.com/ELYOS-Racing/team-portfolio"
BASE_URL = "https://elyos-racing.github.io/team-portfolio/"
# Archivo for everything; Caveat only for the handwritten notes in the diagrams (its file loads only where used)
FONTS = ("https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@100..125,400..900"
         "&family=Caveat:wght@500..700&family=JetBrains+Mono:wght@500..800&display=swap")
# Runs before first paint and costs nothing: only flags that JS is on, so entrance states apply.
# (No WebGL probe here any more: creating a GL context in <head> blocked the first paint.)
HEAD_JS = '<script>document.documentElement.classList.add("js")</script>'
THREE = "https://unpkg.com/three@0.170.0"
IMPORTMAP = (f'<script type="importmap">{{"imports":{{"three":"{THREE}/build/three.module.js",'
             f'"three/addons/":"{THREE}/examples/jsm/"}}}}</script>')
README_START, README_END = "<!-- results:start -->", "<!-- results:end -->"

esc = html.escape


# ------------------------------------------------------------------ layout

def page(title: str, body: str, depth: int, description: str = "", current: str = "", car3d: bool = False,
         rail: list[tuple[str, str]] | None = None) -> str:
    up = "../" * depth
    full_title = f"{title} | Elyos Racing Team" if title else "Elyos Racing Team"
    desc = esc(description or "Elyos Racing Team: ultra-efficient electric prototypes for the Shell Eco-marathon, "
               "Tecnológico de Monterrey, Guadalajara campus.")
    def nav(href: str, label: str, key: str) -> str:
        cur = ' aria-current="page"' if key == current else ""
        return f'<a href="{up}{href}"{cur}>{label}</a>'
    rail_html = ""
    if rail:  # chapter index in the left margin of wide screens
        items = "".join(f'<li><a href="#{i}"><span class="n">{n:02d}</span><span class="t">{esc(t)}</span></a></li>'
                        for n, (i, t) in enumerate(rail, 1))
        rail_html = f'<nav class="rail" aria-label="On this page"><ol>{items}</ol></nav>'
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(full_title)}</title>
<meta name="description" content="{desc}">
<meta property="og:title" content="{esc(full_title)}">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="{BASE_URL}assets/og.png">
<meta property="og:type" content="website">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#08202f">
<meta name="color-scheme" content="dark">
<link rel="icon" href="{up}assets/favicon-32.png" sizes="32x32">
<link rel="apple-touch-icon" href="{up}assets/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
<link rel="stylesheet" href="{up}style.css">
{HEAD_JS}
{IMPORTMAP if car3d else ""}
</head>
<body>
<a class="skip" href="#content">Skip to content</a>
<header class="bar">
<div class="bar-in">
<a class="brand" href="{up or "./"}"><img src="{up}assets/logo-on-dark.png" alt="Elyos Racing Team, home" width="132" height="44"></a>
<nav aria-label="Main">{nav("projects/", "Engineering", "engineering")}{nav("mileage", "Mileage", "mileage")}{nav("adc", "Autonomous", "adc")}{nav("members/", "Team", "members")}</nav>
</div>
</header>
{rail_html}
<main id="content" tabindex="-1">
{body}
</main>
<footer>
<div class="foot-in">
<img src="{up}assets/logo-on-dark.png" alt="" width="108" height="36" loading="lazy">
<p>Content © 2026 Luis Xavier García Pimentel Ascencio and Elyos Racing Team, <a href="{REPO}/blob/main/LICENSE.md">PolyForm Strict 1.0.0</a>. Member pages belong to each member. <a href="{REPO}">Source on GitHub</a>.</p>
</div>
</footer>
<script src="{up}site.js" defer></script>
</body>
</html>
"""


# ------------------------------------------------------------------ pieces

def md_to_html(text: str) -> str:
    out = markdown.markdown(text, extensions=["tables", "sane_lists"])
    out = re.sub(r"<thead>\s*<tr>\s*<th>Field</th>\s*<th>Value</th>\s*</tr>\s*</thead>", "", out)
    # links between Markdown pages become clean URLs (GitHub Pages serves /x from x.html)
    out = re.sub(r'href="(?!https?://)([^"#]+)\.md(#[^"]*)?"', lambda m: f'href="{m.group(1)}{m.group(2) or ""}"', out)
    out = out.replace('href="../LICENSE"', f'href="{REPO}/blob/main/LICENSE.md"')
    out = out.replace('href="TEMPLATE"', f'href="{REPO}/blob/main/members/TEMPLATE.md"')
    out = out.replace("<table>", '<div class="table-wrap"><table>').replace("</table>", "</table></div>")
    return out


def split_page(text: str) -> tuple[str, dict[str, str], str]:
    """Title, the leading Field | Value table as a dict, and the rest of the Markdown."""
    m = re.search(r"^# (.+)$", text, re.M)
    title = m.group(1).strip() if m else ""
    rest = text[m.end():] if m else text
    fields: dict[str, str] = {}
    t = re.search(r"\n\| Field \| Value \|\n\|[-| ]+\|\n((?:\|.*\|\n?)+)", rest)
    if t:
        for line in t.group(1).strip().splitlines():
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) >= 2:
                fields[cells[0]] = "|".join(cells[1:]).strip()
        rest = rest[:t.start()] + rest[t.end():]
    return title, fields, rest


def inline_md(s: str) -> str:
    out = markdown.markdown(s)
    return re.sub(r"^<p>(.*)</p>$", r"\1", out.strip(), flags=re.S)


def track_svg(tracks: dict, key: str, label: str, cls: str = "", live: bool = False) -> str:
    """Course outline. Stroke widths scale with --u so every course reads the same at its display size.
    With live=True it also carries the faint base line, the trail and the car used by the circuit animation."""
    t = tracks[key]
    vb = [float(v) for v in t["viewBox"].split()]
    u = max(vb[2], vb[3]) / 800  # viewBox units per "design pixel" at a typical display size
    sx, sy = t["start"]
    nx, ny = t["next"]
    ang = math.degrees(math.atan2(ny - sy, nx - sx))
    flag_x, flag_y, start_dot = sx, sy, ""
    if not t["closed"]:  # open course (ADC): dot at the start, checkered line at the finish
        flag_x, flag_y = t["end"]
        start_dot = f'<circle class="origin" cx="{sx}" cy="{sy}" r="{7 * u:.1f}"/>'
    c = 6 * u  # checker cell
    white = ' class="w"'
    cells = "".join(
        f'<rect{white if (i + j) % 2 else ""} x="{(i - 2) * c:.1f}" y="{(j - 1) * c:.1f}" width="{c:.1f}" height="{c:.1f}"/>'
        for i in range(4) for j in range(2))
    live_bits = ""
    if live:
        live_bits = (f'<path class="trail" d="{t["d"]}" pathLength="1000"/>'
                     f'<g class="car" transform="translate({sx} {sy}) rotate({ang:.1f})"><circle class="halo" r="{16 * u:.1f}"/>'
                     f'<path class="dot" d="M{10 * u:.1f},0 L{-7 * u:.1f},{-7 * u:.1f} L{-3 * u:.1f},0 L{-7 * u:.1f},{7 * u:.1f} Z"/></g>')
    return f"""<svg class="track {cls}" viewBox="{t['viewBox']}" style="--u:{u:.3f}" role="img" aria-label="{esc(label)}" preserveAspectRatio="xMidYMid meet">
<path class="lap-base" d="{t['d']}"/>
<path class="lap" d="{t['d']}" pathLength="1000"/>
<g class="startline" transform="translate({flag_x} {flag_y}) rotate({ang + 90:.1f})">{cells}</g>
{start_dot}{live_bits}</svg>"""


def circuit_hero(tracks: dict, key: str, copy_html: str, label: str, alt: str, mode: dict) -> str:
    """The course as the hero: it draws itself, then the car runs it with a live readout.
    `mode` holds the data-* attributes read by site.js (laps or a single run)."""
    t = tracks[key]
    vb = [float(v) for v in t["viewBox"].split()]
    shape = "wide" if vb[2] / vb[3] > 1.5 else "square"
    svg = track_svg(tracks, key, label, "hero-svg", live=True)
    if shape == "wide":  # anchored bottom right, leaving the top-left quarter to the copy
        svg = svg.replace('preserveAspectRatio="xMidYMid meet"', 'preserveAspectRatio="xMaxYMax meet"')
    attrs = " ".join(f'data-{k}="{esc(str(v))}"' for k, v in mode.items())
    status = ('<div class="hud-cell hud-status"><span class="k"><i class="pulse"></i>Status</span>'
              '<span class="v" data-hud="status">On the grid</span></div>')
    if mode["mode"] == "laps":
        hud = status + f"""<div class="hud-cell"><span class="k">Lap</span><span class="v" data-hud="lap">1<small>/{mode['laps']}</small></span></div>
<div class="hud-cell"><span class="k">Speed</span><span class="v" data-hud="speed">0<small> km/h</small></span></div>
<div class="hud-cell"><span class="k">Distance</span><span class="v" data-hud="dist">0.0<small> km</small></span></div>
<div class="hud-cell hud-meter"><span class="k">Energy left</span><span class="v" data-hud="energy">1,000<small> Wh</small></span><span class="meter"><span data-hud="bar"></span></span></div>"""
    else:
        hud = status + f"""
<div class="hud-cell"><span class="k">Speed</span><span class="v" data-hud="speed">0<small> km/h</small></span></div>
<div class="hud-cell hud-meter"><span class="k">Course</span><span class="v" data-hud="dist">0<small> / {t['length_m']:,.0f} m</small></span><span class="meter"><span data-hud="bar"></span></span></div>"""
    # entrance order: each first-level piece of the copy, then the readout and the toggle
    n = 0
    def enter(m: re.Match) -> str:
        nonlocal n
        n += 1
        return f'{m.group(0)} data-enter style="--i:{n - 1}"'
    copy_html = re.sub(r'<(?:h1|p class="(?:eyebrow|lede|cta)")', enter, copy_html)
    return f"""<section class="hero hero--{shape}" data-circuit {attrs} aria-labelledby="hero-title">
<div class="hero-grid">
<div class="hero-copy">{copy_html}</div>
<figure class="hero-track">{svg}
<figcaption class="sr-only">{esc(alt)}</figcaption></figure>
<div class="hud" aria-hidden="true" data-enter style="--i:{n + 1}">{hud}</div>
<button class="motion-toggle" type="button" aria-pressed="false" data-enter style="--i:{n + 2}"><span class="ico" aria-hidden="true"></span><span class="lbl">Pause motion</span></button>
</div>
</section>"""


def eyebrow(text: str) -> str:
    return f'<p class="eyebrow">{esc(text)}</p>'


def stats_band(data: dict) -> str:
    items = "".join(f'<div class="stat" data-reveal><dt>{esc(label)}</dt>'
                    f'<dd><span class="num" data-count="{v}">{v}</span>'
                    f'<span class="unit{" unit--ord" if unit.startswith(("st", "nd", "rd", "th")) else ""}">{esc(unit)}</span></dd></div>'
                    for v, unit, label in data["stats"])
    return f'<section class="stats" aria-label="Key numbers"><dl>{items}</dl></section>'


def results_list(data: dict, up: str = "") -> str:
    """Grouped by circuit: the bars only compare attempts on the same course."""
    groups: dict[str, list[dict]] = {}
    for r in data["results"]:
        groups.setdefault(r.get("circuit", "Other venues"), []).append(r)
    out = []
    for circuit, rows_in in groups.items():
        best = max((r.get("km_per_kwh") or 0) for r in rows_in) or 1
        rows = []
        for r in rows_in:
            k = r.get("km_per_kwh")
            bar = (f'<div class="eff"><span class="track-bar"><span class="fill" style="--w:{k / best:.3f}"></span></span>'
                   f'<span class="val">{k}<small> km/kWh</small></span></div>') if k else \
                '<div class="eff eff--none"><span class="val">Debut, no score</span></div>'
            rows.append(f'<li data-reveal><a class="year" href="{up}{r["page"].removesuffix(".md")}" '
                        f'aria-label="{r["year"]} season: {esc(r["event"])}">{r["year"]}</a>'
                        f'<div class="res-body"><p class="event">{esc(r["event"])}</p><p class="result">{esc(r["result"])}</p></div>{bar}</li>')
        note = ("Bars compare attempts on this course only." if circuit != "Other venues"
                else "Different courses: each bar is relative to its own event.")
        if circuit == "Other venues":
            rows = [re.sub(r'style="--w:[0-9.]+"', 'style="--w:1"', x) for x in rows]
        out.append(f'<div class="res-group"><h3 class="res-circuit">{esc(circuit)}<span>{note}</span></h3>'
                   f'<ol class="results">{"".join(rows)}</ol></div>')
    return "".join(out)


def project_cards(data: dict, keys: list[str], up: str = "") -> str:
    """Engineering areas as cards: hand-drawn glyph, discipline, name, one line."""
    items = []
    for k in keys:
        p = data["projects"][k]
        items.append(f'<li class="card eng" data-reveal>{diagrams.glyph(k)}'
                     f'<p class="eng-tag">{esc(p.get("discipline", ""))}</p>'
                     f'<h3><a class="stretch" href="{up}{p["page"].removesuffix(".md")}">{esc(p["name"])}</a></h3>'
                     f'<p>{esc(p["summary"])}</p><span class="go" aria-hidden="true">See how it works <span class="arrow">→</span></span></li>')
    return f'<ul class="cards">{"".join(items)}</ul>'


project_list = project_cards


def facts(rows: list, source: str = "") -> str:
    cells = "".join(f"<div><dt>{esc(a)}</dt><dd>{esc(b)}</dd></div>" for a, b in rows)
    return f'<dl class="facts">{cells}</dl>' + (f'<p class="fine">{esc(source)}</p>' if source else "")


def initials(name: str, override: str = "") -> str:
    """First letters of the first two names (Luis Xavier → LX), unless the member sets Initials."""
    if override.strip() and not override.strip().startswith("("):  # "(optional…)" is the template's placeholder
        return override.strip()[:3].upper()
    parts = [p for p in re.split(r"\s+", name) if p]
    return "".join(p[0] for p in parts[:2]).upper() if parts else "?"


ICON_GH = ('<svg class="ico" viewBox="0 0 16 16" aria-hidden="true"><path fill="currentColor" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 '
           '2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52'
           '-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08'
           '-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51'
           '.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0 0 16 8c0'
           '-4.42-3.58-8-8-8Z"/></svg>')
ICON_IN = ('<svg class="ico" viewBox="0 0 16 16" aria-hidden="true"><path fill="currentColor" d="M0 1.15C0 .52.52 0 1.18 0h13.64C15.48 '
           '0 16 .52 16 1.15v13.7c0 .63-.52 1.15-1.18 1.15H1.18C.52 16 0 15.48 0 14.85V1.15Zm4.94 12.24V6.17H2.54v7.22h2.4ZM3.74 5.18c.84 0 '
           '1.36-.55 1.36-1.25-.02-.71-.52-1.25-1.34-1.25-.82 0-1.36.54-1.36 1.25 0 .7.52 1.25 1.33 1.25h.01Zm4.91 8.21V9.36c0-.22.02-.43.08'
           '-.59.18-.43.57-.88 1.23-.88.87 0 1.21.66 1.21 1.63v3.87h2.4V9.25c0-2.22-1.18-3.25-2.76-3.25-1.27 0-1.85.7-2.16 1.19v.03h-.02l.02'
           '-.03V6.17h-2.4c.03.68 0 7.22 0 7.22h2.4Z"/></svg>')


def social(f: dict) -> dict:
    """GitHub and LinkedIn from a member's field table: a Markdown link or a bare URL; placeholders are ignored."""
    out = {}
    gh = re.search(r"https://github\.com/([A-Za-z0-9-]+)", f.get("GitHub", ""))
    if gh and gh.group(1) != "username":
        out["github"] = (f"https://github.com/{gh.group(1)}", gh.group(1))
    li = re.search(r"https?://(?:[a-z]{2,3}\.)?linkedin\.com/in/([A-Za-z0-9_%-]+)/?", f.get("LinkedIn", ""))
    if li and li.group(1) != "your-handle":  # the template's example
        out["linkedin"] = (f"https://www.linkedin.com/in/{li.group(1)}/", f"in/{li.group(1)}")
    return out


def social_link(kind: str, url: str, handle: str) -> str:
    return f'<a class="soc" href="{esc(url)}" rel="me noopener">{ICON_GH if kind == "github" else ICON_IN}<span>{esc(handle)}</span></a>'


def members_list(members: list[dict], up: str = "") -> str:
    """Crew sheet: one small title block per member, plus the invitation to publish."""
    cards = []
    for m in members:
        tag = f'<span class="tag">{esc(m["seasons"])}</span>' if m.get("seasons") else ""
        soc = m.get("social", {})
        icons = "".join(f'<a class="soc-ico" href="{esc(u)}" rel="me noopener" aria-label="{esc(m["name"])} on {"GitHub" if k == "github" else "LinkedIn"}">'
                        f'{ICON_GH if k == "github" else ICON_IN}</a>' for k, (u, _) in soc.items())
        icons = f'<span class="soc-row">{icons}</span>' if icons else ""
        cards.append(f'<li class="member" data-reveal>{monogram(m["name"], "sm", m.get("initials", ""))}'
                     f'<span class="who"><a class="stretch" href="{up}members/{m["slug"]}">{esc(m["name"])}</a>'
                     f'<span class="area">{esc(m["area"])}</span>{tag}{icons}</span>'
                     f'<span class="dwg" aria-hidden="true">{esc(m.get("dwg", ""))}</span></li>')
    join = (f'<li class="member member--join" data-reveal><span class="mono mono--sm mono--empty" aria-hidden="true">+</span>'
            f'<span class="who"><a class="stretch" href="{REPO}/blob/main/members/TEMPLATE.md">Your page here</a>'
            f'<span class="area">Team members publish their own page with one pull request</span></span></li>')
    return f'<ul class="members">{"".join(cards)}{join}</ul>'


def monogram(name: str, size: str = "", ini: str = "") -> str:
    """Initials inside a hand-drawn double circle (the ink layer wobbles like the diagrams)."""
    return (f'<span class="mono{f" mono--{size}" if size else ""}" aria-hidden="true">'
            f'<svg viewBox="0 0 100 100"><circle class="m1" cx="50" cy="50" r="44" pathLength="1"/>'
            f'<circle class="m2" cx="51" cy="49" r="40" pathLength="1"/></svg><b>{esc(initials(name, ini))}</b></span>')


def car_section(data: dict) -> str:
    c = data["car"]
    return f"""<section id="car" class="band" aria-labelledby="car-title"><div class="block car">
<div class="car-copy" data-reveal>{eyebrow("The 2026 car")}<h2 id="car-title">{esc(c['title'])}</h2>
<p class="lede">{esc(c['summary'])}</p>{facts(c['facts'])}</div>
<div class="viewer" data-car3d data-src="assets/car.glb" data-reveal>
<canvas aria-hidden="true"></canvas>
<p class="viewer-status" role="status">The 3D model loads when you get here.</p>
<p class="viewer-hint" aria-hidden="true">Drag to turn the car</p>
<p class="sr-only">Interactive 3D model of the 2026 car in x-ray: a translucent shell with its outline in blue, and the
chassis, steering and wheels visible inside. It turns slowly on its own; drag to turn it.</p>
</div>
</div></section>"""


def section_head(eyebrow_text: str, title: str, hid: str, extra: str = "") -> str:
    return f'<header class="block-head" data-reveal>{eyebrow(eyebrow_text)}<h2 id="{hid}">{esc(title)}</h2>{extra}</header>'


SEASON = "2027"


def sheet(sid: str, no: int, dwg: str, kicker: str, title: str, body: str, note: str = "", lede: str = "",
          h: str = "h2", wide: bool = False) -> str:
    """A drawing sheet on graph paper: zone marks in the frame, a numbered head with a dimension line,
    an optional handwritten margin note, the content, and a CAD title block at the foot."""
    code = f"ELY-{dwg}-{no:02d}"
    hid = f"{sid}-title"
    zones_x = "".join(f"<span>{c}</span>" for c in "ABCDEF")
    zones_y = "".join(f"<span>{i}</span>" for i in range(1, 5))
    note_html = (f'<p class="margin-note" aria-hidden="true"><svg viewBox="0 0 60 30"><path d="M4 22 C 18 26, 36 18, 54 6 M44 6 L54 6 L50 15"/></svg>'
                 f'{esc(note)}</p>') if note else ""
    return f"""<section id="{sid}" class="sheet-wrap" aria-labelledby="{hid}">
<div class="sheet{' sheet--wide' if wide else ''}">
<div class="zones zones-x" aria-hidden="true">{zones_x}</div><div class="zones zones-y" aria-hidden="true">{zones_y}</div>
<header class="sheet-head" data-reveal>
<p class="sheet-no" aria-hidden="true">{no:02d}</p>
<div class="sheet-title"><p class="kicker">{esc(kicker)}</p><{h} id="{hid}">{esc(title)}</{h}>{f'<p class="lede">{lede}</p>' if lede else ''}</div>
{note_html}
</header>
<div class="dim" data-reveal aria-hidden="true"><span>{code}</span></div>
<div class="sheet-body">{body}</div>
<footer class="title-block" aria-hidden="true">
<span class="tb-team"><b>ELYOS</b> Racing Team</span><span><i>DWG</i>{code}</span><span class="tb-title"><i>Title</i>{esc(title)}</span>
<span><i>Season</i>{SEASON}</span><span><i>Scale</i>NTS</span><span><i>Sheet</i>{no:02d}</span>
</footer>
</div>
</section>"""


# figure numbers and titles of the project diagrams, in home-page order
FIGS = {k: (i, t) for i, (k, t) in enumerate((("mechanics", "Layout and steering"), ("electronics", "Motor-driver board"),
                                              ("driver", "Field-oriented control"), ("telemetry", "Telemetry data flow"),
                                              ("strategy", "Pulse and glide"), ("adc", "Autonomy pipeline")), 1)}


# ------------------------------------------------------------------ pages

def index(data: dict, tracks: dict, members: list[dict]) -> str:
    h = data["hero"]
    laps = round(h["km_per_kwh"] / h["lap_km"])
    progs = data["programs"]
    split = "".join(f"""<a class="program" href="{key}" data-reveal>
<span class="program-track">{track_svg(tracks, p['track'], f"{p['circuit']} course outline", "small")}</span>
<span class="program-tag">{esc(p['circuit'])}</span>
<h3>{esc(p['name'])}</h3><p>{esc(p['summary'])}</p><span class="go" aria-hidden="true">Explore <span class="arrow">→</span></span></a>"""
                    for key, p in progs.items())
    copy = ('<p class="eyebrow">Shell Eco-marathon · <span class="long">Tec de Monterrey, Guadalajara</span>'
            '<span class="short">Tec GDL</span></p>'
            f'<h1 id="hero-title"><span class="line">One kilowatt-hour,</span> <span class="line accent">{laps} laps.</span></h1>'
            f'<p class="lede">{h["km_per_kwh"]} km on the energy of a single kilowatt-hour: {laps} laps of '
            f'Indianapolis Motor Speedway at the {esc(h["event"])}.</p>'
            f'<p class="cta"><a class="btn btn-primary" href="#engineering">See the engineering</a>'
            f'<a class="btn btn-ghost" href="#results">Results</a></p>')
    alt = (f"Animation: the outline of Indianapolis Motor Speedway draws itself and a car marker runs it lap after lap, "
           f"speeding up as a time-lapse, while a readout counts laps, distance and the energy left of one "
           f"kilowatt-hour, down to zero after {laps} laps and {h['km_per_kwh']} km. Use the Pause motion button to stop it.")
    mode = {"mode": "laps", "laps": laps, "length-m": tracks[progs['mileage']['track']]["length_m"],
            "total-km": h["km_per_kwh"], "vmax": 32, "finish": f"{h['km_per_kwh']} km on one kilowatt-hour."}
    about = sheet("about", 1, "WEB", "Who we are", "A student team chasing every watt.",
                  f'<div class="split">{split}</div>', note="two challenges, one car",
                  lede=esc(data["tagline"]))
    eng = sheet("engineering", 2, "WEB", "Engineering", "Everything on the car, designed by students.",
                project_cards(data, list(data["projects"])), note="each page has its own drawing",
                lede="Mechanics, electronics, embedded control, data, simulation and autonomy: what we built and why, "
                     "with a diagram of how it works. The design files and the code stay private.")
    res = sheet("results", 3, "WEB", "Test log", "Every attempt, on the record.",
                results_list(data) + '<p class="note">Best official attempt of each event. Tracks differ between events, '
                'so bars compare only within the same circuit.</p>', note="same track = comparable")
    team = sheet("members", 4, "WEB", "Crew", "The people behind it", members_list(members),
                 lede="Each member writes their own page, in résumé language, with what they built and measured.")
    body = f"""{circuit_hero(tracks, progs['mileage']['track'], copy,
                     "Outline of the Mileage Challenge course at Indianapolis Motor Speedway", alt, mode)}
{stats_band(data)}
{about}
{eng}
{car_section(data)}
{res}
{team}
<section class="block sources" aria-labelledby="sources-title"><h2 id="sources-title">Sources</h2><ul>{"".join(f'<li><a href="{s["url"]}">{esc(s["label"])}</a></li>' for s in data["sources"])}</ul></section>"""
    rail = [("content", "Start"), ("about", "Who we are"), ("engineering", "Engineering"), ("car", "The car"),
            ("results", "Test log"), ("members", "Crew")]
    return page("", body, 0, data["tagline"], car3d=True, rail=rail)


def program_page(key: str, data: dict, tracks: dict) -> str:
    p = data["programs"][key]
    t = tracks[p["track"]]
    code = "MIL" if key == "mileage" else "ADC"
    rail = [("content", "Course"), ("facts", "Key facts"), ("build", "What we build")]
    facts_sheet = sheet("facts", 1, code, "Rules of the attempt", "Key facts", facts(p["facts"], p["facts_source"]),
                        note="from the official rules")
    build_sheet = sheet("build", 2, code, "Engineering", "What we build", project_cards(data, p['projects']))
    if key == "mileage":
        extra = sheet("results", 3, code, "Test log", "Every attempt, on the record.", results_list(data),
                      note="same track = comparable")
        rail.append(("results", "Test log"))
        h = data["hero"]
        laps = round(h["km_per_kwh"] / h["lap_km"])
        mode = {"mode": "laps", "laps": laps, "length-m": t["length_m"], "vmax": 32, "total-km": h["km_per_kwh"],
                "finish": f"{h['km_per_kwh']} km on one kilowatt-hour."}
        alt = (f"Animation: the outline of {p['circuit']} draws itself and a car marker runs it lap after lap while a "
               f"readout counts laps, distance and the energy left of one kilowatt-hour. Use the Pause motion button to stop it.")
    else:
        adc_md = (ROOT / "projects" / "adc.md").read_text(encoding="utf-8")
        _, _, rest = split_page(adc_md)
        # drop the first paragraph of adc.md: it repeats the program summary shown in the hero
        rest = re.sub(r"^[^\n|#][^\n]*\n", "", rest.lstrip("\n"), count=1)
        fig, ftitle = FIGS["adc"]
        extra = sheet("kit", 3, code, "The kit", "What goes on the car.",
                      diagrams.sheet("adc", fig, ftitle) + f'<div class="doc-body">{md_to_html(rest)}</div>',
                      note="nothing comes back to the car")
        rail.append(("kit", "The kit"))
        mode = {"mode": "run", "length-m": t["length_m"], "vmax": 22, "finish": "Finish line, no hands.", "running": "Driving itself"}
        alt = (f"Animation: the outline of the {p['circuit']} course draws itself and a car marker drives it on its own "
               f"from the start to the checkered finish line, with a readout of speed and distance. Use the Pause motion button to stop it.")
    copy = (f'{eyebrow(p["circuit"])}<h1 id="hero-title"><span class="line">{esc(p["name"])}</span></h1>'
            f'<p class="lede">{esc(p["summary"])}</p>')
    course = f"{p['circuit']} course outline, {t['length_m']:,.0f} m"
    body = f"""{circuit_hero(tracks, p['track'], copy, course, alt, mode)}
{facts_sheet}
{build_sheet}
{extra}
<p class="block fine">Course outline from the official coordinates of the Shell Eco-marathon Data and Telemetry Portal.</p>"""
    return page(p["name"], body, 0, p["summary"], current=key, rail=rail)


# ------------------------------------------------------------------ member: the engineer's data sheet

# "Worked on": areas come from the Area field; only strategy work is also recognised in the text
AREA_PROJECTS = (("motor", "driver"), ("firmware", "driver"), ("telemetry", "telemetry"), ("autonomous", "adc"),
                 ("adc", "adc"), ("electronic", "electronics"), ("mechanic", "mechanics"), ("strategy", "strategy"))
TEXT_PROJECTS = (("energy-strategy", "strategy"), ("energy strategy", "strategy"), ("loss-budget", "strategy"))


def split_sections(md: str) -> tuple[str, list[tuple[str, str]]]:
    """Text before the first '## ', and every '## heading' with its body."""
    parts = re.split(r"^## (.+)$", md, flags=re.M)
    return parts[0], [(parts[i].strip(), parts[i + 1]) for i in range(1, len(parts), 2)]


def md_table(body: str) -> list[list[str]]:
    rows = [[c.strip() for c in l.strip().strip("|").split("|")] for l in body.splitlines() if l.strip().startswith("|")]
    return [r for r in rows[2:]] if len(rows) > 2 else []


def num(s: str) -> float | None:
    try:
        return float(s.replace(",", ""))
    except ValueError:
        return None


def metrics_html(rows: list[list[str]]) -> str:
    out = []
    for r in rows:
        r = (r + ["", "", "", ""])[:4]
        name, before, after, unit = r
        b, a = num(before), num(after)
        u = f" {esc(unit)}" if unit else ""
        if b and a is not None:
            hi, lo = max(b, a), min(b, a)
            ratio = hi / lo if lo else 0
            verb = "lower" if a < b else "higher"
            out.append(f"""<figure class="metric" data-reveal><figcaption>{esc(name)}</figcaption>
<div class="bars"><span class="mbar mbar--before" style="--w:{b / hi:.3f}"><i>before</i><b>{esc(before)}{u}</b></span>
<span class="mbar mbar--after" style="--w:{a / hi:.3f}"><i>after</i><b>{esc(after)}{u}</b></span></div>
<p class="ratio"><span class="dimline" aria-hidden="true"></span><b>{ratio:.1f}× {verb}</b></p></figure>""")
        elif a is not None:
            out.append(f'<figure class="metric metric--big" data-reveal><b class="big">{esc(after)}<small>{u}</small></b>'
                       f'<figcaption>{esc(name)}</figcaption></figure>')
    return f'<div class="metrics">{"".join(out)}</div>' if out else ""


def split_skills(text: str) -> list[str]:
    items, depth, cur = [], 0, ""
    for ch in re.sub(r"\s+", " ", text.strip().rstrip(".")):
        depth += (ch == "(") - (ch == ")")
        if ch == "," and depth == 0:
            items.append(cur.strip())
            cur = ""
        else:
            cur += ch
    return [i for i in items + [cur.strip()] if i]


def member_page(slug: str, text: str, data: dict, n: int) -> tuple[str, dict]:
    title, f, rest = split_page(text)
    intro, sections = split_sections(rest)
    soc = social(f)
    seasons_txt = f.get("Seasons on the team") or f.get("Semesters on the team", "")
    area = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", f.get("Area", ""))
    revs = sorted(((int(m.group(1)), m.group(2).strip(), body) for h, body in sections
                   if (m := re.match(r"Season (\d{4})\s*·\s*(.+)", h))), key=lambda x: x[0])
    role = revs[-1][1] if revs else ""
    dwg = f"ELY-TEAM-{n:02d}"
    metrics = next((metrics_html(md_table(b)) for h, b in sections if h.lower().startswith("measured")), "")
    skills = next((split_skills(re.sub(r"\n+", " ", b)) for h, b in sections if h.lower() == "skills"), [])
    others = [(h, b) for h, b in sections if not (h.lower().startswith(("measured", "skills", "season ")))]

    ident = [("Role", esc(role[:1].upper() + role[1:]) if role else ""), ("Area", esc(area)),
             ("Seasons", inline_md(seasons_txt) if seasons_txt else ""),
             ("Links", "".join(social_link(k, *v) for k, v in soc.items())),
             ("Degree", inline_md(f["Degree"]) if f.get("Degree") else "")]
    ident_html = "".join(f'<div><dt>{k}</dt><dd>{v}</dd></div>' for k, v in ident if v)

    letters = "ABCDEFGHIJ"
    rev_html = "".join(f"""<li class="rev" data-reveal><p class="rev-tag"><b>REV {letters[i]}</b><span>{y}</span></p>
<div class="rev-body"><h3>{esc(r[:1].upper() + r[1:])}</h3>{md_to_html(body)}</div></li>""" for i, (y, r, body) in enumerate(revs))
    bom = "".join(f'<tr><td class="item">{i:02d}</td><td>{esc(s[:1].upper() + s[1:])}</td></tr>' for i, s in enumerate(skills, 1))
    hits = [p for k, p in AREA_PROJECTS if k in area.lower()] + [p for k, p in TEXT_PROJECTS if k in text.lower()]
    worked = list(dict.fromkeys(p for p in hits if p in data["projects"]))

    blocks = []
    if metrics:
        blocks.append(f'<section class="ds-block" aria-labelledby="m-{slug}"><h2 class="ds-h" id="m-{slug}"><span>01</span>Measured results</h2>{metrics}</section>')
    if rev_html:
        blocks.append(f'<section class="ds-block" aria-labelledby="r-{slug}"><h2 class="ds-h" id="r-{slug}"><span>02</span>Revision history</h2><ol class="revs">{rev_html}</ol></section>')
    if bom:
        blocks.append(f'<section class="ds-block" aria-labelledby="b-{slug}"><h2 class="ds-h" id="b-{slug}"><span>03</span>Bill of skills</h2>'
                      f'<table class="bom"><thead><tr><th scope="col">Item</th><th scope="col">Description</th></tr></thead><tbody>{bom}</tbody></table></section>')
    if worked:
        blocks.append(f'<section class="ds-block" aria-labelledby="w-{slug}"><h2 class="ds-h" id="w-{slug}"><span>04</span>Worked on</h2>{project_cards(data, worked, "../")}</section>')
    for h, b in others:
        blocks.append(f'<section class="ds-block"><h2 class="ds-h">{esc(h)}</h2><div class="doc-body">{md_to_html(b)}</div></section>')
    intro_html = f'<div class="doc-body">{md_to_html(intro)}</div>' if intro.strip() else ""

    body = f"""<div class="sheet-wrap sheet-wrap--page"><article class="sheet datasheet" aria-labelledby="ds-name">
<div class="zones zones-x" aria-hidden="true">{"".join(f"<span>{c}</span>" for c in "ABCDEF")}</div><div class="zones zones-y" aria-hidden="true">{"".join(f"<span>{i}</span>" for i in range(1, 5))}</div>
<header class="ds-head" data-reveal>
{monogram(title, "lg", f.get("Initials", ""))}
<div class="ds-id"><p class="kicker">Engineer's data sheet · {dwg}</p><h1 id="ds-name">{esc(title)}</h1>
<dl class="ds-facts">{ident_html}</dl></div>
<p class="stamp" aria-hidden="true">Published<br><span>by its owner</span></p>
</header>
<div class="dim" data-reveal aria-hidden="true"><span>{dwg}</span></div>
{intro_html}
{"".join(blocks)}
<footer class="title-block" aria-hidden="true">
<span class="tb-team"><b>ELYOS</b> Racing Team</span><span><i>DWG</i>{dwg}</span><span class="tb-title"><i>Title</i>{esc(title)}</span>
<span><i>Rev</i>{letters[len(revs) - 1] if revs else "A"}</span><span><i>Season</i>{revs[-1][0] if revs else SEASON}</span><span><i>Sheet</i>01</span>
</footer>
</article></div>"""
    info = {"slug": slug, "name": title, "area": area, "dwg": dwg, "initials": f.get("Initials", ""), "social": soc,
            "seasons": re.sub(r"\s*\(.*?\)", "", re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", seasons_txt)).strip()}
    return page(title, body, 1, f"{title}, {area}, Elyos Racing Team", current="members"), info


def doc_page(text: str, current: str = "", kicker: str = "", dwg: str = "DOC", no: int = 1) -> str:
    title, f, rest = split_page(text)
    meta = "".join(f"<div><dt>{esc(k)}</dt><dd>{inline_md(v)}</dd></div>" for k, v in f.items())
    aside = f'<aside class="doc-aside" aria-label="Summary"><dl class="facts facts--stack">{meta}</dl></aside>' if meta else ""
    inner = f'<div class="doc-grid{" doc-grid--aside" if meta else ""}"><div class="doc-body">{md_to_html(rest)}</div>{aside}</div>'
    body = f'<div class="sheet-page">{sheet("doc", no, dwg, kicker, title, inner, h="h1")}</div>'
    return page(title, body, 1, current=current)


def project_page(key: str, text: str, data: dict) -> str:
    """Engineering page: one sheet with the lede, the hand-drawn diagram, the spec table and the details."""
    title, _, rest = split_page(text)
    rest = rest.lstrip("\n")
    m = re.match(r"([^\n|#][^\n]*)\n", rest)
    lede = ""
    if m:
        lede, rest = m.group(1), rest[m.end():]
    p = data["projects"].get(key, {})
    fig, ftitle = FIGS.get(key, (0, title))
    keys = list(data["projects"])
    i = keys.index(key) if key in keys else -1
    nxt = data["projects"][keys[(i + 1) % len(keys)]] if i >= 0 else None
    pager = (f'<nav class="pager" aria-label="Next area"><a href="{nxt["page"].split("/")[-1].removesuffix(".md")}">'
             f'<span class="k">Next · {esc(nxt.get("discipline", ""))}</span><span class="t">{esc(nxt["name"])} →</span></a></nav>') if nxt else ""
    inner = f'{diagrams.sheet(key, fig, ftitle)}<div class="doc-body">{md_to_html(rest)}</div>'
    body = (f'<div class="sheet-page">{sheet("doc", max(fig, 1), "ENG", p.get("discipline", "Engineering"), title, inner, h="h1", lede=inline_md(lede) if lede else "")}'
            f'<div class="block">{pager}</div></div>')
    cur = "adc" if key == "adc" else "engineering"
    return page(title, body, 1, lede and re.sub(r"<[^>]+>", "", inline_md(lede)), current=cur)


def engineering_index(data: dict) -> str:
    inner = project_cards(data, list(data["projects"]), "../")
    body = f'<div class="sheet-page">{sheet("doc", 0, "ENG", "Engineering", "Everything on the car, designed by students.", inner, h="h1", note="six areas, one car", lede="Each page explains what we built, how it works and what we measured, with a hand-drawn diagram; the design files and the code stay private.")}</div>'
    return page("Engineering", body, 1, "Mechanics, electronics, embedded control, telemetry, energy strategy and autonomy "
                "of the Elyos Racing Team prototype.", current="engineering")


# ------------------------------------------------------------------ README sync

def readme_table(data: dict) -> str:
    rows = ["| Season | Event | Result |", "|---|---|---|"]
    for r in data["results"]:
        res = f"**{r['result'].split(',')[0]}**" + (r["result"][len(r["result"].split(",")[0]):])
        if r.get("km_per_kwh"):
            res += f" · {r['km_per_kwh']} km/kWh"
        rows.append(f"| [{r['year']}]({r['page']}) | {r['event']} | {res} |")
    return "\n".join(rows)


def sync_readme(data: dict, write: bool) -> bool:
    path = ROOT / "README.md"
    text = path.read_text(encoding="utf-8")
    block = f"{README_START}\n{readme_table(data)}\n{README_END}"
    if README_START in text:
        new = re.sub(re.escape(README_START) + r".*?" + re.escape(README_END), block, text, flags=re.S)
    else:  # first time: replace the table under "## Results"
        new = re.sub(r"(## Results\n\n)(\|.*?\n)(?=\n)", lambda m: m.group(1) + block + "\n", text, count=1, flags=re.S)
    if write and new != text:
        path.write_text(new, encoding="utf-8")
    return new == text


# ------------------------------------------------------------------ build

def build() -> None:
    data = yaml.safe_load((SITE / "data.yaml").read_text(encoding="utf-8"))
    tracks = json.loads((SITE / "tracks.json").read_text(encoding="utf-8"))
    OUT.mkdir(exist_ok=True)
    for child in OUT.iterdir():  # empty it in place (a local preview server may hold the folder open)
        shutil.rmtree(child) if child.is_dir() else child.unlink()
    for f in ("style.css", "site.js", "car3d.js"):
        shutil.copy(SITE / f, OUT / f)
    shutil.copytree(SITE / "assets", OUT / "assets")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")

    members = []
    (OUT / "members").mkdir()
    for n, md in enumerate(sorted(p for p in (ROOT / "members").glob("*.md") if p.stem not in ("README", "TEMPLATE")), 1):
        html_page, info = member_page(md.stem, md.read_text(encoding="utf-8"), data, n)
        (OUT / "members" / f"{md.stem}.html").write_text(html_page, encoding="utf-8")
        members.append(info)
    crew = sheet("doc", 1, "TEAM", "Crew", "Members", members_list(members, "../") +
                 f'<p class="note">Each member publishes their own page with a pull request from the <a href="{REPO}/blob/main/members/TEMPLATE.md">template</a>; that pull request is their consent to make it public.</p>',
                 h="h1", note="one pull request each")
    (OUT / "members" / "index.html").write_text(page("Members", f'<div class="sheet-page">{crew}</div>', 1, current="members"), encoding="utf-8")

    (OUT / "seasons").mkdir()
    for md in sorted((ROOT / "seasons").glob("*.md")):
        (OUT / "seasons" / f"{md.stem}.html").write_text(
            doc_page(md.read_text(encoding="utf-8"), "mileage", f"Season {md.stem} · logbook", "SEA", int(md.stem) % 100), encoding="utf-8")
    (OUT / "projects").mkdir()
    for md in sorted((ROOT / "projects").glob("*.md")):
        (OUT / "projects" / f"{md.stem}.html").write_text(
            project_page(md.stem, md.read_text(encoding="utf-8"), data), encoding="utf-8")
    (OUT / "projects" / "index.html").write_text(engineering_index(data), encoding="utf-8")

    for key in data["programs"]:
        (OUT / f"{key}.html").write_text(program_page(key, data, tracks), encoding="utf-8")
    (OUT / "index.html").write_text(index(data, tracks, members), encoding="utf-8")
    lost = sheet("doc", 404 % 100, "ERR", "404", "Off track.",
                 '<p class="lede">This page does not exist. Head back to the <a href="/team-portfolio/">start line</a>.</p>', h="h1",
                 note="wrong turn")
    (OUT / "404.html").write_text(page("Off track", f'<div class="sheet-page">{lost}</div>', 0), encoding="utf-8")
    print(f"built {OUT}")


def serve(port: int) -> None:
    """Preview _site/ the way GitHub Pages serves it: /x falls back to x.html, /dir/ to dir/index.html."""
    import functools
    import http.server

    class Handler(http.server.SimpleHTTPRequestHandler):
        def translate_path(self, path: str) -> str:
            local = Path(super().translate_path(path))
            if not local.exists() and not local.suffix and local.with_suffix(".html").exists():
                return str(local.with_suffix(".html"))
            return str(local)

    print(f"serving {OUT} on http://localhost:{port}/")
    http.server.ThreadingHTTPServer(("", port), functools.partial(Handler, directory=str(OUT))).serve_forever()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write-readme", action="store_true")
    ap.add_argument("--check-readme", action="store_true")
    ap.add_argument("--serve", type=int, nargs="?", const=8000, metavar="PORT",
                    help="build, then preview with clean URLs like GitHub Pages")
    a = ap.parse_args()
    data = yaml.safe_load((SITE / "data.yaml").read_text(encoding="utf-8"))
    if a.write_readme:
        sync_readme(data, write=True)
        print("README.md results table updated")
        return
    if a.check_readme:
        if not sync_readme(data, write=False):
            sys.exit("README.md results table differs from site/data.yaml: run python site/build.py --write-readme")
        print("README.md in sync")
        return
    build()
    if a.serve:
        serve(a.serve)


if __name__ == "__main__":
    main()
