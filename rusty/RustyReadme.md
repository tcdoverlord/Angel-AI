# Angel AI — Rusty Continuity & Genesis v1.1 → v1.2 Guide

> **Purpose:** Continuity bridge for Angel AI's Rusty brain/execution work.
>
> **Central rule:** Protect what works. Preserve the truth. Carry the knowledge forward.

---

# 1. Project Identity

**Project:** Angel AI

**Current development line:** Genesis v1.1

**Target:** Genesis v1.2 — Trustworthy Agent Brain

**Historical protected release:** Genesis 1.0 / `v1.0.0` / `8b06235`

Rusty is the trusted Rust backend and execution engine for Angel's modular Windows toolkit.

---

# 2. Genesis v1.2 Vision

The team is not replacing Angel with a larger model.

The goal is to build the operational brain around the model.

Angel should become:

```text
trustworthy
+
capable
+
evidence-driven
+
modular
+
recoverable
```

---

# 3. Canonical Rusty Brain

The six-function architecture is the official team-facing model:

```text
Understand
Plan
Route
Execute
Verify
Recover
```

## Understand

- intent
- context
- goal
- constraints

## Plan

- required capabilities
- action sequence
- approval requirements
- stopping conditions

## Route

- capability discovery
- tool selection
- model routing
- permission/risk routing

## Execute

- capability invocation
- tool execution
- result collection
- error boundaries

## Verify

- result validation
- evidence
- freshness
- provenance
- expected vs actual

## Recover

- retry
- safe stop
- error explanation
- rollback where appropriate
- evidence preservation

The six functions remain simple and memorable. The internal concepts make the implementation professional and scalable.

---

# 4. Responsibility Model

## Angel

Owns:

- identity
- personality
- conversation
- user-facing response

## Rusty

Owns:

- Understand
- Plan
- Route
- Execute
- Verify
- Recover

## Ollama / LLM

Owns:

- natural-language reasoning
- language generation
- response formulation
- planning assistance where appropriate

It does not own live machine truth.

## Capabilities

Own:

- actual operations
- structured results
- risk/permission declarations
- verification

## Knowledge

Owns stored information and project memory.

Knowledge is not live evidence.

---

# 5. Evidence Contract

Rusty should distinguish:

```text
requested
executed
successful
verified
source
observed value
error
```

The model receives evidence that has passed the appropriate validation boundary.

---

# 6. Verification Contract

The intended lifecycle is:

```text
Request
 ↓
Understand
 ↓
Plan
 ↓
Route
 ↓
Execute
 ↓
Observe
 ↓
Verify
 ├── success → Reason → Respond
 └── failure → Recover
```

A model-generated statement is never sufficient evidence that an action occurred.

---

# 7. First Reference Capability

`current_datetime` is the first reference capability.

Success means:

- Angel identifies the request;
- Rusty understands it;
- Rusty plans the required operation;
- Rusty routes to `current_datetime`;
- the real system clock is queried;
- the result becomes evidence;
- the evidence is verified;
- the model explains the verified result.

The model must not invent the current time.

---

# 8. WeatherBrain

Weather remains a dedicated subsystem.

Do not permanently route weather through generic web search.

The weather runtime path remains an integration investigation until registration, dispatch, backend access, and model routing are verified.

Inspect:

```text
angel/weather/
angel/tools.py
angel/brain.py
angel/context.py
angel/app.py
tests/
```

Trace:

```text
registration
→ dispatch
→ backend
→ result
→ evidence
→ verification
→ model
```

---

# 9. Migration Strategy

The existing Python system remains part of the project.

Migration proceeds by responsibility:

```text
Python responsibility
   ↓
inspect
   ↓
define Rusty boundary
   ↓
implement Rusty service
   ↓
integrate
   ↓
test
   ↓
retain compatibility
```

Do not delete working Python code simply to make the architecture look cleaner.

---

# 10. Capability Expansion

Recommended progression:

```text
current_datetime
filesystem
system_information
process_inspection
Git
PowerShell
project_inspection
web
```

Each capability should be independently testable.

---

# 11. Memory

Keep separate:

### Working memory
Current conversation and task.

### Project memory
Architecture, decisions, checkpoints, known issues.

### Retrieved knowledge
Information loaded from durable sources.

### Live evidence
Results from the current execution.

Never silently convert one category into another.

---

# 12. Safety

Administrative execution must use:

- read-only inspection first
- allowlisted actions
- least privilege
- explicit approval
- logging
- validation
- recovery

Administrator access is not permission to bypass safety.

---

# 13. Testing

Use:

```powershell
.\.venv\Scripts\python.exe -m pytest .	ests -q
```

Historical Genesis 1.0 baseline:

```text
85 passed in 12.42s
```

Current results must be rerun rather than assumed.

Test the real runtime path in addition to unit tests.

---

# 14. Git Safety

Before significant work:

```powershell
git status --short
git branch --show-current
git log --oneline --decorate -5
```

Use:

```text
Inspect
Protect
Implement
Validate
Commit
Verify
```

Never:

- force-push
- rewrite shared history
- reset/clean blindly
- delete recovery material
- claim commits that do not exist

---

# 15. Genesis v1.2 Checkpoints

```text
G12-ARCH  combined architecture contract
G12-CAP   capability contract
G12-TIME  current datetime
G12-EVID  evidence/verification
G12-BRIDGE Angel/Rusty bridge
G12-PLAN  planner
G12-TOOLS  capability expansion
G12-MEM   memory separation
G12-AGENT engineering workflows
G12-EXE   executable candidate
```

Record actual commit hashes only after verification.

---

# 16. Completion Standard

A milestone is complete only when we can state:

```text
What changed
What passed
What failed
What was not tested
What evidence exists
What commit protects it
What recovery path exists
What comes next
```

No vague "everything works" claims.

---

# 17. Final Goal

Rusty should become the dependable operational brain underneath Angel.

Angel remains Angel.

Ollama remains the reasoning/language engine.

Capabilities are the hands and senses.

Knowledge is memory.

Evidence is truth.

Verification is the guard.

Planning is the bridge from conversation to useful action.

Recovery keeps the system safe.

That is the Genesis v1.2 destination.
