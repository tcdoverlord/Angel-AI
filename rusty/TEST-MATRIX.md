# Angel AI — Cross-Machine Test Matrix

This file is the durable compatibility test log.

Use it to record results from different computers rather than relying on memory or chat history.

## Environment Profiles

| Profile | Windows | Python | PowerShell | Rust | Git | Hardware | Contributor |
|---|---|---|---|---|---|---|---|
| MACHINE-001 | — | — | — | — | — | — | — |
| MACHINE-002 | — | — | — | — | — | — | — |

## Test Matrix

| Test ID | Test | Profile | Result | Date | Evidence / Notes |
|---|---|---|---|---|---|
| TEST-001 | Bootstrap | — | — | — | |
| TEST-002 | Python suite | — | — | — | |
| TEST-003 | Date/time | — | — | — | |
| TEST-004 | WeatherBrain | — | — | — | |
| TEST-005 | Weather failure handling | — | — | — | |
| TEST-006 | Backup picker | — | — | — | |
| TEST-007 | USB backup | — | — | — | |
| TEST-008 | Backup capacity | — | — | — | |
| TEST-009 | Backup verifier | — | — | — | |
| TEST-010 | Restore | — | — | — | |
| TEST-011 | Rust backend | — | — | — | |

## Environment Record

### MACHINE-###

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
Backup drive:
USB/removable drive:

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

Result: PASS / FAIL / BLOCKED

Evidence:

Notes:

Follow-up:
```

## Interpretation Rules

- PASS means the test actually passed.
- FAIL means the expected behavior did not occur.
- BLOCKED means the test could not be completed.
- Unknown must not be converted into PASS.
- Environment-specific behavior should remain documented.
- Repeated failures across machines may indicate a product issue.
- A failure on one machine may indicate compatibility or environment differences.

Never fabricate a result to fill an empty row.
