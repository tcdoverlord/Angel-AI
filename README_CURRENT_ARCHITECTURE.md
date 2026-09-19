# Angel Platform 3.2.5
## Current Architecture Document

**Project:** Angel Nexus / Angel Platform  
**Developer/Brand:** TCDOVERLORD  
**Architecture checkpoint:** `v3.2.5-repair-weather-forecast`  
**Environment:** Windows development / Repair Mode  
**AI engine:** Local Ollama  
**Web server:** Python HTTP server  
**Desktop shell:** pywebview  
**Runtime address:** `http://127.0.0.1:8765/`  
**Default weather location:** New York, NY  
**Verified test location:** Beech Grove, Indiana 46107  

> "Peace Be The Journey" --- TCD_OVERLORD

---

## 1. Architecture Purpose

Angel Platform is a local-first AI assistant and system-management platform.

The current architecture combines:

- A Python application launcher
- A local HTTP server
- A browser-based Angel Platform interface
- An optional pywebview desktop shell
- Local Ollama inference
- Deterministic application routes
- Angel Nexus monitoring and dashboard elements
- Projects, modules, system tools, DevOps, and memory areas
- Provider-backed live weather and forecast retrieval

The project is currently being developed through **Repair Mode**. Source code is edited and tested directly before the final Windows executable is rebuilt.

---

## 2. High-Level Architecture

```text
+--------------------------------------------------------------+
|                    ANGEL PLATFORM UI                        |
|                                                              |
|  Just Chat | Projects | Modules | DevOps | Settings         |
|  System Tools | Memory | Angel Nexus Dashboard               |
+-------------------------------+------------------------------+
                                |
                                | HTTP requests
                                v
+--------------------------------------------------------------+
|                PYTHON APPLICATION LAYER                     |
|                                                              |
|  run_angel_platform.py                                       |
|       |                                                      |
|       v                                                      |
|  angel_platform/app.py                                       |
|       |                                                      |
|       +--> Start HTTP server on 127.0.0.1:8765               |
|       +--> Open UI with pywebview                            |
|       `--> Browser fallback if pywebview fails               |
+-------------------------------+------------------------------+
                                |
                                v
+--------------------------------------------------------------+
|                    WEB SERVER LAYER                         |
|                                                              |
|  angel_platform/webui/server.py                             |
|                                                              |
|  /api/chat                                                   |
|       |                                                      |
|       +--> Request parsing                                   |
|       +--> Conversation history                              |
|       +--> Lane and request selection                        |
|       +--> Deterministic routes                              |
|       +--> Live date/time                                    |
|       +--> Current weather                                   |
|       +--> Tomorrow forecast                                 |
|       `--> Ollama streaming fallback                         |
+-------------------+----------------------+-------------------+
                    |                      |
                    v                      v
+---------------------------+   +------------------------------+
|       Open-Meteo          |   |          Ollama               |
|                           |   |                              |
| Geocoding API             |   | Local model inference         |
| Forecast API              |   | Normal conversation          |
| Current weather           |   | Non-deterministic responses  |
| Tomorrow forecasts        |   |                              |
+---------------------------+   +------------------------------+
```

---

## 3. Project Directory Tree

```text
D:\angel-platform-3.2.5\
|
|-- angel_platform\
|   |
|   |-- app.py
|   |   |-- Imports the web server.
|   |   |-- Starts the server.
|   |   |-- Opens the desktop UI through pywebview.
|   |   `-- Falls back to the system browser if needed.
|   |
|   |-- builder.py
|   |   `-- Build-related/generated application support.
|   |
|   `-- webui\
|       `-- server.py
|           |-- HTTP server implementation
|           |-- /api/chat endpoint
|           |-- Ollama connectivity and streaming
|           |-- Date/time helpers
|           |-- Request classification
|           |-- Current weather handling
|           |-- Tomorrow forecast handling
|           `-- Application response routing
|
|-- dist\
|   `-- AngelPlatform\
|       `-- AngelPlatform.exe
|           `-- Existing packaged executable.
|
|-- run_angel_platform.py
|   `-- Python source entry point.
|
|-- RUN_WINDOWS.bat
|   `-- Launches dist\AngelPlatform\AngelPlatform.exe.
|
|-- RUN_REPAIR_MODE.bat
|   `-- Runs the application from Python source.
|
|-- build_windows_exe.bat
|   `-- Used later for final executable packaging.
|
|-- README.md
|   `-- Repair Mode checkpoint and project documentation.
|
`-- README_CURRENT_ARCHITECTURE.md
    `-- This architecture document.
