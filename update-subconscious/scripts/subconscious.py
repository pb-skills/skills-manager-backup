"""Build subconscious entries: one realized dream -> Markdown (source of truth) + VML image.

Usage (run with the system Python that has Pillow):
  python subconscious.py build SPEC.json      validate, write <ID>-<slug>.md/.png, update index.md
  python subconscious.py rebuild ENTRY.md     regenerate an entry from the spec block inside its .md
  python subconscious.py check [ENTRY.md]     confirm .md, .png and index agree (all entries if omitted)
  python subconscious.py legend               write legend.png
  python subconscious.py decode ENTRY.png     print the capsule (exact spec) stored in the image

Root: C:/ai/memories/subconscious (override with env SUBCONSCIOUS_DIR, e.g. for tests).
"""
import hashlib, json, os, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vml  # noqa: E402

ROOT = Path(os.environ.get("SUBCONSCIOUS_DIR", "C:/ai/memories/subconscious"))
OUTCOMES = {"validated", "deployed", "implemented", "passed", "resolved_by_memory"}
MAX_NODES = 16
SPEC_FENCE = "```json vml-spec"
INDEX_HEAD = """# Subconscious — realized discoveries

One entry per realized dream: the idea that was discovered and the verified way to achieve it.
Each entry has a Markdown file (read this; it is the source of truth) and a VML image for humans
(legend: `legend.png`). Built and checked by the `update-subconscious` skill. Newest first.

| ID | Discovery | Realized | Outcome | Files |
| --- | --- | --- | --- | --- |
"""


class SpecError(ValueError):
    pass


def validate(s):
    errs = []
    for k in ("id", "slug", "title", "date", "outcome", "discovery", "correct_way", "applies_when", "nodes", "edges", "refs"):
        if k not in s:
            errs.append(f"missing field '{k}'")
    if errs:
        raise SpecError("; ".join(errs))
    if not re.fullmatch(r"DREAM-\d{3,}", s["id"]):
        errs.append("id must look like DREAM-001")
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", s["slug"]):
        errs.append("slug must be lowercase-kebab-case")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", s["date"]):
        errs.append("date must be YYYY-MM-DD")
    if s["outcome"] not in OUTCOMES:
        errs.append(f"outcome must be one of {sorted(OUTCOMES)} (only realized dreams belong here)")
    if not isinstance(s["correct_way"], list) or not s["correct_way"]:
        errs.append("correct_way must be a non-empty list of steps")
    if not isinstance(s["refs"], dict) or "report" not in s["refs"]:
        errs.append("refs must include 'report' (the experiment report that proves it)")
    if s.get("style", "plain") not in ("plain", "cyber"):
        errs.append("style must be 'plain' or 'cyber' (optional, default plain)")
    nodes, ids = s["nodes"], set()
    if not 2 <= len(nodes) <= MAX_NODES:
        errs.append(f"use 2-{MAX_NODES} nodes (images cost 2-3x Markdown tokens; keep the map small)")
    for n in nodes:
        nid = n.get("id")
        if not nid or nid in ids:
            errs.append(f"node id missing or duplicated: {nid!r}")
        ids.add(nid)
        if n.get("kind") not in vml.KINDS:
            errs.append(f"node {nid}: kind must be one of {list(vml.KINDS)}")
        if n.get("status") not in vml.STATUS and n.get("status") is not None:
            errs.append(f"node {nid}: status must be one of {list(vml.STATUS)} or null")
        if not n.get("label") or len(n["label"]) > 60:
            errs.append(f"node {nid}: label required, at most 60 characters")
        if n.get("way") and n.get("status") != "verified":
            errs.append(f"node {nid}: part of the correct way ('way': true) but not verified")
    if not any(n.get("way") for n in nodes):
        errs.append("mark the verified steps of the correct way with \"way\": true (at least one)")
    seen = set()
    for e in s["edges"]:
        if e.get("src") not in ids or e.get("dst") not in ids:
            errs.append(f"edge {e}: src/dst must be node ids")
        if e.get("rel") not in vml.RELS:
            errs.append(f"edge {e}: rel must be one of {list(vml.RELS)}")
        if e.get("src") == e.get("dst"):
            errs.append(f"edge {e}: self-loop")
        key = (e.get("src"), e.get("rel"), e.get("dst"))
        if key in seen:
            errs.append(f"edge {e}: duplicate")
        seen.add(key)
    if errs:
        raise SpecError("\n  ".join(["spec is invalid:"] + errs))
    missing = [v for v in s["refs"].values() if isinstance(v, str) and re.match(r"^[A-Za-z]:[/\\]", v)
               and not Path(v.split("#")[0]).exists()]
    return [f"ref path not found: {m}" for m in missing]


def spec_hash(s):
    return hashlib.sha256(vml.canonical(s)).hexdigest()


def base(s):
    return f"{s['id']}-{s['slug']}"


