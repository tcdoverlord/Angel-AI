# Windows Diagnostics

1. Start with read-only observations: OS version, uptime, disk capacity, memory pressure, and network state.
2. Capture command output before making changes so a later comparison is possible.
3. Prefer built-in tools such as Get-ComputerInfo, Get-Volume, Get-CimInstance, Get-NetIPConfiguration, and Get-WinEvent.
4. Treat cleanup, service changes, registry edits, firewall changes, and driver changes as separate approval-required operations.
5. Record the command, timestamp, result, and rollback plan in the audit trail.

## Verification questions

- What evidence was collected?
- What changed, if anything?
- Can the operation be reversed?
- What requires the user's explicit approval?
