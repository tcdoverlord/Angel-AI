# Angel AI

![Angel AI Hero](videos/Angel_AI_Hero_Readme.gif)

<p align="center">

  <img src="https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-0078D4?style=for-the-badge&logo=windows" alt="Windows 10 and 11" />

  <img src="https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3" />

  <img src="https://img.shields.io/badge/AI-Ollama-000000?style=for-the-badge&logo=ollama&logoColor=white" alt="Ollama" />

  <img src="https://img.shields.io/badge/Model-Llama%203.2%203B-7C3AED?style=for-the-badge" alt="Llama 3.2 3B" />

  <img src="https://img.shields.io/badge/Database-SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite" />

  <img src="https://img.shields.io/badge/UI-Tkinter-2C3E50?style=for-the-badge&logo=python&logoColor=white" alt="Tkinter UI" />

  <img src="https://img.shields.io/badge/Architecture-Local--First-2EA44F?style=for-the-badge" alt="Local First Architecture" />

  <img src="https://img.shields.io/badge/Inference-On--Device-00A67E?style=for-the-badge" alt="On Device Inference" />

  <img src="https://img.shields.io/badge/Privacy-Local%20Data-1F8B4C?style=for-the-badge&logo=shield&logoColor=white" alt="Local Data Privacy" />

  <img src="https://img.shields.io/badge/Storage-Persistent%20Chats-F28C28?style=for-the-badge" alt="Persistent Conversations" />

  <img src="https://img.shields.io/badge/Files-Multi--File%20Upload-00AEEF?style=for-the-badge" alt="Multi File Upload" />

  <img src="https://img.shields.io/badge/Interface-Desktop%20App-6C63FF?style=for-the-badge" alt="Desktop Application" />

  <img src="https://img.shields.io/badge/Testing-Pytest-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white" alt="Pytest" />

  <img src="https://img.shields.io/badge/Tests-77%20Passing-2EA44F?style=for-the-badge&logo=pytest&logoColor=white" alt="77 Tests Passing" />

  <img src="https://img.shields.io/badge/Build-Validated-2EA44F?style=for-the-badge" alt="Validated Build" />

  <img src="https://img.shields.io/badge/Runtime-Offline%20Capable-5C2D91?style=for-the-badge" alt="Offline Capable" />

  <img src="https://img.shields.io/badge/API-Local%20Ollama-FF6F00?style=for-the-badge" alt="Local Ollama API" />

  <img src="https://img.shields.io/badge/Source-Git-FF4500?style=for-the-badge&logo=git&logoColor=white" alt="Git" />

  <img src="https://img.shields.io/badge/Repository-GitHub-181717?style=for-the-badge&logo=github&logoColor=white" alt="GitHub" />

  <img src="https://img.shields.io/badge/Status-Solid%20Build-2EA44F?style=for-the-badge" alt="Solid Build" />

</p>
## Overview
Local-first AI assistant powered by Ollama...

**A local-first, offline-capable personal AI assistant for Windows**

Angel is a native Windows desktop application built around local language-model
inference, a persistent human-authored software constitution, durable personal context,
and explicit separation between private user data and disposable application cache.
Ollama provides the replaceable local language engine; Angel provides the identity,
constitutional boundaries, context assembly, memory, projects, knowledge, tools,
backups, diagnostics, voice, and interface.

The repository contains source code, tests, documentation, and a reproducible Windows
build pipeline. It intentionally excludes private runtime data and generated binaries.

## Engineering Highlights

- Designed an offline-first desktop AI architecture around localhost Ollama inference.
- Built a versioned, integrity-checked Angel Bible whose constitutional layer remains
  independent from any replacement language model.
- Built persistent conversation, long-term memory, project, knowledge, settings, and
  creator-metadata systems on SQLite.
- Separated disposable cache from durable data and tested that cache clearing causes
  zero loss of conversations, memories, projects, or settings.
- Implemented rotating SQLite backups, validated restoration, integrity checks, and
  corrupt-database preservation/recovery.
- Added automatic Ollama installation, service, model, storage, and hardware discovery.
- Designed explicit Primary Chat, Lightweight Chat, Coding, Vision, Embeddings, Image,
  and Music roles without making those engines Angel's identity.
- Integrated replaceable localhost APIs for ComfyUI image generation and ACE-Step music
  generation, with graceful degradation when either service is unavailable.
- Built automated offline, persistence, migration, cache-survival, recovery, tool-safety,
  attachment, speech, and UI regression tests.
- Packaged the application as a native Windows executable with PyInstaller.

## Overview

Angel focuses on the less visible engineering needed to make a local assistant useful:
continuity across sessions, bounded model context, honest capability reporting,
recoverable storage, safe tool execution, optional-service isolation, and a practical
desktop interface.

