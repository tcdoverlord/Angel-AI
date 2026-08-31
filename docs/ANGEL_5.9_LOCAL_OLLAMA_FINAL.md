# Angel AI 5.9 — Local Knowledge + Ollama

Normal questions always retain access to the local Ollama model.

When relevant local knowledge is retrieved, it is passed to Ollama as additional authoritative context.
When no relevant local knowledge is retrieved, Ollama can answer using its general trained knowledge.
The application—not Ollama—owns GPT identity, retrieval provenance, and source truth.

The runtime uses:
- `dist\\AngelAI.exe`
- `data\\` as the single persistent data location

No launcher or shortcut is required.
