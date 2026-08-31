# Angel AI 2.7 — Windows EXE Build

## Recommended build
Open PowerShell or Command Prompt in the Angel_AI folder and run:

```bat
.\BUILD-EXE.bat
```

The finished executable must be:

```text
dist\AngelAI\AngelAI.exe
```

## Start
Once the EXE exists, run:

```bat
.\START-ANGEL.bat
```

START-ANGEL.bat prefers the packaged EXE and falls back to Python only when no EXE exists.

## Why the old builder could be confusing
The previous script invoked PyInstaller directly against `launcher.py` and only printed the expected output path. The revised builder explicitly uses `AngelAI.spec`, cleans stale build output, checks Python/PyInstaller, and verifies that `dist\AngelAI\AngelAI.exe` actually exists before reporting success.
