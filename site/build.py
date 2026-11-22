"""Builds the static portfolio site into _site/ from site/data.yaml and the Markdown pages.

    pip install markdown pyyaml
    python site/build.py            # → _site/index.html, seasons/*.html, projects/*.html, members/*.html
"""

from __future__ import annotations

import html
import json
import re
import shutil
from pathlib import Path

import markdown
import yaml

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
OUT = ROOT / "_site"
REPO = "https://github.com/ELYOS-Racing/team-portfolio"
SECTIONS = ("seasons", "projects", "members")

FONTS = "https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,300..900&display=swap"


def page(title: str, body: str, depth: int, description: str = "") -> str:
    up = "../" * depth
    desc = html.escape(description or "Elyos Racing Team, Shell Eco-marathon, Tecnológico de Monterrey")
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{desc}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
<link rel="stylesheet" href="{up}style.css">
</head>
<body>
<header class="bar"><a class="home" href="{up}index.html">Elyos Racing Team</a>
<nav><a href="{up}index.html#results">Results</a><a href="{up}index.html#projects">Projects</a><a href="{up}members/index.html">Members</a></nav></header>
<main>
{body}
</main>
<footer><p>Content © 2026 Luis Xavier García Pimentel Ascencio and Elyos Racing Team, <a href="{REPO}/blob/main/LICENSE.md">PolyForm Strict 1.0.0</a>. Member pages belong to each member. <a href="{REPO}">Source</a>.</p></footer>
</body>
</html>
"""


def md_to_html(text: str) -> str:
    out = markdown.markdown(text, extensions=["tables", "sane_lists"])
    out = re.sub(r"<thead>\s*<tr>\s*<th>Field</th>\s*<th>Value</th>\s*</tr>\s*</thead>", "", out)
    out = re.sub(r'href="(?!https?://)([^"#]+)\.md(#[^"]*)?"', lambda m: f'href="{m.group(1)}.html{m.group(2) or ""}"', out)
    out = out.replace('href="../LICENSE.html"', f'href="{REPO}/blob/main/LICENSE.md"')
    out = out.replace('href="TEMPLATE.html"', f'href="{REPO}/blob/main/members/TEMPLATE.md"')
    return out


def title_of(text: str, fallback: str) -> str:
    m = re.search(r"^# (.+)$", text, re.M)
    return m.group(1).strip() if m else fallback


def field(text: str, name: str) -> str:
    m = re.search(rf"^\| {re.escape(name)} \| (.+?) \|$", text, re.M)
    return re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", m.group(1)).strip() if m else ""


def track_svg(data: dict, laps: float) -> str:
    t = json.loads((SITE / "track.json").read_text(encoding="utf-8"))
    sx, sy = t["start"]
    nx, ny = t["next"]
    lap_m = data["hero"]["lap_km"] * 1000
    return f"""<figure class="track" aria-labelledby="track-caption">
