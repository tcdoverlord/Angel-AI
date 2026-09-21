
"""Frontend refresh events emitted after module state mutations."""
from dataclasses import dataclass, asdict
from datetime import datetime, timezone

@dataclass(frozen=True)
class ModuleRefreshEvent:
    module_id: str
    reason: str
    refresh_required: bool = True
    emitted_at: str = ""

    def to_dict(self):
        result = asdict(self)
        result["emitted_at"] = self.emitted_at or datetime.now(timezone.utc).isoformat()
        return result

def after_mutation(module_id: str, reason: str):
    return ModuleRefreshEvent(module_id, reason).to_dict()
