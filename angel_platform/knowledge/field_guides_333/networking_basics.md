# Networking Basics

1. Separate link state, IP configuration, routing, DNS, and application connectivity when troubleshooting.
2. Check interface state first, then address and route information, then DNS resolution, then the target service.
3. A successful ping does not prove that a TCP service or HTTP endpoint is healthy.
4. Preserve the original network configuration before changing adapters, routes, DNS, or firewall rules.
5. Document whether a failure is local, gateway-related, DNS-related, remote, or application-specific.

## Verification questions

- What evidence was collected?
- What changed, if anything?
- Can the operation be reversed?
- What requires the user's explicit approval?
