# Angel Platform 3.2.3

- Added a verified Open-Meteo current-weather route for requests containing weather terms and current-time intent.
- Defaults to Beech Grove, Indiana when no location is provided.
- Supports a location after `in`, `near`, or `for`.
- Uses timeouts and safe failure messaging; never fabricates weather data.
- Normal conversation remains routed to Ollama.
