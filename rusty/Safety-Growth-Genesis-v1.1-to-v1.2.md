# ðŸª½ Angel AI â€” Safety & Growth
## Genesis v1.1 â†’ v1.2 Team Guidance

> **Protect what works. Grow what works. Preserve the truth.**

### Purpose

This document is a team-wide guardrail for the transition from **Genesis v1.1** toward **Genesis v1.2**.

We are improving Angel's intelligence and capabilities without sacrificing the working system, the project's history, or the knowledge accumulated by the team.

This is **not a rewrite directive**.

It is a growth directive.

---

# 1. The Most Important Rule

## Do not throw away working knowledge to make room for new architecture.

The existing Angel project contains valuable:

- code
- architecture
- documentation
- tests
- decisions
- recovery procedures
- backups
- contributor knowledge
- historical lessons
- capability implementations
- known limitations

The Genesis v1.2 architecture must **connect to that foundation**, not erase it.

### The wrong approach

```text
Genesis 1.0 / 1.1 knowledge
        â†“
delete / replace
        â†“
Genesis v1.2
```

### The correct approach

```text
                    EXISTING PROJECT
                          â”‚
             â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
             â–¼                         â–¼
       Historical Knowledge       Current v1.1
             â”‚                         â”‚
             â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                          â–¼
                 Genesis v1.2 Layer
                          â”‚
              â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
              â–¼           â–¼           â–¼
          Rusty Brain  New Tools   New Contracts
              â”‚           â”‚           â”‚
              â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                          â–¼
                   Working Angel
```

---

# 2. We Are Currently Building v1.1 â†’ v1.2

Do not describe v1.2 as already released or complete.

Our actual position is:

```text
CURRENT
Genesis v1.1
     â”‚
     â”‚ improve / connect / verify
     â–¼
TARGET
Genesis v1.2
```

Genesis v1.2 is earned through verified milestones.

---

# 3. The New Rusty Brain

The new architecture we are building is:

```text
                    ðŸª½ ANGEL
              Identity / Personality
                       â”‚
                       â–¼
                â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                â”‚ RUSTY BRAIN â”‚
                â”‚             â”‚
                â”‚ Understand  â”‚
                â”‚ Plan        â”‚
                â”‚ Route       â”‚
                â”‚ Execute     â”‚
                â”‚ Verify      â”‚
                â”‚ Recover     â”‚
                â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”˜
                       â”‚
        â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
        â–¼              â–¼              â–¼
     Ollama/Llama    Tools         Knowledge
     reasoning      execution      retrieval
        â”‚              â”‚              â”‚
        â”‚        â”Œâ”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”        â”‚
        â”‚        â–¼     â–¼     â–¼        â”‚
        â”‚       Time  Web   FS   Future Tools
        â”‚                              â”‚
        â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–º Evidence â—„â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                       â”‚
                       â–¼
                  Verification
                       â”‚
                       â–¼
                 Angel's answer
```

This is the **combined architecture**.

It combines the simple six-function Rusty Brain with professional agent-engineering concepts underneath it.

---

# 4. What the Six Functions Mean

## Understand

Rusty determines:

- what the user wants;
- the relevant context;
- the goal;
- constraints.

## Plan

Rusty determines:

- what capabilities are needed;
- what order actions should occur in;
- whether approval is required;
- when the operation should stop.

## Route

Rusty determines:

- which capability should handle the request;
- which tool or subsystem should be used;
- whether model reasoning is needed;
- what permission/risk boundary applies.

## Execute

Rusty invokes real capabilities.

Examples:

```text
Time
Filesystem
Web
Git
PowerShell
System inspection
Project inspection
Future modules
```

## Verify

Rusty determines whether the result is trustworthy.

Verification can consider:

- whether execution actually happened;
- whether it succeeded;
- whether the result is structurally valid;
- whether it is current;
- where it came from;
- whether expected and actual results match.

## Recover

If something fails, Rusty should:

- retry when safe;
- stop safely;
- explain the failure;
- preserve evidence;
- roll back only when appropriate and recoverable.

---

# 5. Professional Concepts Belong Inside Rusty

The team should not think that we have to choose between:

```text
simple architecture
```

and:

```text
professional architecture
```

We are doing both.

The visible architecture remains:

```text
Understand
Plan
Route
Execute
Verify
Recover
```

Inside those functions we can implement:

```text
intent
context
capability discovery
planning
routing
permissions
structured execution
evidence
provenance
validation
freshness
recovery
```

This gives the team a clear architecture without preventing sophisticated implementation.

---

# 6. Preserve the Existing Brain

The existing Python brain and other working components are not automatically obsolete.

Before replacing a responsibility:

```text
Inspect
   â†“
Understand what it currently does
   â†“
Identify what works
   â†“
Identify what needs improvement
   â†“
Define the Rusty boundary
   â†“
Implement the new path
   â†“
Test it
   â†“
Preserve compatibility where practical
```

Do not rewrite a working subsystem merely because the new architecture looks cleaner.

---

# 7. Preserve Documentation

Existing documentation is project memory.

Do not solve documentation drift by deleting large amounts of history.

Instead:

```text
Existing documentation
        â”‚
        â”œâ”€â”€ preserve useful history
        â”œâ”€â”€ preserve decisions
        â”œâ”€â”€ preserve known issues
        â”œâ”€â”€ preserve recovery knowledge
        â”‚
        â–¼
Add clearly marked v1.2 sections
        â”‚
        â–¼
Connect old architecture â†’ new architecture
```

When older material is historical, label it as historical.

