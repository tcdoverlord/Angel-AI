# Angel AI — Contributor Quick Start

Welcome to Angel AI.

This guide is for a developer or AI assistant joining the project.

## Before Coding

Read these files in order:

```text
Rusty/RustyReadme.md
Rusty/HANDOFF.md
Rusty/CURRENT-STATE.md
Rusty/NEXT-BUILD.md
Rusty/CONTRIBUTOR-TEAM.md
```

Then inspect the actual repository.

## Confirm Git State

```powershell
git status --short
git branch --show-current
git log --oneline --decorate -5
```

Current protected release:

```text
v1.0.0
8b06235
```

## Run Baseline Tests

```powershell
.\.venv\Scripts\python.exe -m pytest .\tests -q
```

Genesis baseline:

```text
85 passed in 12.42s
```

## Before Taking a Task

Check `Rusty/CONTRIBUTOR-TEAM.md`.

If the task is already `ACTIVE`, do not duplicate it.

Claim an available task with:

- task ID
- owner
- branch
- intended files
- goal

## AI Assistants

Tell your AI:

> Read the Rusty folder first. Inspect the repository before changing anything. Check the contributor board. Do not duplicate active work. Preserve working systems. Make the smallest responsible change. Run relevant tests. Report exactly what was changed and tested.

## Testing

When possible, record:

- OS version
- runtime versions
- hardware
- drive layout
- network state
- dependencies
- exact result

Different computers are valuable test environments.

## Finish Properly

Before declaring a task done:

```text
Tests pass
Changes reviewed
Commit verified
Task board updated
Known limitations recorded
```

Do not claim success without evidence.

## Core Principle

> One project. Shared knowledge. No duplicated work. More real-world testing.