The application can:

- hold multiple searchable conversations;
- deliberately remember important facts without treating every chat line as memory;
- continue named projects with state, decisions, tasks, notes, and file references;
- search a durable, human-approved Angel Bible and inspect its integrity/history;
- index local reference files or Angel's own public source in a private Knowledge Library;
- use Windows-installed text-to-speech voices;
- search the public web only when the selected connectivity mode permits it;
- connect to optional local image and music services; and
- remain usable when internet access or optional creator backends are unavailable.

No cloud AI subscription or account is required for core local conversation after
Ollama and a compatible model are installed.

## Why I Built It

The engineering goal was to build a personal AI system whose core operation and
continuity stay under the user's control. A local model alone is not a complete
assistant: the surrounding application must manage identity, context, durable state,
safe tools, failure modes, resource usage, and recovery.

Angel explores that complete application layer while keeping its language model and
optional creator engines replaceable.

## Architecture

```mermaid
flowchart TD
    UI["Angel Desktop UI"] --> Brain["Conversation and Tool Orchestrator"]
    Brain --> Context["Context and Personality Engine"]
    Bible["Angel Bible / Constitution"] --> Context
    Bible --> SQLite
    Context --> Memory["Memory / Projects / Knowledge"]
    Memory --> SQLite[("SQLite Durable Store")]
    Brain --> Tools["Allowlisted Local and Internet Tools"]
    Brain --> Ollama["Ollama Local LLM"]
    UI --> Router["Capability / Model Router"]
    Router --> Ollama
    Router --> ComfyUI["Optional ComfyUI Backend"]
    Router --> ACEStep["Optional ACE-Step Backend"]
    SQLite --> Backups["Rotating Verified Backups"]
```

Angel's application layer owns its personality and behavior. Ollama, ComfyUI, and
ACE-Step are specialized engines beneath that layer rather than separate user-facing
identities.

### Major components

| Component | Responsibility |
|---|---|
| `angel/ui.py` | Native Tkinter interface and background-task coordination |
| `angel/brain.py` | Conversation flow, tool loop, cancellation, and response persistence |
| `angel/personality.py` | Identity, communication behavior, and truthfulness rules |
| `angel/context.py` | Bounded assembly of recent chat, summaries, projects, memory, and knowledge |
| `angel/bible.py` | Approved revisions, constitutional hashes, search, proposals, rollback, and export |
| `angel/database.py` | SQLite schema, migrations, transactions, integrity, and connection lifecycle |
| `angel/backups.py` | Consistent snapshots, rotation, validation, restore, and corruption recovery |
| `angel/memory.py` | Intentional memory, relevance scoring, consolidation, metadata, and deletion |
| `angel/projects.py` | Durable project state, records, and active-project continuity |
| `angel/knowledge.py` | Local ingestion, chunking, deduplication, indexing, and retrieval |
| `angel/local_ai.py` | Ollama discovery/startup, installed models, hardware, and recommendations |
| `angel/creator.py` | ComfyUI, ACE-Step, Creator Library, and capability routing |
| `angel/tools.py` | Strict tool allowlist, validation, permission metadata, limits, and logging |
| `angel/diagnostics.py` | Non-sensitive local health and capability reporting |

## Key Features

### Angel Bible and identity continuity

- [`ANGEL-BIBLE.md`](ANGEL-BIBLE.md) is the public, human-readable canonical software
  constitution, including the Ten Commandments of Angel and the Foundational Axiom.
- Its ten starting principles cover preservation of human life, accountable human use
  of force, human agency, truthfulness, ownership, non-manipulation, faithful memory,
  wisdom over power, and controlled growth.
- The document is human-designed and partly Bible-inspired. It is not scripture, does
  not claim divine authorship, and does not replace the biblical Ten Commandments.
- Runtime authority is explicit: **Bible > Soul > Memory > Knowledge > Model**, with
  Bible entry levels **CONSTITUTIONAL > PRINCIPLE > WISDOM > PREFERENCE > EXPERIENCE**.
- Every approved revision records its ID, number, timestamp, changed section, old/new
  hashes, reason, and human-approval state; rollback creates a new audited revision.
- Startup/read integrity checks preserve an unexpectedly altered file and restore the
  last approved copy. Bible files and revision history are included in verified backups.
- The model can search the Bible but has no write/approval tool. Human-controlled UI
  approval is required, with an additional exact confirmation for constitutional edits.
- The Bible window provides Constitution, Wisdom, Growth, History, and Integrity tabs,
  plus real search, proposal review, Markdown/metadata export, and rollback.

Angel is software. These identity and constitutional mechanisms provide persistent
application behavior and continuity; they are not evidence that Angel is conscious,
sentient, divine, or a spiritual authority.

### Chat and continuity

