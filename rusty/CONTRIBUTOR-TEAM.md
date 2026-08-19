# Angel AI — Contributor Team Board

> **Purpose:** Coordinate human and AI contributors so work is not duplicated, tests are shared, and discoveries from different computers become reusable project knowledge.

## Read Before Working

Before starting any Angel AI task:

1. Read `Rusty/RustyReadme.md`.
2. Read `Rusty/HANDOFF.md`.
3. Read `Rusty/CURRENT-STATE.md`.
4. Read `Rusty/NEXT-BUILD.md`.
5. Read this file.
6. Inspect the actual repository and Git status.
7. Check active tasks before claiming work.

The repository is the source of truth.

Do not assume a task is unclaimed.

---

# 1. Protected Foundation

Current release:

```text
Genesis 1.0
v1.0.0
8b06235
```

The Genesis 1.0 release must not be rewritten.

Future work moves forward in new commits and branches.

---

# 2. Active Work Board

Use a task ID for every meaningful piece of work.

| Task ID | Area | Owner | Status | Branch | Files / Area | Notes |
|---|---|---|---|---|---|---|
| ANGEL-WEATHER-001 | WeatherBrain runtime integration | Angel/Core | ACTIVE | main | `angel/weather/`, tools, brain | Diagnose live weather routing before changing code |
| ANGEL-BACKUP-001 | Backup payload capacity check | OPEN | PLANNED | — | `bootstrap/Backup-Angel.ps1` | Calculate eligible payload while preserving exclusions |
| ANGEL-RUSTY-001 | Rust backend | OPEN | OPEN | — | Rust backend area | Claim only after inspecting current architecture |
| ANGEL-TEST-001 | Cross-machine testing | SHARED | ACTIVE | — | tests + contributor records | Record machine-specific results |
| ANGEL-DOCS-001 | Documentation continuity | Angel/Core | ACTIVE | main | `Rusty/`, README files | Keep verified knowledge current |

### Status meanings

- `OPEN` — available to claim
- `PLANNED` — desired but not started
- `ACTIVE` — someone is currently working on it
- `BLOCKED` — waiting on another dependency or investigation
- `REVIEW` — implementation complete; needs review/testing
- `DONE` — verified and checkpointed

## Claiming Work

Before starting an unclaimed task, record:

- contributor name/handle
- task ID
- branch
- intended files
- short goal
- expected validation

Do not independently solve an `ACTIVE` task without coordinating with its owner.

---

# 3. AI Contributor Rules

If a contributor uses an AI coding assistant:

1. Give the AI the `Rusty/` continuity documents first.
2. Tell it to inspect the repository before changing anything.
3. Tell it to read this contributor board.
4. Tell it which task ID it is working on.
5. Do not allow it to assume work is unclaimed.
6. Preserve working code.
7. Make the smallest responsible change.
8. Test the real path.
9. Report exact results.
10. Never invent tests, commits, builds, releases, or successful results.
11. Do not force-push or rewrite shared history.
12. Update the task record when work is complete.

Recommended AI startup prompt:

> You are contributing to Angel AI. Read the entire `Rusty/` folder before making changes. Check `CONTRIBUTOR-TEAM.md` for active work. Do not duplicate an active task. Inspect the actual repository and Git status. Preserve working systems. Make the smallest responsible change. Run relevant tests and report exactly what was inspected, changed, tested, and left unresolved.

---

# 4. Cross-Machine Testing

Angel is intended to run on different Windows systems and configurations.

A failure on another machine is valuable compatibility evidence.

Do not dismiss environment-specific failures as "just that computer."

Record enough information to reproduce the environment.

## Environment Capture

For each contributor machine, record when practical:

- Contributor
- Machine name or safe label
- Windows version/build
- PowerShell version
- Python version
- Rust version
- Git version
- CPU
- RAM
- GPU
- available storage
- project drive
- backup drive
- USB/removable-drive details
- Ollama/runtime configuration
- network availability
- relevant dependencies
- date tested

Avoid recording secrets, tokens, API keys, passwords, or private personal information.

---

# 5. Cross-Machine Test Matrix

| Test ID | Area | Environment | Result | Contributor | Notes |
|---|---|---|---|---|---|
| TEST-001 | Bootstrap | Windows 11 | — | — | |
| TEST-002 | Bootstrap | Windows 10 | — | — | |
| TEST-003 | Python test suite | `.venv` | — | — | |
| TEST-004 | Current date/time | Local machine | — | — | |
| TEST-005 | WeatherBrain | Network available | — | — | |
| TEST-006 | Weather failure handling | Network unavailable | — | — | |
| TEST-007 | Backup destination picker | Local drive | — | — | |
| TEST-008 | Backup destination picker | USB/removable drive | — | — | |
| TEST-009 | Backup capacity check | Small destination | — | — | |
| TEST-010 | D: backup | Permanent backup location | — | — | |
| TEST-011 | USB backup | Removable/offline copy | — | — | |
| TEST-012 | Backup verifier | Local backup | — | — | |
| TEST-013 | Backup verifier | USB backup | — | — | |
| TEST-014 | Restore workflow | Recovery copy | — | — | |
| TEST-015 | Rust backend | Windows environment | — | — | |

