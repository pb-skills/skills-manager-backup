---
name: windows-archiver-vuln-research
description: Method for finding previously-unknown vulnerabilities in Windows archiving tools (7-Zip, WinRAR, Bandizip, PeaZip, NanaZip, WinZip) — reparse-point/link-following, path traversal, DLL search-order/sideloading, SFX execution, and Mark-of-the-Web. Use when researching or testing archiver security, doing variant analysis of archiver CVEs, or reproducing file-extraction security boundaries. Distilled from a validated multi-vendor CWE-59 finding (pre-existing NTFS junction following, CAND-2026-001).
---

# Windows Archiver Vulnerability Research

Find previously-unknown, reproducible security weaknesses in Windows archiving tools. This skill
codifies the method that produced **CAND-2026-001** — a multi-vendor **CWE-59** ("junction
following" → arbitrary file write outside the extraction destination), validated on the latest
7-Zip, Bandizip and PeaZip — plus the surrounding test matrix, the metadata schemas to record
findings and historical CVEs, and the exact pitfalls to avoid.

The core lesson: a vulnerability is **not** a crash, a missing DLL, or a documented behavior. It
is a reproduced crossing of a real security boundary (a file written where the user did not
authorize, code executed that was not configured, or a privilege boundary crossed) on a
**supported (latest) version**.

## When to use

- Researching or testing the security of 7-Zip, WinRAR, Bandizip, PeaZip, NanaZip, or WinZip.
- Variant analysis: turning a historical CVE into a hunt for *incomplete fixes* or *adjacent* code paths.
- Reproducing an extraction / archive-parsing / reparse-point issue with a minimal, harmless PoC.
- Building the evidence base (versions, hashes, test matrix, disclosure draft) for a finding.

## Target applications

| Priority | App | Official source |
|---|---|---|
| P1 | 7-Zip | https://www.7-zip.org/ |
| P1 | WinRAR | https://www.rarlab.com/ |
| P1 | Bandizip | https://www.bandisoft.com/bandizip/ |
| P2 | PeaZip | https://peazip.github.io/ |
| P2 | NanaZip | https://nanazip.org/downloads/ |
| P2 | WinZip | https://www.winzip.com/ |

Record for each: latest stable version, release date, architecture, installer type, license,
SFX capability, and known advisories. Never assume every app has the same SFX capabilities.

## Safety rules (non-negotiable)

- Work in an isolated VM with no sensitive data. Standard user for initial tests; elevated only
  when a specific hypothesis requires it and is authorized.
- Download only from official project sites; record SHA-256 and verify against the official
  source (many archiver installers, e.g. 7-Zip, are **NotSigned** — the hash is the verification).
- Use only harmless marker files. Never overwrite system files or app binaries.
- Treat crashes and missing-DLL messages as **leads**, not findings.
- Request approval before any destructive or privileged active test. Stop at vendor notification;
  never publish exploits.

## Vulnerability class taxonomy (what to hunt)

1. DLL search-order hijacking / sideloading.
2. Self-extracting archive (SFX) execution behavior.
3. Arbitrary file write / directory traversal.
4. Symbolic-link / **reparse-point** (junction) handling.
5. Unexpected process execution during extraction.
6. Unsafe temporary file/dir handling.
7. Privilege escalation via unsafe loading/extraction.
8. Mark-of-the-Web (MOTW) boundary failures.
9. Previously patched CVEs with incomplete fixes.

## Phases

### Phase 0 — Preparation
- Detect OS/arch. Record execution identity and integrity level (low/medium/high) — this defines
  what is testable and whether a "standard user" can actually trigger it.
- Create the workspace tree and keep **one test case per directory**, each with its own logs/artifacts.
- Inventory tools (Procmon, Process Explorer, Python 3, `pefile`, git). Missing pieces (C compiler,
  Procmon driver, elevation) become explicit blockers, not excuses to skip.

### Phase 1 — Discovery and installation
- Official download URL + date → download → SHA-256 → Authenticode (if any) → install/portable.
- Record install dir, binaries, and **hash + file version of every tested binary**.
- Prefer **portable builds** when elevation is unavailable: 7-Zip's installer is itself a 7z SFX
  (extract with `7z x`), Bandizip ships `BANDIZIP-PORTABLE.ZIP`, PeaZip ships `peazip_portable-*.zip`.

### Phase 2 — Historical CVE research (variant analysis)
- Collect prior CVEs with: app, CVE, affected/fixed versions, class, root cause, impact, source.
- Prioritize CVEs where multiple formats/SFX modules share code. A historical issue is a
  *starting point*, never re-reported. Record into `historical_vulnerabilities.csv` (schema below).

### Phase 3 — Baseline
- Harmless ZIP/7z/RAR + SFX; extract and record the process tree. Build a lightweight process
  observer with Python `ctypes` (`CreateToolhelp32Snapshot` / `Process32First`) when Procmon's
  driver is unavailable — you can still detect unexpected child processes.

### Phase 4 — DLL search-order
- Enumerate static imports with `pefile`; cross-reference against the `KnownDLLs` registry key.
- Flag non-KnownDLL imports. Note the **dynamic** loads (7-Zip → `7z.dll`, WinRAR → `Rarext.dll`)
  are invisible to static import analysis; they need Procmon or a benign probe DLL.
- Classify missing-DLL events without a proven security consequence as informational.

### Phase 5 — SFX execution
- Baseline: a default SFX (no config) must launch **nothing**.
- Then configure documented execution (`7z` `RunProgram=`, WinRAR `Setup=`) and confirm it launches
  *only* that program (a marker-writing `cmd.exe /c echo` is enough).
- Key question: can an archive trigger execution **outside** the explicitly configured actions?

### Phase 6 — Filesystem security (see "The key technique" below)
### Phase 7 — MOTW
- Set `Zone.Identifier` (ZoneId=3) on an archive and check whether extracted files inherit it.
- Remember: 7-Zip propagation is **opt-in** (`-snz`). "No propagation" without `-snz` is *not* a bug.

## The key technique — reparse-point / link-following test (found CAND-2026-001)

The highest-value, lowest-privilege probe for archive extraction. Two **distinct** attack surfaces
must be kept separate:

1. **Archive-embedded link** — the archive *contains* a symlink entry the archiver creates, then
   writes through (CVE-2025-11001/11002, CVE-2025-55188; WinRAR VU136809).
2. **Pre-existing link in the destination** — a junction already exists in the folder the user
   extracts into; the archiver follows it (CAND-2026-001, still unfixed in latest 7-Zip/Bandizip/PeaZip).

Test procedure (deterministic, one case at a time):

```
mkdir dest  protected
# junction dest\sub -> protected   (NO admin needed for junctions)
cmd /c mklink /J dest\sub protected            # or: New-Item -ItemType Junction -Path dest\sub -Target protected
# archive containing  sub\evil.txt
python -c "import zipfile; z=zipfile.ZipFile('evil.zip','w'); z.writestr('sub/evil.txt','MARKER'); z.close()"
# extract
7z x evil.zip -odest -y                         # or Bandizip.x64.exe x -o:dest -y evil.zip
# verdict
#   evil.txt in protected  -> ESCAPE (writes outside destination)
#   evil.txt in dest\sub   -> safe
```

Required rigor:

- **Isolate the protected dir per tool** (separate `protected_<tool>`). A shared target dir leaks a
  prior tool's write into the next tool's result (this produced a false positive in the field).
- **Verify "followed" vs "replaced"** — after extraction, check the reparse attribute, because a
  safe tool may *replace* the junction with a real directory:
  ```python
  import ctypes
  def is_reparse(p):
      a = ctypes.windll.kernel32.GetFileAttributesW(p)
      return a != -1 and bool(a & 0x400)   # FILE_ATTRIBUTE_REPARSE_POINT
  ```
- Test **root-level and nested** junctions, and both **ZIP and RAR** formats.
- **Reproduce 3×** and **compare across tools** (WinRAR is a useful "safe" reference — it replaces
  the junction).

Why it matters: a junction (`mklink /J`) needs **no admin** (unlike a symlink `mklink /D`), so a
standard/low-integrity user can both plant the junction and trigger the write. The escalation
variant appears when the archiver runs **elevated**.

## Metadata schemas (record everything logically)

**Finding** (one per candidate; also the disclosure template):

```
Finding ID / Application / Vendor / Affected version / Test environment /
Vulnerability class / CWE / Attack prerequisites / Security boundary crossed /
Affected component / Technical root cause / Reproduction procedure /
Expected behavior / Observed behavior / Security impact / Supporting evidence /
Existing CVE comparison / Suggested remediation / Disclosure contact / Disclosure status
```

**Historical CVE** (`historical_vulnerabilities.csv`):

```
app, cve, affected_versions, fixed_version, class, root_cause, impact, status, source
# status: verified (fetched this run) | to-verify (prior knowledge, confirm later)
```

**Test case** (`test_matrix.csv`):

```
test_id, app, version, category, description, expected, observed, result, date
# result: PASS | CANDIDATE | PASS (documented) | LEAD
# category: baseline | path-traversal | MOTW | SFX | junction-escape | reserved-names | ADS-entry | dll-imports
```

**Application inventory** (`applications.json`): name, vendor, official_url, latest_version,
latest_release_date, installed_version, install_path, installer_type, license, sfx_support,
status, binaries{sha256}, portable{path,sha256}.

## Gotchas & lessons learned (these cost time when forgotten)

1. `mklink` is a **cmd.exe builtin**, not a PowerShell command. In PowerShell use
   `cmd /c mklink /J <link> <target>` or `New-Item -ItemType Junction -Path <link> -Target <target>`.
2. **Junctions need no admin; symlinks do.** This is exactly what makes the pre-existing-junction
   attack accessible to standard users.
3. `Rar.exe` / `UnRAR.exe` are **RAR-only** — they reject ZIP ("not RAR archive", exit 10). For
   WinRAR ZIP tests use `WinRAR.exe` (GUI) with `-inul`, or use RAR-format archives.
4. 7-Zip/Bandizip **do** sanitize `../`, `C:/`, reserved names (`CON`→`_CON`) and the ADS colon
   (`file.txt:stream`→`file.txt_stream`). Test these, but expect safe results.
5. 7-Zip MOTW propagation is **opt-in** (`-snz`). "No Zone.Identifier on extracted files" is
   expected behavior, not a finding.
6. Installers may be unsigned (7-Zip) — verify by SHA-256 against the official release page.
7. `KnownDLLs` registry reads can return an incomplete list; re-check before claiming a DLL is
   "non-KnownDLL" and therefore hijackable.
8. Default SFX (no config) launches nothing; execution only happens via configured
   `RunProgram`/`Setup`. Confirming this baseline is what makes "unexpected execution" detectable.

## Validation & disclosure

For every candidate: reproduce ≥3× → confirm OS/app version → test against the **latest** release
→ list attacker capabilities → name the boundary crossed → exclude documented behavior → search
existing CVEs/advisories for duplicates → write a minimal harmless PoC → then decide if private
disclosure is warranted.

**When a candidate is promoted to "confirmed"** (security impact reproduced on a supported/latest
version, not a duplicate, not documented behavior), **hand off to the `vuln-disclosure` skill**:
load it with `skill("vuln-disclosure")` and follow it to build the per-vendor `disclosure/`
package (exact REPRODUCE commands, harmless PoC, explanation, email draft, evidence). Do not
re-implement the packaging steps inline.

- Draft the disclosure (full environment, exact version, hashes, impact, reproduction) but **do not
  send** without operator approval. Stop at vendor notification / coordinated disclosure.
- Never self-assign a CVE. Keep candidates private. Rank certainty separately from severity:
  only *confirmed* records get a severity.

## Deliverables

Use the phase-aligned folder structure defined by the `cve-to-test-framework` skill; archiver
specifics map onto it as follows:

```
research/
├── research_plan.md              # this framework instantiated for the archiver target
├── 01_target/
│   ├── target.json               # product identity (supersedes applications.json)
│   └── baseline.json             # version, platform, architecture
├── 02_cves/
│   ├── historical_cves.csv       # CVE corpus + patch analysis (supersedes historical_vulnerabilities.csv)
│   └── fix_versions.csv          # CVE → fixed version
├── 03_surface/
│   └── attack_surface.md         # reachable code paths (formats, CLI/GUI, SFX, plugins)
├── 04_tests/
│   ├── test_matrix.csv           # derived cases (junction-escape, MOTW, SFX, dll-imports, …)
│   └── execution_environment.json
├── test_logs/                    # per-test setup / execution / observation / verdict
├── findings/                     # dll_findings.csv, sfx_findings.csv, triage_log.md
├── scripts/                      # reproducer scripts
└── candidate_findings.md
```

Confirmed findings additionally produce the `disclosure/` package — see the `vuln-disclosure` skill.

## Relationship to other skills

- **`cve-to-test-framework`** drives the process: it produces the baseline, CVE corpus, pattern
  extraction, test matrix, and the log/triage workflow. When the target is an archiver, run the
  framework first and apply this skill's techniques inside its Phases 3–4.
- **`vuln-disclosure`** receives promoted findings and builds the per-vendor disclosure package.
