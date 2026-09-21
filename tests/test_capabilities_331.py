from pathlib import Path
from angel_platform.capabilities.registry import inventory
from angel_platform.capabilities.refresh import after_mutation
from angel_platform.capabilities.audit import make_record, append_record

def test_registry_contains_growth():
    ids={item['id'] for item in inventory()}
    assert {'web-research','context-grounding','safe-execution-audit','module-refresh'} <= ids

def test_refresh_event_shape():
    event=after_mutation('demo','prepare')
    assert event['module_id']=='demo' and event['refresh_required'] is True

def test_audit_round_trip(tmp_path: Path):
    path=tmp_path/'audit.json'
    append_record(path, make_record('diagnostic','success',0,True))
    assert path.exists() and 'diagnostic' in path.read_text()
