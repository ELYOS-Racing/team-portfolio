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

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
OUT = ROOT / "_site"
REPO = "https://github.com/ELYOS-Racing/team-portfolio"
BASE_URL = "https://elyos-racing.github.io/team-portfolio/"
FONTS = "https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,300..900&display=swap"
THREE = "https://unpkg.com/three@0.170.0"
IMPORTMAP = (f'<script type="importmap">{{"imports":{{"three":"{THREE}/build/three.module.js",'
             f'"three/addons/":"{THREE}/examples/jsm/"}}}}</script>')
README_START, README_END = "<!-- results:start -->", "<!-- results:end -->"

esc = html.escape


# ------------------------------------------------------------------ layout

def page(title: str, body: str, depth: int, description: str = "", current: str = "", hero3d: bool = False) -> str:
    up = "../" * depth
    full_title = f"{title} | Elyos Racing Team" if title else "Elyos Racing Team"
    desc = esc(description or "Elyos Racing Team: ultra-efficient electric prototypes for the Shell Eco-marathon, "
               "Tecnológico de Monterrey, Guadalajara campus.")
    def nav(href: str, label: str, key: str) -> str:
        cur = ' aria-current="page"' if key == current else ""
        return f'<a href="{up}{href}"{cur}>{label}</a>'
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
<meta name="color-scheme" content="light">
<link rel="icon" href="{up}assets/favicon-32.png" sizes="32x32">
<link rel="apple-touch-icon" href="{up}assets/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
<link rel="stylesheet" href="{up}style.css">
<script>document.documentElement.classList.add("js")</script>
{IMPORTMAP if hero3d else ""}
</head>
<body>
<a class="skip" href="#content">Skip to content</a>
<header class="bar">
<a class="brand" href="{up}index.html"><img src="{up}assets/logo-on-dark.png" alt="Elyos Racing Team" width="132" height="44"></a>
<nav aria-label="Main">{nav("mileage.html", "Mileage", "mileage")}{nav("adc.html", "Autonomous", "adc")}{nav("members/index.html", "Members", "members")}</nav>
</header>
<main id="content" tabindex="-1">
{body}
</main>
<footer>
<p>Content © 2026 Luis Xavier García Pimentel Ascencio and Elyos Racing Team, <a href="{REPO}/blob/main/LICENSE.md">PolyForm Strict 1.0.0</a>. Member pages belong to each member. <a href="{REPO}">Source on GitHub</a>.</p>
</footer>
<script src="{up}site.js" defer></script>
{f'<script type="module" src="{up}hero3d.js"></script>' if hero3d else ""}
</body>
</html>
"""


# ------------------------------------------------------------------ pieces

def md_to_html(text: str) -> str:
    out = markdown.markdown(text, extensions=["tables", "sane_lists"])
    out = re.sub(r"<thead>\s*<tr>\s*<th>Field</th>\s*<th>Value</th>\s*</tr>\s*</thead>", "", out)
    out = re.sub(r'href="(?!https?://)([^"#]+)\.md(#[^"]*)?"', lambda m: f'href="{m.group(1)}.html{m.group(2) or ""}"', out)
    out = out.replace('href="../LICENSE.html"', f'href="{REPO}/blob/main/LICENSE.md"')
    out = out.replace('href="TEMPLATE.html"', f'href="{REPO}/blob/main/members/TEMPLATE.md"')
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


def track_svg(tracks: dict, key: str, label: str, cls: str = "") -> str:
    t = tracks[key]
    sx, sy = t["start"]
    nx, ny = t["next"]
    ang = math.degrees(math.atan2(ny - sy, nx - sx))
    flag_x, flag_y, start_dot = sx, sy, ""
    if not t["closed"]:  # open course (ADC): white dot at the start, checkered line at the finish
        flag_x, flag_y = t["end"]
        start_dot = f'<circle class="finish" cx="{sx}" cy="{sy}" r="9"/>'
    return f"""<svg class="track {cls}" viewBox="{t['viewBox']}" role="img" aria-label="{esc(label)}">
<path class="lap" d="{t['d']}" pathLength="1000"/>
<g class="startline" transform="translate({flag_x} {flag_y}) rotate({ang + 90:.1f})"><rect x="-16" y="-5" width="8" height="5"/><rect x="-8" y="0" width="8" height="5"/><rect x="0" y="-5" width="8" height="5"/><rect x="8" y="0" width="8" height="5"/><rect class="w" x="-16" y="0" width="8" height="5"/><rect class="w" x="-8" y="-5" width="8" height="5"/><rect class="w" x="0" y="0" width="8" height="5"/><rect class="w" x="8" y="-5" width="8" height="5"/></g>
{start_dot}</svg>"""


def hero3d(tracks: dict, key: str, copy_html: str, label: str, alt: str) -> str:
    """Sticky 3D stage; until WebGL is ready (or without it) the static course outline shows instead."""
    return f"""<section class="hero3d" data-hero3d data-track="{key}" data-base="" aria-labelledby="hero-title">
