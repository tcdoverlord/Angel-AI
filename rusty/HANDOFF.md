# Angel AI — Active Engineering Handoff

## Do Not Start Over

Angel is currently in the **Genesis v1.1 development line**.

Genesis 1.0 remains the protected historical foundation:

```text
v1.0.0
8b06235
```

The current repository may be ahead of that release. Inspect Git before assuming the current state.

## Current Mission

**Genesis v1.1 → v1.2 — Trustworthy Agent Brain**

The target is the combined architecture:

```text
Angel
  ↓
Rusty Brain
  ↓
Understand
  ↓
Plan
  ↓
Route
  ↓
Execute
  ↓
Evidence
  ↓
Verify
  ├── success → reason/respond
  └── failure → Recover
```

## First Milestone

Create and approve the combined architecture/capability contract.

Then use `current_datetime` as the first end-to-end capability.

## Current Known Capability State

Date/time has been observed working.

Weather has not been proven through the intended WeatherBrain runtime path.

Do not assume WeatherBrain is broken until registration, allowlist, dispatch, backend, and model-routing boundaries are inspected.

## Immediate Inspection

Inspect:

```text
angel/brain.py
angel/context.py
angel/tools.py
angel/weather/
angel/app.py
rusty/
tests/
```

Trace:

```text
request
→ Understand
→ Plan
→ Route
→ Execute
→ Evidence
→ Verify
→ model
→ response
```

## Safety

Do not:

- rewrite the brain
- fabricate live data
- use generic search as a permanent replacement for dedicated capabilities
- modify the protected v1.0.0 tag
- delete recovery material
- reset/clean uncommitted work
- force-push

## Baseline

Use:

```powershell
.\.venv\Scripts\python.exe -m pytest .	ests -q
```

Historical Genesis 1.0 baseline:

```text
85 passed in 12.42s
```

## Goal

Build the Rusty Brain promised by the architecture while preserving the working v1.1 system.

## Final Principle

Protect what works. Preserve the truth. Carry the knowledge forward.
