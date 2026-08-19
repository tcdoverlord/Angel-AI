# RustyReadme.md

# Angel AI â€” Rusty Continuity & Next-Build Guide

> **Purpose:** This document is the continuity bridge for the next Angel AI engineering session.
>
> Read this before making changes. It records the verified state, important decisions,
> recovery points, current problem, architecture direction, and the responsible next steps.
>
> **Central rule:** Protect what works. Preserve the truth. Carry the knowledge forward.

---

## 1. Project Identity

**Project:** Angel AI
**Current release:** Genesis 1.0
**Git tag:** `v1.0.0`
**Genesis commit:** `8b06235`
**Branch:** `main`
**GitHub repository:** `tcdoverlord/Angel-AI`

Genesis 1.0 was successfully committed and pushed to GitHub.

The release includes:

- WeatherBrain/current-information groundwork
- Angel brain/context/personality/tool changes
- Windows backup engine improvements
- Windows backup verifier improvements
- Bootstrap README updates
- Current-information/weather tests
- Verified recovery workflow

---

# 2. Genesis 1.0 â€” VERIFIED FACTS

The following were actually verified during this build.

### Python tests

The project's virtual environment was used:

```powershell
.\.venv\Scripts\python.exe -m pytest .\tests -q
```

Result:

```text
85 passed in 12.42s
```

### Git staged validation

```powershell
git diff --cached --check
```

Result:

```text
(no output)
```

### Genesis commit

```text
8b06235 Genesis 1.0: WeatherBrain and recovery bootstrap
```

### Release tag

```text
v1.0.0
```

The tag points to:

```text
8b062354b8c96768f55eb0932ed8c99a603adead
```

### GitHub

`main` was pushed successfully.

`v1.0.0` was pushed successfully.

Verified remote state:

```text
8b06235 (HEAD -> main, tag: v1.0.0, origin/main)
Genesis 1.0: WeatherBrain and recovery bootstrap
```

The GitHub tag was also verified with:

```powershell
git ls-remote --tags origin v1.0.0
```

---

# 3. IMPORTANT â€” DO NOT CONFUSE RELEASE WITH WORKING TREE

After the Genesis 1.0 commit, these remained untracked locally:

```text
bootstrap/Angel_Backup_Test/
bootstrap/Backup-Angel.ps1.before-capacity-20260819-145659
bootstrap/Backup-Angel.ps1.before-usb-20260819-143923
bootstrap/Verify-Angel-Backup.ps1.before-backup-selection-fix-20260819-152718
bootstrap/Verify-Angel-Backup.ps1.before-checks-fix-20260819-152232
bootstrap/Verify-Angel-Backup.ps1.before-final-menu-20260819-152006
bootstrap/Verify-Angel-Backup.ps1.before-location-picker-20260819-151435
bootstrap/Verify-Angel-Backup.ps1.before-picker-20260819-151546
bootstrap/Verify-Angel-Backup.ps1.before-picker-runtime-20260819-151710
moveable/
```

These were deliberately NOT included in Genesis 1.0.

Do not blindly `git add .`.

Do not delete recovery material merely to make `git status` clean.

`moveable/` was explicitly excluded from Genesis 1.0 by decision.

---

# 4. BACKUP SYSTEM â€” VERIFIED

Angel's Windows backup system was actively tested during this build.

## D: backup

A full backup completed successfully:

```text
D:\Angel_Backups\Angel_Backup_2026-08-19_150550
```

Robocopy reported:

```text
Files : 14535
Bytes : 223.87 m
FAILED : 0
```

The backup verifier reported:

```text
VERIFICATION: PASS
```

Verified:

- backup manifest
- backup report
- `ANGEL-BIBLE.md`
- `README.md`
- `angel`
- `bootstrap`
- `skills`
- `tests`
- no nested Angel backup
- `.git` excluded
- no reparse points

## USB backup

A removable USB drive was identified as:

```text
G:
VolumeName: RepoBackups
DriveType: 2
```

The backup system was patched so a drive root is permitted ONLY when the drive is a removable disk.

Fixed/internal drive roots remain blocked.

The USB backup was successfully created and later successfully verified.

This proves the backup verifier can work with an external/offline backup location.

## Three-copy goal

The intended protection model is:

1. Working Angel project on D:
2. Local permanent backup on D:
3. Offline/removable USB backup

Do not weaken this recovery model.

---

# 5. BACKUP CAPACITY WORK

The backup engine originally only checked for a fixed minimum free-space threshold.

