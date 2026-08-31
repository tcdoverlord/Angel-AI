from pathlib import Path
import json
class GPTManager:
    def __init__(self,root="data/gpts"): self.root=Path(root)
    def list_gpts(self):
        out=[]
        for p in self.root.iterdir() if self.root.exists() else []:
            s=p/"seed.json"
            if p.is_dir() and s.exists():
                try: d=json.loads(s.read_text(encoding="utf-8")); out.append(d)
                except Exception: pass
        return out