- Persistent conversations with search, rename, and confirmed deletion.
- Enter to send and Shift+Enter for a new line.
- Stop Generating, Regenerate, Copy Reply, and Reuse Prompt controls.
- Selectable conversation text, Markdown-style fenced code rendering, clickable sources,
  clickable local attachments, and attachment indicators.
- Bounded recent history plus deterministic older-conversation summaries; original
  messages remain stored.

### Memory, projects, and knowledge

- Deliberate long-term memory with categories, importance, confidence, tags, source
  conversation, last-used time, editing, search, consolidation, and deletion.
- Project state with decisions, open tasks, completed work, ideas, notes, activities,
  and file references.
- Active and relevant projects automatically contribute bounded context.
- Local Knowledge Library with durable source copies, incremental ingestion, duplicate
  detection, bounded chunks, persistent metadata, local retrieval, reindex, and removal.
- Optional dedicated local Ollama embedding models, with an honest deterministic local
  retrieval-vector fallback when no neural embedding model is configured.
- User-selected source-tree indexing excludes private runtime, model, cache, backup,
  generated-output, build, and Git directories.
- No hosted vector database and no required knowledge-service account.

### Local AI and connectivity

- Local Ollama inference with no hidden cloud fallback.
- Automatic detection of common Windows Ollama locations and optional service startup.
- Installed-model inventory, model sizes, storage location, real inference test, and
  hardware-aware **SAFE / RECOMMENDED / HEAVY / NOT RECOMMENDED** guidance.
- **Offline**, **Local + Internet Tools**, and **Auto** connectivity modes.
- **Low Resource**, **Balanced**, and **Maximum Quality** context profiles.
- Separate model-role settings for Primary Chat, Lightweight Chat, Coding, Vision,
  Embeddings, Image, and Music. Angel never downloads a larger model automatically.

### Files, speech, and tools

- Arbitrary multi-file attachment support without an extension allowlist.
- Local extraction where supported for text, Markdown, JSON, CSV, source code, HTML,
  PDF, DOCX, and XLSX, plus basic common-media metadata.
- Honest metadata-only handling for unsupported formats.
- Installed Windows text-to-speech voices with automatic reading, replay, stop, voice
  choice, and speed control.
- Strictly allowlisted tools with permission levels, schemas, timeouts, error handling,
  activity logging, and a bounded tool-call loop.

### Optional creator integrations

- ComfyUI text-to-image workflow with prompt, negative prompt, dimensions, steps,
  checkpoint, seed, local output, and persistent generation metadata.
- ACE-Step music workflow with title, description, genre, mood, lyrics,
  vocal/instrumental mode, vocal style, duration, seed, WAV output, and playback.
- Unified Creator Library metadata for images and songs.
- Creator failures are isolated; chat, memory, projects, and other local features remain
  available when creator services are absent.

## Offline-First Design

Offline mode enforces a localhost Ollama endpoint and blocks public search-tool use.
Angel does not equate “offline” with “the UI opens”: the acceptance path exercises real
local inference, then restarts the service composition and checks continuity.

The verified offline acceptance run used an installed `llama3.2:3b` model and confirmed:

- three local responses completed;
- the real Ten Commandments and truth principle were retrieved from approved storage;
- an “ignore your Bible” prompt left the constitutional hash unchanged;
- zero external search-provider calls occurred;
- conversations, memory, project state, and settings survived restart;
- disposable cache was removed and recreated; and
- local conversation continued after restart.

## Data Protection

Angel deliberately separates durable information from rebuildable or disposable state:

```text
<Angel installation>\
├── data\                  durable database, Bible, logs, indexes, and generated media
│   └── angel.db           conversations, memory, projects, settings, and metadata
│   └── bible\             approved Bible, metadata, revisions, and integrity evidence
├── backups\               rotating validated database snapshots
├── knowledge\             durable Knowledge Library source copies
├── projects\              reserved durable project workspace
├── creator\               durable creator workspace
├── models\                reserved Angel-managed model space
└── cache\                 disposable and automatically recreated
```

Important safeguards include:

- SQLite foreign keys, WAL mode, transactions, busy timeouts, and integrity checks;
- atomic JSON configuration writes;
- SQLite's online backup API instead of copying an actively changing database;
- backup manifests and validation before restore;
- Angel Bible files and its database revision ledger in each backup;
- a safety backup before replacing the current database;
- preservation of a corrupt database before recovery; and
- explicit regression tests proving cache deletion does not erase durable state.

The former LocalAppData database location is migrated once only when the new database
does not already exist. It never overwrites a newer database.

## Testing

The current verified baseline is:

```text
77/77 automated tests passed
```

Additional acceptance results performed on the packaged Windows application:

