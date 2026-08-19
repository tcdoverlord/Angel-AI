# Angel AI — Recovery Guide

## Primary Git Recovery Point

Genesis 1.0:

```text
v1.0.0
8b06235
```

This is the protected GitHub release checkpoint.

## Backup Recovery

Verified local backup:

```text
D:\Angel_Backups\Angel_Backup_2026-08-19_150550
```

A removable USB backup was also successfully verified.

## Verification

Run the verifier from the Angel project:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\bootstrap\Verify-Angel-Backup.ps1
```

Choose:

```text
1. Browse for a folder
```

or:

```text
2. Enter a path manually
```

The verifier discovers:

```text
Angel_Backup_*
```

inside the selected parent folder.

## Backup Safety

Do not restore over working code blindly.

Before recovery:

1. Inspect current Git status.
2. Identify uncommitted work.
3. Preserve current recovery copies.
4. Confirm the backup being restored.
5. Verify the restored result.

## Git Recovery

Inspect:

```powershell
git status --short
git log --oneline --decorate -10
git tag -n
```

Do not use destructive reset/clean commands without an explicit recovery plan.

## Principle

Recovery is not only restoring files.

Recovery means preserving evidence, working code, configuration, decisions, and the ability to continue safely.
