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
│   │      Restores Angel files from backup
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
│   ├── Wake-Angel.ps1
│   │      Final recovery startup check
│   │
│   ├── Backup-Angel.sh
│   │      Linux backup engine
│   │
│   └── Verify-Angel-Backup.sh
│          Linux backup verification
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

For a backup that will be kept offline, use:

```text
Backup
  |
  v
Verify Backup
  |
  v
Safely Eject / Disconnect Backup Drive
```

---

# Requirements

Angel Bootstrap currently supports:

## Windows

- Windows PowerShell
- Python
- Git
- Ollama
- Required Angel folder structure
- Robocopy
- Windows-accessible backup storage

## Linux

- Bash
- Python
- Git
- Ollama
- Required Angel folder structure
- Standard Linux backup utilities

---

# Important Safety Rule

The Bootstrap is designed to protect the working Angel system.

Before performing recovery or backup operations:

1. Verify the Angel installation.
2. Confirm the source and destination.
3. Review the operation before confirming it.
4. Never place a backup inside the live Angel project.
5. Verify important backups after they are created.
6. Keep an offline backup when possible.

For removable backup media such as a USB flash drive:

```text
Create Backup
     |
     v
Verify Backup
     |
     v
Safely Eject USB
```

The offline copy should remain disconnected when it is not being used.

---

# Quick Start

The examples below assume the Angel project is located at:

```text
D:\Angel_AI
```

---

# Windows Quick Start

Open PowerShell and go to the Angel project:

```powershell
cd D:\Angel_AI
```

You can then run Bootstrap tools from the project root using:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\bootstrap\<script-name>
```

This form allows the Bootstrap scripts to run even when the normal PowerShell execution policy blocks unsigned local scripts.

---

# Verify Angel

## Windows

From:

```text
D:\Angel_AI
```

run:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\bootstrap\Verify-Angel.ps1
```

Checks:

- Required folders
- Protected files
- Angel structure

A successful verification reports:

```text
ANGEL STATUS: VERIFIED
```

---

# Check Environment

## Windows

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\bootstrap\Check-Environment.ps1
```

Checks:

- Operating system
- Python
- Git
- Ollama
- Storage availability

---

# Create an Angel Backup

## Windows

Run:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\bootstrap\Backup-Angel.ps1
```

The backup engine provides a menu for selecting the destination.

Available destination types include:

```text
1. Backup Test
2. Permanent Backups
3. Browse for a folder
4. Enter a path manually
0. Cancel
```

For example:

```text
D:\Angel_Backups
```

or a removable USB drive:

```text
G:\Angel_Backups
```

The backup engine checks the destination and asks for confirmation before starting.

The backup engine also performs a capacity preflight before copying. It calculates the eligible backup payload while honoring the existing exclusions, adds a safety margin, and compares the requirement with available destination space.

---

# Backup Storage Recommendations

A strong Angel recovery arrangement uses multiple copies.

Example:

```text
Working Angel
D:\Angel_AI
      |
      +----> Local Backup
      |      D:\Angel_Backups
      |
      +----> Offline Backup
             G:\Angel_Backups
```

The removable backup can then be safely disconnected after verification.

This provides:

- Working copy
- Local recovery copy
- Offline recovery copy

---

# Verify an Angel Backup

After creating an important backup, verify it.

## Windows

Run:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\bootstrap\Verify-Angel-Backup.ps1
```

The verifier can locate available `Angel_Backup_*` folders inside a selected backup location.

Example:

```text
G:\Angel_Backups
```

The verification checks items including:

- Backup manifest
- Backup report
- Required files
- Required directories
- Nested backup protection
- Git exclusion
- Reparse points

A successful verification reports:

```text
BACKUP VERIFIED
```

For an offline USB backup, verify it before disconnecting the drive.

---

# Create Recovery Seed

## Windows

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\bootstrap\Build-Angel-Seed.ps1
```

Creates a portable Angel recovery copy.

---

# Restore Angel

## Windows

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\bootstrap\Restore-Angel.ps1
```

Restores Angel from a selected backup or recovery source.

### Important

Review the source and destination carefully before confirming a restore operation.

Do not restore over a working Angel installation unless that is the intended recovery operation and a verified recovery path exists.

---

# Start Angel Recovery

## Windows

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\bootstrap\Start-Angel-Recovery.ps1
```

Runs the recovery preparation process.

---

# Wake Angel

## Windows

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\bootstrap\Wake-Angel.ps1
```

Runs:

1. Recovery verification
2. Environment validation
3. Integrity checks
4. Angel readiness confirmation

---

# Windows Backup Example

A typical user workflow is:

```powershell
cd D:\Angel_AI
```

Verify Angel:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\bootstrap\Verify-Angel.ps1
```

