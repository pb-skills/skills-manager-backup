"""VML - Visual Memory Language renderer (18 symbols).

Validated in C:/ai/memories/dreams/experiments/EXP-vml/run-20261124-01/report.md:
79/79 edges and every node kind/status read back correctly from rendered images.

  6 node kinds  (shape + tint): fact, action, decision, tool, issue, outcome
  7 relations   (line + head + colour): causes, fixes, requires, part_of, supersedes, contradicts, evidence_for
  5 status badges: verified, hypothesis, rejected, pending, risk
  + thick green outline marks a step of the verified correct way
Capsule: the exact spec as JSON in a PNG iTXt chunk (keyword 'vml-capsule', zlib).
The capsule is a convenience copy only; the Markdown file is the source of truth.
"""
import hashlib, json, math, struct, textwrap, zlib
from PIL import Image, ImageDraw, ImageFont

KINDS = {  # kind: (shape, fill)
    "fact":     ("rect",    "#f1f5f9"),
    "action":   ("pill",    "#dcfce7"),
    "decision": ("diamond", "#fef9c3"),
    "tool":     ("hexagon", "#e0e7ff"),
    "issue":    ("octagon", "#fee2e2"),
    "outcome":  ("ellipse", "#f3e8ff"),
}
RELS = {  # rel: (colour, style, head)
    "causes":       ("#1f2937", "solid",  "triangle"),
    "fixes":        ("#15803d", "solid",  "tee"),
    "requires":     ("#1d4ed8", "dotted", "open"),
    "part_of":      ("#6b7280", "solid",  "diamond"),
    "supersedes":   ("#7c3aed", "double", "triangle"),
    "contradicts":  ("#dc2626", "dashed", "cross"),
    "evidence_for": ("#d97706", "dashed", "dot"),
}
STATUS = {  # status: (colour, glyph); "pending" is drawn as three dots (the U+2026 glyph was unreadable)
    "verified":   ("#16a34a", "\u2713"),
    "hypothesis": ("#ca8a04", "?"),
    "rejected":   ("#dc2626", "\u2717"),
    "pending":    ("#6b7280", None),
    "risk":       ("#ea580c", "!"),
}
COLOUR_NAMES = {"#1f2937": "black", "#15803d": "green", "#1d4ed8": "blue", "#6b7280": "grey",
                "#7c3aed": "purple", "#dc2626": "red", "#d97706": "orange"}
WAY_COLOUR = "#15803d"  # thick green outline = step of the verified correct way
THEME = {"ink": "#111827", "text": "#111827", "ring": "white", "way": WAY_COLOUR}
# Cyber look: same hues as the plain legend so colour cues survive; only "causes" goes black -> white.
CYBER_THEME = {"ink": "#e6f1ff", "text": "#f5faff", "ring": "#0b0618", "way": "#39ff88"}
CYBER_FILL = {"fact": "#1b2540", "action": "#0f3a2e", "decision": "#3d3510", "tool": "#1c2a6b", "issue": "#47142a", "outcome": "#341452"}
CYBER_REL = {"causes": "#f5faff", "fixes": "#39ff88", "requires": "#4d8dff", "part_of": "#9aa5b8",
             "supersedes": "#b36bff", "contradicts": "#ff3b5c", "evidence_for": "#ffa726"}
FONT_DIR = "C:/Windows/Fonts/"
WRAP = 26  # characters per label line


def font(size, bold=False, sym=False):
    name = "seguisym.ttf" if sym else ("arialbd.ttf" if bold else "arial.ttf")
    try:
        return ImageFont.truetype(FONT_DIR + name, size)
    except OSError:
        return ImageFont.load_default()


def wrap(label):
    return "\n".join(textwrap.wrap(label, WRAP)[:3]) or label


