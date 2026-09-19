# Angel Platform 3.1.15 — Stable Focused Repair

- Preserves the existing modular architecture and safety executor.
- Adds a controlled pending-command approval path for supported read-only diagnostics.
- Captures and reports verified execution status, return code, stdout, stderr, and notes.
- Prevents approval without a pending command from executing anything.
- Keeps normal conversation routing separate from actionable system requests.
- Includes regression coverage for execution honesty and approval boundaries.

This release does not claim live weather/news capability unless a verified provider is connected.