A read-only capacity calculation was developed/tested conceptually to calculate:

```text
Eligible files
Payload
Safety margin
Required space
Destination free space
```

The actual backup payload observed during testing was approximately:

```text
223.88 MB
```

with a test safety margin of:

```text
100 MB
```

The next responsible enhancement is to make the production backup engine calculate the real eligible payload before starting the backup, while honoring its existing exclusions.

Existing exclusions are:

```text
.git
models
cache
backups
```

Do not replace these exclusions accidentally.

The backup engine should eventually:

1. Calculate eligible payload.
2. Calculate a safety margin.
3. Determine required space.
4. Check destination free space.
5. Block before creating a backup if insufficient.
6. Record the calculation in the manifest/report.
7. Then perform Robocopy.

This remains a future improvement unless already present in the current tracked code.

---

# 6. BACKUP SAFETY RULES

The backup system uses:

- explicit destination selection
- Windows folder picker
- manual path option
- path validation
- live-project protection
- drive-root safety rules
- removable USB root support
- free-space checks
- confirmation before backup
- manifest/report files
- Robocopy
- exclusions
- verification afterward

Administrator access must never bypass safety checks.

Never make a backup destination inside:

```text
D:\Angel_AI
```

or its subdirectories.

---

# 7. BACKUP VERIFIER â€” CURRENT BEHAVIOR

`bootstrap/Verify-Angel-Backup.ps1` was repaired during this session.

Current intended workflow:

```text
Choose where backups are stored

1. Browse for a folder
2. Enter a path manually
0. Cancel

        â†“

Discover Angel_Backup_* folders

        â†“

Choose backup number

        â†“

Confirm verification

        â†“

Run verification
```

The old hard-coded:

```text
D:\Angel_Backup_Test
D:\Angel_Backups
```

menu was intentionally removed from the verifier.

The user should choose the real backup location.

The folder picker works.

The backup discovery/selection workflow works.

The verifier successfully verified:

```text
D:\Angel_Backups\Angel_Backup_2026-08-19_150550
```

and the USB backup.

---

# 8. CURRENT BUG â€” WEATHERBRAIN

This is the immediate next engineering task.

Genesis 1.0 contains:

```text
angel/weather/__init__.py
angel/weather/combined.py
angel/weather/date_time.py
angel/weather/weather_brain.py
```

and tests:

```text
tests/test_current_info_planning.py
tests/test_weather_pipeline.py
```

The 85-test suite passes.

However, live runtime testing exposed an integration problem.

When Angel was asked:

> â€œWhat is today's date, what day of the week is it, and what is the current weather where I am?â€

Angel responded that:

```text
current_datetime()
```

worked successfully.

But weather failed because:

```text
search_web()
```

was attempted and returned a network failure.

Angel reported that she could not retrieve weather.

### Important interpretation

This means:

```text
CURRENT DATETIME
    â†“
WORKING

WEATHER
    â†“
Weather-specific runtime path
    â†“
NOT PROVEN WORKING

GENERIC search_web fallback
    â†“
FAILED
```

Do NOT assume the WeatherBrain code itself is broken.

The likely investigation area is:

- tool registration
- tool allowlist
- tool naming
- tool dispatch
- WeatherBrain integration
- model/tool routing
- runtime import path
- whether Angel can actually see the weather-specific capability

The next build should determine exactly where the failure occurs.

---

# 9. NEXT WEATHER TEST

Before modifying code, test Angel with:

> Angel, use your weather-specific tool or WeatherBrain to get the current weather. Do not use search_web. If you do not have a weather-specific tool available, tell me exactly that.

This test helps distinguish:

1. WeatherBrain is not registered.
2. WeatherBrain is registered but not selected.
3. WeatherBrain is selected but backend fails.
4. The model is incorrectly falling back to `search_web`.
5. Runtime imports/tool wiring are incomplete.

Do not guess.

Inspect the actual project.

---

# 10. WEATHERBRAIN INVESTIGATION PLAN

Start with read-only inspection.

Inspect:

```text
angel/weather/weather_brain.py
angel/weather/combined.py
angel/weather/date_time.py
angel/weather/__init__.py
angel/tools.py
angel/brain.py
angel/context.py
angel/app.py
tests/test_current_info_planning.py
tests/test_weather_pipeline.py
```

Search for:

```text
weather
WeatherBrain
current_datetime
search_web
allowlist
tool
dispatch
registry
```

Determine:

