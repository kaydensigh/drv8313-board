#!/usr/bin/env python3
"""Schematic READABILITY lint -- a numeric oracle for visual quality.

ERC/netlist checks prove a schematic is electrically right; they say nothing
about whether a human can read it. This lint scores the visual defects agents
introduce when editing schematics blind: overlapping value/reference text,
text printed through symbol bodies or across wires, wire crossings, stacked
symbols, and off-grid endpoints. Iterate edits against this score the same way
copper edits iterate against DRC, and confirm the result with render_sch.py.

All geometry is HEURISTIC (text boxes are estimated from character counts, and
symbol bodies from pin extents) -- treat findings as pointers to look at in a
render, and the totals as a score to drive down, not as ground truth.

Run with KiCad's bundled Python (needs kicad-skip):

    & "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" tools\\sch_lint.py
    ... sch_lint.py --sch path/to/x.kicad_sch --verbose --json
    ... sch_lint.py --fail-over 0        # CI gate: nonzero exit if any issue

Exit codes: 0 ok / within threshold, 1 over --fail-over threshold, 2 tool error.
"""
import argparse
import json
import math
import sys
from pathlib import Path

EXIT_OK, EXIT_GATE, EXIT_ERROR = 0, 1, 2

GRID = 1.27          # KiCad schematic grid (50 mil), mm
EPS = 0.02           # coordinate coincidence tolerance, mm
CHAR_ADVANCE = 0.78  # est. average glyph advance as a fraction of font size
TEXT_HEIGHT = 1.3    # est. text box height as a fraction of font size
MIN_PEN = 0.25       # min penetration (mm) before an overlap is reported
DETAIL_LIMIT = 15    # findings printed per check without --verbose


# --------------------------------------------------------------------------- #
# s-expression helpers (operate on kicad-skip .raw nodes: nested lists whose
# heads are sexpdata Symbols)

def _sym(x):
    return str(x) if not isinstance(x, list) else None


def _find_lists(node, head):
    """Yield sublists of `node` whose first element is Symbol(head)."""
    if isinstance(node, list):
        for child in node:
            if isinstance(child, list) and child and _sym(child[0]) == head:
                yield child


def _find_deep(node, head):
    """Yield lists with Symbol(head) head anywhere under `node`."""
    if isinstance(node, list):
        if node and _sym(node[0]) == head:
            yield node
        for child in node:
            yield from _find_deep(child, head)


def _effects_info(node):
    """(size, justify_h, justify_v, hidden) from any node containing (effects ...)."""
    size, jh, jv, hidden = 1.27, "center", "center", False
    for eff in _find_deep(node, "effects"):
        for font in _find_lists(eff, "font"):
            for sz in _find_lists(font, "size"):
                try:
                    size = float(sz[1])
                except (ValueError, IndexError, TypeError):
                    pass
        for just in _find_lists(eff, "justify"):
            toks = {_sym(t) for t in just[1:]}
            if "left" in toks:
                jh = "left"
            elif "right" in toks:
                jh = "right"
            if "top" in toks:
                jv = "top"
            elif "bottom" in toks:
                jv = "bottom"
    # (hide yes) can sit at the property level OR inside (effects ...)
    for hide in _find_deep(node, "hide"):
        val = _sym(hide[1]) if len(hide) > 1 else "yes"
        if val in ("yes", "true", "True"):
            hidden = True
    return size, jh, jv, hidden


# --------------------------------------------------------------------------- #
# geometry

def text_bbox(x, y, rot, text, size, jh, jv):
    """Estimated (x0, y0, x1, y1) for a text anchored at (x, y).

    Schematic Y grows downward. rot in degrees; 0/180 horizontal, 90/270
    vertical (reads bottom-to-top). Justification places the anchor on the
    named edge of the box.
    """
    w = max(len(text), 1) * size * CHAR_ADVANCE
    h = size * TEXT_HEIGHT
    rot = rot % 180
    if rot < 45:  # horizontal
        x0 = {"left": x, "right": x - w, "center": x - w / 2}[jh]
        y0 = {"top": y, "bottom": y - h, "center": y - h / 2}[jv]
        return (x0, y0, x0 + w, y0 + h)
    # vertical: text runs along -y from the anchor for left-justify
    y1 = {"left": y, "right": y + w, "center": y + w / 2}[jh]
    x0 = {"top": x, "bottom": x - h, "center": x - h / 2}[jv]
    return (x0, y1 - w, x0 + h, y1)


