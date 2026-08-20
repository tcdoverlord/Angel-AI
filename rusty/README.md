# 🪽 Angel AI — Genesis v1.1 → v1.2

> **A trustworthy local-first AI assistant that is becoming a trustworthy engineering agent.**

Angel AI is a modular Windows AI project built around local inference, real system capabilities, persistent project knowledge, safe execution, validation, and recovery.

Angel is currently in the Genesis v1.1 development line. Genesis v1.2 is the next architectural step: **make Angel capable without giving up the honesty and safety established during Genesis 1.0 and strengthened through v1.1.**

---

## 🚀 Current Direction

Angel is moving from:

```text
A trustworthy conversational assistant
```

toward:

```text
A trustworthy, evidence-driven engineering agent
```

The central idea is simple:

> **Do not make the model pretend to be the computer. Give the model a reliable brain and real capabilities.**

---

# 🧠 Genesis v1.1 → v1.2 Architecture

```text
                         🪽 ANGEL
                  Identity / Personality
                           │
                           ▼
                  ┌─────────────────┐
                  │   RUSTY BRAIN   │
                  │                 │
                  │  Understand     │
                  │  Plan           │
                  │  Route          │
                  │  Execute        │
                  │  Verify         │
                  │  Recover        │
                  └────────┬────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
     Ollama/Llama      Capabilities       Knowledge
       Reasoning         / Tools           / Memory
          │                │                │
          │          ┌─────┼─────────┐      │
          │          ▼     ▼     ▼    ▼      │
          │        Time   FS   Web  System   │
          │                                  │
          └──────────────► EVIDENCE ◄────────┘
                            │
                            ▼
                       VERIFICATION
                            │
                 ┌──────────┴──────────┐
                 ▼                     ▼
             VERIFIED               FAILED
                 │                     │
                 ▼                     ▼
             RESPONSE               RECOVER
                 │                     │
                 └──────────┬──────────┘
                            ▼
                       🪽 ANGEL ANSWER
```

### Rusty Brain — professional internal model

The six visible Rusty functions are the product-level architecture. The following concepts live inside those functions:

```text
UNDERSTAND
├── intent
├── context
├── goal
└── constraints

PLAN
├── required capabilities
├── action sequence
├── approval requirements
└── stop conditions

ROUTE
├── capability discovery
├── tool selection
├── model routing
└── permission/risk routing

EXECUTE
├── capability invocation
├── tool execution
├── result collection
└── error boundaries

VERIFY
├── result validation
├── evidence
├── freshness
├── provenance
└── expected vs actual

RECOVER
├── retry
├── safe stop
├── error explanation
├── rollback where appropriate
└── preserve evidence
```

This is a combined architecture: the six Rusty functions remain the simple, memorable design; the internal contracts make the implementation professional, testable, and extensible.

## Responsibility Split

### 🪽 Angel

Angel owns:

- identity
- personality
- conversation
- user-facing communication

Angel should never invent live tool results.

### 🦀 Rusty

Rusty is the trusted Rust backend and execution engine.

Genesis v1.2 expands Rusty toward the orchestration/brain layer responsible for:

- intent
- context assembly
- capability discovery
- planning
- execution orchestration
- evidence
- verification
- recovery

### 🧠 Ollama / Local LLM

The local model provides:

- language reasoning
- interpretation
- planning assistance
- response formulation

The model is **not** the source of truth for live system state.

### 🛠️ Capabilities

Capabilities are the real operations Angel can perform.

Examples include:

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

Each capability should eventually have:

```text
name
description
input schema
output schema
risk level
permissions
execution method
verification method
```

### 📚 Knowledge

Knowledge contains durable information such as:

- project architecture
- decisions
- documentation
- learned project facts
- retrieved information

Knowledge is not automatically live evidence.

### 🔎 Evidence

Evidence represents what the system actually observed during execution.

```text
Knowledge:
"Angel has a current_datetime capability."

Evidence:
"The operating system returned this time during the current request."
```

Those are different things.

### 🛡️ Verification

Rusty should verify capability results before treating them as trusted live evidence.

The intended lifecycle is:

```text
Request
  ↓
Intent
  ↓
Capability discovery
  ↓
Plan
  ↓
Execute
  ↓
Observe
  ↓
Verify
  ↓
Reason
  ↓
Respond
```

---

# 🎯 Genesis v1.1 → v1.2 Mission

The Genesis v1.2 build proceeds incrementally from the working v1.1 foundation.

## Milestones

```text
G12-ARCH
Architecture contract
        ↓
G12-CAP
Capability contract
        ↓
G12-TIME
Current datetime reference capability
        ↓
G12-EVID
Evidence / verification
        ↓
G12-BRIDGE
Angel ↔ Rusty integration
        ↓
G12-PLAN
Planner
        ↓
G12-TOOLS
Additional capabilities
        ↓
G12-MEM
Memory separation
        ↓
G12-AGENT
Engineering-agent workflows
        ↓
G12-EXE
Genesis v1.2 executable candidate
```

Each meaningful milestone should receive a verified local Git checkpoint.

---

# ⏰ First Reference Capability

The first capability is:

```text
current_datetime
```

This is intentionally simple.

We want to prove the complete architecture with something that can be objectively verified.

For:

> Angel, what time is it?

the system should perform:

```text
Angel
 ↓
Rusty
 ↓
Intent: CURRENT_TIME
 ↓
Capability: current_datetime
 ↓
Real system clock
 ↓
Structured result
 ↓
Evidence
 ↓
Verification
 ↓
Ollama
 ↓
Angel response
```

The model does not need to know the time.

**Rusty knows because the computer actually provided it.**

---

# 🌦️ WeatherBrain

