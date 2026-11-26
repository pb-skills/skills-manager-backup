---
name: update-subconscious
description: Turn a successfully realized dream into a "subconscious" entry in C:\ai\memories\subconscious\ - a Markdown file (source of truth) plus a VML diagram image showing what was discovered, the verified correct way to achieve it, and how the pieces connect. Use at dream-realizer Gate 9 when a dream reaches passed, validated, deployed, implemented or resolved_by_memory with verified evidence; when the user asks to update the subconscious or draw what a dream achieved; or to rebuild/check existing entries.
---

# Update Subconscious

The subconscious holds **how things were successfully achieved**. Each entry is written once a dream is realized. It records the idea that was discovered and the correct way to do it, both as text and as a diagram in the Visual Memory Language (VML).

Why both: the VML test (`C:\ai\memories\dreams\experiments\EXP-vml\run-20261124-01\report.md`) showed diagrams read back perfectly (79/79 edges) but cost 2–3× the tokens of Markdown. The hidden capsule is also lost on any re-save. So **agents read the `.md`**; the `.png` is the visual overview for people, and for an agent only when the shape of the connections matters.

## Location
```
C:\ai\memories\subconscious\
  index.md                         one row per entry, newest first (generated)
  legend.png                       the 18 symbols + the correct-way outline (generated)
  DREAM-NNN-<slug>.md              source of truth: discovery, correct way, map, refs, spec block
  DREAM-NNN-<slug>.png             VML diagram built from the same spec (capsule = exact spec)
```
Tool: `C:\Users\joker\.claude\skills\update-subconscious\scripts\subconscious.py` (needs Pillow; `python` = `C:\Python312\python.exe`). Template: `spec-template.json` next to this file.

## When an entry is allowed
Only for a **realized** dream. Its outcome must be one of `passed`, `validated`, `deployed`, `implemented` or `resolved_by_memory`, and a report must prove it. Don't write entries for proposals, failed or inconclusive runs, or ideas that only sound right. Those stay in `dreams.md`, or in the run's report. If a dream was realized only in part, include just the verified part and show the rest with honest statuses (`pending`, `hypothesis`).

## Steps
1. **Gather the evidence.** Read the run's `report.md`, the memory entries it corrected or added (`issues.md`, `successes.md`, `procedures.md`) and the dream record. Use only what the report demonstrates.
2. **Write the spec** as JSON with the **Write tool**, never inline through Bash, because backslashes get halved. Put it in the scratchpad, starting from `spec-template.json`. Fields:
   - `id` (`DREAM-NNN`), `slug` (kebab-case), `title` (the discovery in under 8 words), `date` (realization date), `outcome`.
   - `discovery`: what was learned, in 2–4 plain sentences, including the version/environment it was verified on.
   - `correct_way`: the verified steps, in order, each one an instruction someone can follow.
   - `applies_when`: the situations where this knowledge should be recalled.
   - `nodes` (2–16) and `edges`, using the vocabulary below. Give every node a short `label` (60 chars at most) and a one-line `fact` with the exact detail (numbers, ids, paths).
   - `refs`: at least `report`; add the memory entries and the dream record. Use forward-slash absolute paths.
3. **Build:** `python <tool> build <spec.json>`. It validates the spec, writes the `.md` and `.png`, updates `index.md`, and creates `legend.png` if missing. Fix every validation error; don't loosen the rules.
4. **Look at the image** with Read. Check that the correct-way steps stand out, that no label is cut off, and that no arrow is ambiguous. If a layout is cluttered, drop the least important nodes rather than squeezing them in.
5. **Check:** `python <tool> check` must print `OK` for every entry.
6. **Link it back.** Add `Subconscious: subconscious/DREAM-NNN-<slug>.md` to the dream's record (in `dreams.md` → Implemented, or in `archive.md`). Then show the image to the user.

To change an entry, edit the `json vml-spec` block at the bottom of its `.md`, then run `python <tool> rebuild <entry.md>`. Never hand-edit the generated parts: `check` reports any drift. If a later finding overturns an entry, rebuild it with the old step marked `rejected` and a `supersedes` edge from the new step. Don't delete it silently.

## Vocabulary (VML, 18 symbols + 1 marker)
| Group | Symbols |
| --- | --- |
| Node kind (shape) | `fact` rectangle · `action` pill · `decision` diamond · `tool` hexagon · `issue` octagon · `outcome` ellipse |
| Relation (line) | `causes` solid black ▶ · `fixes` solid green ⊣ · `requires` dotted blue open › · `part_of` grey ◆ · `supersedes` double purple ▶ · `contradicts` dashed red ✕ (no direction) · `evidence_for` dashed orange ● |
| Status (badge) | `verified` ✓ · `hypothesis` ? · `rejected` ✗ · `pending` ••• · `risk` ! |
| Correct way | `"way": true` draws a **thick green outline**. Only `verified` nodes may carry it. |

Arrows point from the cause, part or fixer to the effect, whole or target. Typical shape for an entry:
- the **issue** found, with the **evidence** that proved it
- the **rejected** old belief, which the new rule `supersedes`
- the **action(s) of the correct way**, which `fix` the issue
- the **outcome** they produced, with measured numbers in its `fact`
- any **tool** still `pending` deployment

## Look (style)
Add `"style": "cyber"` to the spec for the dark neon look (default `"plain"` is the flat light one). Both use the **same symbols**. Only decoration changes: backdrop, glow, scanlines, and a small seeded layout jitter, derived from the dream number so rebuilds are identical. Colours keep their hues; the only change is that `causes` arrows are white instead of black. Keep the legend in mind: it is drawn in the plain look.

Tested 2026-11-25 with blind reads of random graphs: 44/44 edges, 34/34 nodes and 12/12 questions correct on the cyber look (after one fix). The first round found 2 of 21 edges missed because a node hid an arrowhead; the renderer now draws arrowheads on top. If a style ever hides a symbol, tone the style down rather than the symbol. Report: `C:\ai\memories\dreams\experiments\EXP-vml\run-20261125-01\report.md`.

## Rules
- Verified-only for the correct way; never upgrade a hypothesis to make the picture complete.
- One entry per dream; rebuilding replaces it. Keep the map to the essentials (2–16 nodes); detail goes in `fact` and `refs`.
- Never store secrets, credentials or personal data in a spec. The capsule copies the spec into the image.
- Lessons still belong in the category files (`memory-optimizer`). The subconscious entry links to them; it doesn't replace them.
