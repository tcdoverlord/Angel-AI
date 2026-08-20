# Angel AI — Genesis v1.1 → v1.2 Test Matrix

This file records durable validation evidence across machines and milestones.

## Environment Profiles

| Profile | Windows | Python | PowerShell | Rust | Git | Hardware | Contributor |
|---|---|---|---|---|---|---|---|
| MACHINE-001 | — | — | — | — | — | — | — |
| MACHINE-002 | — | — | — | — | — | — | — |

## Transition Test Matrix

| Test ID | Area | Profile | Result | Evidence / Notes |
|---|---|---|---|---|
| G12-001 | Current v1.1 baseline | — | — | |
| G12-002 | Understand / intent | — | — | |
| G12-003 | Capability contract | — | — | |
| G12-004 | Capability registration | — | — | |
| G12-005 | Capability routing | — | — | |
| G12-006 | Current datetime execution | — | — | |
| G12-007 | Evidence generation | — | — | |
| G12-008 | Evidence verification | — | — | |
| G12-009 | Angel ↔ Rusty bridge | — | — | |
| G12-010 | Planner single-step | — | — | |
| G12-011 | Planner multi-step | — | — | |
| G12-012 | Filesystem capability | — | — | |
| G12-013 | System information | — | — | |
| G12-014 | Process inspection | — | — | |
| G12-015 | Git capability | — | — | |
| G12-016 | PowerShell capability | — | — | |
| G12-017 | WeatherBrain integration | — | — | |
| G12-018 | Failure honesty | — | — | |
| G12-019 | Recovery behavior | — | — | |
| G12-020 | Cross-machine runtime | — | — | |
| G12-021 | EXE candidate | — | — | |

## Environment Record

```text
Contributor:
Date:
Machine label:

Windows:
PowerShell:
Python:
Rust:
Git:

CPU:
RAM:
GPU:

Project drive:
Ollama/runtime:
Network:

Additional dependencies:
```

## Test Record

```text
Test ID:
Environment profile:

Procedure:

Expected:

Actual:

Result: PASS / FAIL / BLOCKED / NOT CHECKED

Evidence:

Known limitations:

Follow-up:
```

## Interpretation Rules

- PASS means the test actually passed.
- FAIL means expected behavior did not occur.
- BLOCKED means it could not be completed.
- NOT CHECKED means no evidence exists yet.
- Unknown must never become PASS.
- Unit tests do not automatically prove live runtime behavior.
- A model response does not prove that a capability executed.
- Cross-machine failures are compatibility evidence and must be recorded.
