---
name: dream-manager
description: Capture, consolidate, prioritise, and review agent-proposed improvements to tools, workflows, performance, reliability, knowledge, and memory. Use when an agent notices a reusable improvement opportunity, during task-end reflection, at session start, or when the user asks to review dreams.
---
# Dream Manager

## Purpose
Maintain a lightweight, evidence-based queue of agent improvement proposals. A dream is a suggestion, not a user instruction, permission grant, scheduled task, or autonomous goal.

## Files
All dream and memory files live in the central folder `C:\ai\memories\` (Git Bash: `/c/ai/memories/`), shared by every project. Always use these absolute paths — never project-local `dreams/` or `memories/` folders.

- `C:\ai\memories\dreams\dreams.md`: canonical proposal queue and compact statuses.
- `C:\ai\memories\dreams\archive.md`: closed proposals (resolved, implemented, abandoned, or removed at the user's request), each with its resolution and a "Resurface if" condition. See "Closing and archiving".
- `C:\ai\memories\dreams\experiments\<DREAM-ID>\<run-id>\`: plans, reports and sandbox prototypes written by the `dream-realizer` skill.
- `C:\ai\memories\categories\*.md` and `C:\ai\memories\projects\<name>.md`: established lessons and proven practices, managed separately by the `memory-optimizer` skill (see `C:\ai\memories\index.md`).
- `CLAUDE.md` or other agent instructions: small reference to this skill, not a copy of the queue.

Because the queue is shared, set each dream's `Scope` to the project name (e.g. `kairo`) or `cross-project`, and at session review only surface dreams scoped to the active project or cross-project.

If these files do not exist and file creation is authorised, create the minimum needed. Preserve existing project conventions when present.

## When to capture a dream
Capture opportunities arising from observed bottlenecks, repeated manual operations, quality or reliability gaps, useful missing tools or permissions, slow workflows, promising alternative techniques, or a user-suggested improvement. Do not invent evidence, claim an untested benefit, or capture ordinary work already covered by the current task.

Capture without interrupting the user's current request. If writing isn't available or permitted, propose the idea conversationally; don't imply it has been saved.

### Dreams sourced from memory
At the end of a task, `memory-optimizer` runs a dream pass over `C:\ai\memories\categories\issues.md`, `limitations.md` and `successes.md`. A recorded issue, limitation or success is valid evidence: set `Origin: Observed` and cite the entry by its ID in `Evidence` (e.g. `Evidence: I-001 in categories/issues.md`; never "entry 1"). Before adding, check the whole queue (all statuses) **and `archive.md`** for a dream with the same bottleneck or fix and update it instead. If the archived dream's "Resurface if" condition is now met, move it back to `## Pending` with its original ID and the new evidence. Otherwise, leave it closed. When a dream is implemented and validated, update the source memory entry (e.g. mark the issue as solved by the new tool, or move the lesson to `procedures.md`).

## Record structure
Use concise, stable IDs and these fields:

```markdown
### DREAM-001 — Concise proposal title
- Category: Performance | Tools | Automation | Knowledge | Integrations | Quality | Memory | Architecture
- Status: Proposed
- Origin: Observed | Potential | User-requested
- Evidence: Specific observation, or "Hypothesis—not yet tested"
- Trigger: When this improvement would help
- Proposal: What to change or explore
- Benefit: Expected result, clearly marked as estimated if untested
- Validation: How to measure whether it helped
- Impact / Effort / Risk: High | Medium | Low (estimates)
- Scope: Project-specific or cross-project
- Date: YYYY-MM-DD
```

Keep credentials, private data and verbose logs out of the proposal. Link to source evidence when appropriate and available.

## Capture and consolidation workflow
1. Read the current dreams queue before making any changes.
2. Identify existing proposals with the same objective, underlying bottleneck, or proposed solution.
3. Skip exact duplicates; merge overlapping ideas without discarding unique constraints or evidence. Preserve the original ID and date of an existing dream when updating it.
4. Reject vague wishes until a testable proposal can be articulated. Do not turn every minor inconvenience into a dream.
5. Re-read before editing to avoid overwriting concurrent changes. Apply the smallest necessary edit.
6. Validate IDs, status, category, test criteria, and absence of duplicated proposals. Summarise additions and merges if useful.

