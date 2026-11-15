"""Constrained HTML page -> native scene records (``engine design html-import``).

The host model designs a page in a restricted HTML/CSS subset because browsers give it real grid/flex
layout and real text measurement. This fixed tool renders that page in a headless Chromium browser,
reads the computed geometry with a tool-owned extractor, and compiles it into the ordinary declarative
scene (text, shape, path, table and chart nodes plus content records). Build, render, review and delivery
gates are unchanged: HTML never reaches the PPTX, and task-authored scripts never run.
"""
from __future__ import annotations

import html as html_lib
import json
import os
import re
import shutil
import tempfile
from pathlib import Path

from lxml import html as lxml_html

from .contract import validate, walk
from .runtime import run_process
from .store import DesignError, canonical, digest

MAX_HTML = 2 * 1024 * 1024
EXTRACTOR = Path(__file__).with_name("html_extract.js")
FORBIDDEN_TAGS = {"script", "iframe", "frame", "frameset", "object", "embed", "applet", "link", "img", "picture",
                  "video", "audio", "source", "track", "canvas", "form", "input", "button", "select", "textarea",
                  "base", "portal", "math", "template", "noscript", "foreignobject", "use", "image"}
FORBIDDEN_ATTRS = {"src", "href", "xlink:href", "srcset", "action", "formaction", "poster", "background", "ping"}
FORBIDDEN_CSS = re.compile(r"url\s*\(|@import|@font-face|expression\s*\(|javascript:|behavior\s*:|-moz-binding", re.I)
CJK_HINT = re.compile(r"CJK|SC\b|TC\b|JP\b|KR\b|Han|Hei|Song|Kai|Ming|YaHei|PingFang|Hiragino|微软|雅黑|苹方|黑体|宋体|思源|"
                      r"Noto Sans SC|Noto Serif SC|Source Han|HarmonyOS|MiSans|Alibaba", re.I)
DECOR = re.compile(r"[\s ·•↳→←⇄⟶⚠①②③④⑤⑥⑦⑧⑨⑩▶▸►✓✔✗×|｜]+")
BROWSER_CANDIDATES = (
    "google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome", "msedge", "microsoft-edge",
)
MAC_BROWSERS = ("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "/Applications/Chromium.app/Contents/MacOS/Chromium",
                "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge")


# ---------------------------------------------------------------- policy

def check_policy(text: str):
    """Reject active content and external resources before any browser sees the file."""
    if len(text.encode("utf-8")) > MAX_HTML:
        raise DesignError("HTML_TOO_LARGE")
    if FORBIDDEN_CSS.search(text):
        raise DesignError("HTML_EXTERNAL_OR_ACTIVE_CSS_FORBIDDEN: url(), @import, @font-face and scripts are not allowed")
    try:
        root = lxml_html.document_fromstring(text)
    except Exception as exc:  # lxml raises several parser types
        raise DesignError(f"HTML_PARSE_FAILED: {exc}") from exc
    for el in root.iter():
        if not isinstance(el.tag, str):
            continue
        tag = el.tag.lower().split("}")[-1]
        if tag in FORBIDDEN_TAGS:
            raise DesignError(f"HTML_TAG_FORBIDDEN: <{tag}>")
        if tag == "meta" and el.get("http-equiv"):
            raise DesignError("HTML_META_REFRESH_FORBIDDEN")
        for name, value in el.attrib.items():
            low = name.lower()
            if low.startswith("on") or low in FORBIDDEN_ATTRS or "javascript:" in str(value).lower():
                raise DesignError(f"HTML_ATTRIBUTE_FORBIDDEN: {name}")
    slides = root.xpath('//*[@id="slide"]')
    if len(slides) != 1:
        raise DesignError("HTML_SLIDE_ROOT_REQUIRED: exactly one element with id=\"slide\"")
    return {"status": "passed", "sha256": digest(text.encode("utf-8"))}


# ---------------------------------------------------------------- browser

