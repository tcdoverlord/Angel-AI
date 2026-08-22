# Angel AI — Current State

## Current Version Position

Angel is currently in the **Genesis v1.1 development line**.

The next target is **Genesis v1.2 — Trustworthy Agent Brain**.

This is a controlled architectural evolution, not a rewrite.

## Protected Historical Release

```text
Genesis 1.0
v1.0.0
8b06235
```

The release remains protected.

## Current System

The project has:

- a real Angel implementation;
- Python brain/tooling;
- knowledge systems;
- Rusty continuity material;
- tests;
- an existing EXE/build path;
- working and recovery material that must be preserved.

The actual repository and Git state must be inspected before changes.

## What v1.1 Has Established

The current direction has prioritized:

- honesty about unavailable live information;
- modular components;
- local model integration;
- capability/tool infrastructure;
- knowledge boundaries;
- recovery and validation.

The verified Genesis 1.0 baseline was:

```text
85 passed in 12.42s
```

`current_datetime()` was also observed working during earlier live testing.

## Current Problem

Angel needs more than honesty.

The next gap is operational intelligence:

```text
Angel can understand a request
but the system still needs a stronger,
general Understand → Plan → Route → Execute
→ Evidence → Verify → Recover lifecycle.
```

## v1.2 Target

Rusty becomes the operational brain while retaining a clean six-function mental model:

```text
UNDERSTAND
PLAN
ROUTE
EXECUTE
VERIFY
RECOVER
```

Inside those functions, Rusty will use professional concepts such as:

- intent/context
- capability discovery
- structured execution
- evidence
- verification
- bounded planning
- recovery

## Live Current-Information Capabilities

`current_datetime` remains the reference capability and now has a dedicated routing path.

`current_weather` is now a dedicated live capability backed by Open-Meteo geocoding and current conditions. Weather/date-time requests no longer fall back to generic `search_web()`.

The reusable path is:

```text
Angel
→ WeatherBrain
→ capability
→ real system
→ structured evidence
→ model reasoning
→ Angel
```

The current-weather capability resolves an explicit location when supplied, otherwise it uses Angel's configured city/region. If live weather is unavailable, Angel does not fabricate conditions.

## WeatherBrain

WeatherBrain is now a dedicated routing layer for current date/time and weather requests.

- Date/time routes to `current_datetime`.
- Weather routes to `current_weather`.
- Combined weather/date/time routes to `current_weather`, whose verified live snapshot also carries the local date/time.
- Offline combined requests retain the verified `current_datetime` path instead of attempting a network request.
- Generic `search_web()` is no longer the weather execution path.

## Next Responsible Action

Finish the combined v1.2 architecture contract, then implement the first reusable capability boundary with `current_datetime` as the reference path.
