# Angel Platform 3.2.3

## Focused reliability improvement: authoritative date and time

- Angel's application clock is authoritative for local date, time, timezone, and weekday.
- The model is explicitly instructed not to recalculate weekdays from memory or UTC.
- Deterministic date/time responses remain enabled before the Ollama response path.
- Existing Read Aloud / speech code was not intentionally modified.
- No framework migration or starter-kit dependency was added.


## Persistent user data

- Persistent data now lives under `Path.home() / "Angel_Platform"` (Windows: `C:\Users\<current-user>\Angel_Platform`).
- Chat history, activity, module state, backups, secure data, logs, and workspaces survive new source folders and rebuilt EXEs.
- A first-run migration copies legacy JSON data from the prior build's local `data` folder when the persistent file does not already exist.
