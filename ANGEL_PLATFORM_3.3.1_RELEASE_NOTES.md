# Angel Platform 3.3.1

## Consolidation and capability growth

This release is built from the complete 3.3.0 FULL BUILD. It adds integrated capability services rather than standalone notes:

- `/api/capabilities` exposes a machine-readable capability inventory.
- `/api/search?q=...` provides bounded web search with structured source links.
- `angel_platform.capabilities.grounding` models source-grounded answers.
- `angel_platform.capabilities.audit` provides atomic append-only execution records.
- `angel_platform.capabilities.refresh` defines module refresh events.

## Validation

Compile the package and run the release tests before packaging the Windows executable. Web access is treated as optional and failures are returned explicitly rather than presented as successful results.
