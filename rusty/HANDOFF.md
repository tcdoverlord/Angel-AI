# Angel AI — Active Engineering Handoff

## READ THIS FIRST

**Do not start over.**

Angel AI Genesis 1.0 is complete and protected.

```text
Release: v1.0.0
Commit: 8b06235
Branch: main
GitHub: tcdoverlord/Angel-AI
```

## Verified Foundation

```text
85 passed in 12.42s
```

The D: backup and USB backup were both successfully verified.

## Current Mission

The next build is:

**Current Information & WeatherBrain Integration**

## Current Failure

Live testing showed:

```text
current_datetime()
    works

weather
    fails

search_web()
    attempted as weather fallback
    network failure reported
```

Do not assume WeatherBrain is broken.

Find the actual integration boundary first.

## First Action

Inspect:

```text
angel/weather/
angel/tools.py
angel/brain.py
angel/context.py
angel/app.py
tests/test_current_info_planning.py
tests/test_weather_pipeline.py
```

Then trace:

```text
request
→ brain
→ tool selection
→ registry/allowlist
→ WeatherBrain
→ backend
→ result
```

## Do Not

- rewrite the brain
- fabricate weather
- make search_web the permanent weather engine
- modify v1.0.0
- force-push
- delete recovery files
- blindly stage `moveable/`
- blindly stage backup copies

## Baseline

```powershell
.\.venv\Scripts\python.exe -m pytest .\tests -q
```

Expected:

```text
85 passed
```

## Goal

Make the real Angel runtime reliably use WeatherBrain for current weather, while preserving honest failure behavior and keeping the existing tests green.

## Final Principle

Protect what works.

Inspect before changing.

Test the real path.

Make the smallest responsible change.

Commit stable milestones.

Carry the knowledge forward.
