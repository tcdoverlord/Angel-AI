# Angel Platform 3.2.3

## Cooperative Angel Core

- Removed the obsolete broad live-data interception and its `LIVE DATA REQUEST DETECTED` response.
- Normal conversation, including weather/news/current-event discussion, now reaches the configured AI model.
- Added a lightweight cooperative lane selector: `fast`, `balanced`, or `deep`.
- Lane selection is a routing hint inside the shared Angel conversation; it does not require extra models and cannot interrupt the core.
- Preserved verified deterministic routes for application actions and date/time.
- Preserved the existing speech/read-aloud implementation.
- No new framework dependency was introduced.

## Scope

This release adds the coordination foundation without pretending that separate model workers or a web provider already exist. Those can be added later behind tested fallbacks.
