# Angel AI — Recovery Guide

## Current Version Position

```text
Current development: Genesis v1.1
Target: Genesis v1.2
```

## Protected Historical Recovery Point

```text
Genesis 1.0
v1.0.0
8b06235
```

## Verified Backup

Known verified local backup:

```text
D:\Angel_Backups\Angel_Backup_2026-08-19_150550
```

A removable USB backup was also verified during Genesis 1.0 work.

## Before Recovery

1. Inspect Git status.
2. Identify uncommitted work.
3. Preserve current recovery copies.
4. Confirm the intended recovery source.
5. Verify the recovered result.

Do not restore over working code blindly.

## Git Inspection

```powershell
git status --short
git branch --show-current
git log --oneline --decorate -10
git tag -n
```

Do not use destructive reset/clean operations without an explicit recovery plan.

## Genesis v1.2 Recovery Principle

Rusty development must remain reversible.

Each major milestone should have:

- a local Git checkpoint
- relevant tests
- documented changes
- preserved recovery material when needed

## Capability Recovery

If a new capability fails:

```text
stop
→ preserve evidence
→ identify boundary
→ disable/restore only the affected component
→ rerun targeted tests
→ resume
```

Do not roll back the whole project for an isolated capability defect unless evidence requires it.

## Core Principle

Recovery means preserving the ability to continue, not merely restoring files.
