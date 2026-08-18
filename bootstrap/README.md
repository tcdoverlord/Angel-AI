# Angel AI Bootstrap System

## Purpose

The Angel AI Bootstrap system is the recovery foundation that allows Angel to be restored, verified, and started from a clean backup or portable seed.

The goal:

> Angel can always be rebuilt from her foundation.

The bootstrap contains the tools required to verify the environment, restore Angel files, create portable recovery seeds, and prepare Angel for startup.

---

# Bootstrap Architecture

```text
Angel AI
│
├── Bootstrap
│   │
│   ├── Verify-Angel.ps1
│   │      Checks Angel files and required structure
│   │
│   ├── Check-Environment.ps1
│   │      Checks system requirements
│   │
│   ├── Restore-Angel.ps1
│   │      Restores Angel from backup
│   │
│   ├── Backup-Angel.ps1
│   │      Creates Angel backups
│   │
│   ├── Build-Angel-Seed.ps1
│   │      Creates portable Angel recovery copies
│   │
│   ├── Start-Angel-Recovery.ps1
│   │      Runs recovery preparation
│   │
│   └── Wake-Angel.ps1
│          Final recovery startup check
│
└── manifests
    ├── angel-manifest.json
    └── angel-seed.json
```

---

# Recovery Workflow

The normal Angel recovery process:

```text
Backup
  |
  v
Restore
  |
  v
Environment Check
  |
  v
Integrity Verification
  |
  v
Wake Angel
```

---

# Requirements

Angel Bootstrap currently supports:

- Windows PowerShell
- Python
- Git
- Ollama
- Required Angel folder structure

---

# Quick Start

From the bootstrap folder:

## Verify Angel

```powershell
.\Verify-Angel.ps1
```

Checks:

- Required folders
- Protected files
- Angel structure

---

## Check Environment

```powershell
.\Check-Environment.ps1
```

Checks:

- Operating system
- Python
- Git
- Ollama
- Storage availability

---

## Create Recovery Seed

```powershell
.\Build-Angel-Seed.ps1
```

Creates a portable Angel recovery copy.

---

## Restore Angel

```powershell
.\Restore-Angel.ps1
```

Restores Angel to a selected destination.

---

## Wake Angel

```powershell
.\Wake-Angel.ps1
```

Runs:

1. Recovery verification
2. Environment validation
3. Integrity checks
4. Angel readiness confirmation

---

# Manifests

## angel-manifest.json

Defines:

- Angel identity
- Required folders
- Protected files

## angel-seed.json

Defines:

- Recovery seed identity
- Bootstrap version
- Angel version

---

# Backup Philosophy

The repository contains the blueprint.

The backup contains the living system.

Git stores:

- Source code
- Scripts
- Documentation
- Recovery tools

Local backups contain:

- Runtime data
- Generated files
- Personal configuration
- AI models

---

# Current Version

Angel AI:

Genesis 0.8

Bootstrap:

1.0

Status:

READY

---

# Mission

Angel is designed to be recoverable.

The bootstrap is the first layer of survival.

```text
Build.
Backup.
Recover.
Wake.
Continue.
```
