# Angel AI — Architecture

## Principle

Keep Angel modular. Each subsystem should have a clear responsibility.

```text
Angel Application
│
├── Brain / reasoning
├── Context
├── Personality
├── Bible / identity
├── Tool registry
│
├── Current Information
│   ├── Date/Time
│   └── WeatherBrain
│
├── Rusty
│   └── Rust backend / execution engine
│
├── PowerShell modules
│   └── Windows administration
│
├── Backup / recovery
│
└── Tests / validation
```

## Rusty

Rusty is the trusted Rust backend and execution engine for Angel's modular Windows toolkit.

Rusty should remain separate from GUI, PowerShell administration, backup scripts, and WeatherBrain.

## WeatherBrain

WeatherBrain should own weather-specific behavior.

Do not bury weather logic inside generic `search_web()`.

The current investigation is to determine whether WeatherBrain is:

- registered
- allowlisted
- exposed to the model
- dispatched correctly
- able to reach its backend
- returning the expected structure

## Bootstrap

Bootstrap provides recovery and verification.

Important components include:

- backup
- restore
- environment checking
- verification
- recovery startup
- seed creation

## Safety

Administrative actions should use:

- read-only inspection first
- allowlisted operations
- least privilege
- explicit approval
- logging
- validation
- recovery paths
