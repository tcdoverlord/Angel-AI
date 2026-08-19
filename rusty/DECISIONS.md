# Angel AI — Engineering Decisions

## Genesis 1.0 Is Protected

Genesis 1.0 is the verified foundation:

```text
v1.0.0
8b06235
```

Future development moves forward from it.

## Smallest Responsible Change

Prefer focused repairs over rewrites.

Preserve unrelated working behavior.

## Modular Architecture

Keep GUI, brain, tools, WeatherBrain, Rusty, PowerShell, backup, validation, and documentation separated where practical.

## Weather Separation

Weather functionality should use the dedicated WeatherBrain path rather than making generic web search the permanent weather implementation.

## Honest Failure

If current information cannot be retrieved, Angel must say so.

Never fabricate current weather or date information.

## Backup Safety

Maintain multiple recovery copies.

The intended protection model is:

- working project
- D: backup
- offline USB backup

## Git Safety

Git is the development safety system.

Use local commits as stable checkpoints.

Do not force-push or rewrite remote history without explicit approval.

## Recovery Material

Recovery copies and `moveable/` are not automatically part of source releases.

Do not stage them blindly.

## Testing

Use the project's `.venv`.

Target the real test suite:

```powershell
.\.venv\Scripts\python.exe -m pytest .\tests -q
```

## Documentation

Important architectural decisions and verified lessons should be carried forward into Rusty documentation.
