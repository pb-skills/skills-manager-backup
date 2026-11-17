---
name: vuln-disclosure
description: Turn a confirmed vulnerability into a ready-to-send private/coordinated disclosure package. Create a disclosure/ tree with one self-contained sub-folder per affected vendor (exact REPRODUCE commands, minimal harmless PoC, technical explanation, email draft, evidence JSONs + hashes) plus a README index and coordination guardrails. Use once a vulnerability is confirmed (reproduced on a latest version, real security boundary crossed, not a duplicate) and private vendor disclosure is warranted. Never sends on its own — stops at drafting for operator approval.
---

# Vulnerability Disclosure Packaging

Build the private, coordinated-disclosure package for a **confirmed** vulnerability. This skill
turns a validated finding into per-vendor folders that are ready to send, but **does not send
anything** — it stops at drafting for operator approval.

## When to use

A finding is ready for this skill only when it is **confirmed**, meaning **all** of:

- reproduced ≥3× on a **supported (latest)** version;
- a real security boundary is crossed (a file written where the user did not authorize it, code
  executed that was not configured, or a privilege boundary crossed);
- not a crash, missing DLL, or documented / opt-in behavior;
- searched against existing CVEs/advisories and **not a duplicate**.

A *candidate* (not yet confirmed) or an informational note is **not** disclosure-ready — keep it
in `candidate_findings.md` / the research log and continue validating.

## Inputs you need before starting (the Finding)

Collect the metadata-schema fields for the finding and, **per affected vendor**:

| Field | Example (CAND-2026-001) |
|---|---|
| Product / Vendor | 7-Zip / Igor Pavlov |
| Version tested | 26.06 (latest) |
| Exact binary used | `Applications\7-Zip-26.06\7z.exe` |
| Extract command | `7z.exe x evil.zip -oC:\jtest\dest -y` |
| Artifact hash | installer/portable SHA-256 (verified vs official source) |
| Contact channel | GitHub ip7z/7zip · SourceForge "sevenzip" |
| Evidence | `Results/test_06_junction_2606/result.json` |
| Test IDs | T08 / T10 |

Also record:

- the **not-affected** reference product/version (e.g. WinRAR 7.11) — name it in every email and
  explanation so the vendor sees the differential that isolates their bug;
- the **reporter identity / credit line**, e.g. `Paulo Bazzo — https://cybersamurai.co.uk` — used on
  the email's `Credit:` line and as the sign-off.

## Output layout

```
disclosure/
├── README.md                        # index: affected table, layout, coordination policy
└── <Vendor>/                        # one folder per AFFECTED vendor
    ├── REPRODUCE.md                 # EXACT commands + steps used to reproduce
    ├── explanation.md               # root cause, impact, remediation, CVSS, CVE comparison
    ├── email.txt                    # disclosure email draft
    ├── poc/attacker.zip          # minimal HARMLESS PoC archive (marker, no real payload)
    └── evidence/result*.json        # recorded test results
```

Only affected vendors get a folder. The not-affected reference is documented in the README and in
each email/explanation — it never gets its own folder.

## Procedure

### 1. Gate — confirm the finding
Re-check the confirmation criteria above. If not confirmed, stop: this is not disclosure-ready.

### 2. Enumerate vendors
List every affected product + version + vendor + contact channel, and the not-affected reference.

### 3. Build the tree and the PoC
- Create `disclosure/<Vendor>/poc/` and `disclosure/<Vendor>/evidence/`.
- Craft a minimal **harmless** PoC archive per vendor — one entry that the bug writes outside the
  destination. Example (junction escape):
  ```
  python -c "import zipfile; z=zipfile.ZipFile('attacker.zip','w'); z.writestr('sub/evil.txt','ESCAPE MARKER'); z.close()"
  ```
  Use a marker string. Never bundle a real payload, an exploit, or malware.
- Copy the recorded `result*.json` evidence into each vendor's `evidence/`.

### 4. Write `REPRODUCE.md` (per vendor)
Exact, copy-pasteable commands in a `cmd` code block:
1. create the destination + a "protected" sentinel folder;
2. plant the trigger (junction, symlink, etc.) — the exact `mklink` / setup command;
3. craft the archive (exact command);
4. run the tool with the **exact binary path + flags** used in testing;
5. observe — name the file(s) that prove the boundary was crossed and the exit code.

Always include: product + exact version; the exact binary path used in testing **and** the
standard install-path equivalent; expected (vulnerable) vs observed result with exit codes; the
artifact SHA-256 and its verified source; a pointer to the reproducing script.

### 5. Write `explanation.md` (per vendor)
Summary, affected/not-affected table, root cause, attack prerequisites (state whether admin is
required), impact, relationship to prior CVEs (why it is not a duplicate), suggested remediation,
preliminary CVSS, evidence pointers, and a closing `Status: not disclosed` line.

### 6. Write `email.txt` (per vendor)

Use this exact structure, substituting the `<…>` values (fill the credit line and sign-off from the
reporter identity input; keep the `To:` line as a placeholder until the operator verifies it):

```text
To: <vendor security contact>   [VERIFY the current security-contact address before sending]

Subject: [Privileged] <class> — <impact> in <product> <version>

Hi,

I'm reporting a security issue in <product> <version> found during an independent review. I have not
published any of this and am reaching out for coordinated disclosure.

Credit: <reporter name> — <website/URL>
Please see both explanation and reproduce attached.
----
Summary:
<2–3 sentences: the class + CWE, matching explanation.md's summary.>

Impact: <arbitrary write → code execution / persistence; privilege escalation when elevated; state
whether admin is required.>

Affected: <product> <version>
Not affected (for comparison): <reference product/version and what it does differently.>

Full reproduction steps, root cause, suggested fix, and environment details are in the attached
REPRODUCE.md and explanation.md, along with a minimal PoC archive (poc/attacker.zip).

I'd like to coordinate a fix and disclosure and have not published anything. Please let me know your
preferred timeline (e.g. 90 days). I'm happy to provide further detail, logs, or a live demonstration.

Regards,

<reporter name>
```

Notes:
- The `Credit:` line carries the reporter's name + site; the sign-off repeats the name.
- Reference the PoC by the actual filename in the package (`attacker.zip`).
- Keep the body short — the detail lives in the attached `REPRODUCE.md` / `explanation.md`.

### 7. Write `README.md`
Index with the affected table, the per-vendor layout, status ("prepared, not sent"), coordination
plan, and pointers to the workspace evidence (finding file, replication report, test matrix,
result JSONs).

## Guardrails (non-negotiable)

- **Never send** the emails or publish the PoC automatically. This skill only drafts; the operator
  approves sending and fills in identity / PGP / the real contact address.
- **Never self-assign a CVE.** Request one through the vendor/CNA during coordination.
- **Harmless PoC only.** Marker files; no real payload; never overwrite system files or app binaries.
- **Verify contact addresses** from the vendor's official site/GitHub before sending.
- **Coordinate a timeline** (e.g. 90 days); do not publish details before agreement.
- Keep certainty ("confirmed") separate from severity (CVSS). Only confirmed findings are packaged.

## Relationship to research skills

A research skill (e.g. `windows-archiver-vuln-research`) produces candidates and promotes them to
confirmed. It should call this `vuln-disclosure` skill at the moment a candidate becomes
**confirmed**, to hand off the validated finding and build the package.
