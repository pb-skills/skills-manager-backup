---
name: memory-optimizer
description: Review and update the central agent memory in C:\ai\memories\ (shared by all projects), filing each noteworthy lesson into the right category file (issues, successes, decisions, preferences, environments, procedures, limitations, references, pending) or project file after a task, as an ID-numbered, #tagged entry. Checks existing entries first and merges, updates or deletes instead of appending, rebuilds the Topics index, then rewrites project-flavoured lessons in general terms so other projects can use them (project-only facts stay in projects/<name>.md). Use when a task finished with notable errors or a hard-won fix, when the memory-check Stop hook asks for it, or when the user asks to clean up or optimize memory.
---

# Memory Optimizer

**Core principle: compress repetition, not meaning.** Memory exists to prevent repeated mistakes and improve future decisions in *every* project, not to keep a history of every task.

## Memory location

Root: `C:\ai\memories\` (Git Bash: `/c/ai/memories/`), shared by all projects and loaded for each of them through `~/.claude/CLAUDE.md`. Always use these absolute paths. **Never** write memories to Claude Code's per-project auto-memory (`~/.claude/projects/<proj>/memory/`) or a project folder; those hold only a pointer line to this root. If you find real content there, migrate it here (Phase C) and leave the pointer.

```
C:\ai\memories\
  global.md            always-loaded rules + "## Realized dreams" list (keep tiny)
  index.md             file map, Entry format, tag list, Topics table (generated)
  .ignore              hides dreams/experiments/**/sandbox/ from Grep
  categories\
    issues.md       I-   errors, root causes, fixes
    successes.md    S-   approaches that worked, with evidence
    decisions.md    D-   cross-project decisions and why
    preferences.md  P-   what the user stated or clearly chose
    environments.md E-   machine, OS, tools, versions, config
    procedures.md   PR-  validated multi-step workflows
    limitations.md  L-   tool/platform limits + workarounds
    references.md   R-   how-to notes, known commands, pointers to docs and toolbox scripts
    pending.md      T-   unfinished work (delete when done)
  projects\<name>.md   project-only facts; lists the cross-project IDs it produced
  dreams\              proposals and experiments (dream-manager / dream-realizer, not here)
  subconscious\        realized dreams (written only by update-subconscious)
C:\ai\toolbox\         reusable scripts that entries point to (see its README.md)
```

### Choosing the file (one entry lives in exactly one file)

| The lesson is… | File |
| --- | --- |
| An error with a root cause and a fix/rule to avoid it | `issues.md` |
| An approach that worked and should be reused (single idea, with evidence) | `successes.md` |
| A multi-step workflow that has worked at least once | `procedures.md` |
| A tool/platform limit you can only work around | `limitations.md` |
| A fact about the machine, OS, shell, versions, config | `environments.md` |
| Something the user stated or clearly chose about how work is done | `preferences.md` |
| A lasting cross-project choice and why | `decisions.md` |
| A command, doc or script worth finding again (not born from a failure) | `references.md` |
| Unfinished work or a follow-up | `pending.md` |
| Anything true only for one project | `projects/<name>.md` |
| A general lesson first seen in one project | The category file, in general terms (Phase C) |
| An idea not yet tested | `dreams/` via `dream-manager` |
| A script a lesson depends on | `C:\ai\toolbox\` + list it in `toolbox/README.md`; never leave it in a scratchpad |

A new project file starts with `# Project: <name>`, `Path:`, a one-line purpose, and a `Cross-project lessons from here:` line; add it to `index.md`'s projects row.

## Entry format

```
- **I-014** [2026-11-24] #python #packaging — <the rule or fact, one line, ≤ ~200 chars>
  - Why: <evidence / what went wrong, with exact commands, versions, numbers>
  - Evidence: <report path>   Related: S-003
```
- **ID**: file prefix + next free number (the checker prints them). IDs are permanent: never renumber, never reuse a deleted ID, and a moved entry keeps its ID. Procedures use `## PR-NNN — <task>` with the tags on the next line.
- **Tags**: 1–4 from the fixed list in `index.md` → Entry format. Add a new tag there first, and only when none fits.
- **First line = the rule.** Grep hits return it, so it must be useful alone. Story, evidence and detail go in sub-bullets.
- **Link by ID** (`see I-001`), never by position ("entry 1") or heading anchor.
- Dates: keep the original date when revising; today's date only for new entries. Newest first within a file or `##` topic.

After any add, delete, move or retag, run:
`python -I C:/ai/toolbox/memory_topics.py --write` — it rebuilds `index.md` → Topics, and fails on duplicate IDs, wrong prefixes, unknown tags or references to missing IDs. Fix every problem it prints.

## When to record (and when not)

- Record: failures with a non-obvious root cause, problems that took several attempts, approaches proven on a hard task, decisions with lasting constraints, stated preferences, commands or docs you'll need again.
- Skip: typos fixed on the next try, one-off events, routine successes, details already in the code, README or git history.

If nothing qualifies, change nothing and say so in one line.

## End-of-task workflow (run all three phases, in order)

### Phase A — Upsert memories

