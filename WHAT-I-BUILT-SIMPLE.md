# What I built — explained simply

Think of Angel like a small office on your `D:` drive.

## 1. The front desk: `Angel.exe`

This is the part you double-click. It draws the window, accepts your messages, sends
with Enter, attaches files, shows replies, and reads replies aloud with Windows voices.

The front desk is not the “brain.” It is the place where you and all the other parts
meet.

## 2. The local engine: Ollama

Ollama runs the language model on your computer. Angel asks Ollama to produce words,
but the model is replaceable. Angel's name, behavior, memory rules, tools, projects,
and safety rules live in Angel's own code.

Simple version: Ollama is the motor; Angel is the whole car.

## 2A. The rulebook: `ANGEL-BIBLE.md`

The Angel Bible is a human-written software constitution. It is Bible-inspired, but it
is not scripture and does not claim that Angel is divine or conscious. It gives Angel
durable rules about life, truth, human choice, ownership, memory, tools, and growth.

Angel keeps an approved copy, hashes it like a digital fingerprint, and checks that
fingerprint when it starts or reads the Bible. If someone changes the file behind
Angel's back, Angel saves the changed copy as evidence and restores the last approved
version. The model can search the rulebook, but it gets no button or tool that can
approve changes. A person must review proposals, and every approved version stays in a
history that can be rolled back.

Simple version: changing the motor does not rewrite the car's rulebook.

## 3. The filing cabinet: `data\angel.db`

SQLite is a database stored in one local file. It keeps chats, messages, memory,
projects, settings, summaries, knowledge indexes, creator records, Bible revisions,
and Bible proposals.

I used transactions and foreign keys so related records change together. I also added
integrity checks, Write-Ahead Logging, and proper connection closing so Windows does not
leave the database locked during restore.

Simple version: write important things in the filing cabinet, not on a sticky note.

## 4. The trashable scratch pad: `cache`

Cache is only temporary work. Angel can delete it and recreate it. Important things do
not live there.

I added a test that creates a conversation, memory, project, and setting, deletes the
cache, reopens the database, and proves those things still exist.

Simple version: losing scratch paper must not empty the filing cabinet.

## 5. The spare keys: `backups`

Angel periodically makes a consistent copy of the database and approved Bible files
inside a ZIP file. It adds a
manifest so the backup can be checked. Old backups rotate instead of growing forever.

Before restoring, Angel checks the chosen backup and creates a safety backup of the
current database. If the main database is corrupt, Angel keeps the damaged file for
inspection and can recover from the newest good backup.

Simple version: check the spare key before throwing away the key you have.

## 6. Memory: important facts, not every word

Chat history is the transcript. Memory is the smaller list of facts that should matter
later. You can add, search, edit, or delete memories. Memories have categories,
importance, confidence, tags, source information, and last-use time. Similar duplicates
are combined.

When you ask a question, Angel finds only the relevant memories instead of dumping
everything into the prompt.

## 7. Projects: “where did we leave off?”

A project stores its description, current state, important files, decisions, tasks,
completed work, ideas, notes, and activity. One project can be active. Angel adds the
active or relevant project to the conversation so a new chat can still continue the
work.

## 8. Knowledge: your local reference shelf

When you add a file to Knowledge, Angel copies it into its durable library, extracts
what it honestly can read, splits long text into smaller pieces, and makes a tiny local
search index. It finds useful pieces by comparing words and local numeric fingerprints.
You can also choose a source-code folder, including Angel's own public code. Private
runtime folders are skipped. If you deliberately configure a local Ollama embedding
model, Angel uses its real vectors; otherwise it labels and uses the simpler local
fallback honestly.

No cloud vector database or account is needed. If Angel cannot parse a format, it keeps
metadata and says that plainly.

## 9. Context: packing one useful backpack

A model has a limited context window. Angel builds a bounded “backpack” for each turn:

1. The approved Angel Bible.
2. Angel's identity and truth rules.
3. Your saved preferences.
4. The active/relevant project.
5. Relevant memories.
6. Relevant Knowledge Library excerpts.
7. An older-chat summary when needed.
8. Recent messages.
9. Verified tool results.

Anything retrieved from memory, a project, a document, a website, or a tool is marked
as data—not as a new instruction that can rewrite the rulebook.

That keeps context useful without loading the entire database every time.

## 10. Tools: labeled drawers, not a chainsaw

The model may only request tools that Angel registered in a strict list. Each tool has
a description, permission type, argument validation, and call limit. Search is blocked
in Offline mode. There is no general shell, arbitrary Python, unrestricted file write,
password, cookie, purchase, email, posting, or computer-control tool.

Simple version: the model gets a few labeled drawers, not the keys to the building.

## 11. Image and music creation

Angel can talk to ComfyUI for images and ACE-Step for music over localhost. It checks
whether each service exists, sends a real job, waits for the result, saves the output,
and records the prompt/settings in Creator Library.

Those programs and their large models are separate. I did not secretly download them.
When they are missing, Angel shows “unavailable” and everything else keeps working.

## 12. The tests

There are two kinds:

- Automated tests use fake local pieces and check 77 behaviors quickly without the
  internet.
- Acceptance tests use the real app and installed local model. The Offline acceptance
  test replaces public search with a tripwire, asks several questions, clears cache,
  reopens Angel, verifies chat/memory/project/settings continuity, retrieves the real
  commandments and truth rule, and proves an “ignore your Bible” prompt did not change
  the approved constitutional hash.

The key design lesson is separation: permanent data, disposable data, replaceable AI
engines, safe tools, and user interface each have a different job. When those jobs are
kept separate, the app is easier to fix and much harder to accidentally wipe.
