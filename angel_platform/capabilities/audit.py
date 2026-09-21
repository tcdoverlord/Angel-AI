
"""Append-only execution audit records with atomic replacement."""
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
import json, os, tempfile

@dataclass(frozen=True)
class AuditRecord:
    operation: str
    requested_at: str
    outcome: str
    exit_code: int | None = None
    verified: bool = False
    detail: str = ""

def make_record(operation, outcome, exit_code=None, verified=False, detail=""):
    return AuditRecord(operation, datetime.now(timezone.utc).isoformat(), outcome,
                       exit_code, verified, detail)

def append_record(path: Path, record: AuditRecord):
    path.parent.mkdir(parents=True, exist_ok=True)
    records = []
    if path.exists():
        try: records = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError): records = []
    records.append(asdict(record))
    fd, temp = tempfile.mkstemp(prefix=path.name, dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(records[-500:], handle, indent=2)
            handle.flush(); os.fsync(handle.fileno())
        os.replace(temp, path)
    finally:
        if os.path.exists(temp): os.unlink(temp)
    return record