def rect_overlap(a, b):
    """Overlap (min penetration depth) of two rects, or 0 if disjoint."""
    ox = min(a[2], b[2]) - max(a[0], b[0])
    oy = min(a[3], b[3]) - max(a[1], b[1])
    return min(ox, oy) if (ox > 0 and oy > 0) else 0.0


def seg_rect_intersects(p1, p2, r):
    """True if segment p1-p2 passes through rect r (not just touches edge)."""
    (x0, y0, x1, y1) = r
    inside = lambda p: x0 + EPS < p[0] < x1 - EPS and y0 + EPS < p[1] < y1 - EPS
    if inside(p1) or inside(p2):
        return True
    corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    edges = [(corners[i], corners[(i + 1) % 4]) for i in range(4)]
    return any(seg_intersection(p1, p2, a, b) for a, b in edges)


def seg_intersection(p1, p2, p3, p4):
    """Proper-intersection point of segments, or None (excludes touching ends)."""
    d1x, d1y = p2[0] - p1[0], p2[1] - p1[1]
    d2x, d2y = p4[0] - p3[0], p4[1] - p3[1]
    denom = d1x * d2y - d1y * d2x
    if abs(denom) < 1e-9:
        return None  # parallel / collinear
    t = ((p3[0] - p1[0]) * d2y - (p3[1] - p1[1]) * d2x) / denom
    u = ((p3[0] - p1[0]) * d1y - (p3[1] - p1[1]) * d1x) / denom
    lo, hi = 1e-4, 1 - 1e-4  # strictly interior on both segments
    if lo < t < hi and lo < u < hi:
        return (p1[0] + t * d1x, p1[1] + t * d1y)
    return None


def near(a, b, eps=EPS):
    return abs(a[0] - b[0]) < eps and abs(a[1] - b[1]) < eps


def off_grid(v):
    return abs(v / GRID - round(v / GRID)) * GRID > 1e-3


# --------------------------------------------------------------------------- #
# schematic model extraction

def find_sch(explicit):
    if explicit:
        p = Path(explicit)
        return p if p.exists() else None
    hits = [p for p in Path.cwd().rglob("*.kicad_sch")
            if not p.name.startswith("_autosave")
            and not any(part.startswith((".", "_scratch")) or part.endswith("-backups")
                        for part in p.parts)]
    return hits[0] if len(hits) == 1 else None


