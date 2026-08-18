# Angel Backup Contract

Version: 1.0

## Purpose

Windows and Linux use native backup engines, but both produce the same logical Angel backup format.

## Engines

- `Backup-Angel.ps1` — native Windows engine
- `Backup-Angel.sh` — native Linux engine
- `Verify-Angel-Backup.ps1` — Windows verifier
- `Verify-Angel-Backup.sh` — Linux verifier
- `Angel-Backup-Menu.ps1` — Windows user-facing launcher

## Required control files

Every successful backup must contain:

- `backup-manifest.json`
- `backup-report.json`

Both files use JSON and include:

- `contract_version`
- `backup_id`
- `platform`
- `engine`
- `engine_version`
- timestamps
- source
- destination
- status

## Safety principles

1. Never guess an ambiguous destination.
2. Never back up into the live Angel project.
3. Never use a filesystem root as a backup destination.
4. Require explicit confirmation before starting.
5. Check destination availability and free space.
6. Do not follow Windows junctions/reparse points.
7. Do not follow Linux symbolic links during backup.
8. Keep backup and verification read/write responsibilities separate.
9. Keep test backups outside Git.
10. Platform-specific engines share the same backup contract.

## Portability

The Windows engine uses PowerShell and Robocopy.

The Linux engine uses Bash and prefers `rsync`.

The backup contract is platform-independent even though the implementations are native to their operating systems.
