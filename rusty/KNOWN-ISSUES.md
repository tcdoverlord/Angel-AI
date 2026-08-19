# Angel AI — Known Issues

## 1. Weather Runtime Integration

### Status

**Open — next build**

Automated tests pass, but live runtime testing exposed a problem.

Date/time retrieval worked through:

```text
current_datetime()
```

Weather retrieval did not succeed. Angel attempted:

```text
search_web()
```

and reported a network failure.

### Unknown

It is not yet proven whether the failure is:

- WeatherBrain registration
- tool allowlist
- tool naming
- dispatch
- runtime import
- model tool routing
- weather backend
- network access

Inspect before changing.

## 2. Test Discovery

Backup/recovery trees can contain duplicate test modules.

Use:

```powershell
.\.venv\Scripts\python.exe -m pytest .\tests -q
```

instead of unrestricted discovery.

## 3. Untracked Recovery Material

Local untracked material remains outside Genesis 1.0:

```text
bootstrap/Angel_Backup_Test/
bootstrap/*.before-*
moveable/
```

Do not automatically remove it.

## Issue Handling Rule

Record what is known, unknown, tested, and untested.

Never claim a fix until the actual runtime behavior has been verified.
