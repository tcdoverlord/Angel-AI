# Angel Platform 3.2.5

- Fixed combined date/time + weather requests being handled by the local model.
- Weather intent no longer requires words such as "today" or "current".
- Combined requests now return the authoritative application clock and verified Open-Meteo conditions.
- No default city is assumed.
- Device/browser location is attempted for weather requests without an explicit place.
- If location permission is unavailable, Angel asks for a city, state, or ZIP code.
