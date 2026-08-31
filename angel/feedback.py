from pathlib import Path
import json
class Feedback:
    def __init__(self,path=None):
        self.path=Path(path) if path else Path("data")/"feedback.json"
    def record(self,v):
        d=self.stats(); d["total"]+=1; d[v]+=1
        self.path.parent.mkdir(parents=True,exist_ok=True)
        self.path.write_text(json.dumps(d,indent=2),encoding="utf-8")
    def stats(self):
        return json.loads(self.path.read_text(encoding="utf-8")) if self.path.exists() else {"total":0,"up":0,"down":0}
