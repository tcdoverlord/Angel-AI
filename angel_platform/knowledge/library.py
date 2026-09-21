from __future__ import annotations
from pathlib import Path
import json, re
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
SEED_FILE = ROOT / "seed_cards.json"
EXPANSION_FILE = ROOT / "expansion_cards.json"
DATA = Path.home() / "Angel_Platform"
KNOWLEDGE_FILE = DATA / "knowledge_cards.json"
FEEDBACK_FILE = DATA / "feedback.json"
FIELD_GUIDES = ROOT / "field_guides"
DATA.mkdir(parents=True, exist_ok=True)

def _load(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return default

def _save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(path)

def cards():
    seed = _load(SEED_FILE, [])
    expansion = _load(EXPANSION_FILE, [])
    custom = _load(KNOWLEDGE_FILE, [])
    by_id = {str(x.get("id")): x for x in seed if isinstance(x, dict) and x.get("id")}
    for item in expansion:
        if isinstance(item, dict) and item.get("id"):
            by_id[str(item["id"])] = item
    for item in custom:
        if isinstance(item, dict) and item.get("id"):
            by_id[str(item["id"])] = item
    # Field guides are indexed as local knowledge documents. The full files remain
    # on disk; indexing a bounded excerpt keeps chat retrieval responsive.
    if FIELD_GUIDES.exists():
        for path in sorted(FIELD_GUIDES.glob("*.md")):
            try:
                body = path.read_text(encoding="utf-8")
            except OSError:
                continue
            item_id = "field-guide-" + path.stem
            by_id[item_id] = {
                "id": item_id,
                "title": path.stem.replace("-", " ").title(),
                "tags": ["field-guide", path.stem],
                "content": body[:12000],
                "source": str(path.name),
            }
    return list(by_id.values())

def search(query: str, limit: int = 4):
    terms = {x for x in re.findall(r"[a-z0-9][a-z0-9_-]{2,}", str(query).lower())}
    ranked = []
    for card in cards():
        hay = " ".join([
            str(card.get("title", "")),
            " ".join(map(str, card.get("tags", []))),
            str(card.get("content", "")),
        ]).lower()
        score = sum(2 if term in str(card.get("tags", [])).lower() else 1 for term in terms if term in hay)
        if score:
            ranked.append((score, card))
    ranked.sort(key=lambda pair: (-pair[0], str(pair[1].get("title", ""))))
    return [card for _, card in ranked[:max(1, min(int(limit), 10))]]

def context_for(query: str, limit: int = 4):
    found = search(query, limit)
    if not found:
        return ""
    lines = ["Relevant Angel Knowledge Library context:"]
    for card in found:
        lines.append(f"- {card.get('title','Untitled')}: {card.get('content','')}")
    lines.append("Use this context carefully; do not claim that a knowledge card proves a live system state.")
    return "\n".join(lines)

def record_feedback(message: str, rating: str, note: str = "", conversation_id: str = ""):
    allowed = {"helpful", "incorrect", "incomplete", "correction"}
    rating = str(rating).strip().lower()
    if rating not in allowed:
        raise ValueError("Feedback rating must be helpful, incorrect, incomplete, or correction.")
    records = _load(FEEDBACK_FILE, [])
    records.append({
        "id": datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f"),
        "rating": rating,
        "message": str(message)[:4000],
        "note": str(note)[:4000],
        "conversation_id": str(conversation_id)[:200],
        "time": datetime.now(timezone.utc).isoformat(),
    })
    _save(FEEDBACK_FILE, records[-500:])
    return records[-1]["id"]

def status():
    return {"seed_cards": len(_load(SEED_FILE, [])), "expansion_cards": len(_load(EXPANSION_FILE, [])), "total_cards": len(cards()), "feedback_file": str(FEEDBACK_FILE)}
