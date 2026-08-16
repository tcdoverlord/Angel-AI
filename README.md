# ANGEL

Angel is a local-first Windows AI companion. The normal launcher is:

```text
D:\Angel_AI\Angel.exe
```

The window, personality, conversations, memory, projects, settings, knowledge library,
creator library, backups, and diagnostics belong to Angel. Ollama is the replaceable
local language engine behind the conversation.

Angel has no account requirement, telemetry, analytics, or tracking. In **Offline**
mode it only permits a localhost Ollama connection and does not run the public search
tool.

## Start here

1. Double-click `D:\Angel_AI\Angel.exe`.
2. Type in the box at the bottom.
3. Press **Enter** to send. Press **Shift+Enter** for a new line.
4. Use **Upload Files** for any file type.
5. Use **Read Last Reply** or enable automatic read-aloud to use installed Windows
   voices.

Angel detects the usual Windows Ollama install locations and can start its local
service. It never silently downloads a model. If no model is installed, open **Setup**
for a clear status and hardware-aware recommendation. The current starter model is
`llama3.2:3b`.

## What is included

- Persistent conversations with search, rename, and confirmed deletion.
- Send with Enter, multiline with Shift+Enter, Stop Generating, Regenerate, Copy Reply,
  and Reuse Prompt.
- Arbitrary multi-file upload with honest local extraction for text, code, Markdown,
  JSON, CSV, HTML, DOCX, XLSX, PDF, and basic media metadata when supported.
- Windows built-in text-to-speech voices, automatic read-aloud, replay, stop, voice
  choice, and speed control.
- Deliberate long-term memory with categories, importance, confidence, edit, search,
  consolidation, and deletion.
- Persistent projects with current state, decisions, tasks, ideas, notes, files, and an
  active-project context.
- A private local Knowledge Library with copied source files, local chunking,
  deduplication, deterministic local retrieval, source display, removal, and reindex.
- Offline, Local + Internet Tools, and Auto connectivity modes.
- Low Resource, Balanced, and Maximum Quality context profiles.
- One More Thing, Make Money, Get Me Out, Build Something, Something Free, and
  Surprise Me quick actions.
- Local diagnostics for database health, paths, backups, cache, Ollama, installed
  models, storage, hardware, creator backends, internet state, and recent errors.
- A local Creator workspace and library for ComfyUI image generation and ACE-Step
  music generation when those optional localhost services and models are installed.
- Daily rotating database backups, manual backups, verified restore, corrupt-database
  preservation/recovery, and safe cache clearing.

## The folders are intentionally separated

```text
D:\Angel_AI\
├── Angel.exe              normal launcher
├── _internal\             packaged runtime files required by Angel.exe
├── data\                  NEVER treat as disposable
│   ├── angel.db           chats, memory, projects, settings, indexes, metadata
│   ├── generated\         generated images and music
│   └── logs\              rotating diagnostic log
├── backups\               rotating verified database backup ZIP files
├── knowledge\             durable copies of Knowledge Library source files
├── models\                Angel-managed model space (not Ollama's own store)
├── projects\              durable project files reserved for project workflows
├── creator\               durable creator workspace
└── cache\                 disposable; Angel recreates it if deleted
```

Deleting `cache` must not delete or reset conversations, memories, projects, settings,
knowledge records, or creator records. Never use cleanup software against `data`,
`backups`, `knowledge`, `projects`, or `creator`.

The former `%LOCALAPPDATA%\Angel\angel.db` is copied into the new `data` folder once if
the new database does not exist. It is never used to overwrite a newer database.

## Memory and projects

Conversation history and memory are separate. Angel only saves a chat detail as a
long-term memory when you explicitly ask (for example, “Remember that…”) or add it in
**Memory**. Memory categories cover people, preferences, dislikes, projects, goals,
tasks, decisions, hardware, software, routines, creative work, ideas, and important
facts.

Projects keep durable state outside one chat. Open **Projects** to create a project,
make it active, update where you left off, and add a decision, task, completed item,
idea, note, file reference, or activity. Angel adds the active or relevant project to
conversation context without stuffing the entire database into each prompt.

## Knowledge Library

Open **Knowledge**, choose one or more files, and Angel copies them into the durable
`knowledge` folder. Supported content is extracted locally, divided into bounded
chunks, and indexed without a cloud account or hosted vector database. Unsupported
formats remain available as honest metadata-only records.

PDF text extraction uses `pypdf`. Image OCR, audio transcription, and video
transcription are not bundled, so Angel does not pretend those operations happened.

## Local AI and connectivity

