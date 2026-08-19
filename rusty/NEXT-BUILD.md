# Angel AI — Next Build

## Mission

Repair and validate the live Current Information / WeatherBrain runtime path without disturbing Genesis 1.0.

## First Reproduction

Ask Angel:

> Angel, use your weather-specific tool or WeatherBrain to get the current weather. Do not use search_web. If you do not have a weather-specific tool available, tell me exactly that.

Then record the exact response.

## Inspect First

Review:

```text
angel/weather/__init__.py
angel/weather/combined.py
angel/weather/date_time.py
angel/weather/weather_brain.py
angel/tools.py
angel/brain.py
angel/context.py
angel/app.py
tests/test_current_info_planning.py
tests/test_weather_pipeline.py
```

Search for:

```text
WeatherBrain
weather
current_datetime
search_web
allowlist
dispatch
tool
registry
```

## Trace

Follow:

```text
User request
  ↓
Angel brain
  ↓
Tool selection
  ↓
Tool registry / allowlist
  ↓
WeatherBrain
  ↓
Weather backend
  ↓
Result
```

Determine exactly where the live path differs from the passing tests.

## Rules

Do not:

- rewrite the brain
- make generic web search the permanent weather implementation
- fabricate weather
- weaken tool safety
- modify `v1.0.0`
- force-push
- delete recovery material

## Baseline Test

```powershell
.\.venv\Scripts\python.exe -m pytest .\tests -q
```

Expected Genesis baseline:

```text
85 passed
```

## Acceptance Criteria

Angel must be able to:

- report the current date
- report the current weather
- provide temperature/conditions when available
- report precipitation information when available
- identify the tool/source path
- honestly report failures
- avoid treating stored knowledge as current weather

Add regression tests for the actual runtime integration.

Then create a focused Git checkpoint.
