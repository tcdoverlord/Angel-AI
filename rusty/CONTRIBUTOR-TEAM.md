# Angel AI — Contributor Team Board

> **Purpose:** Coordinate human and AI contributors during the Genesis v1.1 → v1.2 transition. One shared understanding, no duplicated work, and evidence-backed progress.

## Read Before Working

1. Read `Rusty/RustyReadme.md`.
2. Read `Rusty/HANDOFF.md`.
3. Read `Rusty/CURRENT-STATE.md`.
4. Read `Rusty/NEXT-BUILD.md`.
5. Read this board.
6. Inspect the actual repository and Git state.
7. Check active tasks before claiming work.

The repository is the source of truth.

---

# 1. Version Position

```text
Current development line: Genesis v1.1
Target: Genesis v1.2
```

Historical protected release:

```text
Genesis 1.0
v1.0.0
8b06235
```

Genesis 1.0 must not be rewritten.

Genesis v1.2 work builds on the actual v1.1 repository state.

---

# 2. Genesis v1.2 Work Board

| Task ID | Area | Owner | Status | Goal |
|---|---|---|---|---|
| ANGEL-GEN12-001 | Combined architecture contract | Angel/Core | ACTIVE | Formalize six-function Rusty Brain plus internal professional contracts |
| ANGEL-GEN12-002 | Capability contract | OPEN | PLANNED | Define reusable capability interface |
| ANGEL-GEN12-003 | Current datetime | OPEN | PLANNED | Make live time the reference end-to-end capability |
| ANGEL-GEN12-004 | Evidence/verification | OPEN | PLANNED | Establish evidence and verification boundary |
| ANGEL-GEN12-005 | Angel ↔ Rusty bridge | OPEN | PLANNED | Integrate without rewriting working v1.1 behavior |
| ANGEL-GEN12-006 | Planner | OPEN | PLANNED | Enable bounded multi-step planning |
| ANGEL-GEN12-007 | Capability expansion | OPEN | PLANNED | Add real system capabilities incrementally |
| ANGEL-GEN12-008 | WeatherBrain | BLOCKED | BLOCKED | Resolve runtime integration after capability boundary is established |
| ANGEL-GEN12-009 | Memory separation | OPEN | PLANNED | Separate conversation, project memory, knowledge, live evidence |
| ANGEL-GEN12-010 | Engineering-agent workflows | OPEN | PLANNED | Enable inspect/diagnose/plan/act/verify workflows |
| ANGEL-GEN12-011 | Regression tests | OPEN | PLANNED | Cover the real runtime path |
| ANGEL-GEN12-012 | EXE packaging | OPEN | PLANNED | Package only after brain milestone is stable |

### Status meanings

- `OPEN` — available to claim
- `PLANNED` — desired but not started
- `ACTIVE` — currently owned
- `BLOCKED` — waiting on a dependency
- `REVIEW` — implementation complete; needs validation
- `DONE` — verified and checkpointed

Do not duplicate an `ACTIVE` task without coordination.

---

# 3. Canonical Rusty Brain

The team-level architecture is:

```text
Understand
Plan
Route
Execute
Verify
Recover
```

Do not replace this with a complicated subsystem diagram in team-facing documentation.

The professional implementation details live underneath those six functions.

---

# 4. AI Contributor Rules

AI contributors must:

1. Read the Rusty continuity material first.
2. Inspect the actual repository before changing code.
3. Check this board.
4. Preserve uncommitted work.
5. Make the smallest responsible change.
6. Test the real path.
7. Never invent runtime evidence.
8. Never claim a commit unless it exists.
9. Never force-push or rewrite shared history.
10. Update the task record when complete.

---

# 5. v1.1 → v1.2 Engineering Sequence

```text
Current v1.1
     ↓
Architecture contract
     ↓
Capability contract
     ↓
Current datetime
     ↓
Evidence / verification
     ↓
Angel ↔ Rusty bridge
     ↓
Planner
     ↓
Additional capabilities
     ↓
Memory separation
     ↓
Engineering-agent workflows
     ↓
v1.2 candidate
```

Do not jump to packaging merely because an executable can be produced.

---

# 6. Completion Record

When a task is complete:

```text
Task ID:
Owner:
Branch:
Commit:
Files:
Tests:
Runtime evidence:
Known limitations:
Next dependency:
```

Only record evidence that actually exists.

---

# 7. Shared Engineering Rules

Protect what works.

Inspect before changing.

Use read-only inspection first.

Preserve evidence.

Use least privilege.

Keep Windows protections enabled.

Do not expose secrets.

Do not force-push.

Do not delete another contributor's work.

Do not overwrite unrelated changes.

Do not confuse model knowledge with live system evidence.

---

# 8. Team Workflow

```text
Notice task
   ↓
Read Rusty/
   ↓
Check board
   ↓
Claim task
   ↓
Inspect
   ↓
Protect baseline
   ↓
Implement smallest change
   ↓
Validate
   ↓
Commit
   ↓
Verify
   ↓
Update board
```

## Core Goal

> One project. One shared understanding. Evidence before claims. No duplicated work.
