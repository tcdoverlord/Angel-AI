# Angel Platform 3.2.3

## Persistent conversation history repair

- Stores user data under `%USERPROFILE%\Angel_Platform` via `Path.home() / "Angel_Platform"`.
- Stops truncating chat history to the last 100 records; history continues growing.
- Uses atomic writes with a temporary file and `.bak` backup.
- Flushes and fsyncs writes before replacing the active file.
- Recovers from the backup if the main history JSON is damaged.
- Application files can be replaced or rebuilt without removing user history.

The EXE still needs to be built and tested on Windows.