Weather remains a dedicated capability.

Weather logic should remain inside WeatherBrain rather than turning generic `search_web()` into the permanent weather implementation.

The current WeatherBrain runtime path is still an investigation area.

Do not assume a component is broken until the actual path has been traced:

```text
request
 ↓
brain
 ↓
capability selection
 ↓
registry / allowlist
 ↓
WeatherBrain
 ↓
backend
 ↓
result
 ↓
verification
```

---

# 🧩 Migration Strategy

Genesis v1.2 is **not a rewrite**.

The existing Python system remains valuable.

The migration strategy is:

```text
Existing component
       ↓
Inspect responsibility
       ↓
Define Rusty boundary
       ↓
Implement Rusty service
       ↓
Integrate
       ↓
Test
       ↓
Preserve compatibility
```

Do not delete working Python simply because Rusty is expanding.

---

# 🛡️ Engineering Safety

Angel is intended to protect working systems.

Before significant changes:

```powershell
git status --short
git branch --show-current
git log --oneline --decorate -5
```

Then:

```text
Inspect
Protect
Implement
Validate
Commit
Verify
Document
```

### Do not

- reset working changes blindly
- clean untracked recovery material
- overwrite unrelated work
- force-push
- rewrite shared history
- move or rewrite protected historical tags
- invent tests
- invent commits
- invent builds
- claim runtime success without evidence

Administrative actions should use:

- read-only inspection first
- allowlisted operations
- least privilege
- explicit approval
- logging
- validation
- recovery

---

# 🧪 Testing

Use the project's virtual environment:

```powershell
.\.venv\Scripts\python.exe -m pytest .	ests -q
```

The verified Genesis 1.0 baseline was:

```text
85 passed in 12.42s
```

That number is **historical evidence**, not a claim about every future working tree.

Always run the current tests before claiming a new milestone.

Unit tests do not automatically prove live runtime behavior.

For important capabilities, test the actual runtime path as well.

---

# 🗂️ Project Continuity Documents

The `Rusty/` continuity material is part of the engineering system.

Important documents include:

```text
Rusty/
├── RustyReadme.md
├── ARCHITECTURE.md
├── CURRENT-STATE.md
├── DECISIONS.md
├── GIT-CHECKPOINTS.md
├── HANDOFF.md
├── KNOWN-ISSUES.md
├── NEXT-BUILD.md
├── RECOVERY.md
├── TEST-BASELINE.md
├── TEST-MATRIX.md
├── CONTRIBUTOR-QUICKSTART.md
└── CONTRIBUTOR-TEAM.md
```

Read these before beginning significant work.

The repository remains the source of truth.

---

# 👥 Team Workflow

Before starting a task:

```text
Read continuity documents
        ↓
Inspect repository
        ↓
Check Git status
        ↓
Check contributor board
        ↓
Claim task
        ↓
Make smallest responsible change
        ↓
Run tests
        ↓
Review evidence
        ↓
Commit
        ↓
Update documentation
```

Do not duplicate another contributor's active work.

If a task is marked `ACTIVE`, coordinate before changing the same subsystem.

---

# 🧠 Engineering-Agent Goal

Eventually Angel should be able to handle workflows such as:

```text
"Inspect my project and tell me
why the build is failing."
```

Rusty should be able to:

```text
1. Understand the goal
2. Inspect available capabilities
3. Build a bounded plan
4. Execute safe inspections
5. Collect evidence
6. Verify observations
7. Reason about the evidence
8. Recommend or perform an approved action
9. Validate the result
10. Report exactly what happened
```

That is the real intelligence upgrade.

Not merely a bigger model.

---

# 💾 Recovery

Genesis development must remain recoverable.

The intended protection model is:

```text
Working project
      +
Permanent backup
      +
Offline/removable backup
      +
Git checkpoints
```

Recovery means preserving:

- working code
- evidence
- configuration
- architecture decisions
- documentation
- Git history
- ability to continue

---

# 📌 Historical Foundation

Genesis 1.0 established the protected foundation:

```text
Release: v1.0.0
Commit: 8b06235
```

Genesis 1.0 should not be rewritten.

Genesis v1.2 moves forward through new development checkpoints.

---

# 🤝 For AI Contributors

Use this startup instruction:

> You are contributing to Angel AI Genesis v1.2. Read the Rusty continuity documents before changing anything. Inspect the actual repository and Git status. Check the contributor board. Preserve working systems and uncommitted changes. Make the smallest responsible change. Never invent capabilities, tests, commits, builds, or runtime results. Test the real path and report exactly what changed, what was validated, what remains unknown, and what checkpoint protects the work.

---

# 🧠 The Combined Rusty Brain

The team-facing model is intentionally simple:

```text
Understand
Plan
Route
Execute
Verify
Recover
```

Professional engineering concepts—intent, capability discovery, evidence, provenance, validation, bounded planning, and recovery—live underneath those six functions.

This keeps Angel's architecture understandable while giving Rusty the machinery needed to scale.

# 🌱 The Genesis v1.2 Principle

Angel does not need to pretend she is smart.

She needs to become **reliably capable**.

```text
Angel
  = Identity

Rusty
  = Brain / Orchestration

Ollama
  = Reasoning / Language

Capabilities
  = Hands and senses

Knowledge
  = Memory

Evidence
  = Truth

Verification
  = Guard

Planner
  = Bridge from thought to action
```

## Final Goal

> **Build Angel into a trustworthy engineering agent that can understand, plan, act, verify, recover, and tell the truth about what she actually did.**

**Protect what works.  
Inspect before changing.  
Build in modules.  
Preserve the truth.  
Carry the knowledge forward.** 🪽