Create a backup:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\bootstrap\Backup-Angel.ps1
```

Verify the backup:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\bootstrap\Verify-Angel-Backup.ps1
```

Then, for an offline USB backup:

```text
Safely eject the USB drive.
```

---

# Linux Quick Start

The Bootstrap also contains Linux shell versions of the backup and verification tools.

From the Angel project directory:

```bash
cd /path/to/Angel_AI
```

Make the shell scripts executable if necessary:

```bash
chmod +x ./bootstrap/Backup-Angel.sh
chmod +x ./bootstrap/Verify-Angel-Backup.sh
```

---

# Linux Backup

Run:

```bash
./bootstrap/Backup-Angel.sh
```

The Linux backup engine creates an Angel backup using the Linux backup workflow.

---

# Linux Backup Verification

Run:

```bash
./bootstrap/Verify-Angel-Backup.sh
```

This verifies the resulting Angel backup.

---

# Linux Backup Example

```bash
cd /path/to/Angel_AI
```

Then:

```bash
chmod +x ./bootstrap/Backup-Angel.sh
chmod +x ./bootstrap/Verify-Angel-Backup.sh
```

Create the backup:

```bash
./bootstrap/Backup-Angel.sh
```

Verify it:

```bash
./bootstrap/Verify-Angel-Backup.sh
```

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

# Backup Contract

Angel backups use a shared backup contract.

A valid backup contains:

```text
backup-manifest.json
backup-report.json
```

The backup report should indicate:

```text
status = SUCCESS
```

The backup should then be verified using the Bootstrap verification system.

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

Backups and Git serve different purposes.

Git is the source-history and development safety system.

Backups are the recovery system.

---

# Recommended Three-Copy Strategy

For important Angel checkpoints, maintain:

```text
1. WORKING COPY
   D:\Angel_AI

2. LOCAL BACKUP
   D:\Angel_Backups\Angel_Backup_*

3. OFFLINE BACKUP
   USB:\Angel_Backups\Angel_Backup_*
```

Recommended workflow:

```text
              D:\Angel_AI
                   |
          +--------+--------+
          |                 |
          v                 v
 D:\Angel_Backups     USB:\Angel_Backups
          |                 |
          v                 v
       Verify             Verify
                            |
                            v
                     Safely Eject
```

The offline backup should be disconnected after verification whenever practical.

---

# Recovery Workflow

When Angel needs to be recovered:

```text
1. Identify the verified backup
        |
        v
2. Check the environment
        |
        v
3. Restore Angel
        |
        v
4. Verify the restored installation
        |
        v
5. Wake Angel
```

Useful commands:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\bootstrap\Check-Environment.ps1
```

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\bootstrap\Restore-Angel.ps1
```

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\bootstrap\Verify-Angel.ps1
```

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\bootstrap\Wake-Angel.ps1
```

---

# If PowerShell Blocks a Script

If Windows reports:

```text
cannot be loaded because it is not digitally signed
```

use the explicit Bootstrap execution form:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\bootstrap\Backup-Angel.ps1
```

or replace the script name with the Bootstrap tool you need.

This does not permanently change the user's PowerShell execution policy.

---

# Troubleshooting

## Angel verification fails

Run:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\bootstrap\Verify-Angel.ps1
```

Review the reported missing folder or protected file.

Do not immediately overwrite files. Identify the problem first.

---

## Backup verification fails

Confirm that you selected the **parent backup folder** containing the `Angel_Backup_*` directories.

Example:

```text
G:\Angel_Backups
```

not:

```text
G:\Angel_Backups\Angel_Backup_2026-08-19_144218
```

The verifier can then display the available Angel backups and allow you to select the specific backup.

---

## Backup destination is blocked

Confirm that the destination is outside the live Angel project.

For:

```text
D:\Angel_AI
```

do not use:

```text
D:\Angel_AI\backups
```

as the external recovery destination.

Use a separate location such as:

```text
D:\Angel_Backups
```

or a removable backup drive such as:

```text
G:\Angel_Backups
```

---

# Current Version

Angel AI:

```text
Genesis 0.8
```

Bootstrap:

```text
1.0
```

Status:

```text
READY
```

---

# Mission

Angel is designed to be recoverable.

The bootstrap is the first layer of survival.

```text
Build.
Backup.
Verify.
Recover.
Wake.
Continue.
```

---

# Core Principle

> Protect what works. Preserve the truth. Carry the knowledge forward.
