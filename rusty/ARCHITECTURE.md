# Angel AI — Architecture

## Current Development Position

Angel is **currently in the Genesis v1.1 development line** and is being prepared for **Genesis v1.2**.

Genesis v1.2 is an architectural evolution of the working v1.1 system, not a rewrite.

## Genesis v1.2 Goal

Turn Angel from a trustworthy conversational assistant into a trustworthy, evidence-driven engineering agent.

The project keeps the strengths already established in v1.1—honesty about unavailable information, modularity, local inference, recovery, and testable behavior—while adding a stronger operational brain.

## Canonical Genesis v1.2 Architecture

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


## Responsibility Boundaries

### Angel

Owns:

- identity
- personality
- conversation
- user-facing response

Angel should not independently invent live tool results.

### Rusty Brain

Rusty is the trusted Rust backend and execution engine.

For v1.2, Rusty becomes the operational brain that coordinates:

- understanding
- planning
- routing
- execution
- verification
- recovery

Rusty remains separate from GUI, backup scripts, and capability-specific implementation.

### Ollama / Local LLM

The model provides language reasoning and response formulation.

The model is not the source of truth for live machine state.

### Capabilities / Tools

Capabilities perform real operations such as:

```text
current_datetime
WeatherBrain
filesystem
system information
process inspection
Git
PowerShell
project inspection
web
future approved modules
```

Each capability should eventually define:

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

### Knowledge / Memory

Knowledge provides durable project information and retrieved context.

Live execution evidence is separate from stored knowledge.

## Evidence Rule

A model statement is not proof.

A capability registration is not proof of execution.

A successful execution is not automatically proof of correctness.

Live evidence must be collected and verified before Rusty treats it as trusted current information.

## Execution Lifecycle

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
Evidence
  ↓
Verify
  ├── success → reason/respond
  └── failure → recover
```

## WeatherBrain

Weather-specific behavior remains owned by WeatherBrain.

Do not permanently replace it with generic `search_web()` merely because the current runtime path needs investigation.

The actual registration, dispatch, backend, and model-routing path must be verified before conclusions are made.

## Migration Principle

The existing Python brain is not discarded.

Migration proceeds by responsibility:

```text
Existing Python responsibility
        ↓
Inspect
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

No rewrite is justified merely because Rusty is expanding.

## Safety

Administrative actions use:

- read-only inspection first
- allowlisted operations
- least privilege
- explicit approval
- logging
- validation
- recovery

## v1.2 Success

Angel v1.2 should reliably:

1. understand a request;
2. plan the required work;
3. route to a real capability;
4. execute it;
5. collect evidence;
6. verify the result;
7. reason about verified evidence;
8. respond naturally;
9. recover or stop honestly when execution fails.
