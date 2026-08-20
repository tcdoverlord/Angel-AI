# Angel AI — Engineering Decisions

## Current Version Position

The project is currently in the **Genesis v1.1 development line**.

The next target is **Genesis v1.2**.

## Genesis 1.0 Is Protected

Historical verified foundation:

```text
v1.0.0
8b06235
```

Do not rewrite the release.

## Genesis v1.2 Direction

The project is not solving capability problems by simply adding a larger model.

The selected direction is:

> **Build a stronger operational brain around the model.**

## Combined Rusty Brain Decision

The team-facing Rusty architecture is intentionally simple:

```text
Understand
Plan
Route
Execute
Verify
Recover
```

These six functions are the canonical mental model.

Professional internal concepts live underneath them.

## Responsibility Split

### Angel

- identity
- personality
- conversation
- user-facing response

### Rusty

- understanding
- planning
- routing
- execution orchestration
- evidence
- verification
- recovery

### Ollama / LLM

- language reasoning
- response formulation
- planning assistance where appropriate

The model is not live system truth.

### Capabilities

- real operations
- structured results
- risk/permission declarations
- verification

### Knowledge

- stored/project information
- retrieved context
- durable engineering knowledge

Knowledge is not live evidence.

## Current Date/Time

`current_datetime` is the first reference capability.

It must prove the complete execution lifecycle before the pattern is expanded.

## Weather

Weather-specific behavior remains owned by WeatherBrain.

Generic web search must not become the permanent weather implementation merely because the WeatherBrain path currently needs investigation.

## Smallest Responsible Change

Prefer focused changes over rewrites.

Preserve unrelated working behavior.

## Git Safety

Use local commits as stable checkpoints.

Do not force-push or rewrite shared history without explicit approval.

## Evidence Rule

A model statement is not proof.

A capability registration is not proof of execution.

A successful execution is not automatically proof of correctness.

Live evidence must be validated before being given to the model as verified fact.