def find_browser():
    explicit = os.environ.get("PPTSMITH_BROWSER")
    if explicit:
        return explicit if Path(explicit).is_file() else None
    for name in BROWSER_CANDIDATES:
        path = shutil.which(name)
        if path:
            return path
    for path in MAC_BROWSERS:
        if Path(path).is_file():
            return path
    if os.name == "nt":
        for key in ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA"):
            for rel in ("Google/Chrome/Application/chrome.exe", "Microsoft/Edge/Application/msedge.exe"):
                p = Path(os.environ.get(key, "")) / rel
                if os.environ.get(key) and p.is_file():
                    return str(p)
    return None


def _browser_args(browser, profile, width, height):
    args = [browser, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
            "--no-default-browser-check", "--disable-extensions", "--disable-background-networking",
            "--disable-sync", "--disable-component-update", "--mute-audio", "--host-resolver-rules=MAP * ~NOTFOUND",
            f"--user-data-dir={profile}", f"--window-size={int(round(width))},{int(round(height))}"]
    if hasattr(os, "geteuid") and os.geteuid() == 0:
        args.append("--no-sandbox")  # Chromium refuses to start as root otherwise (CI containers).
    return args


def render_layout(text: str, width: float, height: float, *, browser=None, screenshot_scale=1.5, timeout=90):
    """Return (layout dict, preview PNG bytes) for policy-checked HTML."""
    browser = browser or find_browser()
    if not browser:
        raise DesignError("HTML_BROWSER_UNAVAILABLE: install Chrome/Chromium/Edge or set PPTSMITH_BROWSER")
    with tempfile.TemporaryDirectory(prefix="pptsmith-html-") as tmp:
        root = Path(tmp)
        extractor = "pptsmith-extract-" + digest(EXTRACTOR.read_bytes())[:12] + ".js"
        shutil.copyfile(EXTRACTOR, root / extractor)
        tag = f'<script src="{extractor}"></script>'
        page = re.sub(r"</body\s*>", tag + "</body>", text, count=1, flags=re.I) if re.search(r"</body\s*>", text, re.I) else text + tag
        (root / "page.html").write_text(page, encoding="utf-8")
        url = (root / "page.html").as_uri()
        env = {k: v for k, v in os.environ.items() if k in {"PATH", "HOME", "USER", "LANG", "LC_ALL", "SystemRoot",
                                                             "LOCALAPPDATA", "APPDATA", "USERPROFILE", "FONTCONFIG_PATH",
                                                             "FONTCONFIG_FILE", "XDG_DATA_DIRS"}}
        env["TMPDIR"] = str(root)
        dom = run_process(_browser_args(browser, root / "profile", width, height) +
                          ["--virtual-time-budget=8000", "--dump-dom", url], cwd=root, timeout=timeout, env=env)
        shot = root / "preview.png"
        run_process(_browser_args(browser, root / "profile-shot", width, height) +
                    [f"--force-device-scale-factor={screenshot_scale}", "--virtual-time-budget=8000",
                     f"--screenshot={shot}", url], cwd=root, timeout=timeout, env=env)
        png = shot.read_bytes() if shot.is_file() else b""
    m = re.search(r'<pre id="__pptsmith_layout"[^>]*>(.*?)</pre>', dom, re.S)
    if not m:
        raise DesignError("HTML_LAYOUT_EXTRACTION_FAILED: extractor produced no output")
    layout = json.loads(html_lib.unescape(m.group(1)))
    if layout.get("error"):
        raise DesignError("HTML_" + layout["error"])
    if abs(layout["width"] - width) > 0.5 or abs(layout["height"] - height) > 0.5:
        raise DesignError(f"HTML_SLIDE_SIZE_MISMATCH: #slide is {layout['width']:.0f}x{layout['height']:.0f}px, "
                          f"canvas is {width:.0f}x{height:.0f}pt (1 CSS px = 1 pt)")
    return layout, png


# ---------------------------------------------------------------- conversion helpers

