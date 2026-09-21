# Angel Platform 3.3.3 — Persistent Intelligence Database

## Purpose

3.3.3 extends the verified 3.3.2 stability baseline with a local SQLite persistence layer and additional operational knowledge field guides. The goal is stronger continuity without replacing the existing JSON compatibility files or removing the existing UI and module catalog.

## Included

- SQLite database under the user's `Angel_Platform` data directory.
- Conversations and messages with timestamps and conversation IDs.
- Approved-memory records with approval and deletion flags.
- Feedback records separate from long-term memory.
- Tool audit records for future and existing execution adapters.
- One-time import of legacy `chat_history.json` when the database has no messages.
- JSON history retained as a compatibility and recovery copy.
- Additional Windows, Linux, networking, Git, Ollama, RAG, memory, safety, Raspberry Pi, database, feedback, and recovery guides.
- Database unit tests and existing regression tests.

## Honest scope

SQLite improves persistence and organization; it does not train model weights or guarantee that an Ollama model will reason correctly. The current release keeps JSON compatibility because migration and rollback must be verified before old storage is retired.
