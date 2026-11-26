---
name: dream-realization
description: Safely turn an approved Dream Manager proposal into an evidence-backed, reproducible experiment, validate improvements in isolation, and propose staged deployment with explicit user approval.
---

# Dream Realization

## Purpose and boundaries
Dream Manager **identifies and prioritizes** improvement proposals. Dream Realization **investigates, prototypes, tests, and evaluates** a specific proposed improvement. Memory Optimizer **records verified lessons**. Dream Realization must never treat dream creation or experiment approval as permission to install globally.

**Core rule:** No persistent configuration changes, new dependencies, external network access, execution of untrusted transcripts, or global installation without permission appropriate to the action. Follow the host agent's existing tool permission model. Do not bypass authorization or security controls.

## Locations
- Queue: `C:\ai\memories\dreams\dreams.md`. Closed dreams: `C:\ai\memories\dreams\archive.md`.
- Experiment artifacts: `C:\ai\memories\dreams\experiments\<DREAM-ID>\<run-id>\` (`plan.md`, `report.md`, `sandbox\`). Use `run-YYYYMMDD-NN` for run IDs.
- Scratch work (corpora, temp runs): the session scratchpad. Copy only the artifacts worth keeping (prototype, cases, runner, results) into the experiment folder.

## When to invoke
- User explicitly asks to realize/test a dream, or approves a bounded experiment for a named dream ID.
- A proposal reaches `approved_for_experiment` after review. Do not silently execute from an unapproved queue.
- `rejected`, `deferred`, and `resolved_by_memory` dreams are not candidates unless new evidence justifies reopening and the user approves.

## Inputs
1. Dream ID and status, original problem, evidence, related memory IDs, expected benefit.
2. Relevant **specific** memory entries (`issues.md`, `successes.md`, `limitations.md`, possibly `procedures.md` and environment details); load only relevant entries, not full archives.
3. Baseline, acceptance criteria, constraints, environment and permissions.
4. Rollback strategy and target deployment scope.

## Lifecycle and gates

### Gate 0 — Intake, deduplicate, classify
Read the named dream and its cited memories. Check existing dreams and prior realization reports. Confirm proposal is not already fixed, rejected, deployed or a duplicate. Give it a unique `run_id`. Keep immutable source links/identifiers for provenance. No experiment may begin without approval.

### Gate 1 — Verify the problem *still exists*
Check fresh events **at or after the memory rule or previous fix** was introduced. Distinguish pre-fix incidents from post-fix regression. Search only available and authorized logs/transcripts. Never claim future dates or unavailable transcripts were scanned. If the issue is absent, mark `unconfirmed_after_fix` (not `fixed`); recommend monitoring or close as `resolved_by_memory` only if evidence suffices. If the problem is still reproducible, proceed. If uncertain, request more evidence or a bounded monitoring period rather than manufacturing a failure.

Write a short Gate 1 `report.md` even when you stop here, and record the dream's status in `dreams.md`. If the user still asks for an experiment while recurrence is unconfirmed, a **sandbox-only** run is fine. Label its results as "mechanism and detector quality", not as proof that the problem still recurs.

### Gate 2 — Approve an experiment plan
Write `C:\ai\memories\dreams\experiments\<DREAM-ID>\<run-id>\plan.md` using the template. Include hypothesis, exact versioned fixtures, no-change baseline, success and failure thresholds, false positive/negative constraints, security review, execution budget, expected artifacts, sandbox design and rollback. Present concise plan and obtain explicit approval before actions outside preapproved scope.

### Gate 3 — Build a safe isolated test environment
Prefer a disposable local temp directory or container/VM with least privilege. Use synthetic/redacted data. Pin dependencies and versions; disable network where possible; do not expose credentials or production directories. For hooks or agent settings: simulate hook inputs and execution in isolation, and never edit user/global settings during experiments. Record environment information sufficient to reproduce results.

**Real-history corpus (preferred over synthetic data alone).** Extract the relevant past tool calls (command, `is_error`, output head) from the **current project's** transcripts (`~/.claude/projects/<project>/*.jsonl`) into the scratchpad. Redact secrets, and record the row count and a SHA-256 prefix in the report. Don't copy transcript data into the memory folder: the auto-mode classifier blocks that as unauthorized access. Hand-label the real failures (positives). Mark calls that errored for unrelated reasons as neutral and exclude them.

**Fixtures without extra escaping.** Write each test case as its own file, verbatim, with the Write tool (`cases/pos01-….sh`, `neg01-…`, `edge01-…`). Have a runner script build any JSON input (e.g. hook stdin) with `JSON.stringify`. Never hand-escape test data inside JSON or inline Bash.

### Gate 4 — Baseline and regression test
Run the **same test corpus** without the proposed improvement. Confirm the failure occurs for representative known-bad cases and normal cases succeed. If baseline cannot reproduce the problem, report inconclusive results; do not claim the fix works. Use historical post-change evidence separately from synthetic reproductions.

**Ground truth must come from the real execution path.** A proxy (e.g. `bash file.sh`) can behave differently from the agent's actual tool. Spot-check at least one case through the real tool. If the results differ, find the extra layer: run a tiny harmless probe through the real tool, then compare what the transcript recorded as sent with the output's **bytes** (`od -An -tx1`, not `od -c` or `echo`). Vary one factor at a time (quoting style, following character). Once a layer is confirmed, relabel the ground truth before evaluating any candidate, and note the relabelling as a deviation from the plan.

### Gate 5 — Prototype and compare
Implement the smallest testable fix inside the sandbox. Run baseline and candidate on identical versioned fixtures. Include positive, negative, edge and adversarial cases. Measure reliability, runtime, resource overhead and false alerts. Limit retries; changing strategy after repeated failures is better than grinding indefinitely. Capture test commands/results and all deviations from plan.

For detectors (hooks, linters, checkers), always measure three things on the real corpus: **the no-change baseline, the naive trigger proposed in the dream, and the candidate**. Report recall on the labelled failures and the warning rate on calls that didn't fail. Set a revision budget in the plan (default: 3) and keep a one-line history of what each revision changed and why. Before counting a "false positive", inspect it: a call that exited 0 can still have silently produced broken output. Reclassify it only with deterministic evidence. Drop any rule that can't separate failures from successes (e.g. script length), rather than tuning it to fit the corpus.

### Gate 6 — Evaluate against predeclared gates
Classify as `passed`, `failed`, or `inconclusive`. `passed` requires demonstrated baseline failure, candidate improvement, no unacceptable regression, and measurement against stated thresholds. Synthetic success alone does not prove a live incident still occurs or that production deployment will work. Capture all outcomes in `report.md`, including unresolved limitations.

### Gate 7 — Request **separate deployment approval**
A passed experiment yields a **proposal**, not permission. Present precise target paths, files, diff, privilege level, potential impact, backup and rollback commands. Prefer project-local or canary rollout before user-level/global rollout. Obtain explicit approval **for the exact deployment scope**. Never assume authorization from conversation, proposal status or previous experiment permission.

### Gate 8 — Deploy, observe, rollback if needed
After approval, create a backup, deploy only approved files, verify settings syntax, test a harmless canary, observe for agreed interval and rollback on stop conditions. No arbitrary modifications to other projects. Avoid claiming success until post-install validation passes. For ongoing monitoring beyond the current session, rely on an approved external scheduler or ask user to supply results; do not promise background work.

### Gate 9 — Close learning loop
Update the dream status and link `plan.md`, `report.md`, diff and deployment record. Save **only reusable validated lessons** to the correct memory category. Update index entries and `last_evaluated_version`; do not duplicate incident counts when task-end and session-end both run. Failed experiments can still generate useful lessons, but never label hypotheses as verified facts.

Close the loop with `memory-optimizer`, in this order:
1. **Correct the source memory.** If the experiment found a different or deeper root cause than the memory entry that inspired the dream, edit that entry in place. Keep its date, add the verified cause and the environment/version it was verified on, and link the report.
2. **Record what worked.** Add the reusable *methods* the run validated to `categories/successes.md` (single ideas with evidence), or to `procedures.md` if they form a multi-step workflow.
3. **Close or keep the dream.** When the user closes or removes a dream, or it is resolved, implemented or rejected, **move it to `archive.md`; never delete it.** Use the archive record format in the `dream-manager` skill. If closing before validation finished, state what remains unconfirmed and give a concrete "Resurface if" condition.
4. **Update the subconscious.** If the dream was realized (`passed`, `validated`, `deployed`, `implemented` or `resolved_by_memory` with a report that proves it), run the `update-subconscious` skill. It writes `C:\ai\memories\subconscious\DREAM-NNN-<slug>.md` + `.png`: the discovery, the verified correct way, and a VML map of how they connect. Link the entry from the dream record. Skip this for failed, inconclusive or unconfirmed runs.
5. **Add a reference to global memory.** For the same realized dreams as step 4, add one line to the `## Realized dreams` section of `C:\ai\memories\global.md`, so every session knows what was already proven. Format: `- DREAM-NNN (YYYY-MM-DD, <outcome>) — <discovery>; <the correct way, in a few words> → subconscious/DREAM-NNN-<slug>.md`. Keep it under ~200 characters with no evidence or detail, since the subconscious entry holds those. If the dream already has a line, update it in place (for example, `passed` → `deployed`). If a realized dream is later rolled back or disproved, remove its line. Newest goes first. If the section grows past ~15 lines, ask the user before merging or dropping old lines.
6. **Keep the index current.** If new memory files or folders were created, list them in `C:\ai\memories\index.md`.

## Status model
`proposed` → `approved_for_experiment` → `baseline_verified` → `testing` → `passed` / `failed` / `inconclusive` → `awaiting_deployment_approval` → `canary` → `deployed` → `validated` / `rolled_back`.

Alternative terminal states: `rejected`, `deferred`, `duplicate`, `resolved_by_memory`, `unconfirmed_after_fix`.

## Dream acceptance filter
Decline or defer implementation when evidence shows a one-off inconvenience, an existing documented procedure adequately solves it, or no repeatable measurable benefit is likely. Explicitly record why; do not create a tool merely to satisfy the existence of a dream.

## Quality gates
- Reproducible baseline; versioned fixtures; deterministic pass/fail criteria.
- Safety: no secrets in artifacts; no untrusted command evaluation; least-privilege test environment.
- Performance: compare against baseline; state acceptable overhead.
- Practicality: maintenance owner, rollback and project vs global scope.
- Trust: clearly distinguish observed evidence, hypotheses and predictions.

## Specific example: DREAM-001 (worked example — archived 2026-11-23)
Issue: inline Bash/JavaScript/JSON snippets generated by an agent suffer quoting, `${...}` interpolation, or invalid JSON when passed through shell layers. Historical report includes four distinct breakages, **all before** `issues.md` rule was written.

What actually happened shows the gates in use. Use it as the pattern:
- **Gate 1:** found no repeats in 25 calls after the rule (`unconfirmed_after_fix`). It also showed the naive trigger warned on 28% of good calls.
- **Sandbox run:** a corpus of 409 real calls with 4 labelled failures. The proxy runs disagreed with the real tool, and a byte-level probe found that the Bash tool halves `\\` even inside single quotes and quoted heredocs. That was the true root cause.
- **Candidate result:** 4/4 failures caught, 4.0% warnings on good calls vs 23.1% for the naive trigger. Two of those "false positives" turned out to be silent failures.
- **Close-out:** `issues.md` was corrected, the methods went into `successes.md`, and the dream was archived with a "Resurface if" condition. The hook was never deployed.
- **Artifacts:** `C:\ai\memories\dreams\experiments\DREAM-001\`.
- **Subconscious:** the verified discovery from the sandbox run (2026-11-23) is in `C:\ai\memories\subconscious\DREAM-001-bash-tool-backslash-layer.md` + `.png`. The dream itself resurfaced on 2026-11-24 to propose deploying the hook. Rebuild the entry if that deployment is validated.

If and only if recurrence is confirmed, propose a `PreToolUse` warning hook in supported Claude Code settings. Use the current documented hook API/schema for the installed Claude Code version; fail safe (warn/permit by default rather than silently blocking useful work). The hook may inspect tool metadata to flag risky inline snippets, but must never execute candidate command text. Test positives (broken shell/JSON/interpolation), negatives (valid multiline scripts), escaped variants, and benign Bash commands; measure false warning frequency. Validate in an isolated mock harness, then project-local canary, then a **separately approved** user-level install (`~/.claude/settings.json` on supported systems, platform-dependent). Back up settings and preserve unrelated hooks; document disable/rollback.

Target: eliminate demonstrated recurrence in the test corpus, with a field target of near-zero such errors and no more than one false warning/day **during an observed trial**. A daily false warning target cannot be proven by a short synthetic run.

## Specific example: DREAM-002
One-off transcript-mining inconvenience; `procedures.md` already describes the process and the backslash breakage belongs to DREAM-001. Status: `rejected`. Do not build a reusable mining script unless distinct new evidence later supports reconsideration.

## Outputs
Templates sit next to this file: `experiment-plan.md`, `experiment-report.md`, `deployment-record.md`. Keep all experiment artifacts grouped by dream and run ID under the experiments folder (see Locations).