```

---

## 4. Application Startup Flow

### Source entry point

`run_angel_platform.py`

```python
from angel_platform.app import main

if __name__ == '__main__':
    main()
```

### Application launcher

`angel_platform/app.py`

Current responsibilities:

1. Import the server `run` function.
2. Start the server.
3. Run the server in a background thread.
4. Use `http://127.0.0.1:8765/` as the application URL.
5. Open a pywebview window sized for the Angel Platform interface.
6. Fall back to the system browser if pywebview is unavailable or fails.
7. Shut down the server when the application closes.

### Startup flow

```text
run_angel_platform.py
        |
        v
angel_platform.app.main()
        |
        v
server = run()
        |
        v
server.serve_forever() in background thread
        |
        v
pywebview opens http://127.0.0.1:8765/
        |
        v
Angel Platform UI becomes available
```

---

## 5. Repair Mode

Repair Mode is the current development method.

### Existing packaged mode

```text
RUN_WINDOWS.bat
        |
        v
dist\AngelPlatform\AngelPlatform.exe
```

### Source-based repair mode

```text
RUN_REPAIR_MODE.bat
        |
        v
python run_angel_platform.py
        |
        v
Current Python source is loaded
```

### Why Repair Mode is being used

Repair Mode allows the project to:

- Avoid rebuilding the executable after every change.
- Test changes through the real Angel Platform UI.
- See startup errors directly in PowerShell.
- Preserve the existing packaged executable.
- Iterate on features before final packaging.

### Repair cycle

```text
Inspect source
      |
      v
Back up the target file
      |
      v
Make one controlled change
      |
      v
Run syntax validation
      |
      v
Restart Repair Mode
      |
      v
Test through the UI
      |
      v
Document the result
```

---

## 6. Request Routing Architecture

The main chat endpoint is:

```text
POST http://127.0.0.1:8765/api/chat
```

The request contains values such as:

```json
{
  "message": "User request",
  "model": "llama3.2:3b",
  "history": [],
  "location": null
}
```

The server currently uses a routing pattern that separates verified application actions from ordinary model conversation.

### General routing sequence

```text
Incoming /api/chat request
        |
        v
Read message, model, history, and location
        |
        v
Select AI lane / request type
        |
        v
Check deterministic application routes
        |
        +--> Approval-related route
        |
        +--> GitHub-related route
        |
        +--> Windows diagnostic route
        |
        +--> Combined date/time and weather
        |
        +--> Tomorrow weather forecast
        |
        +--> Current weather
        |
        +--> Current date/time
        |
        `--> Ollama conversation fallback
```

The exact route order should be inspected before future modifications because route order can affect which handler receives a request.

---

## 7. Current Weather Architecture

### Current weather responsibilities

The current weather handler:

- Detects a weather-related request.
- Searches the user's message for a location after terms such as `in`, `near`, or `for`.
- Accepts approved device coordinates when supplied.
- Geocodes named locations through Open-Meteo.
- Uses New York, NY when no location or device coordinates are available.
- Requests current weather data from Open-Meteo.
- Returns temperature, apparent temperature, conditions, humidity, wind, and observation time.

### Location resolution order

```text
Approved device coordinates?
        |
        +--> Yes: use coordinates
        |
        `--> No
              |
              v
Location explicitly included in message?
              |
              +--> Yes: geocode requested location
              |
              `--> No: use New York, NY
```

### Current weather provider flow

```text
User weather question
        |
        v
Extract location or use default
        |
        v
Open-Meteo geocoding API
        |
        v
Latitude and longitude
        |
        v
Open-Meteo forecast API
        |
        v
Current weather response
```

---

## 8. Tomorrow Forecast Architecture

A dedicated tomorrow forecast handler was added during this checkpoint.

### Forecast responsibilities

The tomorrow forecast handler:

- Detects weather-related requests containing `tomorrow`.
- Extracts an explicit location when present.
- Uses approved device coordinates when available.
- Defaults to New York, NY when no location is provided.
- Geocodes the location when necessary.
- Requests daily forecast data from Open-Meteo.
- Selects the next forecast day.
- Returns:
  - Forecast date
  - High temperature
  - Low temperature
  - Weather description
  - Precipitation probability
  - Maximum wind speed
  - Provider attribution

### Forecast flow

```text
User asks about tomorrow's weather
        |
        v
Tomorrow + weather intent detected
        |
        v
Resolve device location, explicit location, or default
        |
        v
Open-Meteo geocoding if needed
        |
        v