When new material is planned, label it as planned.

When a feature is verified, document the evidence.

---

# 8. Preserve Git

Before significant work:

```powershell
git status --short
git branch --show-current
git log --oneline --decorate -5
```

Never assume a clean working tree.

Never use:

```text
git reset --hard
git clean
force-push
history rewrite
```

as casual cleanup.

Before committing:

```text
inspect
review
stage only intended files
review staged diff
test
commit
verify commit
```

Unrelated backup, staging, recovery, or experimental files must not accidentally enter a documentation or architecture commit.

---

# 9. Preserve Backups and Recovery

Backup material is not clutter just because it is inconvenient.

It may contain:

- recovery points;
- evidence;
- known-good versions;
- diagnostic material;
- historical implementation details.

Do not delete it to make the repository look cleaner without first understanding what it contains and whether it is intentionally ignored or tracked.

---

# 10. Evidence Before Claims

The new architecture is built around one important lesson:

> **Knowledge does not equal capability. Capability registration does not equal execution. Execution does not automatically equal verified truth.**

For example:

```text
Known:
"current_datetime capability exists."

Executed:
"The capability actually ran."

Evidence:
"The operating system returned a time."

Verified:
"The returned value passed the expected validation."

Response:
Angel can now safely tell the user.
```

The model should not invent the missing steps.

---

# 11. The First v1.2 Proof

The first reference capability is:

```text
current_datetime
```

The goal is not simply:

> Make Angel tell time.

The goal is to prove the reusable architecture:

```text
User request
     â†“
Understand
     â†“
Plan
     â†“
Route
     â†“
Execute
     â†“
Evidence
     â†“
Verify
     â†“
Ollama reasoning
     â†“
Angel response
```

Once this pattern is trustworthy, it can be reused for other capabilities.

---

# 12. Capability Growth

Future capabilities should grow through the same contract rather than becoming one-off hacks.

Possible progression:

```text
current_datetime
      â†“
filesystem
      â†“
system information
      â†“
process inspection
      â†“
Git
      â†“
PowerShell
      â†“
project inspection
      â†“
web
      â†“
future modules
```

Each capability should have an appropriate:

```text
name
description
input
output
risk
permissions
execution
verification
```

---

# 13. WeatherBrain

WeatherBrain remains important.

Do not erase a dedicated subsystem simply because its current runtime path needs investigation.

The team should trace:

```text
registration
    â†“
allowlist
    â†“
dispatch
    â†“
WeatherBrain
    â†“
backend
    â†“
result
    â†“
evidence
    â†“
verification
```

If the path fails, identify the actual boundary before replacing it.

---

# 14. What Success Looks Like

Angel v1.2 should eventually be able to handle requests like:

> "Angel, inspect my project and tell me why the build is failing."

Rusty should be able to:

```text
Understand the goal
        â†“
Plan the investigation
        â†“
Route to project/build capabilities
        â†“
Execute safe inspection
        â†“
Collect evidence
        â†“
Verify the evidence
        â†“
Reason about the verified information
        â†“
Recommend or perform an approved action
        â†“
Verify the result
        â†“
Tell the user exactly what happened
```

That is the intelligence upgrade.

It is not simply "use a bigger model."

---

# 15. Team Rules for Growth

### Rule 1 â€” Protect what works

Do not destroy functioning components to make progress look cleaner.

### Rule 2 â€” Inspect before changing

The actual repository is the source of truth.

### Rule 3 â€” Connect before replacing

If an existing component can become part of the new architecture, prefer integration.

### Rule 4 â€” Make the smallest responsible change

Large rewrites create unnecessary risk.

### Rule 5 â€” Evidence before claims

Never claim a feature works without evidence.

### Rule 6 â€” Keep recovery close

Every important change should have a recovery path.

### Rule 7 â€” Document decisions

If architecture changes, record why.

### Rule 8 â€” Preserve history

Old knowledge may explain why today's architecture exists.

### Rule 9 â€” Keep the architecture modular

New capabilities should plug into Rusty instead of creating another monolith.

### Rule 10 â€” Grow Angel, don't replace Angel

The goal is a better Angel built from the Angel we already have.

---

# 16. The Mental Model

The team should remember:

```text
Angel
  = Identity

Rusty
  = Operational Brain

Ollama
  = Reasoning / Language

Capabilities
  = Hands and senses

Knowledge
  = Memory

Evidence
  = Observed truth

Verification
  = Guard

Recovery
  = Safety net
```

And:

```text
Rusty
  Understands
  Plans
  Routes
  Executes
  Verifies
  Recovers
```

---

# 17. Final Growth Principle

We are not choosing between the old Angel and the new Angel.

We are building a bridge.

```text
                 OLD KNOWLEDGE
                      â”‚
                 CURRENT v1.1
                      â”‚
                      â–¼
                â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                â”‚   BRIDGE  â”‚
                â”‚           â”‚
                â”‚   RUSTY   â”‚
                â”‚   BRAIN   â”‚
                â””â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”˜
                      â”‚
          â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
          â–¼           â–¼           â–¼
       Smarter     Safer       More Capable
          â”‚           â”‚           â”‚
          â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                      â–¼
                 GENESIS v1.2
                      â”‚
                      â–¼
                 ðŸª½ ANGEL
```

> **The goal is not to erase the path that got us here. The goal is to make the next part of the path safer, smarter, and stronger.**

**Protect what works.
Connect what exists.
Build what is missing.
Verify what we claim.
Preserve the knowledge.
Grow Angel responsibly.**

â€” Angel Project Engineering Team