def _rgba(value):
    m = re.match(r"rgba?\(([^)]+)\)", value or "")
    if not m:
        return None, 1.0
    parts = [float(x) for x in re.split(r"[,\s/]+", m.group(1).strip()) if x]
    alpha = parts[3] if len(parts) > 3 else 1.0
    return "%02X%02X%02X" % tuple(max(0, min(255, round(v))) for v in parts[:3]), alpha


def _font(run, canvas_min=6):
    color, _ = _rgba(run["color"])
    stack = run["stack"] or ["Arial"]
    family = stack[0]
    spec = {"family": family, "size": max(canvas_min, round(run["size"], 2)), "color": color or "000000",
            "bold": run["weight"] >= 600, "italic": bool(run["italic"])}
    if not CJK_HINT.search(family):
        ea = next((f for f in stack[1:] if CJK_HINT.search(f)), None)
        if ea:
            spec["ea_family"] = ea
    return spec


def _clamp_box(x, y, w, h, cw, ch):
    x, y = max(0.0, x), max(0.0, y)
    w, h = max(0.1, min(w, cw - x)), max(0.1, min(h, ch - y))
    return {"x": round(x, 2), "y": round(y, 2), "width": round(w, 2), "height": round(h, 2)}


def _norm(text):
    return DECOR.sub("", text or "")


PATH_TOKENS = re.compile(r"[MLCQZmlcqzHVhvSsTtAa]|-?\d*\.?\d+(?:e-?\d+)?")


def _parse_path(d, sx, sy):
    tokens = PATH_TOKENS.findall(d or "")
    cmds, i = [], 0
    counts = {"M": 1, "L": 1, "Q": 2, "C": 3, "Z": 0}
    while i < len(tokens):
        op = tokens[i]
        i += 1
        if op not in counts:
            raise DesignError(f"SVG_PATH_COMMAND_UNSUPPORTED: {op} (use absolute M, L, Q, C, Z)")
        n = counts[op] * 2
        vals = [float(v) for v in tokens[i:i + n]]
        if len(vals) != n:
            raise DesignError("SVG_PATH_ARITY_INVALID")
        i += n
        cmds.append((op, [(vals[k] * sx, vals[k + 1] * sy) for k in range(0, n, 2)]))
    if not cmds or cmds[0][0] != "M":
        raise DesignError("SVG_PATH_MUST_START_WITH_M")
    return cmds


# ---------------------------------------------------------------- layout -> scene

