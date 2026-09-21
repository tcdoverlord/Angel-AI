# Angel Platform 3.3.2 — Stability Patch 1

This patch preserves the larger 3.3.2 baseline and addresses observed chat UX and persistence risks.

## Changes
- New chats open completely blank; no automatic Angel greeting is inserted.
- User messages display as `Me` instead of `A You`.
- Recovered server history remains available in the conversation list without being injected into a fresh active chat.
- Active browser conversations are saved after assistant responses.
- Persistent history append operations are protected against concurrent read/modify/write races.
- Knowledge retrieval context window increased from 4 to 6 results.

## Scope
This is a stability and UX patch. It does not claim that local Ollama has human-level reasoning or that persistent history is model training.