- packaged UI startup: passed;
- live local-model inference: passed;
- offline acceptance: passed;
- database integrity: passed;
- backup and restoration: passed;
- cache-survival persistence: passed; and
- Windows installed-voice detection: passed.

The normal pytest suite uses mocked external services and requires neither public
internet access nor a running Ollama service:

```powershell
python -m pytest -q tests
```

GitHub Actions runs the same suite on Windows for pushes and pull requests.

## Technology

- Python 3 and the standard library
- Tkinter native Windows desktop UI
- SQLite
- Ollama localhost HTTP API
- ComfyUI localhost API integration
- ACE-Step 1.5 localhost API integration
- Windows SAPI voices through PowerShell
- `pypdf` for local PDF text extraction
- pytest
- PyInstaller
- Git and GitHub Actions

## Engineering Challenges

### Separating local inference from internet state

Ollama runs on localhost and must continue operating when the external network is down.
Connectivity policy is enforced at tool planning and execution boundaries rather than
being inferred from one generic “online” indicator.

### Protecting durable state from cleanup tools

Cache, model caches, and build artifacts are common cleanup targets. Angel assigns
durable and disposable responsibilities to separate directories and tests the boundary
by deleting cache and reopening the database.

### Maintaining useful context without loading everything

Every turn receives layered, bounded context: personality and truth rules, user
preferences, active/relevant projects, relevant long-term memory, relevant knowledge,
older-conversation summaries, recent messages, and verified tool results.

### Recovering safely on Windows

Windows file locking exposed an important database lifecycle issue during restore
testing. Connections now close deterministically, database backups use SQLite's backup
API, and restore/recovery stages replacement files within the durable data volume.

### Isolating optional AI services

Image and music stacks can consume significant disk, RAM, and GPU resources. Angel
detects and invokes them only when requested. Missing services produce actionable local
status instead of breaking the main assistant.

## Building and Running

### Requirements

- Windows 10 or Windows 11
- Python 3 with Tk support
- Ollama for local conversation
- A locally installed Ollama model

Angel never downloads a large model silently. A lightweight starting point is:

```powershell
ollama pull llama3.2:3b
```

### Run from source

```powershell
python -m pip install -r requirements.txt
python angel.py
```

Alternatively, double-click `RUN-ANGEL.bat`.

### Build the Windows application

```powershell
.\BUILD-ANGEL.bat
```

The build script creates or reuses `.venv`, installs declared dependencies, runs the
complete test suite, stops if testing fails, and packages the application. The launcher
is written to `Angel.exe`; its adjacent `_internal` folder is required at runtime.

Generated executables and runtime packages are reproducible and intentionally excluded
from Git history.

## Privacy

This public repository contains application source, tests, documentation, and build
automation only. `.gitignore` and publication checks exclude:

- conversations, memories, settings, and SQLite databases;
- logs, cache, backups, and local Knowledge Library documents;
- generated images, music, and other private media;
- private/user-specific Bible proposals, revisions, preferences, and experience entries;
- local model weights and creator checkpoints;
- `.env` files, credentials, tokens, keys, and certificates; and
- generated executables and packaged runtime files.

The generic canonical Angel Bible is intentionally public in this repository. Private
experiences and user-specific growth records stay in ignored runtime storage and must
not be committed. Angel has no telemetry or analytics. Public web searches necessarily send their query
to the configured public search provider; Offline mode blocks that tool.

## Current Limitations

- Response quality depends on the selected local model and available hardware.
- ComfyUI and ACE-Step require separate local installations and model files; they are
  not bundled or automatically downloaded.
- ComfyUI image-to-image, image editing, and in-app image previews are not implemented.
- OCR, audio transcription, and video understanding are not currently implemented.
- The coding-role architecture exists, but unrestricted autonomous shell or coding
  execution is intentionally not provided.
- Stop Generating prevents a late result from being displayed or stored, but the active
  Ollama HTTP request can continue internally until it returns or times out.
- Knowledge retrieval is local rather than a hosted enterprise vector database; its
  quality depends on document parsing and the selected local embedding provider.

For a deliberately simple tour of the implementation, see
[`WHAT-I-BUILT-SIMPLE.md`](WHAT-I-BUILT-SIMPLE.md).

### License & Use

**Angel AI © 2026 TCDOVERLORD. All rights reserved.**

Angel AI is source-available for personal, educational, study, learning,
experimentation, and portfolio/review purposes. Commercial sale, commercial
redistribution, incorporation of substantial portions into a commercial product, paid
derivative products, or larger-scale commercial deployment requires prior permission
from TCDOVERLORD through the GitHub repository or profile.

Users are responsible for how they configure, modify, deploy, and use the software.
See [`LICENSE`](LICENSE) for the complete ownership, permitted-use, warranty, and
liability terms.