def to_scene(layout, page_id, canvas, *, default_source):
    """Compile extractor output into (content items, nodes, background, conversion notes)."""
    cw, ch = canvas["width"], canvas["height"]
    items, nodes, notes = [], [], []
    used = set()
    counter = {"c": 0, "n": 0}

    def cid(preferred=None):
        if preferred:
            if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,79}", preferred) or preferred in used:
                raise DesignError(f"HTML_CONTENT_ID_INVALID_OR_DUPLICATE: {preferred}")
            used.add(preferred)
            return preferred
        while True:
            counter["c"] += 1
            value = f"{page_id}-c{counter['c']:03d}"
            if value not in used:
                used.add(value)
                return value

    def nid():
        counter["n"] += 1
        return f"{page_id}-n{counter['n']:03d}"

    def provenance(item):
        return {"kind": "user", "source": (item.get("src") or default_source)[:500], "checked": False,
                "uncertainties": ["model-authored wording; basis recorded in page-plan.md"] if item.get("authored") else []}

    def shape(box, style, kind="rect"):
        nodes.append({"id": nid(), "page_id": page_id, "type": "shape", "role": "native_shape", "shape": kind,
                      "box": box, "z": len(nodes), "style": style})

    for it in layout["items"]:
        k = it["kind"]
        if k == "box":
            fill, alpha = _rgba(it["fill"]) if it["fill"] else (None, 1.0)
            borders = it["borders"]
            uniform = all(borders) and len({(b["w"], b["c"]) for b in borders}) == 1
            radii = it["radius"]
            radius = radii[0] if len(set(radii)) == 1 else 0
            if len(set(radii)) > 1:
                notes.append({"code": "NONUNIFORM_RADIUS_SQUARED", "at": f"{it['x']:.0f},{it['y']:.0f}"})
            box = _clamp_box(it["x"], it["y"], it["w"], it["h"], cw, ch)
            if fill or uniform:
                style = {"fill": fill}
                if fill and alpha < 0.999:
                    style["fill_alpha"] = round(alpha, 3)
                if uniform:
                    sc, sa = _rgba(borders[0]["c"])
                    style.update(stroke=sc, stroke_width=round(borders[0]["w"], 2))
                    if sa < 0.999:
                        style["stroke_alpha"] = round(sa, 3)
                else:
                    style["stroke"] = None
                if radius > 0.5:
                    style["radius"] = round(radius, 2)
                shape(box, style, "rounded_rect" if radius > 0.5 else "rect")
            if not uniform:
                for side, b in zip("TRBL", borders):
                    if not b:
                        continue
                    x, y, w, h = it["x"], it["y"], it["w"], it["h"]
                    geo = {"T": (x, y, w, b["w"]), "B": (x, y + h - b["w"], w, b["w"]),
                           "L": (x, y, b["w"], h), "R": (x + w - b["w"], y, b["w"], h)}[side]
                    c, a = _rgba(b["c"])
                    st = {"fill": c, "stroke": None}
                    if a < 0.999:
                        st["fill_alpha"] = round(a, 3)
                    shape(_clamp_box(*geo, cw, ch), st)
        elif k == "text":
            runs = it["runs"]
            text = "".join(r["text"] for r in runs)
            base = _font(runs[0])
            spans, offset = [], 0
            for r in runs:
                f = _font(r)
                if f != base:
                    spans.append({"start": offset, "end": offset + len(r["text"]), "font": f})
                offset += len(r["text"])
            fs = max(r["size"] for r in runs)
            lh = it["lineHeight"]
            single = it["lines"] == 1
            if single:
                w = it["w"] + 6
                x = {"left": it["x"] - 1, "center": it["x"] + it["w"] / 2 - w / 2,
                     "right": it["x"] + it["w"] - w + 1}.get(it["align"], it["x"])
            else:
                x, w = it["content"]["x"], it["content"]["w"] + 1
            # Browsers centre glyphs in the CSS line box; Office places extra leading above the glyphs.
            dy = (lh - fs * 1.32) / 2
            content_id = cid(it.get("cid"))
            items.append({"id": content_id, "page_id": page_id, "type": "text", "text": text,
                          "required_edit": "native", "provenance": provenance(it)})
            node = {"id": nid(), "page_id": page_id, "type": "text", "role": "native_text", "content_id": content_id,
                    "box": _clamp_box(x, it["y"] - dy, w, it["h"], cw, ch), "z": len(nodes), "font": base,
                    "align": it["align"] if it["align"] in {"left", "center", "right"} else "left",
                    "valign": "top", "wrap": not single, "line_height": round(lh, 2), "margin": 0}
            if runs[0]["letterSpacing"]:
                node["letter_spacing"] = max(-10, min(20, round(runs[0]["letterSpacing"], 2)))
            if spans:
                node["spans"] = spans
            nodes.append(node)
        elif k == "table":
            rows = it["rows"]
            ncols = max(len(r["cells"]) for r in rows)
            if any(len(r["cells"]) != ncols for r in rows):
                raise DesignError("HTML_TABLE_RAGGED: every row needs the same number of cells (no colspan/rowspan)")
            cells, styles = [], []
            for r in rows:
                cells.append(["".join(x["text"] for x in c["runs"]) for c in r["cells"]])
                row_styles = []
                for c in r["cells"]:
                    f = _font(c["runs"][0] if c["runs"] else {**c["font"]})
                    fill, fa = _rgba(c["fill"]) if c["fill"] else (None, 1.0)
                    st = {"fill": fill, "font": f, "align": c["align"] if c["align"] in {"left", "center", "right"} else "left",
                          "valign": c["valign"], "line_height": round(c["font"]["lineHeight"], 2),
                          "margin": [round(c["pad"][0], 2), round(max(0, c["pad"][1] - 2.5), 2), round(c["pad"][2], 2), round(c["pad"][3], 2)],
                          "border_bottom": None}
                    if fill and fa < 0.999:
                        st["fill_alpha"] = round(fa, 3)
                    if c["borderBottom"]:
                        bc, ba = _rgba(c["borderBottom"]["c"])
                        st["border_bottom"] = {"color": bc, "width": round(c["borderBottom"]["w"], 2), **({"alpha": round(ba, 3)} if ba < 0.999 else {})}
                    row_styles.append(st)
                styles.append(row_styles)
            box = _clamp_box(it["x"], it["y"], it["w"], it["h"], cw, ch)
            widths = [c["w"] for c in rows[0]["cells"]]
            scale = box["width"] / sum(widths)
            widths = [round(w * scale, 3) for w in widths]
            widths[-1] = round(box["width"] - sum(widths[:-1]), 3)
            content_id = cid(it.get("cid"))
            items.append({"id": content_id, "page_id": page_id, "type": "table", "cells": cells,
                          "required_edit": "native", "provenance": provenance(it)})
            first = styles[-1][0]["font"]
            nodes.append({"id": nid(), "page_id": page_id, "type": "table", "role": "native_table", "content_id": content_id,
                          "box": box, "z": len(nodes), "font": first, "fill": "FFFFFF", "header_fill": "FFFFFF",
                          "header_color": first["color"], "column_widths": widths,
                          "row_heights": [round(max(0.1, r["h"]), 2) for r in rows], "cell_styles": styles})
        elif k == "chart":
            spec = it["spec"]
            kind = spec.get("type", "line")
            if kind not in {"line", "column", "bar"}:
                raise DesignError(f"HTML_CHART_TYPE_UNSUPPORTED: {kind}")
            series = spec.get("series") or []
            cats = [str(c) for c in spec.get("categories", [])]
            if not cats or not series or any(len(s.get("values", [])) != len(cats) for s in series):
                raise DesignError("HTML_CHART_DATA_INVALID: categories and equal-length series values are required")
            content_id = cid(it.get("cid"))
            items.append({"id": content_id, "page_id": page_id, "type": "chart", "categories": cats,
                          "series": [{"name": str(s["name"]), "values": [float(v) for v in s["values"]]} for s in series],
                          "data_basis": "user_data", "required_edit": "native", "provenance": provenance(it)})
            axis = {"gridline_color": "EDEFF5", "line_color": "E6E8F0", "label_color": "A0A4B8", "label_size": 8,
                    "category_padding": True, **{k2: spec[k2] for k2 in ("min", "max", "major") if k2 in spec},
                    **spec.get("axis", {})}
            colors = [str(s.get("color", "4B4FD6")).lstrip("#").upper() for s in series]
            node = {"id": nid(), "page_id": page_id, "type": "chart", "role": "native_chart", "content_id": content_id,
                    "box": _clamp_box(it["x"], it["y"], it["w"], it["h"], cw, ch), "z": len(nodes), "chart_type": kind,
                    "font": {"family": spec.get("font", "__page__"), "size": spec.get("font_size", 8.5), "color": axis["label_color"]},
                    "colors": colors, "legend": bool(spec.get("legend", False)), "labels": bool(spec.get("labels", True)),
                    "axis": axis, "label_position": "above" if kind == "line" else "outside_end"}
            if kind == "line":
                node["markers"] = bool(spec.get("markers", True))
                area = [i for i, s in enumerate(series) if s.get("area")]
                if area:
                    node["area_series"] = area
            else:
                node["gap_width"] = int(spec.get("gap_width", 100))
            nodes.append(node)
        elif k == "path":
            cmds = _parse_path(it["d"], it.get("sx", 1), it.get("sy", 1))
            pts = [p for _, ps in cmds for p in ps]
            x0, y0 = min(p[0] for p in pts), min(p[1] for p in pts)
            x1, y1 = max(p[0] for p in pts), max(p[1] for p in pts)
            w, h = max(0.1, x1 - x0), max(0.1, y1 - y0)
            style = {"fill": None, "stroke": None}
            if it["fill"]:
                c, a = _rgba(it["fill"])
                a *= it.get("fillOpacity", 1)
                style["fill"] = c
                if a < 0.999:
                    style["fill_alpha"] = round(a, 3)
            if it["stroke"]:
                c, a = _rgba(it["stroke"])
                a *= it.get("strokeOpacity", 1)
                style.update(stroke=c, stroke_width=round(min(20, it["strokeWidth"]), 2))
                if a < 0.999:
                    style["stroke_alpha"] = round(a, 3)
            commands = [{"op": op, "points": [[round(px - x0, 3), round(py - y0, 3)] for px, py in ps]} for op, ps in cmds]
            nodes.append({"id": nid(), "page_id": page_id, "type": "path", "role": "native_shape",
                          "box": _clamp_box(it["ox"] + x0, it["oy"] + y0, w, h, cw, ch), "z": len(nodes),
                          "commands": commands, "style": style})
    # Charts without an explicit font use the page's dominant Latin/East Asian pair, not a generic face.
    from collections import Counter
    pairs = Counter((n["font"]["family"], n["font"].get("ea_family")) for n in nodes if n["type"] == "text")
    family, ea = pairs.most_common(1)[0][0] if pairs else ("Arial", None)
    for n in nodes:
        if n["type"] == "chart" and n["font"]["family"] == "__page__":
            n["font"]["family"] = family
            if ea:
                n["font"]["ea_family"] = ea
    background, _ = _rgba(layout.get("background")) if layout.get("background") else ("FFFFFF", 1)
    return items, nodes, background or "FFFFFF", notes


