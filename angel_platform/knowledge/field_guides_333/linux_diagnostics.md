# Linux Diagnostics

1. Identify the distribution with /etc/os-release and the kernel with uname -a.
2. Inspect system pressure with uptime, free -h, df -h, lsblk, and journalctl --since.
3. Use systemctl status and journalctl to investigate a service before restarting it.
4. Avoid destructive commands until the target device, mount point, and backup state are confirmed.
5. Use sudo only for the smallest command that requires elevation.

## Verification questions

- What evidence was collected?
- What changed, if anything?
- Can the operation be reversed?
- What requires the user's explicit approval?