Request two days of daily forecast data
        |
        v
Select index 1 as tomorrow
        |
        v
Return verified forecast response
```

### Example supported prompts

```text
What is the weather going to be like tomorrow?
```

```text
What is the weather going to be like tomorrow in Beech Grove, Indiana 46107?
```

### Verified behavior

- Beech Grove, Indiana forecast worked through the API.
- Beech Grove, Indiana forecast worked through the Angel Platform UI.
- New York, NY default forecast worked through the Angel Platform UI.
- The temperature degree symbol displays correctly as `°F`.

---

## 9. Open-Meteo Integration

The current live weather integration uses Open-Meteo endpoints.

### Geocoding endpoint

```text
https://geocoding-api.open-meteo.com/v1/search
```

Used to resolve a named location into latitude and longitude.

### Forecast endpoint

```text
https://api.open-meteo.com/v1/forecast
```

Used for current conditions and daily forecast data.

### Current weather fields

The current weather route requests values including:

```text
temperature_2m
relative_humidity_2m
apparent_temperature
weather_code
wind_speed_10m
```

### Daily forecast fields

The tomorrow forecast route requests values including:

```text
temperature_2m_max
temperature_2m_min
weather_code
precipitation_probability_max
wind_speed_10m_max
```

### Reliability rule

Live information should come from the provider-backed deterministic route whenever the request matches a supported live-information pattern.

Ollama should not be relied upon to invent current weather, forecast values, or live timestamps.

---

## 10. User Interface Architecture

The current Angel Platform UI includes:

- Angel Platform branding
- Dark visual theme with blue accents
- Just Chat area
- Local Ollama model selector
- ChatGPT, OpenRouter, and Custom options in the interface
- Projects navigation
- Modules navigation
- System Tools navigation
- DevOps navigation
- Memory navigation
- Settings navigation
- Conversation history
- Angel Nexus dashboard
- Live monitor area
- System health card
- Registered modules card
- AI engine status card
- Quick Actions
- Recent Activity
- Read-aloud controls
- Message copy controls
- Voice and attachment controls

The UI was visually verified in the Windows environment during Repair Mode testing.

---

## 11. Current AI and Conversation Design

### Just Chat

The current primary conversational interface is intended for:

- Normal conversation
- Questions and explanations
- Planning
- Creative work
- General assistant interaction
- Natural-language requests

### Planned Sys Chat

The intended Sys Chat lane is designed for:

- Windows administration
- Linux administration
- Troubleshooting
- Diagnostics
- Module discovery
- Script preparation
- Tool execution planning
- Approval-controlled actions
- Structured technical responses

### Design principle

The system should preserve a clear separation between:

```text
Normal conversation
```

and:

```text
System administration and executable actions
```

The deterministic route layer should handle verified application actions, while Ollama handles ordinary conversational responses when no deterministic route applies.

---

## 12. Safety and Execution Model

The current interface displays approval-related status, including:

```text
Execution: Approval required
```

The architecture should continue to use an approval-controlled approach for actions that can modify the system.

Recommended separation:

```text
Read-only inspection
        |
        v
Explain intended action
        |
        v
Request approval when required
        |
        v
Execute only approved action
        |
        v
