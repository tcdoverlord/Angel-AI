# Raspberry Pi Home Lab

1. Record hostname, OS image, architecture, storage device, and network address for each Pi.
2. Use SSH keys and disable unnecessary services; keep management access on a trusted network or VPN.
3. Monitor storage health and maintain a tested backup before changing boot media or services.
4. Separate public-facing services from management interfaces.
5. Treat power loss as a design condition: use journaling, graceful shutdown, and recoverable configuration.

## Verification questions

- What evidence was collected?
- What changed, if anything?
- Can the operation be reversed?
- What requires the user's explicit approval?
