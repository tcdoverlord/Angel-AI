# Angel AI — Next Build

# Genesis v1.1 → v1.2 — Trustworthy Agent Brain

## Current Position

We are **currently working on v1.1**.

The immediate mission is to prepare and execute the transition into v1.2 without breaking the working v1.1 foundation.

## Mission

Upgrade Angel from a trustworthy conversational assistant into a trustworthy, evidence-driven engineering agent.

Do this without rewriting the existing project.

## Step 1 — Combined Architecture Contract

Formalize the team-facing Rusty Brain:

```text
Understand
Plan
Route
Execute
Verify
Recover
```

Then define the professional internal contracts underneath it:

```text
intent/context
capability discovery
planning
routing
structured execution
evidence
verification
recovery
```

Do not move code until the responsibility map is clear.

## Step 2 — Capability Contract

Create the generic model for a capability:

```text
name
description
input schema
output schema
risk
permissions
execute
verify
```

## Step 3 — Current Date/Time

Use `current_datetime` as the reference implementation.

The live date/time path is already registered and routed by the current WeatherBrain layer.

Required flow:

```text
request
→ Understand
→ Plan
→ Route
→ Execute
→ structured result
→ Evidence
→ model
→ response
```

The model must not be the source of the live time.

## Step 3a — Current Weather

Use `current_weather` as the dedicated live weather capability.

Required behavior:

```text
weather request
→ WeatherBrain
→ current_weather
→ Open-Meteo geocoding
→ Open-Meteo current conditions
→ structured live evidence
→ model
→ response
```

Do not route weather through generic `search_web()`.

If the user supplies a location, use it. Otherwise use Angel's configured city/region. If no location is available, report that clearly rather than guessing.

## Step 4 — Evidence / Verification

Every live capability result must be distinguishable from stored knowledge.

The model receives verified evidence rather than assumptions.

## Step 5 — Angel ↔ Rusty Integration

Integrate Rusty with the existing Python system through a controlled compatibility boundary.

Do not delete `angel/brain.py` merely because Rusty is growing.

## Step 6 — Planner

Add bounded multi-step planning after individual capabilities are reliable.

Example:

```text
Goal
→ plan
→ action
→ observe
→ verify
→ next action
→ final result
```

## Step 7 — Expand Capabilities

Recommended order:

```text
current_datetime
filesystem
system_information
process_inspection
Git
PowerShell
project_inspection
web
```

Each capability must be real, tested, documented, and safely bounded.

## Step 8 — Memory Separation

Separate:

- current conversation
- project memory
- retrieved knowledge
- live evidence

## Step 9 — Engineering Agent

Enable workflows such as:

```text
inspect project
diagnose issue
plan repair
execute safe action
verify result
report evidence
```

## Step 10 — EXE Candidate

Package only after the brain/core milestone is stable.

The executable is the delivery surface, not the architecture.

## Baseline

```powershell
.\.venv\Scripts\python.exe -m pytest .	ests -q
```

Historical Genesis 1.0 baseline:

```text
85 passed in 12.42s
```

## Rules

Do not:

- rewrite the brain prematurely
- fabricate live information
- bypass capability safety
- modify v1.0.0
- delete recovery material
- force-push
- claim runtime success without runtime evidence

## Acceptance

The v1.1 → v1.2 transition is moving correctly when Angel can reliably:

1. understand a request;
2. plan the required work;
3. identify a real capability;
4. route to it;
5. execute it;
6. collect evidence;
7. verify it;
8. reason about verified evidence;
9. respond naturally;
10. recover or stop honestly when evidence is unavailable.