Report result and errors honestly
```

No future feature should claim that an action succeeded before the underlying operation confirms success.

---

## 13. Validation and Testing

### Syntax validation

```powershell
python -m py_compile .\angel_platform\webui\server.py
```

The syntax check passed during this checkpoint.

### API validation

The `/api/chat` endpoint was tested on port `8765`.

Verified API behavior included:

- Current weather for Beech Grove, Indiana.
- Tomorrow forecast for Beech Grove, Indiana.
- Default tomorrow forecast for New York, NY.
- Correct Fahrenheit degree-symbol display.

### UI validation

The same forecast behavior was tested through the Windows Angel Platform interface in Repair Mode.

### Process and port checks

Port `8765` is the active development port. If startup exits immediately, inspect existing processes using:

```powershell
Get-NetTCPConnection -LocalPort 8765 -ErrorAction SilentlyContinue
```

Identify a listening process with:

```powershell
Get-Process -Id <PID>
```

Only stop a process after confirming it belongs to the old Angel session or another process that can safely be closed.

---

## 14. Known Architecture Limitations

The following areas are not yet complete:

- Hourly forecast support.
- Severe weather alert integration.
- Natural-language forecast summaries.
- Readable date formatting.
- Better timezone presentation.
- Multi-day forecast handling.
- Stronger location context retention.
- More complete weather intent classification.
- Unit tests for location parsing.
- Structured provider-error logging.
- Full separation and dedicated UI behavior for Just Chat and Sys Chat.
- Final executable packaging after all repairs are complete.

The current architecture document describes the known and verified state. It should be updated whenever a structural change is confirmed.

---

## 15. Recommended Next Architecture Improvements

### Priority 1: Weather routing quality

- Add explicit intent functions for current weather, tomorrow weather, hourly weather, and multi-day weather.
- Prevent current-weather routing from intercepting tomorrow-forecast prompts.
- Improve location extraction for ZIP codes and city/state combinations.
- Format dates in a human-readable way.
- Add provider response validation.

### Priority 2: Conversation context

- Preserve the last confirmed location during the active conversation.
- Make context retention explicit and visible.
- Avoid silently reusing stale locations across unrelated conversations.
- Allow the user to override the current location naturally.

### Priority 3: Just Chat and Sys Chat

- Define separate UI lanes.
- Define separate system prompts.
- Share only the memory and project context that is appropriate.
- Keep system actions approval-controlled.
- Add clear status indicators for the active lane.

### Priority 4: Testing

- Add unit tests for intent detection.
- Add location extraction tests.
- Add provider response tests.
- Add route-order tests.
- Add UI smoke tests for common prompts.
- Add safe failure tests for unavailable providers.

---

## 16. Architecture Principles

1. **Local-first:** Prefer local services and local model inference where practical.
2. **Transparent:** Tell the user when information comes from a provider, model, or local application route.
3. **Deterministic when needed:** Use verified handlers for live data and system operations.
4. **Approval-controlled:** Require approval for actions that can change the system.
5. **Test-driven repair:** Make small changes and test each change.
6. **Preserve working builds:** Do not replace the packaged executable during Repair Mode.
7. **Honest failures:** Never claim an operation succeeded without confirmation.
8. **Modular growth:** Keep weather, diagnostics, modules, memory, and AI routing separable.
9. **User control:** Keep the user informed about location use, actions, and execution behavior.
10. **Document checkpoints:** Record the verified state before ending a work session.

---

## 17. Current Leave-Off State

```text
Version checkpoint:
v3.2.5-repair-weather-forecast

Working:
- Python source launcher
- Repair Mode
- pywebview desktop UI
- Local Ollama connection
- Angel Nexus dashboard
- Current weather route
- Tomorrow forecast route
- Beech Grove weather lookup
- New York default location
- Correct °F encoding
- API and UI verification

Preserved:
- Existing Windows EXE
- RUN_WINDOWS.bat
- Source-based development workflow

Not yet finalized:
- Hourly forecasts
- Alerts
- Advanced location context
- Dedicated Sys Chat lane
- Final executable rebuild
```

---

## 18. Continuation Prompt

Copy this prompt into the next development session:

```text
Continue development of Angel Platform 3.2.5 from the current architecture checkpoint.

Project path:
D:\angel-platform-3.2.5

Checkpoint:
v3.2.5-repair-weather-forecast

Current architecture:
- Python source launcher through run_angel_platform.py
- angel_platform/app.py starts the server and pywebview UI
- HTTP server runs at 127.0.0.1:8765
- Main chat endpoint is /api/chat
- Local Ollama is connected
- Repair Mode is the active development workflow
- RUN_WINDOWS.bat and the existing EXE must remain preserved
- RUN_REPAIR_MODE.bat launches the source version
- Current weather lookup is deterministic and provider-backed
- Tomorrow forecast lookup is deterministic and provider-backed
- Open-Meteo is the weather provider
- New York, NY is the default weather location
- Beech Grove, Indiana 46107 has been tested successfully
- The °F encoding issue has been fixed
- The Windows UI has been tested successfully

Before making changes:
1. Inspect the actual source code.
2. Do not invent file paths, functions, or results.
3. Explain the intended change in plain language.
4. Back up important files.
5. Make one controlled change.
6. Run syntax validation.
7. Restart Repair Mode.
8. Test through the actual Angel Platform UI.
9. Confirm the result before continuing.

Potential next work:
- Improve weather response formatting.
- Add hourly forecasts.
- Add severe weather alerts.
- Improve location context.
- Expand deterministic live-information routing.
- Continue designing separate Just Chat and Sys Chat lanes.

Keep Angel local-first, transparent, modular, and approval-controlled.
```

---

## Document Status

This document reflects the current known architecture at the `v3.2.5-repair-weather-forecast` checkpoint.

It is an architecture snapshot, not a claim that every planned feature is complete.
