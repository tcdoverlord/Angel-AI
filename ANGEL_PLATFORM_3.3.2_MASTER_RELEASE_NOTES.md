# Angel Platform 3.3.2 — Intelligence Core Expansion

This release preserves the Angel Platform 3.3.1 Master Intelligence baseline and adds an integrated local knowledge expansion.

## Included
- Expanded procedural knowledge library for Windows, Linux, Python, networking, AI, Angel workflows, Git, Docker, and Raspberry Pi.
- Interaction patterns for acknowledgement, plain-language explanations, correction handling, evidence discipline, approval gates, and user-led pacing.
- Knowledge search and context injection through the existing `angel_platform.knowledge.library` integration.
- Knowledge and feedback API support retained from the 3.3.2 intelligence core work.
- Existing persistent history, module library, safe execution, web search, and UI assets preserved.

## Design boundary
This is retrieval and prompt-context growth, not model-weight fine-tuning. The local model still determines the final response, while the knowledge library supplies relevant guidance and procedures.

## Validation
Run:
```powershell
.\.venv\Scripts\python.exe -m compileall -q angel_platform run_angel_platform.py
.\.venv\Scripts\python.exe -m pytest -q
```