# ---------------------------------------------------------------- source checks

def source_segment(text, heading=None):
    """Slice one page of a manuscript: from the line starting with ``heading`` to the next sibling heading."""
    if not heading:
        return text
    lines = text.splitlines()
    start = next((i for i, l in enumerate(lines) if l.strip().startswith(heading)), None)
    if start is None:
        raise DesignError(f"SOURCE_HEADING_NOT_FOUND: {heading}")
    pattern = re.compile("^" + re.sub(r"\d+", r"\\d+", re.escape(heading.strip()).replace(r"\ ", r"\s*")))
    end = next((i for i in range(start + 1, len(lines)) if pattern.match(lines[i].strip())), len(lines))
    return "\n".join(lines[start:end])


def trace(items, source):
    """Mark records that literally occur in the source as checked; list the rest for the author."""
    src = _norm(source)
    numbers = set(re.findall(r"\d+(?:\.\d+)?", source))
    untraced = []
    for c in items:
        prov = c["provenance"]
        if c["type"] == "text":
            ok = _norm(c["text"]) in src
            parts = [] if ok else [c["text"]]
        elif c["type"] == "table":
            parts = [cell for row in c["cells"] for cell in row if cell.strip() and _norm(cell) not in src]
            ok = not parts
        else:
            vals = [f"{v:g}" for s in c["series"] for v in s["values"]]
            parts = [v for v in vals if v not in numbers] + [x for x in c["categories"] if _norm(x) not in src]
            ok = not parts
        if ok:
            prov["checked"] = True
        elif prov["uncertainties"]:  # data-authored: author-declared wording, still listed for review
            prov["checked"] = True
        else:
            untraced.append({"content_id": c["id"], "missing": [p[:80] for p in parts][:6]})
    return untraced


