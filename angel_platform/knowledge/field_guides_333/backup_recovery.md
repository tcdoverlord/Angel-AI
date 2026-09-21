# Backup and Recovery

1. A backup is useful only if its contents and restoration process are verified.
2. Use timestamped backups and retain the last known-good build before upgrades.
3. Separate application source, user data, secrets, and generated artifacts.
4. Test a restore into a temporary directory before overwriting the active installation.
5. Document recovery steps in plain language so the process does not depend on memory.

## Verification questions

- What evidence was collected?
- What changed, if anything?
- Can the operation be reversed?
- What requires the user's explicit approval?