def extract(sch):
    """Pull texts, symbols, wires, junctions out of a skip.Schematic."""
    texts = []      # {owner, kind, text, x, y, rot, bbox}
    symbols = []    # {ref, lib_id, at, pins:[(num,x,y)], power, body}
    wires = []      # ((x1,y1),(x2,y2))
    junctions = []  # (x,y)

    for s in sch.symbol:
        ref, lib_id = "?", ""
        for li in _find_lists(s.raw, "lib_id"):
            lib_id = li[1]
        props = []
        for p in _find_lists(s.raw, "property"):
            name, value = str(p[1]), str(p[2])
            ats = list(_find_lists(p, "at"))
            if not ats:
                continue
            x, y = float(ats[0][1]), float(ats[0][2])
            rot = float(ats[0][3]) if len(ats[0]) > 3 else 0.0
            size, jh, jv, hidden = _effects_info(p)
            props.append((name, value, x, y, rot, size, jh, jv, hidden))
            if name == "Reference":
                ref = value
        power = ref.startswith("#") or str(lib_id).startswith("power:")
        for (name, value, x, y, rot, size, jh, jv, hidden) in props:
            if hidden or not value.strip():
                continue
            texts.append({"owner": ref, "kind": name, "text": value,
                          "x": x, "y": y,
                          "bbox": text_bbox(x, y, rot, value, size, jh, jv)})
        try:
            at = [float(v) for v in s.at.value[:2]]
        except Exception:
            at = None
        pins = []
        try:
            for pin in s.pin:
                loc = pin.location.value
                pins.append((str(pin.number), float(loc[0]), float(loc[1])))
        except Exception:
            pass
        symbols.append({"ref": ref, "lib_id": str(lib_id), "at": at,
                        "pins": pins, "power": power,
                        "body": body_box(pins, power)})

    for coll, kind in (("global_label", "global_label"), ("label", "label"),
                       ("text", "text")):
        try:
            elems = list(getattr(sch, coll))
        except Exception:
            continue
        for el in elems:
            try:
                value = str(el.value)
                at = el.at.value
                x, y = float(at[0]), float(at[1])
                rot = float(at[2]) if len(at) > 2 else 0.0
            except Exception:
                continue
            size, jh, jv, hidden = _effects_info(el.raw)
            if hidden or not value.strip():
                continue
            # global labels get an outline slightly larger than the text
            pad = size * 0.8 if kind == "global_label" else 0.0
            bb = text_bbox(x, y, rot, value, size, jh, jv)
            bb = (bb[0] - pad, bb[1], bb[2] + pad, bb[3])
            texts.append({"owner": kind, "kind": kind, "text": value,
                          "x": x, "y": y, "bbox": bb})

    for w in sch.wire:
        try:
            a, b = w.start.value, w.end.value
            wires.append(((float(a[0]), float(a[1])), (float(b[0]), float(b[1]))))
        except Exception:
            continue
    try:
        for j in sch.junction:
            junctions.append((float(j.at.value[0]), float(j.at.value[1])))
    except Exception:
        pass
    return texts, symbols, wires, junctions


def body_box(pins, power):
    """Approximate symbol body rect from pin endpoints. None if unknowable."""
    if power or len(pins) < 2:
        return None
    xs = [p[1] for p in pins]
    ys = [p[2] for p in pins]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    if len(pins) == 2:
        # passive: body is the middle ~50% of the pin-to-pin span, ~2 mm wide
        if x1 - x0 >= y1 - y0:  # horizontal part
            span = x1 - x0
            return (x0 + 0.25 * span, (y0 + y1) / 2 - 1.0,
                    x1 - 0.25 * span, (y0 + y1) / 2 + 1.0)
        span = y1 - y0
        return ((x0 + x1) / 2 - 1.0, y0 + 0.25 * span,
                (x0 + x1) / 2 + 1.0, y1 - 0.25 * span)
    # multi-pin: pins stick out of the body; shrink the pin bbox by one pin length
    box = (x0 + 2.54, y0 + 2.54, x1 - 2.54, y1 - 2.54)
    return box if (box[2] - box[0] > 0.5 and box[3] - box[1] > 0.5) else None


# --------------------------------------------------------------------------- #
# checks

