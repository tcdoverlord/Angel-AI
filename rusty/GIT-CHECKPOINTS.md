# Angel AI — Git Checkpoints

## Current Version Position

```text
Current development: Genesis v1.1
Target: Genesis v1.2
```

## Protected Genesis 1.0

```text
Commit: 8b06235
Tag: v1.0.0
```

The tag is historical and protected.

Do not rewrite or move it.

## Current Development

Genesis v1.2 proceeds from the actual v1.1 repository state.

Before significant changes:

```powershell
git status --short
git branch --show-current
git log --oneline --decorate -5
```

Preserve uncommitted work.

## Checkpoint Pattern

```text
Inspect
Protect
Implement
Validate
Commit
Verify
Document
```

## Genesis v1.2 Checkpoint Targets

```text
G12-ARCH   Combined architecture contract
G12-CAP    Capability contract
G12-TIME   Current datetime reference capability
G12-EVID   Evidence / verification
G12-BRIDGE Angel ↔ Rusty integration
G12-PLAN   Planner
G12-TOOLS  Additional capabilities
G12-MEM    Memory separation
G12-AGENT  Engineering-agent workflows
G12-EXE    Genesis v1.2 executable candidate
```

Actual commit hashes must be recorded only after commits exist.

## Commit Rules

Keep unrelated changes out of a checkpoint.

Do not:

- force-push
- reset destructively
- clean untracked recovery material
- rewrite shared history
- move the v1.0.0 tag

## Release Rule

A release is not established by documentation alone.

Require:

- verified commit
- verified tag
- relevant tests
- runtime evidence
- build evidence
- documented limitations
