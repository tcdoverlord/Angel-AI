# Angel AI — Test Baseline

## Genesis 1.0 Baseline

The project's virtual environment was used.

Command:

```powershell
.\.venv\Scripts\python.exe -m pytest .\tests -q
```

Verified result:

```text
85 passed in 12.42s
```

## Git Validation

Command:

```powershell
git diff --cached --check
```

Verified result:

```text
No output / clean
```

## Important Test Discovery Note

The repository contains backup/recovery material that can contain duplicate test modules.

Unrestricted:

```powershell
pytest -q
```

previously caused duplicate-module collection errors.

For the production test suite, target:

```powershell
.\.venv\Scripts\python.exe -m pytest .\tests -q
```

## Next Weather Tests

Relevant files:

```text
tests/test_current_info_planning.py
tests/test_weather_pipeline.py
```

The next change should add coverage for the real runtime tool-registration/dispatch path if that path is currently not covered.

## Manual Acceptance Test

Ask:

> Angel, what is today's date, what day of the week is it, and what is the current weather where I am? Tell me which information came from current-information tools.

Then specifically test:

> Angel, use your weather-specific tool or WeatherBrain to get the current weather. Do not use search_web. If you do not have a weather-specific tool available, tell me exactly that.