def to_markdown(s):
    lab = {n["id"]: n["label"] for n in s["nodes"]}
    b = base(s)
    out = [f"# {s['id']} — {s['title']}", "",
           f"Realized: {s['date']} · Outcome: `{s['outcome']}` · Proof: `{s['refs']['report']}`", "",
           f"![{s['title']}]({b}.png)", "",
           "## Discovery", s["discovery"].strip(), "",
           "## The correct way"]
    out += [f"{i}. {step}" for i, step in enumerate(s["correct_way"], 1)]
    out += ["", "## Applies when", s["applies_when"].strip(), "", "## Map", "### Nodes"]
    for n in s["nodes"]:
        tags = n["kind"] + (f", {n['status']}" if n.get("status") else "") + (", **correct way**" if n.get("way") else "")
        out.append(f"- `{n['id']}` {n['label']} — {tags}" + (f". {n['fact']}" if n.get("fact") else ""))
    out.append("### Relations")
    out += [f"- {lab[e['src']]} --{e['rel']}--> {lab[e['dst']]}" for e in s["edges"]]
    out += ["", "## References"] + [f"- {k}: `{v}`" for k, v in s["refs"].items()]
    out += ["", "## Spec",
            f"Generated by `update-subconscious`. Edit this block, then run `rebuild` so the image matches. sha256 `{spec_hash(s)[:16]}`.",
            "", SPEC_FENCE, json.dumps(s, ensure_ascii=False, indent=1), "```", ""]
    return "\n".join(out)


def spec_from_md(path):
    text = Path(path).read_text(encoding="utf-8")
    m = re.search(re.escape(SPEC_FENCE) + r"\n(.*?)\n```", text, re.S)
    if not m:
        raise SpecError(f"{path}: no {SPEC_FENCE} block")
    return json.loads(m.group(1))


def update_index(s):
    idx = ROOT / "index.md"
    rows = []
    if idx.exists():
        rows = [ln for ln in idx.read_text(encoding="utf-8").splitlines() if ln.startswith("| DREAM-")]
    rows = [r for r in rows if not r.startswith(f"| {s['id']} |")]
    b = base(s)
    rows.append(f"| {s['id']} | {s['title']} | {s['date']} | {s['outcome']} | [{b}.md]({b}.md) · [{b}.png]({b}.png) |")
    rows.sort(key=lambda r: r.split("|")[3].strip(), reverse=True)
    idx.write_text(INDEX_HEAD + "\n".join(rows) + "\n", encoding="utf-8")


def build(s):
    warnings = validate(s)
    ROOT.mkdir(parents=True, exist_ok=True)
    for old in list(ROOT.glob(f"{s['id']}-*.md")) + list(ROOT.glob(f"{s['id']}-*.png")):
        if old.stem != base(s):
            old.unlink()  # slug changed: replace the old pair
    md, png = ROOT / f"{base(s)}.md", ROOT / f"{base(s)}.png"
    md.write_text(to_markdown(s), encoding="utf-8")
    graph = {"nodes": s["nodes"], "edges": s["edges"]}
    seed = int(re.sub(r"\D", "", s["id"]))  # decoration is seeded by the dream number, so rebuilds are identical
    size = vml.render(graph, str(png), capsule=s, title=f"{s['id']} — {s['title']}",
                      look=s.get("style", "plain"), seed=seed)
    update_index(s)
    if not (ROOT / "legend.png").exists():
        vml.legend(str(ROOT / "legend.png"))
    md_tokens = (len(md.read_text(encoding="utf-8").split("## Spec")[0]) + 3) // 4
    print(f"wrote {md} and {png} {size}; image ~{vml.image_tokens(str(png))} tokens, Markdown (without spec) ~{md_tokens} tokens")
    for w in warnings:
        print("warning:", w)
    return md


def check(md_path):
    s = spec_from_md(md_path)
    problems = [f"spec: {w}" for w in validate(s)]
    png = Path(md_path).with_suffix(".png")
    if not png.exists():
        problems.append("image missing")
    else:
        cap = vml.decode_capsule(str(png))
        if cap is None:
            problems.append("image has no capsule (re-saved or converted?) — run rebuild")
        elif spec_hash(cap) != spec_hash(s):
            problems.append("image is out of date with the .md spec — run rebuild")
    if Path(md_path).read_text(encoding="utf-8") != to_markdown(s):
        problems.append("Markdown text differs from what the spec generates — run rebuild")
    idx = ROOT / "index.md"
    if not idx.exists() or f"| {s['id']} |" not in idx.read_text(encoding="utf-8"):
        problems.append("not listed in index.md — run rebuild")
    print(f"{Path(md_path).name}: " + ("OK" if not problems else "; ".join(problems)))
    return not problems


def main(argv):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    if len(argv) < 2:
        print(__doc__)
        return 2
    cmd = argv[1]
    try:
        if cmd == "build":
            build(json.loads(Path(argv[2]).read_text(encoding="utf-8")))
        elif cmd == "rebuild":
            build(spec_from_md(argv[2]))
        elif cmd == "check":
            files = [Path(argv[2])] if len(argv) > 2 else sorted(ROOT.glob("DREAM-*.md"))
            return 0 if all([check(f) for f in files]) else 1
        elif cmd == "legend":
            ROOT.mkdir(parents=True, exist_ok=True)
            vml.legend(str(ROOT / "legend.png"))
            print(f"wrote {ROOT / 'legend.png'}")
        elif cmd == "decode":
            print(json.dumps(vml.decode_capsule(argv[2]), ensure_ascii=False, indent=1))
        else:
            print(__doc__)
            return 2
    except SpecError as e:
        print(e)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
