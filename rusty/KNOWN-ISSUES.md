# Angel AI — Known Issues

## 1. Genesis v1.1 → v1.2 Brain Architecture

### Status

**Open — current transition work**

Angel has stronger honesty boundaries but does not yet have the complete generalized operational lifecycle needed for a strong engineering-agent experience.

Missing/immature areas include:

- reusable capability contracts
- centralized Understand/Plan/Route/Execute orchestration
- structured evidence
- verification
- bounded multi-step planning
- recovery behavior across multi-step tasks

These should be built incrementally in Rusty.

## 2. WeatherBrain Runtime Integration

### Status

**Open**

Historical live testing showed:

```text
current_datetime() → works
weather → not proven through WeatherBrain
search_web() fallback → failed network access
```

Do not conclude that WeatherBrain itself is broken.

Investigate:

- registration
- allowlist
- naming
- dispatch
- runtime import
- backend
- model tool routing

## 3. Test Discovery

Backup/recovery material can contain duplicate tests.

Use:

```powershell
.\.venv\Scripts\python.exe -m pytest .	ests -q
```

rather than unrestricted discovery.

## 4. Documentation Transition

Some older documentation may describe Genesis 1.0 or earlier architectural terminology.

During v1.1 → v1.2 work, preserve useful historical information but use the current six-function Rusty Brain as the forward-looking architecture.

## Issue Rule

Record what is known, unknown, tested, and untested.

Never claim a fix until the actual runtime path has been verified.
