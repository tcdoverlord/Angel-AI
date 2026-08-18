# Angel Linux Backup Engine

This version adds:

- Menu-driven destination selection.
- GUI folder picker when Zenity/KDialog is available.
- Optional, user-approved Zenity installation.
- Detection of APT, DNF, Pacman, and Zypper.
- Manual absolute-path fallback.
- Clear examples of valid and invalid Linux paths.
- Explicit confirmation before creating a destination.
- Explicit confirmation before starting a backup.
- Protected Linux system destinations.
- Protection against backing up inside the live Angel project.
- Free-space check.
- Symlink-safe backup behavior.
- Shared Angel backup manifest/report contract.
- `rsync` preferred, with a safe fallback when unavailable.

The script does not install anything unless the user explicitly answers Y.
