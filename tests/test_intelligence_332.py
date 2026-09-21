import json
from pathlib import Path

def test_332_expansion_library_is_present():
    path = Path(__file__).parents[1] / "angel_platform" / "knowledge" / "expansion_cards.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert len(data) >= 2500
    assert any("interaction" in card.get("tags", []) for card in data)

def test_332_release_manifest():
    path = Path(__file__).parents[1] / "ANGEL_3.3.2_BUILD_MANIFEST.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["release"] == "3.3.2"
    assert data["fine_tuning"] is False