Open **Setup** to see CPU, RAM, GPU details when Windows reports them, disk space,
Ollama location/state, installed models, model sizes, and Lightweight/Balanced/Powerful
recommendations. You can start or explicitly restart localhost Ollama and run a real
inference test.

Connectivity modes:

- **Offline** — local Ollama only; public search is blocked.
- **Local + Internet Tools** — stays local unless you explicitly ask to search.
- **Auto** — Angel may search when a request clearly needs current information.

Search results are visibly labeled and contain clickable public sources. If searching
fails, Angel says so instead of inventing current results.

## Image generation

Angel uses an optional local ComfyUI server, defaulting to
`http://127.0.0.1:8188`. It detects the server and available checkpoints, submits a
standard text-to-image workflow, waits for completion, downloads the result locally,
and stores generation metadata in the Creator Library.

If ComfyUI or a checkpoint is missing, Angel shows a setup/unavailable message and the
rest of the app continues normally. Angel does not silently install ComfyUI or large
image models.

## Music generation

Angel uses an optional local ACE-Step API server, defaulting to
`http://127.0.0.1:8001`. The Creator screen supports prompt, lyrics, duration,
instrumental mode, seed, model, generate/regenerate, WAV playback/stop, local save,
and Creator Library metadata.

If ACE-Step or its model is absent, Angel reports that honestly. It does not silently
install or download the large music stack.

## Backups and recovery

Open **Backups** to create a backup, inspect backup status, restore a selected backup,
open the backup folder, or clear only cache. Angel also makes a startup backup when the
newest one is more than a day old and rotates old backups.

A backup uses SQLite's consistent backup API, includes a manifest and settings
snapshot, and is validated before it can restore. Restore creates a safety backup
first. If startup finds a corrupt database, the bad file is preserved with an
`angel.corrupt-...db` name and the newest valid backup is restored when available.

Ollama model blobs and generated media files are deliberately not duplicated into each
database backup. Their Angel metadata is backed up; source/generated files should also
be included in normal disk backup if they matter to you.

## Build from source

Double-click `BUILD-ANGEL.bat`, or run it in a terminal. It creates `.venv`, installs
the small Python/build dependencies, runs every automated test, stops on failure,
packages a windowed executable, and places the launcher at both
`dist\Angel\Angel.exe` and the project root `Angel.exe`. Keep the adjacent `_internal`
runtime folder beside the executable.

To run source directly, double-click `RUN-ANGEL.bat` or run:

```powershell
python angel.py
```

For a real local acceptance check:

```powershell
python angel.py --data-dir .\data\acceptance --acceptance-test --live-model
python angel.py --data-dir .\data\offline-acceptance --offline-acceptance
```

The normal automated suite is fully offline and uses no live model or public internet:

```powershell
python -m pytest -q tests
```

## Developer map

```text
angel.py                  entry point
BUILD-ANGEL.bat           test + package pipeline
Angel.spec                PyInstaller windowed build
angel/app.py              composition and acceptance checks
angel/ui.py               native Tkinter interface
angel/brain.py            response/tool orchestration and cancellation
angel/personality.py      identity, behavior, and truthfulness layers
angel/context.py          bounded chat/memory/project/knowledge context
angel/database.py         schema, migrations, SQLite safety, integrity
angel/backups.py          backups, rotation, restore, corruption recovery
angel/memory.py           durable intentional memory
angel/projects.py         project continuity
angel/knowledge.py        local file library, chunking, and retrieval
angel/attachments.py      arbitrary upload preparation and extraction
angel/local_ai.py         Ollama startup, status, hardware, recommendations
angel/creator.py          ComfyUI, ACE-Step, creator library, model router
angel/diagnostics.py      local health report
angel/tools.py            strict allowlisted tools and permissions
angel/search.py           normalized safe public search
angel/speech.py           Windows installed voice support
angel/paths.py            authoritative durable/disposable folder layout
tests/                    regression and protection tests
```

## Honest limitations

- Conversation quality is limited by the selected local Ollama model and available
  hardware. A small model will not match a frontier cloud model on every task.
- Stop Generating prevents a late result from being stored or shown, but the current
  Ollama HTTP request may continue internally until it returns or times out.
- ComfyUI and ACE-Step are real localhost integrations, but their separate servers and
  model files must already be installed and running.
- There is no automatic large model download, plugin marketplace, unrestricted shell,
  arbitrary code execution, browser/computer control, purchasing, posting, emailing,
  password access, cookie access, or hidden cloud fallback.
- Knowledge retrieval is intentionally lightweight and local; it is not a hosted
  enterprise vector database.

For a deliberately simple explanation of the implementation, read
[`WHAT-I-BUILT-SIMPLE.md`](WHAT-I-BUILT-SIMPLE.md).
