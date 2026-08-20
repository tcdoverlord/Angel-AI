# ðŸª½ Angel AI â€” Genesis v1.1 â†’ v1.2

> **A trustworthy local-first AI assistant that is becoming a trustworthy engineering agent.**

Angel AI is a modular Windows AI project built around local inference, real system capabilities, persistent project knowledge, safe execution, validation, and recovery.

Angel is currently in the Genesis v1.1 development line. Genesis v1.2 is the next architectural step: **make Angel capable without giving up the honesty and safety established during Genesis 1.0 and strengthened through v1.1.**

---

## ðŸš€ Current Direction

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

# ðŸ§  Genesis v1.1 â†’ v1.2 Architecture

```text
                         ðŸª½ ANGEL
                  Identity / Personality
                           â”‚
                           â–¼
                  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                  â”‚   RUSTY BRAIN   â”‚
                  â”‚                 â”‚
                  â”‚  Understand     â”‚
                  â”‚  Plan           â”‚
                  â”‚  Route          â”‚
                  â”‚  Execute        â”‚
                  â”‚  Verify         â”‚
                  â”‚  Recover        â”‚
                  â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                           â”‚
          â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
          â–¼                â–¼                â–¼
     Ollama/Llama      Capabilities       Knowledge
       Reasoning         / Tools           / Memory
          â”‚                â”‚                â”‚
          â”‚          â”Œâ”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”      â”‚
          â”‚          â–¼     â–¼     â–¼    â–¼      â”‚
          â”‚        Time   FS   Web  System   â”‚
          â”‚                                  â”‚
          â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–º EVIDENCE â—„â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                            â”‚
                            â–¼
                       VERIFICATION
                            â”‚
                 â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                 â–¼                     â–¼
             VERIFIED               FAILED
                 â”‚                     â”‚
                 â–¼                     â–¼
             RESPONSE               RECOVER
                 â”‚                     â”‚
                 â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                            â–¼
                       ðŸª½ ANGEL ANSWER
```

### Rusty Brain â€” professional internal model

The six visible Rusty functions are the product-level architecture. The following concepts live inside those functions:

```text
UNDERSTAND
â”œâ”€â”€ intent
â”œâ”€â”€ context
â”œâ”€â”€ goal
â””â”€â”€ constraints

PLAN
â”œâ”€â”€ required capabilities
â”œâ”€â”€ action sequence
â”œâ”€â”€ approval requirements
â””â”€â”€ stop conditions

ROUTE
â”œâ”€â”€ capability discovery
â”œâ”€â”€ tool selection
â”œâ”€â”€ model routing
â””â”€â”€ permission/risk routing

EXECUTE
â”œâ”€â”€ capability invocation
â”œâ”€â”€ tool execution
â”œâ”€â”€ result collection
â””â”€â”€ error boundaries

VERIFY
â”œâ”€â”€ result validation
â”œâ”€â”€ evidence
â”œâ”€â”€ freshness
â”œâ”€â”€ provenance
â””â”€â”€ expected vs actual

RECOVER
â”œâ”€â”€ retry
â”œâ”€â”€ safe stop
â”œâ”€â”€ error explanation
â”œâ”€â”€ rollback where appropriate
â””â”€â”€ preserve evidence
```

This is a combined architecture: the six Rusty functions remain the simple, memorable design; the internal contracts make the implementation professional, testable, and extensible.

## Responsibility Split

### ðŸª½ Angel

Angel owns:

- identity
- personality
- conversation
- user-facing communication

Angel should never invent live tool results.

### ðŸ¦€ Rusty

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

### ðŸ§  Ollama / Local LLM

The local model provides:

- language reasoning
- interpretation
- planning assistance
- response formulation

The model is **not** the source of truth for live system state.

### ðŸ› ï¸ Capabilities

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

### ðŸ“š Knowledge

Knowledge contains durable information such as:

- project architecture
- decisions
- documentation
- learned project facts
- retrieved information

Knowledge is not automatically live evidence.

### ðŸ”Ž Evidence

Evidence represents what the system actually observed during execution.

```text
Knowledge:
"Angel has a current_datetime capability."

Evidence:
"The operating system returned this time during the current request."
```

Those are different things.

### ðŸ›¡ï¸ Verification

Rusty should verify capability results before treating them as trusted live evidence.

The intended lifecycle is:

```text
Request
  â†“
Intent
  â†“
Capability discovery
  â†“
Plan
  â†“
Execute
  â†“
Observe
  â†“
Verify
  â†“
Reason
  â†“
Respond
```

---

# ðŸŽ¯ Genesis v1.1 â†’ v1.2 Mission

The Genesis v1.2 build proceeds incrementally from the working v1.1 foundation.

## Milestones