def run_checks(texts, symbols, wires, junctions):
    f = {"text-overlap": [], "text-over-body": [], "text-over-wire": [],
         "wire-crossing": [], "off-grid": [], "stacked-symbols": [],
         "power-on-pin": []}

    def t_id(t):
        return f"{t['owner']}.{t['kind']} \"{t['text']}\" @({t['x']:.1f},{t['y']:.1f})"

    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            pen = rect_overlap(texts[i]["bbox"], texts[j]["bbox"])
            if pen > MIN_PEN:
                f["text-overlap"].append(f"{t_id(texts[i])} <-> {t_id(texts[j])}")

    bodies = [(s["ref"], s["body"]) for s in symbols if s["body"]]
    for t in texts:
        for ref, box in bodies:
            if rect_overlap(t["bbox"], box) > MIN_PEN:
                f["text-over-body"].append(f"{t_id(t)} over {ref} body")
        for (a, b) in wires:
            if seg_rect_intersects(a, b, t["bbox"]):
                f["text-over-wire"].append(
                    f"{t_id(t)} over wire ({a[0]:.1f},{a[1]:.1f})-({b[0]:.1f},{b[1]:.1f})")
                break  # one report per text is enough

    for i in range(len(wires)):
        for j in range(i + 1, len(wires)):
            a1, a2 = wires[i]
            b1, b2 = wires[j]
            if any(near(p, q) for p in (a1, a2) for q in (b1, b2)):
                continue
            pt = seg_intersection(a1, a2, b1, b2)
            if pt and not any(near(pt, jn) for jn in junctions):
                f["wire-crossing"].append(f"at ({pt[0]:.2f},{pt[1]:.2f})")

    for (a, b) in wires:
        for p in (a, b):
            if off_grid(p[0]) or off_grid(p[1]):
                f["off-grid"].append(f"wire endpoint ({p[0]},{p[1]})")
    for jn in junctions:
        if off_grid(jn[0]) or off_grid(jn[1]):
            f["off-grid"].append(f"junction ({jn[0]},{jn[1]})")

    placed = [s for s in symbols if not s["power"] and s["at"]]
    for i in range(len(placed)):
        for j in range(i + 1, len(placed)):
            a, b = placed[i]["at"], placed[j]["at"]
            if math.hypot(a[0] - b[0], a[1] - b[1]) < 2.0:
                f["stacked-symbols"].append(
                    f"{placed[i]['ref']} and {placed[j]['ref']} anchors within 2 mm "
                    f"@({a[0]:.1f},{a[1]:.1f})")

    # informational: power symbol pin sitting directly on a component pin with
    # no wire -- electrically fine, but the connector/part LOOKS unconnected
    wire_ends = [p for w in wires for p in w]
    comp_pins = [(s["ref"], n, x, y) for s in symbols if not s["power"]
                 for (n, x, y) in s["pins"]]
    for s in symbols:
        if not s["power"] or not s["pins"]:
            continue
        px, py = s["pins"][0][1], s["pins"][0][2]
        if any(near((px, py), e) for e in wire_ends):
            continue
        for (ref, n, x, y) in comp_pins:
            if near((px, py), (x, y)):
                f["power-on-pin"].append(
                    f"{s['ref']} ({s['lib_id']}) directly on {ref} pin {n} "
                    f"@({px:.1f},{py:.1f}) -- consider a short stub wire")
                break
    return f


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--sch", default=None, help="path to the .kicad_sch (default: auto-discover)")
    ap.add_argument("--verbose", action="store_true", help="print every finding")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--fail-over", type=int, default=None, metavar="N",
                    help="exit 1 if counted issues exceed N (info items not counted)")
    args = ap.parse_args()

    try:
        import skip
    except ImportError:
        print("ERROR: kicad-skip not available -- run with KiCad's bundled Python\n"
              '  & "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" tools\\sch_lint.py',
              file=sys.stderr)
        return EXIT_ERROR

    sch_path = find_sch(args.sch)
    if not sch_path:
        print("ERROR: no unique .kicad_sch found (pass --sch)", file=sys.stderr)
        return EXIT_ERROR

    texts, symbols, wires, junctions = extract(skip.Schematic(str(sch_path)))
    findings = run_checks(texts, symbols, wires, junctions)

    info_checks = {"power-on-pin"}
    total = sum(len(v) for k, v in findings.items() if k not in info_checks)

    if args.json:
        print(json.dumps({"schematic": str(sch_path), "total_issues": total,
                          "findings": findings}, indent=2))
    else:
        print(f"Schematic readability lint: {sch_path}")
        print(f"  {len(symbols)} symbols, {len(wires)} wires, "
              f"{len(junctions)} junctions, {len(texts)} visible texts\n")
        for check, items in findings.items():
            tag = "info" if check in info_checks else "issue"
            print(f"[{check}] {len(items)} {tag}{'s' if len(items) != 1 else ''}")
            shown = items if args.verbose else items[:DETAIL_LIMIT]
            for line in shown:
                print(f"  {line}")
            if len(items) > len(shown):
                print(f"  ... {len(items) - len(shown)} more (--verbose)")
        print(f"\nTOTAL issues: {total} (heuristic -- confirm in a render_sch.py image)")

    if args.fail_over is not None and total > args.fail_over:
        return EXIT_GATE
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