- What weather function actually exists?
- What does it accept?
- What does it return?
- How is it registered?
- Is it in the allowlist?
- Does Angel's brain know its name?
- Does the runtime dispatcher expose it?
- Is the weather implementation network-dependent?
- Does it use an API, library, or another mechanism?
- Does the model receive the correct tool schema?
- Does the test suite test the same runtime path that the application uses?

### Key rule

Do not "fix" the system by making `search_web()` pretend to be WeatherBrain.

The architecture should keep responsibilities separate.

---

# 11. ARCHITECTURE DIRECTION

Angel is intended to remain modular.

Preferred responsibilities:

```text
GUI
 â”‚
 â–¼
Angel application
 â”‚
 â”œâ”€â”€ Brain / reasoning
 â”œâ”€â”€ Context
 â”œâ”€â”€ Personality
 â”œâ”€â”€ Bible / identity
 â”œâ”€â”€ Tool registry
 â”‚
 â”œâ”€â”€ Current Information
 â”‚      â”œâ”€â”€ DateTime
 â”‚      â””â”€â”€ WeatherBrain
 â”‚
 â”œâ”€â”€ Rusty
 â”‚      â””â”€â”€ Rust backend / execution engine
 â”‚
 â”œâ”€â”€ PowerShell modules
 â”‚      â””â”€â”€ Windows administration
 â”‚
 â”œâ”€â”€ Backup / recovery
 â”‚
 â””â”€â”€ Validation / tests
```

Do not turn PowerShell into a monolith.

Do not make the GUI responsible for system operations.

Do not bury weather logic inside generic web search.

---

# 12. RUSTY

Rusty is the trusted Rust backend and execution engine for Angel's modular Windows toolkit.

Rusty should remain separate from:

- GUI
- PowerShell administration
- backup scripts
- WeatherBrain
- documentation

When Rusty is expanded, inspect the existing architecture first.

---

# 13. BOOTSTRAP

Important Windows bootstrap files:

```text
bootstrap/Angel-Bootstrap.ps1
bootstrap/Backup-Angel.ps1
bootstrap/Verify-Angel.ps1
bootstrap/Verify-Angel-Backup.ps1
bootstrap/Restore-Angel.ps1
bootstrap/Build-Angel-Seed.ps1
bootstrap/Start-Angel-Recovery.ps1
bootstrap/Wake-Angel.ps1
bootstrap/Check-Environment.ps1
bootstrap/Angel-Backup-Menu.ps1
bootstrap/README.md
bootstrap/ANGEL-BACKUP-CONTRACT.md
```

Bootstrap is the recovery foundation.

The philosophy is:

```text
Build.
Backup.
Recover.
Wake.
Continue.
```

---

# 14. README / GITHUB STATUS

The main README was updated for the Genesis 1.0 milestone.

A new headline was added for:

> **Next Work in Progress: Current Information & WeatherBrain Integration**

The intended public message is that Genesis 1.0 is the protected foundation and development continues forward.

Next work should be visible to GitHub followers rather than hidden.

---

# 15. GIT SAFETY

Current known release point:

```text
v1.0.0
8b06235
```

Before significant changes:

```powershell
git status --short
git branch --show-current
git log --oneline -5
```

Protect the release.

Do not:

```text
force-push
reset --hard
clean untracked files
delete recovery copies
rewrite remote history
```

unless explicitly requested and a recovery path is verified.

For meaningful changes:

```text
inspect
protect
change
validate
commit
verify
```

Keep unrelated work out of commits.

---

# 16. CURRENT LOCAL WORKING MATERIAL

The following remained outside Genesis 1.0:

```text
moveable/
bootstrap/Angel_Backup_Test/
bootstrap/*.before-*
```

Some `*.before-*` files are recovery copies created while repairing the backup/verifier scripts.

They are evidence/recovery material.

Do not automatically delete them.

If cleanup is later desired, inspect each one first and confirm that the current production file and Git checkpoint provide a sufficient recovery path.

---

# 17. TESTING RULE

The repository contains backup/recovery copies and therefore unrestricted:

```powershell
pytest
```

may discover duplicate test modules.

During this build, unrestricted discovery produced duplicate-module collection errors because backup/recovery trees contained copies of tests.

The correct production test command was:

```powershell
.\.venv\Scripts\python.exe -m pytest .\tests -q
```

Result:

```text
85 passed in 12.42s
```

Use the project's `.venv`.

Do not install dependencies globally merely to run the project tests.

---

# 18. RELEASE VALIDATION STANDARD

Before calling a meaningful milestone complete:

### Inspect

- repository root
- Git status
- branch
- relevant history
- changed files