<svg viewBox="{t['viewBox']}" role="img" aria-label="Outline of the Shell Eco-marathon circuit at Indianapolis Motor Speedway">
<path class="lap" d="{t['d']}" pathLength="1000"/>
<line class="startline" x1="{sx}" y1="{sy - 14}" x2="{sx}" y2="{sy + 14}"/>
<path class="arrow" d="M{nx - 30},{ny} l14,-7 v14 z"/>
</svg>
<figcaption id="track-caption">The {lap_m:,.0f} m lap at Indianapolis Motor Speedway, raced to the left from the red start line.</figcaption>
</figure>"""


def index(data: dict, members: list[tuple[str, str, str]]) -> str:
    h = data["hero"]
    laps = h["km_per_kwh"] / h["lap_km"]
    best = max(r.get("km_per_kwh", 0) for r in data["results"])
    rows = []
    for r in data["results"]:
        k = r.get("km_per_kwh")
        bar = (f'<span class="eff"><span class="fill" style="--w:{100 * k / best:.1f}%"></span>'
               f'<span class="val">{k} km/kWh</span></span>') if k else '<span class="eff none"></span>'
        link = r["page"].replace(".md", ".html")
        rows.append(f'<li><a class="year" href="{link}">{r["year"]}</a><div class="what"><p class="event">{html.escape(r["event"])}</p>'
                    f'<p class="result">{html.escape(r["result"])}</p>{bar}</div></li>')
    projects = "".join(f'<li><h3><a href="{p["page"].replace(".md", ".html")}">{html.escape(p["name"])}</a></h3>'
                       f'<p>{html.escape(p["summary"])}</p></li>' for p in data["projects"])
    mem = "".join(f'<li><a href="members/{slug}.html">{html.escape(name)}</a> <span class="area">{html.escape(area)}</span></li>'
                  for slug, name, area in members) or "<li>No member pages yet.</li>"
    sources = "".join(f'<li><a href="{s["url"]}">{html.escape(s["label"])}</a></li>' for s in data["sources"])
    body = f"""<section class="hero">
<h1>One kilowatt-hour, {laps:.0f} laps.</h1>
<p class="lede">That is how far our 2026 prototype would go on the energy of a single kilowatt-hour: {h['km_per_kwh']} km, or {laps:.0f} laps of the circuit below, at {html.escape(h['event'])}.</p>
{track_svg(data, laps)}
<p class="who">{html.escape(data['tagline'])}</p>
</section>
<section id="results">
<h2>Results</h2>
<ol class="results">{''.join(rows)}</ol>
<p class="note">Efficiency is the best official attempt of each event, in kilometres per kilowatt-hour. Tracks differ between events, so compare within the same circuit.</p>
</section>
<section id="projects">
<h2>Projects</h2>
<ul class="projects">{projects}</ul>
<p class="note">The vehicles' code is private. Members' contributions show on their GitHub profiles as private contributions; their pages here explain what is behind them.</p>
</section>
<section id="members">
<h2>Members</h2>
<ul class="members">{mem}</ul>
<p class="note">Pages are opt-in: each member publishes their own with a pull request from the <a href="{REPO}/blob/main/members/TEMPLATE.md">template</a>.</p>
</section>
<section class="sources"><h2>Sources</h2><ul>{sources}</ul></section>"""
    return page(f"{data['team']} · Shell Eco-marathon", body, 0, data["tagline"])


def build() -> None:
    data = yaml.safe_load((SITE / "data.yaml").read_text(encoding="utf-8"))
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copy(SITE / "style.css", OUT / "style.css")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    members = []
    for sec in SECTIONS:
        (OUT / sec).mkdir()
        for md in sorted((ROOT / sec).glob("*.md")):
            if md.stem in ("README", "TEMPLATE"):
                continue
            text = md.read_text(encoding="utf-8")
            title = title_of(text, md.stem)
            (OUT / sec / f"{md.stem}.html").write_text(
                page(f"{title} · Elyos Racing Team", f'<article class="doc">{md_to_html(text)}</article>', 1),
                encoding="utf-8")
            if sec == "members":
                members.append((md.stem, title, field(text, "Area")))
    mem_list = "".join(f'<li><a href="{s}.html">{html.escape(n)}</a> <span class="area">{html.escape(a)}</span></li>'
                       for s, n, a in members) or "<li>No member pages yet.</li>"
    (OUT / "members" / "index.html").write_text(page("Members · Elyos Racing Team", f"""<article class="doc">
<h1>Members</h1><ul class="members">{mem_list}</ul>
<p class="note">Each member publishes their own page with a pull request from the <a href="{REPO}/blob/main/members/TEMPLATE.md">template</a>; that pull request is their consent to make it public.</p>
</article>""", 1), encoding="utf-8")
    (OUT / "index.html").write_text(index(data, members), encoding="utf-8")
    print(f"built {OUT}")


if __name__ == "__main__":
    build()