def coverage(source, items):
    """Source -> slide: phrases and numbers of the page segment that do not appear on the slide."""
    shown = []
    for c in items:
        if c["type"] == "text":
            shown.append(c["text"])
        elif c["type"] == "table":
            shown += [x for row in c["cells"] for x in row]
        else:
            shown += c["categories"] + [s["name"] for s in c["series"]] + [f"{v:g}" for s in c["series"] for v in s["values"]]
    joined = _norm("|".join(shown))
    numbers_shown = set(re.findall(r"\d+(?:\.\d+)?", " ".join(shown)))
    phrases, numbers = [], set()
    for line in source.splitlines()[1:]:
        if not line.strip():
            continue
        for cell in line.split("\t"):
            for ph in re.split(r"[；;。\n•]|：(?=.)", cell):
                ph = _norm(ph).strip("：:（）()、，,")
                if len(ph) >= 2 and ph not in joined and ph != "未标注":
                    phrases.append(ph)
        numbers |= set(re.findall(r"\d+(?:\.\d+)?", line))
    missing_numbers = sorted(n for n in numbers if n not in numbers_shown)
    return {"missing_numbers": missing_numbers, "missing_phrases": sorted(set(phrases))[:200],
            "missing_phrase_count": len(set(phrases))}


# ---------------------------------------------------------------- task update

