# ANGEL

**Local Personal AI**

Angel is a local-first Windows companion built to help you think, remember, search,
decide, and figure out what to do next. The desktop interface, conversation history,
intentional memory, settings, and recommendation history remain on your computer.
Ollama supplies the replaceable local language engine; Angel supplies the identity,
personality, continuity, tools, safety rules, and native interface.

Angel is a native Python/Tkinter application. It is not a web app, does not need an
account, and contains no telemetry, analytics, or tracking.

## What Angel does

- Chats through an installed Ollama model without identifying Angel as that model.
- Keeps multiple persistent conversations in SQLite.
- Saves only intentional memories, with categories, search, manual entry, and deletion.
- Retrieves relevant memories with lightweight token and recency scoring.
- Uses a strict allowlist for web search, memory, and local date/time tools.
- Searches current public information through a replaceable no-key search provider.
- Shows a visible **Searched the web** label and compact clickable sources only when
  real search results were supplied to the model.
- Accepts multiple images, audio files, videos, documents, archives, and arbitrary
  file types from the message composer. Text-like files receive a bounded local text
  extraction; unsupported formats remain honest metadata-only attachments.
- Offers One More Thing, Make Money, Get Me Out, Build Something, Something Free, and
  Surprise Me through the same Angel brain and conversation.
- Tracks recent suggestions locally to reduce repetition and can mark the latest idea
  completed or rejected from natural follow-up language.
- Remains open and usable for conversation history, Memory, and Settings when Ollama or
  the internet is offline.

## Requirements