Replace `—` with verified results only.

---

# 6. Machine Test Record Template

Copy this section for each meaningful environment.

## Test Record

**Test ID:**

```text
TEST-###
```

**Contributor:**

```text
name/handle
```

**Date:**

```text
YYYY-MM-DD
```

**Machine label:**

```text
safe-machine-label
```

### Environment

```text
Windows:
PowerShell:
Python:
Rust:
Git:
CPU:
RAM:
GPU:
Project drive:
Backup drive:
USB/removable media:
Ollama/runtime:
Network:
```

### Test

```text
What was tested:
```

### Command / Procedure

```text
command or exact steps
```

### Expected Result

```text
expected behavior
```

### Actual Result

```text
actual behavior
```

### Result

```text
PASS / FAIL / BLOCKED
```

### Evidence

```text
test output, error summary, log/report path, or other reproducible evidence
```

### Notes

```text
environment-specific observations
```

### Follow-up

```text
next responsible action
```

---

# 7. Current High-Value Tests

## Current Information

Test:

> Angel, what is today's date, what day of the week is it, and what is the current weather where I am?

Verify:

- date is current
- day of week is correct
- weather is current
- temperature is correct when available
- conditions are reported
- precipitation information is reported when available
- tool/source path is honest

## WeatherBrain Isolation

Test:

> Angel, use your weather-specific tool or WeatherBrain to get the current weather. Do not use search_web. If you do not have a weather-specific tool available, tell me exactly that.

This is currently an important diagnostic test.

## Failure Behavior

Test with the relevant weather/network dependency unavailable.

Verify Angel:

- does not invent weather
- identifies the failure
- does not pretend stale knowledge is current
- reports what information remains available

---

# 8. Backup Compatibility Tests

Test:

- Windows folder picker
- manual destination selection
- removable USB destination
- drive-root safety
- fixed-drive safety
- insufficient-space behavior
- existing destination behavior
- backup creation
- backup manifest
- backup report
- backup verification
- nested-backup detection
- `.git` exclusion
- reparse-point detection

Preserve the existing exclusions:

```text
.git
models
cache
backups
```

Do not change those exclusions as part of unrelated testing.

---

# 9. Preventing Duplicate Work

Before implementing a fix, search:

- active task board
- Git branches
- recent commits
- current issue/PR if applicable
- relevant Rusty documents
- relevant tests

If another contributor is already working on the same subsystem:

**coordinate before changing it.**

If two investigations are genuinely independent, assign separate task IDs.

Example:

```text
ANGEL-WEATHER-001
Weather tool registration

ANGEL-WEATHER-002
Weather backend/network compatibility
```

These can proceed independently only if their file/architecture boundaries are clear.

---

# 10. Completion Record

When a task is finished, update its row with:

- final owner
- status
- branch
- commit
- tests
- result
- known limitations

Example:

```text
| ANGEL-WEATHER-001 | WeatherBrain runtime | Alice | DONE | feature/weather-routing | 123abcd | 91 passed | Live weather verified |
```

Only record a commit after verifying that the commit actually exists.

Only record a passing test after actually running it.

---

# 11. Shared Engineering Rules

Protect what works.

Inspect before changing.

Use read-only inspection first.

Prefer modular changes.

Preserve evidence.

Use least privilege for administrative operations.

Keep Windows protections enabled.

Do not expose secrets.

Do not force-push.

Do not rewrite shared history.

Do not delete another contributor's work.

Do not overwrite unrelated changes.

---

# 12. Suggested Team Workflow

```text
Contributor notices task
        ↓
Read Rusty/
        ↓
Check this board
        ↓
Claim task ID
        ↓
Inspect repository
        ↓
Create/confirm branch
        ↓
Implement smallest responsible change
        ↓
Run tests
        ↓
Record machine/environment results
        ↓
Review
        ↓
Commit
        ↓
Update board
        ↓
Share checkpoint
```

---

# 13. Knowledge From Different Computers

Different hardware and software environments are part of the test evidence.

If one contributor discovers:

```text
Windows 10 + Python 3.x → PASS
Windows 11 + Python 3.y → FAIL
```

record both results.

Do not immediately assume the code is universally broken.

Compare:

- versions
- dependencies
- network behavior
- permissions
- hardware
- drive layout
- runtime configuration

Then create a focused compatibility task if needed.

---

# 14. Security and Privacy

Do not put the following into this file:

- passwords
- API keys
- tokens
- private keys
- personal addresses
- account IDs
- confidential logs
- private customer data

Use safe machine labels.

Sanitize screenshots and logs before sharing publicly.

---

# 15. Current Coordination Note

At the time this file was created:

```text
Genesis 1.0 is protected.
v1.0.0 is published.
WeatherBrain runtime integration is the next active investigation.
85 tests passed in the Genesis baseline.
D: and USB backups were verified.
```

The goal of this board is simple:

> **Many contributors, one shared understanding, no duplicated work, and more real-world test coverage.**