```text
G12-ARCH
Architecture contract
        â†“
G12-CAP
Capability contract
        â†“
G12-TIME
Current datetime reference capability
        â†“
G12-EVID
Evidence / verification
        â†“
G12-BRIDGE
Angel â†” Rusty integration
        â†“
G12-PLAN
Planner
        â†“
G12-TOOLS
Additional capabilities
        â†“
G12-MEM
Memory separation
        â†“
G12-AGENT
Engineering-agent workflows
        â†“
G12-EXE
Genesis v1.2 executable candidate
```

Each meaningful milestone should receive a verified local Git checkpoint.

---

# â° First Reference Capability

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
 â†“
Rusty
 â†“
Intent: CURRENT_TIME
 â†“
Capability: current_datetime
 â†“
Real system clock
 â†“
Structured result
 â†“
Evidence
 â†“
Verification
 â†“
Ollama
 â†“
Angel response
```

The model does not need to know the time.

**Rusty knows because the computer actually provided it.**

---

# ðŸŒ¦ï¸ WeatherBrain

Weather remains a dedicated capability.

Weather logic should remain inside WeatherBrain rather than turning generic `search_web()` into the permanent weather implementation.

The current WeatherBrain runtime path is still an investigation area.

Do not assume a component is broken until the actual path has been traced:

```text
request
 â†“
brain
 â†“
capability selection
 â†“
registry / allowlist
 â†“
WeatherBrain
 â†“
backend
 â†“
result
 â†“
verification
```

---

# ðŸ§© Migration Strategy

Genesis v1.2 is **not a rewrite**.

The existing Python system remains valuable.

The migration strategy is:

```text
Existing component
       â†“
Inspect responsibility
       â†“
Define Rusty boundary
       â†“
Implement Rusty service
       â†“
Integrate
       â†“
Test
       â†“
Preserve compatibility
```

Do not delete working Python simply because Rusty is expanding.

---

# ðŸ›¡ï¸ Engineering Safety

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

# ðŸ§ª Testing

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

# ðŸ—‚ï¸ Project Continuity Documents

The `Rusty/` continuity material is part of the engineering system.

Important documents include:

```text
Rusty/
â”œâ”€â”€ RustyReadme.md
â”œâ”€â”€ ARCHITECTURE.md
â”œâ”€â”€ CURRENT-STATE.md
â”œâ”€â”€ DECISIONS.md
â”œâ”€â”€ GIT-CHECKPOINTS.md
â”œâ”€â”€ HANDOFF.md
â”œâ”€â”€ KNOWN-ISSUES.md
â”œâ”€â”€ NEXT-BUILD.md
â”œâ”€â”€ RECOVERY.md
â”œâ”€â”€ TEST-BASELINE.md
â”œâ”€â”€ TEST-MATRIX.md
â”œâ”€â”€ CONTRIBUTOR-QUICKSTART.md
â””â”€â”€ CONTRIBUTOR-TEAM.md
```

Read these before beginning significant work.

The repository remains the source of truth.

---

# ðŸ‘¥ Team Workflow

Before starting a task:

```text
Read continuity documents
        â†“
Inspect repository
        â†“
Check Git status
        â†“
Check contributor board
        â†“
Claim task
        â†“
Make smallest responsible change
        â†“
Run tests
        â†“
Review evidence
        â†“
Commit
        â†“
Update documentation
```

Do not duplicate another contributor's active work.

If a task is marked `ACTIVE`, coordinate before changing the same subsystem.

---

# ðŸ§  Engineering-Agent Goal

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

# ðŸ’¾ Recovery

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

# ðŸ“Œ Historical Foundation

Genesis 1.0 established the protected foundation:

```text
Release: v1.0.0
Commit: 8b06235
```

Genesis 1.0 should not be rewritten.

Genesis v1.2 moves forward through new development checkpoints.

---

# ðŸ¤ For AI Contributors

Use this startup instruction:

> You are contributing to Angel AI Genesis v1.2. Read the Rusty continuity documents before changing anything. Inspect the actual repository and Git status. Check the contributor board. Preserve working systems and uncommitted changes. Make the smallest responsible change. Never invent capabilities, tests, commits, builds, or runtime results. Test the real path and report exactly what changed, what was validated, what remains unknown, and what checkpoint protects the work.

---

# ðŸ§  The Combined Rusty Brain

The team-facing model is intentionally simple:

```text
Understand
Plan
Route
Execute
Verify
Recover
```

Professional engineering conceptsâ€”intent, capability discovery, evidence, provenance, validation, bounded planning, and recoveryâ€”live underneath those six functions.

This keeps Angel's architecture understandable while giving Rusty the machinery needed to scale.

# ðŸŒ± The Genesis v1.2 Principle

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
Carry the knowledge forward.** ðŸª½