# ------------------------------------------------------------------ primitives
def node_poly(shape, cx, cy, w, h):
    x0, y0, x1, y1 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
    if shape == "diamond":
        return [(cx, y0 - 8), (x1 + 14, cy), (cx, y1 + 8), (x0 - 14, cy)]
    if shape == "hexagon":
        return [(x0, cy), (x0 + 14, y0), (x1 - 14, y0), (x1, cy), (x1 - 14, y1), (x0 + 14, y1)]
    if shape == "octagon":
        c = 10
        return [(x0 + c, y0), (x1 - c, y0), (x1, y0 + c), (x1, y1 - c), (x1 - c, y1), (x0 + c, y1), (x0, y1 - c), (x0, y0 + c)]
    return None


def badge(d, bx, by, status):
    col, glyph = STATUS[status]
    r = 11
    d.ellipse([bx - r, by - r, bx + r, by + r], fill=col, outline=THEME["ring"], width=2)
    if glyph is None:
        for dx in (-5, 0, 5):
            d.ellipse([bx + dx - 2, by - 2, bx + dx + 2, by + 2], fill="white")
    else:
        d.text((bx, by + 1), glyph, fill="white", font=font(15, sym=True), anchor="mm")


def draw_node(d, shape, fill, cx, cy, w, h, label, status, f, way=False):
    ink, bw = (THEME["way"], 4) if way else (THEME["ink"], 2)
    box = [cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2]
    if shape == "rect":
        d.rectangle(box, fill=fill, outline=ink, width=bw)
    elif shape == "pill":
        d.rounded_rectangle(box, radius=min(h / 2, 18), fill=fill, outline=ink, width=bw)
    elif shape == "ellipse":
        d.ellipse([box[0] - 10, box[1] - 4, box[2] + 10, box[3] + 4], fill=fill, outline=ink, width=bw)
    else:
        d.polygon(node_poly(shape, cx, cy, w, h), fill=fill, outline=ink, width=bw)
    d.multiline_text((cx, cy), label, fill=THEME["text"], font=f, anchor="mm", align="center", spacing=3)
    if status:
        badge(d, box[2] + 2, box[1] - 2, status)


def styled_line(d, pts, colour, style, width=2):
    segs = list(zip(pts, pts[1:]))
    if style == "double":
        for off in (-2.5, 2.5):
            for (x0, y0), (x1, y1) in segs:
                L = math.hypot(x1 - x0, y1 - y0) or 1
                nx, ny = -(y1 - y0) / L * off, (x1 - x0) / L * off
                d.line([(x0 + nx, y0 + ny), (x1 + nx, y1 + ny)], fill=colour, width=2)
        return
    if style == "solid":
        d.line(pts, fill=colour, width=width, joint="curve")
        return
    on, off = (3, 5) if style == "dotted" else (10, 6)
    for (x0, y0), (x1, y1) in segs:
        L = math.hypot(x1 - x0, y1 - y0)
        t = 0.0
        while t < L:
            t2 = min(t + on, L)
            d.line([(x0 + (x1 - x0) * t / L, y0 + (y1 - y0) * t / L),
                    (x0 + (x1 - x0) * t2 / L, y0 + (y1 - y0) * t2 / L)],
                   fill=colour, width=width + (1 if style == "dotted" else 0))
            t = t2 + off


def head(d, tip, frm, colour, kind):
    (tx, ty), (fx, fy) = tip, frm
    a = math.atan2(ty - fy, tx - fx)
    ux, uy, px, py = math.cos(a), math.sin(a), -math.sin(a), math.cos(a)
    if kind == "triangle":
        d.polygon([(tx, ty), (tx - 14 * ux + 6 * px, ty - 14 * uy + 6 * py), (tx - 14 * ux - 6 * px, ty - 14 * uy - 6 * py)], fill=colour)
    elif kind == "open":
        d.line([(tx - 13 * ux + 7 * px, ty - 13 * uy + 7 * py), (tx, ty), (tx - 13 * ux - 7 * px, ty - 13 * uy - 7 * py)], fill=colour, width=3)
    elif kind == "tee":
        d.line([(tx - 2 * ux + 10 * px, ty - 2 * uy + 10 * py), (tx - 2 * ux - 10 * px, ty - 2 * uy - 10 * py)], fill=colour, width=4)
    elif kind == "diamond":
        d.polygon([(tx, ty), (tx - 9 * ux + 6 * px, ty - 9 * uy + 6 * py), (tx - 18 * ux, ty - 18 * uy), (tx - 9 * ux - 6 * px, ty - 9 * uy - 6 * py)], fill=colour)
    elif kind == "dot":
        d.ellipse([tx - 6 * ux - 6, ty - 6 * uy - 6, tx - 6 * ux + 6, ty - 6 * uy + 6], fill=colour)


