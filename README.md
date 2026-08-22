# Angel AI

## v0.01 Genesis Stable

A small, local-first AI assistant built around Ollama.

Angel is intentionally starting clean.

The Genesis build provides:

- Local Ollama conversation
- A simple terminal interface
- Deterministic date/time capability
- Deterministic current-weather capability
- Combined date/time + weather routing
- Configurable Ollama model
- Configurable location
- Simple capability routing
- Linux-friendly Python architecture
- Windows compatibility
- No cloud AI dependency for normal conversation

The goal of Genesis is not to be large.

The goal is to create a small, understandable, reliable foundation that can grow
into a more capable modular assistant without rebuilding the core.

---

## Architecture

```text
                         ┌─────────────────┐
                         │      User       │
                         └────────┬────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │   Angel CLI     │
                         └────────┬────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │   Angel Brain   │
                         └────────┬────────┘
                                  │
                         ┌────────┴────────┐
                         │                 │
                         ▼                 ▼
                  ┌──────────────┐  ┌──────────────┐
                  │    Router    │  │    Ollama    │
                  └──────┬───────┘  │ Local LLM    │
                         │          └──────────────┘
                    ┌────┴────┐
                    │         │
                    ▼         ▼
              ┌──────────┐ ┌──────────┐
              │ Date/Time│ │ Weather  │
              └──────────┘ └──────────┘