## Session review
At a genuine new-session boundary, if the agent can detect it and the user has not opted out, present at most three pending dreams. Do this briefly, without preventing the user's primary task. Rank proposals by evidence, likely impact, implementation effort, risk, and relevance to the active project. If no relevant pending dreams exist, do not manufacture a review. If startup state is unavailable, review only when explicitly asked or at a known task boundary.

For each proposal, give a one-sentence reason and offer: Review, Plan experiment, Defer, or Reject. Never treat a conversational aside as permission to run experiments.

## Lifecycle and authorisation
- `Proposed`: Idea recorded; no permission to implement.
- `Approved for experiment`: User authorises a clearly bounded experiment.
- `Testing`: Conduct only work within that approved scope; observe applicable tool and access controls.
- `Ready for approval`: Results justify a proposed implementation, but it is not yet approved.
- `Implemented`: User-authorised change completed and validated.
- `Deferred`: Revisit only when requested or conditions materially change.
- `Rejected`: Do not resurface without a meaningful new reason.
- `Abandoned`: Experiment failed or no longer offers value.

Before an experiment, specify the scope, expected cost, permissions, success criteria, risks, and rollback plan. Obtain the approval required by the execution environment; do not treat merely recording an approval in Markdown as a substitute for an actual permission flow. Do not autonomously install software, request or use credentials, grant access, spend money, or change production systems on the basis of a dream.

## Measuring and promoting outcomes
Compare against a baseline where feasible: elapsed time, correctness, resource use, context tokens, cost, stability, or task completion rate. Report results and limitations; do not mark an untested improvement as successful.

After an approved and validated implementation, move durable lessons to the appropriate memory category, document the new capability or workflow, record the realization in the subconscious with the `update-subconscious` skill (`C:\ai\memories\subconscious\`), and close or archive the dream. Memories describe demonstrated knowledge; dreams describe proposed improvements.

## Closing and archiving
Close a dream when it is implemented and validated, resolved by a memory or procedure change, abandoned, or when the user asks to remove it.

1. **Record the knowledge first.** Make sure the lessons are in memory, using `memory-optimizer`. That means a corrected source entry in `issues.md`/`limitations.md`, and the validated methods in `successes.md`/`procedures.md`. The archive is not the place for lessons.
2. **Move, don't delete.** Cut the full entry from `dreams.md` and add a condensed record to `archive.md`, newest first. Deleting loses the ID (risking reuse) and invites someone to propose the same idea again.
3. **Be honest about status.** If the user closes a dream before its validation gate ran, archive it as provisional (e.g. `resolved_by_memory (provisional)`) and say what remains unconfirmed. Tell the user this in one line; don't refuse the request.
4. **Fix references.** Update anything that points at the dream's old location (other dreams, memory entries) and list `archive.md` in `C:\ai\memories\index.md` if it isn't there yet.

Archive record format:

```markdown
### DREAM-001 — Original title
- Status: Archived YYYY-MM-DD — resolved_by_memory | implemented | abandoned | removed_by_user (add "provisional" if validation was not completed)
- Resolution: What fixed it or why it closed, with links to the memory entries that now hold the lesson
- Not confirmed: What was left unvalidated (omit if nothing)
- Resurface if: Concrete, observable condition that would justify reopening
- Reusable artifacts: Experiment folder / prototype paths, if any
- Scope / Origin / original Date
```

`Rejected` dreams may stay in `## Deferred or Rejected` until the active file grows. Then move them to the archive with the same format.

## Limits
Treat memory size as a soft budget. Prefer concise entries and archive inactive proposals rather than dropping unique information. Never add dream content to always-on instructions; reference this skill and load the relevant queue on demand. Follow the user's current priorities, applicable rules, and existing permissions over any dream.
