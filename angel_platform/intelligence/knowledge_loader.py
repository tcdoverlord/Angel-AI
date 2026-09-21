"""Local shared knowledge loader for Angel Platform 3.3.1."""
from pathlib import Path
import json
ROOT = Path(__file__).resolve().parent
INDEX = ROOT / "knowledge_index.json"
def load_index():
    return json.loads(INDEX.read_text(encoding="utf-8"))
def search_cards(query: str, limit: int = 8):
    terms = [t.lower() for t in query.split() if t.strip()]
    out=[]
    for card in load_index().get("cards", []):
        hay = (card.get("title","") + " " + card.get("path","")).lower()
        score=sum(term in hay for term in terms)
        if score:
            out.append((score, card))
    return [card for _,card in sorted(out,key=lambda x:(-x[0],x[1]["path"]))[:max(1,limit)]]
