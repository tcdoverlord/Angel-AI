# Git Safe Workflows

1. Inspect status, branch, remotes, and recent history before modifying a repository.
2. Use a dedicated branch for changes that may require review or rollback.
3. Never force-push or delete a remote branch without explicit confirmation and a recovery reference.
4. Keep generated artifacts and secrets out of commits using .gitignore and secret scanning.
5. After a change, run the narrowest relevant tests before creating a release archive.

## Verification questions

- What evidence was collected?
- What changed, if anything?
- Can the operation be reversed?
- What requires the user's explicit approval?