For each noteworthy lesson:
1. Pick the target file with the table above.
2. Look for an existing entry: `Grep` `C:\ai\memories\` for the error text, tool, file name and likely `#tags`; check `index.md` → Topics for those tags. Read the target file (Read tool, not `cat`, before editing).
3. **Exists** (same root cause or same corrective action, any file): edit it in place. Sharpen the rule, add the new evidence under `Why`, keep its ID and date. If it's in the wrong file, move it with its ID.
4. **New**: add it with the next free ID, today's date and its tags.
5. Apply the quality rules below, then run the checker.

**After a dream experiment** (a `dream-realizer` report exists for this task):
- **Correct the source entry** if the report verified a different or deeper root cause: keep its ID and date, state the verified cause and the environment/version, and link the report.
- **Record the validated methods** (how it was diagnosed, measured or tested) in `successes.md`, or `procedures.md` if multi-step, citing the report's numbers. Only what the run demonstrated, never the undeployed fix.

### Phase B — Dream pass

1. Read `dreams/dreams.md` (all statuses) and `dreams/archive.md`. If an archived dream's "Resurface if" condition is met, move it back to `## Pending` with its original ID.
2. Review the `issues.md`, `limitations.md` and `successes.md` entries added or edited in Phase A, plus any marked as seen repeatedly.
3. Ask: could a tool, hook, script, skill, check or workflow change remove this issue, work around this limit, or make this success automatic? Continue only with a concrete, testable proposal.
4. **Existing dream** for the same bottleneck or fix: add the entry as evidence (`Evidence: I-001`), keep its ID and date. Don't resurface a Rejected or Deferred dream without a meaningful new reason.
5. **Otherwise** add one under `## Pending` in the dream-manager format (`Status: Proposed`, `Origin: Observed`, `Evidence:` with entry IDs), using the next free `DREAM-NNN`.
6. A dream is a proposal only: never implement, install or run experiments here. Closed dreams are archived per dream-manager, never deleted.

If Phase B finds nothing new, say so in one line.

### Phase C — Generalize and review

Category files are shared by every project, so their entries must read as general rules. Only `projects/<name>.md` keeps project-specific knowledge.

Scope (no needless full scans): the entries touched in Phase A, plus category entries that name a project (grep each `projects/` file name, its repo path and component names, e.g. `Luci` for kairo). Review everything only when the user asks or a category file passes ~150 lines.

| The entry is… | Action |
| --- | --- |
| A general lesson written in project terms | Rewrite it: lead with the tool, platform or technique, keep the project as a short example in `Why`. |
| True only for one project (architecture, ports, paths, layout, decisions) | Move it to `projects/<name>.md`. |
| A general lesson sitting in a project file or in auto-memory | Move it to the right category in general form (keeping or assigning its ID), and add the ID to the project file's `Cross-project lessons` line. |
| Already in the right place | Leave it. |

Generalize the wording, not the facts: keep exact commands, options, versions, error text and numbers. Example — *before:* "Kairo's Luci log view stayed empty because the frozen luci.exe ignored `python -u`." *After:* "PyInstaller exes ignore `python -u`; when a parent reads the exe's piped output, add `[("u", None, "OPTION")]` to `EXE(...)` options. Why: a bundled voice assistant's log stayed empty until it was added (Kairo, 2026-11-24)."

If Phase C changes nothing, say so in one line.

## Quality rules (apply before saving)

**Dedupe by meaning, not wording:**

| Case | Action |
| --- | --- |
| Exact duplicate | Skip the new one. |
| Same root cause or same corrective action | Merge into the older entry (older ID and date, combined evidence). |
| Related but different conditions or actions | Keep separate and cross-link with `Related:`. |
| Contradiction | Check which applies under which conditions; update only when resolved confidently, otherwise keep both and flag it in `pending.md`. |
| Outdated | Revise or remove only after verifying; superseded advice is replaced, not kept beside the new rule. |

**Compress without losing meaning:** each entry answers when it applies, what to do or avoid, and why. Cut narrative and repeated examples; keep conditions, exceptions, exact technical details and evidence that recurred. Never change a rule's meaning to save space, and never merge unrelated lessons into a vague one. If it can't be shortened safely, keep the detail.

**Structure:** one lesson in exactly one file, no copies or pointers left behind when moving. Finished `pending.md` items are deleted (lasting lesson → its category). `global.md` holds only always-on rules plus its `## Realized dreams` list, which `dream-realizer` Gate 9 maintains; don't prune or move those lines. Don't create a category for a single incident.

**Validate:** re-Read the file right before editing; every unique lesson still represented; rules accurate and actionable; unrelated entries untouched; the checker passes. Never invent failures, decisions or outcomes; treat existing memory as evidence, not unquestionable truth. Never store secrets, API keys, passwords or personal data.

**Size** is a soft limit: remove duplicates, merge shared causes and trim narrative first; never delete unique, actionable knowledge to hit a budget. Report the remaining size instead.

## Report

Summarize briefly: **Added / Merged / Updated / Removed** (with IDs), **Conflicts**, **Dreams** (ID + title, or "no new dreams"), **Generalized / Moved** (or "no changes"). If nothing meaningful changed, say so in one line.