<div class="stage">
<canvas aria-hidden="true"></canvas>
<div class="fallback">{track_svg(tracks, key, label, "hero-track")}</div>
<div class="overlay">{copy_html}<p class="readout" aria-hidden="true"></p></div>
<button class="motion-toggle" type="button" aria-pressed="false">Pause motion</button>
<p class="sr-only">{esc(alt)}</p>
</div>
</section>"""


def results_list(data: dict, up: str = "") -> str:
    best = max(r.get("km_per_kwh", 0) for r in data["results"])
    rows = []
    for r in data["results"]:
        k = r.get("km_per_kwh")
        bar = (f'<div class="eff"><span class="fill" style="--w:{100 * k / best:.1f}%"></span>'
               f'<span class="val">{k} km/kWh</span></div>') if k else ""
        rows.append(f'<li><a class="year" href="{up}{r["page"].replace(".md", ".html")}">{r["year"]}</a>'
                    f'<div><p class="event">{esc(r["event"])}</p><p class="result">{esc(r["result"])}</p>{bar}</div></li>')
    return f'<ol class="results">{"".join(rows)}</ol>'


def project_list(data: dict, keys: list[str], up: str = "") -> str:
    items = "".join(f'<li><h3><a href="{up}{data["projects"][k]["page"].replace(".md", ".html")}">'
                    f'{esc(data["projects"][k]["name"])}</a></h3><p>{esc(data["projects"][k]["summary"])}</p></li>'
                    for k in keys)
    return f'<ul class="projects">{items}</ul>'


def facts(p: dict) -> str:
    rows = "".join(f"<div><dt>{esc(a)}</dt><dd>{esc(b)}</dd></div>" for a, b in p["facts"])
    return f'<dl class="facts">{rows}</dl><p class="fine">{esc(p["facts_source"])}</p>'


def members_list(members: list[dict], up: str = "") -> str:
    if not members:
        return '<p class="note">No member pages yet.</p>'
    items = "".join(f'<li><a href="{up}members/{m["slug"]}.html">{esc(m["name"])}</a>'
                    f'<span class="area">{esc(m["area"])}</span></li>' for m in members)
    return f'<ul class="members">{items}</ul>'


# ------------------------------------------------------------------ pages

def index(data: dict, tracks: dict, members: list[dict]) -> str:
    h = data["hero"]
    laps = h["km_per_kwh"] / h["lap_km"]
    progs = data["programs"]
    split = "".join(f"""<a class="program" href="{key}.html">
{track_svg(tracks, p['track'], f"{p['circuit']} course outline", "small")}
<h3>{esc(p['name'])}</h3><p class="circuit">{esc(p['circuit'])}</p><p>{esc(p['summary'])}</p></a>"""
                    for key, p in progs.items())
    copy = (f'<h1 id="hero-title">One kilowatt-hour, {laps:.0f} laps.</h1>'
            f'<p class="lede">{h["km_per_kwh"]} km on the energy of a single kilowatt-hour: {laps:.0f} laps of '
            f'Indianapolis Motor Speedway, {esc(h["event"])}.</p>')
    body = f"""{hero3d(tracks, progs['mileage']['track'], copy,
                     "Outline of the Mileage Challenge course at Indianapolis Motor Speedway",
                     "Animation: a 3D model of our 2026 car, shown in x-ray so the chassis, steering and wheels are "
                     "visible, parked on the start line at Indianapolis Motor Speedway. The camera turns around the car "
                     "and then follows it lap after lap. Use the Pause motion button to stop it.")}
<section class="intro"><p>{esc(data['tagline'])}</p></section>
<section class="split" aria-label="Competitions">{split}</section>
<section id="results"><h2>Results</h2>{results_list(data)}
<p class="note">Best official attempt of each event. Tracks differ between events, so compare within the same circuit.</p></section>
<section id="members"><h2>Members</h2>{members_list(members)}
<p class="note">Pages are opt-in: each member publishes their own with a pull request from the <a href="{REPO}/blob/main/members/TEMPLATE.md">template</a>.</p></section>
<section class="sources"><h2>Sources</h2><ul>{"".join(f'<li><a href="{s["url"]}">{esc(s["label"])}</a></li>' for s in data["sources"])}</ul></section>"""
    return page("", body, 0, data["tagline"], hero3d=True)


def program_page(key: str, data: dict, tracks: dict) -> str:
    p = data["programs"][key]
    t = tracks[p["track"]]
    extra = ""
    if key == "mileage":
        extra = f'<section id="results"><h2>Results</h2>{results_list(data)}</section>'
    else:
        adc_md = (ROOT / "projects" / "adc.md").read_text(encoding="utf-8")
        _, _, rest = split_page(adc_md)
        # drop the first paragraph of adc.md: it repeats the program summary shown in the hero
        rest = re.sub(r"^[^\n|#][^\n]*\n", "", rest.lstrip("\n"), count=1)
        extra = f'<section class="doc">{md_to_html(rest)}</section>'
    copy = (f'<h1 id="hero-title">{esc(p["name"])}</h1><p class="circuit">{esc(p["circuit"])}</p>'
            f'<p class="lede">{esc(p["summary"])}</p>')
    course = f"{p['circuit']} course outline, {t['length_m']:,.0f} m"
    alt = (f"Animation: a 3D model of our 2026 car, shown in x-ray, on the {p['circuit']} course. The camera turns "
           f"around the car and then follows it to the finish line. Use the Pause motion button to stop it.")
    body = f"""{hero3d(tracks, p['track'], copy, course, alt)}