def midpoint(pts):
    tot = sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))
    acc = 0
    for a, b in zip(pts, pts[1:]):
        L = math.dist(a, b)
        if acc + L >= tot / 2:
            t = (tot / 2 - acc) / (L or 1)
            return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
        acc += L
    return pts[0]


# ------------------------------------------------------------------ layout (simple Sugiyama)
def layout(g):
    ids = [n["id"] for n in g["nodes"]]
    layer = {i: 0 for i in ids}
    for _ in ids:  # longest path; bounded passes so a cycle cannot loop forever
        for e in g["edges"]:
            layer[e["dst"]] = max(layer[e["dst"]], min(layer[e["src"]] + 1, len(ids)))
    chains = []
    for k, e in enumerate(g["edges"]):
        chain = [e["src"]]
        for L in range(layer[e["src"]] + 1, layer[e["dst"]]):
            dummy = f"_d{k}_{L}"
            layer[dummy] = L
            chain.append(dummy)
        chain.append(e["dst"])
        chains.append(chain)
    nl = max(layer.values()) + 1
    rows = [r for r in ([v for v in layer if layer[v] == L] for L in range(nl))]
    parents = {}
    for c in chains:
        for a, b in zip(c, c[1:]):
            parents.setdefault(b, []).append(a)
            parents.setdefault(a, [])
    pos = {}
    for _ in range(4):
        for L, row in enumerate(rows):
            for i, v in enumerate(row):
                pos.setdefault(v, i)
            if L:
                row.sort(key=lambda v: sum(pos[p] for p in parents.get(v, [])) / len(parents[v]) if parents.get(v) else pos[v])
            for i, v in enumerate(row):
                pos[v] = i
    return layer, rows, chains