def apply(task, page_id, items, nodes, background):
    import copy
    pages = {p["id"]: p for p in task["scene"]["pages"]}
    if page_id not in pages:
        raise DesignError("UNKNOWN_PAGE")
    other = {c["id"] for c in task["content"]["items"] if c["page_id"] != page_id}
    clash = sorted(c["id"] for c in items if c["id"] in other)
    if clash:
        raise DesignError("HTML_CONTENT_ID_USED_ON_ANOTHER_PAGE: " + ", ".join(clash[:5]))
    other_nodes = {n["id"] for p in task["scene"]["pages"] if p["id"] != page_id for n, *_ in walk(p["nodes"])}
    if any(n["id"] in other_nodes for n in nodes):
        raise DesignError("HTML_NODE_ID_CLASH")
    candidate = copy.deepcopy(task)
    candidate["content"]["items"] = [c for c in candidate["content"]["items"] if c["page_id"] != page_id] + items
    page = next(p for p in candidate["scene"]["pages"] if p["id"] == page_id)
    page["nodes"], page["background"] = nodes, background
    reset = False
    design = next(d for d in candidate["design"]["pages"] if d["page_id"] == page_id)
    comp = design.get("composition")
    ids = {c["id"] for c in items}
    if comp and (any(x not in ids for x in comp["reading_path"]) or comp.get("claim_content_id", next(iter(ids), "")) not in ids):
        design.pop("composition")
        reset = True
    validate(candidate)
    return candidate, reset


def import_html(task, page_id, text, *, default_source, source_text=None, browser=None, assume_checked=False):
    """Policy check -> browser layout -> scene records; returns (candidate task, report, layout, png)."""
    policy = check_policy(text)
    layout, png = render_layout(text, task["canvas"]["width"], task["canvas"]["height"], browser=browser)
    items, nodes, background, notes = to_scene(layout, page_id, task["canvas"], default_source=default_source)
    report = {"status": "imported", "page_id": page_id, "html_sha256": policy["sha256"],
              "content_items": len(items), "nodes": len(nodes),
              "objects": {k: sum(n["type"] == k for n in nodes) for k in ("text", "shape", "path", "table", "chart")},
              "browser_warnings": layout.get("warnings", [])[:50], "conversion_notes": notes[:50]}
    if source_text is not None:
        report["untraced"] = trace(items, source_text)
        report["coverage"] = coverage(source_text, items)
    elif assume_checked:
        for c in items:
            c["provenance"]["checked"] = True
        report["traceability"] = "author_asserted_without_source_file"
    else:
        report["traceability"] = "not_run: pass --source-file, or --assume-checked after checking every record"
    unchecked = [c["id"] for c in items if not c["provenance"]["checked"]]
    report["unchecked_count"] = len(unchecked)
    if unchecked:
        # Unchecked records may not be bound to native objects; keep the task unchanged.
        report["status"] = "untraced_content"
        report["next"] = ("Correct the wording to match the source, or mark deliberate model wording with "
                          "data-authored and record its basis in page-plan.md; then import again.")
        return None, report, layout, png
    candidate, reset = apply(task, page_id, items, nodes, background)
    report["composition_reset"] = reset
    if layout.get("warnings") or (report.get("coverage") or {}).get("missing_numbers"):
        report["status"] = "imported_with_findings"
    return candidate, report, layout, png