- Windows 10 or Windows 11.
- Python 3 with Tk support to run from source or build the executable.
- [Ollama](https://ollama.com/) for local AI conversation.
- Internet access only when web search is used.

Angel never downloads a model automatically.

## Ollama setup

Install and start Ollama, then install a model from a terminal. The recommended starter
model is:

```powershell
ollama pull llama3.2:3b
```

Angel defaults to `http://127.0.0.1:11434`. Open **Settings → Local AI** to refresh
installed models, select a different model, change the endpoint, or recheck the
connection. Model selection is not tied to one exact Ollama model.

## Run Angel

After a build, normal use is simply:

```text
dist\Angel.exe
```

Double-click `Angel.exe`; no console is required.

To run the source checkout, double-click `RUN-ANGEL.bat`, or use:

```powershell
python angel.py
```

In the message composer, press **Enter** to send and **Shift+Enter** to insert a new
line. **Upload Files** accepts up to 20 unique files with no extension allowlist. Angel
does not pretend to see, hear, or parse formats the selected local model cannot use.

## Build Angel.exe

Double-click `BUILD-ANGEL.bat`, or run it from a terminal. The script:

1. locates Python;
2. creates `.venv` when needed;
3. installs the test and packaging requirements;
4. runs the complete automated test suite;
5. stops if a test fails;
6. packages the native window with PyInstaller; and
7. writes `dist\Angel.exe`.

Build intermediates stay in `build\`, and both build intermediates and the virtual
environment are ignored by Git.

## Conversations

Use **New Conversation** in the sidebar to start a separate thread. Previous
conversations appear newest-first and survive restarts. Select a conversation and use
**Delete Conversation** (or press Delete while the conversation list is focused) to
remove it and its messages after confirmation. Deleting the last conversation safely
creates a fresh empty one. Angel sends only a capped set of recent messages to the local
model; it never sends the entire database on each turn.

## Memory

Conversation history and memory are intentionally separate. Use the **Memory** button
to view, search, add, categorize, and delete memories. In chat, explicit language such
as “Remember that I prefer purple” is stored through the same allowlisted memory tool.
Angel does not save every sentence. Memory can be disabled in Settings.

Memory categories are preference, dislike, project, goal, routine, person, and general.

## Search and sources

Angel uses a provider abstraction in `angel/search.py`. The default implementation
requests Bing's lightweight RSS search results without secret credentials and returns a
small normalized set of titles, public HTTP(S) URLs, domains, and snippets. Private,
loopback, local, file, and script URLs are rejected.

Search is automatically considered for explicit searches and current facts such as
news, events, local openings, hiring, weather, and prices. Quick actions that depend on
current local information search when enough location context is configured. If search
is disabled, offline, malformed, or times out, Angel says it was unavailable and does
not fabricate current facts or sources.

## One More Thing and quick actions

**One More Thing** answers “What should I do next?” using conversation context, saved
preferences and projects, approximate location, and recent suggestions. It aims for a
small number of strong actions rather than random tasks or a questionnaire.

- **Make Money** proposes realistic earning-related next steps and searches before
  naming current jobs, openings, prices, or opportunities.
- **Get Me Out** uses configured location and current search for nearby public places
  and activities.
- **Build Something** sizes projects for 15 minutes, 30 minutes, an hour, or an evening.
- **Something Free** prioritizes genuinely free local or at-home options.
- **Surprise Me** uses memory and recent context instead of a canned random phrase.

All actions enter the current conversation and use the same brain, tools, and safety
rules as normal chat.

## Settings

Settings includes:

- Ollama URL, installed model selection, model refresh, and connection recheck;
- display name and optional city, state/region, and ZIP/postal code;
- concise, balanced, or detailed response style;
- internet search enable/disable; and
- memory enable/disable.

Approximate location remains local unless it is needed as part of a search query. Angel
does not request GPS or precise location.

## Local data and privacy

Normal user data is outside the repository:

```text
%LOCALAPPDATA%\Angel\angel.db
%LOCALAPPDATA%\Angel\angel.log
```

- Conversations, memories, settings, and suggestion history are stored locally.
- Ollama requests go to the configured Ollama service, normally localhost.
- Web searches necessarily send the search query to the public search provider.
- Tool logs contain short success/failure metadata, not complete private conversations
  or permanent copies of full search payloads.
- Angel has no telemetry, analytics, tracking, arbitrary shell, Python execution,
  computer-control, purchase, posting, email, password, cookie, or unrestricted file
  tools.

The SQLite schema is upgraded idempotently. Existing conversations are never deleted as
part of initialization.

## Troubleshooting

**Local AI · Offline**

Start Ollama, confirm the URL in Settings, click **Recheck Connection**, and make sure at
least one model appears after **Refresh Models**.

**Local AI · No models**

Install a model with `ollama pull llama3.2:3b`, then refresh models in Settings.

**Search unavailable**

Confirm search is enabled and Windows has internet access. Angel continues locally and
will not invent results while the provider is unreachable.

**Build stops**

Read the first reported test or PyInstaller error. The build intentionally stops before
creating an executable when automated tests fail.

**Where is the log?**

Open `%LOCALAPPDATA%\Angel\angel.log`. The rotating log records startup, shutdown,
database initialization, connection failures, tool failures, search failures, and
packaging/runtime diagnostics without logging complete conversations.

## Developer structure

```text
Angel/
├── angel.py                    application entry point
├── BUILD-ANGEL.bat             test and package pipeline
├── RUN-ANGEL.bat               source launcher
├── Angel.spec                  windowed PyInstaller definition
├── angel/
│   ├── app.py                  composition and runtime diagnostics
│   ├── ui.py                   native Tkinter interface and worker coordination
│   ├── brain.py                context and bounded tool orchestration
│   ├── personality.py          Angel identity and honesty instructions
│   ├── database.py             SQLite schema, migration, and persistence
│   ├── settings.py             persisted configuration
│   ├── memory.py               intentional memory and relevance scoring
│   ├── search.py               provider abstraction and safe normalization
│   ├── tools.py                strict allowlist, validation, and activity logging
│   ├── context.py              bounded model context construction
│   ├── recommendations.py      quick actions and suggestion history
│   ├── ollama_client.py        model-neutral Ollama HTTP client
│   ├── paths.py                source/packaged and local-data paths
│   └── logging_setup.py        rotating local log
└── tests/                      offline mocked regression suite
```

The tests require neither a live Ollama service nor internet access.
