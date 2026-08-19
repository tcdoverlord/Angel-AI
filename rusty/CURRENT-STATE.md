# Angel AI — Current State

## Verified Release

- Release: Genesis 1.0
- Git tag: `v1.0.0`
- Commit: `8b06235`
- Branch: `main`
- GitHub `origin/main`: verified at `8b06235`

## Verified Tests

Command:

```powershell
.\.venv\Scripts\python.exe -m pytest .\tests -q
```

Result:

```text
85 passed in 12.42s
```

`git diff --cached --check` was clean before the Genesis commit.

## Verified Backup State

A permanent D: backup was successfully created and verified:

```text
D:\Angel_Backups\Angel_Backup_2026-08-19_150550
```

A removable USB backup was also successfully created and verified.

The intended protection model is:

1. Working project
2. D: backup
3. Offline USB backup

## Current Runtime Issue

Live Angel testing showed:

- `current_datetime()` works.
- Weather retrieval did not work.
- Angel attempted `search_web()` and reported a network failure.

This does NOT yet prove that WeatherBrain itself is broken.

The next task is to trace WeatherBrain registration, tool routing, dispatch, and runtime integration.

## Important Local Untracked Material

The following remained outside Genesis 1.0:

```text
bootstrap/Angel_Backup_Test/
bootstrap/*.before-*
moveable/
```

Do not blindly delete or stage these.

## Current Development Direction

Genesis 1.0 is protected.

The next milestone is:

**Current Information & WeatherBrain Integration**

Do not modify the `v1.0.0` tag.
