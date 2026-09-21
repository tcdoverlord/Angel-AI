# Angel Platform 3.3.0

## Full Foundation Build

- Preserves the existing Angel Platform UI and unified chat experience.
- Loads persistent server chat history from `/api/history` at startup.
- Recovers server history into a dedicated `Recovered Angel History` conversation.
- Updates the current local conversation instead of creating a duplicate record after every response.
- Raises local conversation retention from 30 to 100 records.
- Keeps deterministic application routes for date/time and weather in the existing backend.
- Preserves approval-controlled Nexus actions and existing module workflows.

## Installation

This package is a source upgrade for the existing project. Backups are created by the installer before replacing files. Test source mode first, then build the Windows EXE.
