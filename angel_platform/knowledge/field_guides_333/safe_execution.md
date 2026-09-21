# Safe Execution

1. Classify actions as read-only, reversible change, destructive change, or privileged change.
2. Require explicit approval immediately before impactful execution, not only during setup.
3. Use allowlists, workspace boundaries, timeouts, output capture, and cancellation where possible.
4. Show the exact command and intended target before execution.
5. Record success, failure, exit code, and partial effects without hiding errors.

## Verification questions

- What evidence was collected?
- What changed, if anything?
- Can the operation be reversed?
- What requires the user's explicit approval?