### Protect

- stable commit
- backups
- recovery copies
- unrelated work

### Validate

- syntax
- tests
- tool routing
- safety boundaries
- expected behavior

### Checkpoint

Create a local Git commit.

Verify the commit.

For releases, create and verify a tag.

Push only when explicitly requested.

---

# 19. NEXT BUILD â€” RECOMMENDED ORDER

## Step 1 â€” Reproduce WeatherBrain failure

Use the runtime test prompt.

## Step 2 â€” Inspect actual tool registration

Trace from:

```text
Angel user request
    â†“
brain
    â†“
tool selection
    â†“
tool registry
    â†“
WeatherBrain
    â†“
weather backend
```

## Step 3 â€” Identify exact break

Do not repair symptoms before identifying the broken boundary.

## Step 4 â€” Make smallest responsible change

Preserve:

- existing working date/time
- 85-test suite
- Genesis 1.0
- backup system
- verifier
- existing architecture

## Step 5 â€” Add regression coverage

The new tests should cover:

- weather tool registration
- valid weather result
- safe failure
- no hallucinated weather
- current datetime still working

## Step 6 â€” Validate

```powershell
.\.venv\Scripts\python.exe -m pytest .\tests -q
```

Also test Angel manually.

## Step 7 â€” Git checkpoint

Commit only the WeatherBrain fix and its relevant tests/documentation.

Do not modify the Genesis tag.

---

# 20. WHAT NOT TO DO

Do not:

- rewrite Angel's brain just to solve weather
- make `search_web()` the permanent weather implementation
- hard-code today's weather
- fabricate weather when the backend fails
- weaken tool safety
- remove the current-information tests
- delete recovery files without inspection
- commit `moveable/` unless explicitly decided later
- commit backup copies into the source tree
- force-push
- rewrite `v1.0.0`
- claim weather works until live runtime testing proves it

---

# 21. SUCCESS CRITERIA FOR THE NEXT BUILD

The WeatherBrain milestone should not be considered complete until Angel can answer a live request such as:

> â€œAngel, what is today's date, what day is it, and what is the current weather where I am?â€

and correctly:

- obtain current date/time
- obtain current weather
- identify temperature/conditions
- report precipitation information when available
- identify the source/tool path
- report failure honestly if live data cannot be obtained
- avoid pretending that stored knowledge is current weather

The automated test suite must continue passing.

---

# 22. CONTINUITY NOTE

If this document is opened in a future session, the immediate context is:

> **Angel AI Genesis 1.0 is safely released on GitHub.**
>
> The next build is not a rebuild of Angel.
>
> It is a focused repair/integration milestone for Current Information and WeatherBrain.
>
> The first task is to trace why Angel currently uses `search_web()` and fails to retrieve weather instead of successfully using the dedicated WeatherBrain path.

Start by inspecting the actual repository.

Do not assume.

Do not guess.

Protect Genesis 1.0.

---

# 23. QUICK START FOR THE NEXT SESSION

From:

```powershell
PS D:\Angel_AI>
```

Run:

```powershell
git status --short
git branch --show-current
git log --oneline --decorate -5
```

Confirm:

```text
main
v1.0.0
8b06235
```

Then inspect the WeatherBrain path:

```powershell
Get-Content .\angel\weather\weather_brain.py
Get-Content .\angel\weather\combined.py
Get-Content .\angel\weather\date_time.py
Get-Content .\angel\tools.py
```

Then search the integration points:

```powershell
Select-String -Path .\angel\*.py,.\angel\weather\*.py `
    -Pattern "WeatherBrain|weather|current_datetime|search_web|allowlist|dispatch|tool" `
    -Context 2,4
```

Then run:

```powershell
.\.venv\Scripts\python.exe -m pytest .\tests -q
```

Expected baseline from Genesis 1.0:

```text
85 passed
```

If the baseline fails before making changes, stop and diagnose before modifying WeatherBrain.

---

# 24. FINAL ENGINEERING PRINCIPLE

Angel's future builds should be measured by evidence.

```text
Inspect before changing.
Protect what works.
Build in modules.
Test the real path.
Commit stable milestones.
Preserve recovery.
Tell the truth about failures.
Carry the knowledge forward.
```

**Genesis 1.0 is the foundation.**

**WeatherBrain/current-information integration is the next build.**

**Rusty remains the trusted backend/execution engine.**

**The backup system remains part of Angel's recovery architecture.**

**No important work should depend on memory alone when it can be documented and preserved here.**
