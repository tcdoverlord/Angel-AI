# Angel Genesis V1.1

**Genesis V1.1 — 2026-08-19**

Genesis is the modular brain-cell layer for Angel. It is introduced beside the proven
`angel/brain.py`; it does **not** replace the legacy brain yet.

## Architecture

- `angel/genesis_brain.py` — coordinator and planning boundary.
- `angel/neurons/` — specialized intent cells.
- `angel/synapses/router.py` — controlled intent-to-capability connections.
- Existing `angel/tools.py` — proven execution layer.
- Existing `angel/brain.py` — preserved recovery/legacy brain.

## First cell

`DateTimeNeuron` recognizes common date/time requests and emits the existing
`current_datetime` `ToolRequest`. It does not read the clock itself and does not
ask Ollama to invent a current value.

Execution remains outside Genesis. The existing ToolLoop and `current_datetime`
tool remain responsible for performing the actual capability.

## Safety boundary

Genesis neurons may only return `ToolRequest` objects. The router does not execute
tools, modify application state, or provide arbitrary tool access.

This first package deliberately does not wire Genesis into the application runtime.
That should happen only after its tests and an integration checkpoint are verified.

## Recovery

The existing `angel/brain.py` remains untouched by this package and is the fallback
brain until Genesis has demonstrated equivalent or better behavior through integration
tests.
