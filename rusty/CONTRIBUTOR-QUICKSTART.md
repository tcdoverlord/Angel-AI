# Angel AI — Contributor Quick Start

## Current Mission

Angel is currently being developed in the **Genesis v1.1 line**.

The team is preparing the transition to **Genesis v1.2 — Trustworthy Agent Brain**.

The goal is not to rewrite Angel. The goal is to strengthen the existing system with a professional brain architecture while preserving working behavior.

## Before Coding

Read, in order:

```text
Rusty/RustyReadme.md
Rusty/HANDOFF.md
Rusty/CURRENT-STATE.md
Rusty/NEXT-BUILD.md
Rusty/CONTRIBUTOR-TEAM.md
```

Then inspect the actual repository and Git state.

## v1.1 → v1.2 Rule

We are **building on v1.1**, not pretending v1.1 does not exist.

Preserve:

- working Python behavior
- existing tests
- current knowledge systems
- existing capability implementations
- recovery material
- project identity and branding

## Git Safety

Historical Genesis 1.0 remains protected:

```text
v1.0.0
8b06235
```

Do not assume that tag is the current working state.

Before significant work:

```powershell
git status --short
git branch --show-current
git log --oneline --decorate -5
```

Do not reset, clean, force-push, rewrite history, or delete recovery material.

## Baseline Tests

Use the project's virtual environment:

```powershell
.\.venv\Scripts\python.exe -m pytest .	ests -q
```

The verified Genesis 1.0 baseline was:

```text
85 passed in 12.42s
```

That is historical evidence. Always run the current suite before declaring a v1.1 or v1.2 milestone.

## v1.2 Architecture

Remember the six Rusty functions:

```text
Understand
Plan
Route
Execute
Verify
Recover
```

The professional implementation underneath them includes:

- intent/context
- capability discovery
- planning
- routing
- structured execution
- evidence
- verification
- recovery

## First Reference Capability

`current_datetime` is the reference capability.

It should prove:

```text
request
→ Understand
→ Plan
→ Route
→ Execute
→ Evidence
→ Verify
→ Response
```

The model must not invent the live time.

## AI Assistants

Tell your AI:

> You are contributing to Angel AI during the v1.1 → v1.2 transition. Read the Rusty continuity documents first. Inspect the actual repository and Git status. Preserve working systems and uncommitted work. Use the six-function Rusty Brain architecture as the top-level design. Do not duplicate active work. Make the smallest responsible change. Never invent tools, tests, commits, builds, or runtime results. Run relevant tests and report exactly what changed and what remains unknown.

## Finish Properly

Before declaring a task complete:

```text
Implementation reviewed
Relevant tests pass
Runtime behavior verified when applicable
Commit verified
Task board updated
Known limitations recorded
```

## Core Principle

> Protect what works. Inspect before changing. Build in modules. Preserve evidence. Carry the knowledge forward.
