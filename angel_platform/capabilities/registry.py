
"""Capability registry for measurable Angel growth in 3.3.1."""
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
import json

@dataclass(frozen=True)
class Capability:
    id: str
    name: str
    version: str
    status: str
    description: str
    tests: tuple[str, ...]

CAPABILITIES = (
    Capability("web-research", "Web Research", "3.3.1", "integrated",
               "Retrieves current web results with source links and bounded timeouts.",
               ("search_returns_results", "search_handles_failure")),
    Capability("context-grounding", "Context Grounding", "3.3.1", "integrated",
               "Separates user context, retrieved facts, and uncertainty.",
               ("grounding_has_sources",)),
    Capability("safe-execution-audit", "Execution Audit", "3.3.1", "integrated",
               "Records operation intent, outcome, exit code, and verification state.",
               ("audit_round_trip",)),
    Capability("module-refresh", "Module Refresh Contract", "3.3.1", "integrated",
               "Defines refresh signals after prepare, update, and configuration changes.",
               ("refresh_event_shape",)),
    Capability("release-validation", "Release Validation", "3.3.1", "integrated",
               "Exposes a machine-readable capability inventory for release checks.",
               ("registry_is_complete",)),
)

def inventory():
    return [asdict(item) for item in CAPABILITIES]

def write_inventory(destination: Path):
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps({
        "schema": "angel-capabilities/v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "release": "3.3.1",
        "capabilities": inventory(),
    }, indent=2), encoding="utf-8")
    return destination