<section class="facts-band"><h2 class="sr-only">Key facts</h2>{facts(p)}</section>
<section><h2>What we build</h2>{project_list(data, p['projects'])}</section>
{extra}
<p class="fine">Course outline from the official coordinates of the Shell Eco-marathon Data and Telemetry Portal.</p>"""
    return page(p["name"], body, 0, p["summary"], current=key, hero3d=True)


def member_page(slug: str, text: str) -> tuple[str, dict]:
    title, f, rest = split_page(text)
    gh = re.search(r"\[([^\]]+)\]\((https://github\.com/[^)]+)\)", f.get("GitHub", ""))
    meta = [f'<div><dt>Area</dt><dd>{inline_md(f.get("Area", ""))}</dd></div>' if f.get("Area") else "",
            f'<div><dt>Seasons</dt><dd>{inline_md(f.get("Seasons on the team", ""))}</dd></div>'
            if f.get("Seasons on the team") else "",
            f'<div><dt>GitHub</dt><dd><a href="{gh.group(2)}">{esc(gh.group(1))}</a></dd></div>' if gh else "",
            f'<div><dt>LinkedIn</dt><dd>{inline_md(f["LinkedIn"])}</dd></div>'
            if f.get("LinkedIn") and "optional" not in f["LinkedIn"] else "",
            f'<div><dt>Degree</dt><dd>{inline_md(f["Degree"])}</dd></div>' if f.get("Degree") else ""]
    body = f"""<article class="doc person">
<header><h1>{esc(title)}</h1><dl class="facts">{"".join(meta)}</dl></header>
{md_to_html(rest)}
</article>"""
    info = {"slug": slug, "name": title, "area": re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", f.get("Area", ""))}
    return page(title, body, 1, f"{title}, {info['area']}, Elyos Racing Team", current="members"), info


def doc_page(text: str, current: str = "") -> str:
    title, f, rest = split_page(text)
    meta = "".join(f"<div><dt>{esc(k)}</dt><dd>{inline_md(v)}</dd></div>" for k, v in f.items())
    body = f"""<article class="doc">
<header><h1>{esc(title)}</h1>{f'<dl class="facts">{meta}</dl>' if meta else ""}</header>
{md_to_html(rest)}
</article>"""
    return page(title, body, 1, current=current)


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
    for f in ("style.css", "site.js", "hero3d.js", "tracks.json"):
        shutil.copy(SITE / f, OUT / f)
    shutil.copytree(SITE / "assets", OUT / "assets")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")

    members = []
    (OUT / "members").mkdir()
    for md in sorted((ROOT / "members").glob("*.md")):
        if md.stem in ("README", "TEMPLATE"):
            continue
        html_page, info = member_page(md.stem, md.read_text(encoding="utf-8"))
        (OUT / "members" / f"{md.stem}.html").write_text(html_page, encoding="utf-8")
        members.append(info)
    (OUT / "members" / "index.html").write_text(page("Members", f"""<article class="doc"><header><h1>Members</h1></header>
{members_list(members, "../")}
<p class="note">Each member publishes their own page with a pull request from the <a href="{REPO}/blob/main/members/TEMPLATE.md">template</a>; that pull request is their consent to make it public.</p>
</article>""", 1, current="members"), encoding="utf-8")

    for sec, cur in (("seasons", "mileage"), ("projects", "")):
        (OUT / sec).mkdir()
        for md in sorted((ROOT / sec).glob("*.md")):
            key = "adc" if md.stem == "adc" else ("mileage" if sec == "projects" else cur)
            (OUT / sec / f"{md.stem}.html").write_text(doc_page(md.read_text(encoding="utf-8"), key), encoding="utf-8")

    for key in data["programs"]:
        (OUT / f"{key}.html").write_text(program_page(key, data, tracks), encoding="utf-8")
    (OUT / "index.html").write_text(index(data, tracks, members), encoding="utf-8")
    (OUT / "404.html").write_text(page("Off track", """<article class="doc"><header><h1>Off track.</h1></header>
<p>This page does not exist. Head back to the <a href="/team-portfolio/index.html">start line</a>.</p></article>""", 0),
                                  encoding="utf-8")
    print(f"built {OUT}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write-readme", action="store_true")
    ap.add_argument("--check-readme", action="store_true")
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


if __name__ == "__main__":
    main()