def cyber_background(W, H, seed):
    """Dark synthwave backdrop: gradient, perspective grid, seeded drifting rings and bars. Decoration only."""
    import random
    r = random.Random(seed)
    bg = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(bg)
    for y in range(H):
        t = y / max(H - 1, 1)
        d.line([(0, y), (W, y)], fill=(int(8 + 38 * t * t), int(5 + 6 * t), int(26 + 40 * t)))
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    hy = int(H * 0.72)
    for i in range(-14, 15):  # perspective floor lines
        ld.line([(W / 2 + i * W * 0.02, hy), (W / 2 + i * W * 0.14, H)], fill=(255, 60, 200, 38), width=1)
    for k in range(1, 9):
        y = hy + (H - hy) * (k / 8) ** 2
        ld.line([(0, y), (W, y)], fill=(255, 60, 200, 38), width=1)
    for _ in range(r.randint(4, 7)):  # drifting neon rings
        cx, cy, rad = r.randint(0, W), r.randint(0, H), r.randint(30, 120)
        col = r.choice([(0, 229, 255), (255, 60, 200), (140, 90, 255)])
        ld.ellipse([cx - rad, cy - rad, cx + rad, cy + rad], outline=col + (46,), width=r.randint(1, 3))
    for _ in range(r.randint(5, 9)):  # slanted data bars
        x, y, w2 = r.randint(0, W), r.randint(0, H), r.randint(40, 160)
        col = r.choice([(0, 229, 255), (255, 60, 200)])
        ld.line([(x, y), (x + w2, y - w2 // 3)], fill=col + (40,), width=r.randint(2, 5))
    for _ in range(W * H // 900):  # speckle
        x, y = r.randint(0, W - 1), r.randint(0, H - 1)
        ld.point((x, y), fill=(200, 230, 255, r.randint(30, 110)))
    out = Image.alpha_composite(bg.convert("RGBA"), layer)
    sl = ImageDraw.Draw(out)
    for y in range(0, H, 3):  # scanlines
        sl.line([(0, y), (W, y)], fill=(0, 0, 0, 36))
    return out


def render(g, path, capsule=None, title=None, look="plain", seed=0):
    """look='plain' (default, light, flat) or 'cyber' (dark neon). Same symbols and meaning in both."""
    from PIL import ImageFilter
    import random
    cyber = look == "cyber"
    THEME.update(CYBER_THEME if cyber else {"ink": "#111827", "text": "#111827", "ring": "white", "way": WAY_COLOUR})
    rng = random.Random(seed)
    f = font(15)
    tmp = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    size, labels = {}, {}
    for n in g["nodes"]:
        labels[n["id"]] = wrap(n["label"])
        l, t, r, b = tmp.multiline_textbbox((0, 0), labels[n["id"]], font=f, spacing=3)
        size[n["id"]] = (max(r - l + 34, 90), max(36, b - t + 18))
    layer, rows, chains = layout(g)
    gapx, gapy, dummy_w = 46, 130, 16
    top = 60 + (40 if title else 0)
    rowW = [sum(size.get(v, (dummy_w, 0))[0] for v in r) + gapx * (len(r) - 1) for r in rows]
    W = int(max(rowW + [600]) + 120)
    H = int(top + (len(rows) - 1) * gapy + 60)
    xy = {}
    for L, r in enumerate(rows):
        x = (W - rowW[L]) / 2
        for v in r:
            w = size.get(v, (dummy_w, 0))[0]
            xy[v] = (x + w / 2, top + L * gapy)
            x += w + gapx
    if cyber:  # seeded layout jitter on real nodes only; layers and order stay the same
        for n in g["nodes"]:
            x0, y0 = xy[n["id"]]
            xy[n["id"]] = (x0 + rng.uniform(-9, 9), y0 + rng.uniform(-7, 7))
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0)) if cyber else Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    if title:
        d.text((W / 2, 28), title, fill=THEME["text"], font=font(19, bold=True), anchor="mm")
    nodes = {n["id"]: n for n in g["nodes"]}
    outs, ins = {}, {}
    for k, c in enumerate(chains):
        outs.setdefault(c[0], []).append(k)
        ins.setdefault(c[-1], []).append(k)

    def port(v, k, lst, is_top):
        cx, cy = xy[v]
        w, h = size[v]
        ks = sorted(lst[v], key=lambda kk: xy[chains[kk][-2 if is_top else 1]][0])
        i = ks.index(k)
        span = min(w * 0.7, 24 * (len(ks) - 1))
        dx = -span / 2 + (span / (len(ks) - 1) if len(ks) > 1 else 0) * i
        extra = {"decision": 8, "outcome": 4}.get(nodes[v]["kind"], 0)
        return (cx + dx, cy - h / 2 - extra) if is_top else (cx + dx, cy + h / 2 + extra)

    heads = []
    for k, (e, c) in enumerate(zip(g["edges"], chains)):
        colour, style, hd = RELS[e["rel"]]
        if cyber:
            colour = CYBER_REL[e["rel"]]
        pts = [port(c[0], k, outs, False)] + [xy[v] for v in c[1:-1]] + [port(c[-1], k, ins, True)]
        line = pts if hd == "cross" else pts[:-1] + [(pts[-1][0], pts[-1][1] - 3)]
        styled_line(d, line, colour, style)
        if hd == "cross":
            mx, my = midpoint(pts)
            d.line([(mx - 7, my - 7), (mx + 7, my + 7)], fill=colour, width=4)
            d.line([(mx - 7, my + 7), (mx + 7, my - 7)], fill=colour, width=4)
        else:
            heads.append((pts[-1], pts[-2], colour, hd))  # drawn after the nodes so no node can hide an arrowhead
    for n in g["nodes"]:
        shape, fill = KINDS[n["kind"]]
        if cyber:
            fill = CYBER_FILL[n["kind"]]
        cx, cy = xy[n["id"]]
        draw_node(d, shape, fill, cx, cy, *size[n["id"]], labels[n["id"]], n.get("status"), f, way=bool(n.get("way")))
    for tip, frm, colour, hd in heads:
        head(d, tip, frm, colour, hd)
    if cyber:  # glow = blurred copy of the drawing added under it; the sharp drawing stays on top
        out = cyber_background(W, H, seed)
        glow = img.filter(ImageFilter.GaussianBlur(5))
        out = Image.alpha_composite(Image.alpha_composite(out, glow), glow)
        out = Image.alpha_composite(out, img).convert("RGB")
        out.save(path)
    else:
        img.save(path)
    THEME.update({"ink": "#111827", "text": "#111827", "ring": "white", "way": WAY_COLOUR})
    if capsule is not None:
        embed_capsule(path, capsule)
    return img.size


# ------------------------------------------------------------------ capsule (PNG iTXt)
def canonical(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True).encode("utf-8")


def _chunk(tag, data):
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)


def embed_capsule(path, obj):
    raw = open(path, "rb").read()
    data = b"vml-capsule\x00" + b"\x01\x00" + b"\x00" + b"\x00" + zlib.compress(canonical(obj), 9)
    iend = raw.rfind(b"IEND") - 4
    open(path, "wb").write(raw[:iend] + _chunk(b"iTXt", data) + raw[iend:])
    return hashlib.sha256(canonical(obj)).hexdigest()


def decode_capsule(path):
    raw = open(path, "rb").read()
    i = 8
    while i < len(raw):
        (n,) = struct.unpack(">I", raw[i:i + 4])
        tag, data = raw[i + 4:i + 8], raw[i + 8:i + 8 + n]
        if tag == b"iTXt" and data.startswith(b"vml-capsule\x00"):
            body = data[len(b"vml-capsule\x00"):]
            comp, body = body[0], body[2:]
            body = body[body.index(b"\x00") + 1:]
            body = body[body.index(b"\x00") + 1:]
            return json.loads(zlib.decompress(body) if comp else body)
        i += 12 + n
    return None


def image_tokens(path):
    w, h = Image.open(path).size
    s = min(1.0, 1568 / max(w, h), math.sqrt(1_150_000 / (w * h)))
    return math.ceil(int(w * s) * int(h * s) / 750)


# ------------------------------------------------------------------ legend
def legend(path):
    W, H = 1180, 400
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    f, fb = font(15), font(17, bold=True)
    d.text((20, 14), "VML legend - node kinds (shape)", font=fb, fill="#111827")
    for i, (k, (shape, fill)) in enumerate(KINDS.items()):
        draw_node(d, shape, fill, 100 + i * 185, 75, 120, 36, k, None, f)
    d.text((20, 125), "Relations (arrow points from cause/part/fixer to effect/whole/target)", font=fb, fill="#111827")
    for i, (rel, (col, style, hd)) in enumerate(RELS.items()):
        y = 165 + i * 30
        a, b = (40, y), (240, y)
        styled_line(d, [a, (b[0] - 3, y)] if hd != "cross" else [a, b], col, style)
        if hd == "cross":
            d.line([(133, y - 7), (147, y + 7)], fill=col, width=4)
            d.line([(133, y + 7), (147, y - 7)], fill=col, width=4)
            text = f"{rel}  (dashed red, X in middle, no direction)"
        else:
            head(d, b, a, col, hd)
            text = f"{rel}  ({style} {COLOUR_NAMES[col]}, {hd} head)"
        d.text((260, y), text, font=f, fill="#111827", anchor="lm")
    d.text((720, 125), "Status badges (top-right of node)", font=fb, fill="#111827")
    for i, s in enumerate(STATUS):
        y = 170 + i * 40
        badge(d, 741, y, s)
        d.text((765, y), s, font=f, fill="#111827", anchor="lm")
    draw_node(d, "pill", KINDS["action"][1], 790, 372, 150, 36, "correct way", None, f, way=True)
    d.text((20, 372), "Thick green outline = a verified step of the correct way", font=fb, fill="#111827", anchor="lm")
    img.save(path)
