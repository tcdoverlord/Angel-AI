# Local Database Operations

1. Use transactions for related changes and foreign keys for referential integrity.
2. Prefer migrations that are additive and reversible over destructive table replacement.
3. Keep database files in user data, outside the source checkout, so upgrades do not erase them.
4. Back up before schema migrations and verify that a backup can be read.
5. Use indexes for common retrieval paths and cap user-facing result sizes.

## Verification questions

- What evidence was collected?
- What changed, if anything?
- Can the operation be reversed?
- What requires the user's explicit approval?
