# Angel AI — Test Baseline

## Current Version Position

```text
Current development: Genesis v1.1
Target: Genesis v1.2
```

## Historical Genesis 1.0 Baseline

Command:

```powershell
.\.venv\Scripts\python.exe -m pytest .	ests -q
```

Verified result during Genesis 1.0:

```text
85 passed in 12.42s
```

## Current Rule

Before a significant v1.1 or v1.2 change:

1. inspect Git status;
2. run the targeted baseline;
3. record the actual current result;
4. stop if the baseline unexpectedly fails.

Do not force the current suite to equal `85 passed`.

## Test Discovery

Backup/recovery material can contain duplicate tests.

Use:

```powershell
.\.venv\Scripts\python.exe -m pytest .	ests -q
```

rather than unrestricted discovery.

## v1.2 Test Layers

### Unit

- capability contracts
- schemas
- Understand/Plan/Route logic
- evidence structures
- verification
- recovery boundaries

### Integration

- Angel → Rusty
- Rusty → capability
- capability → result
- result → evidence
- evidence → verification
- verified evidence → model

### Runtime

- real current datetime
- real filesystem inspection
- real project inspection
- approved system capabilities

### Safety

- denied capability
- missing permission
- cancellation
- failed execution
- unverifiable result
- recovery after failure

## First Acceptance Test

Ask:

> Angel, what time is it?

Expected architecture:

```text
Angel
→ Rusty
→ Understand
→ Plan
→ Route
→ current_datetime
→ real system clock
→ Evidence
→ Verify
→ response
```

The model must not supply the time from memory.

## Weather Regression

Ask:

> Angel, use your weather-specific tool or WeatherBrain to get the current weather. Do not use search_web. If you do not have a weather-specific tool available, tell me exactly that.

Record the actual runtime result.

Do not convert an untested weather path into PASS.
