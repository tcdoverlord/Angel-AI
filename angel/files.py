from pathlib import Path
import hashlib, shutil, json, datetime

class FileManager:
    TEXT_EXT={".txt",".md",".py",".ps1",".bat",".cmd",".json",".csv",".log",".ini",".cfg",".xml",".yaml",".yml",".html",".css",".js",".ts",".sql",".toml"}
    def __init__(self,root="data"):
        self.root=Path(root); self.inbox=self.root/"inbox"; self.knowledge=self.root/"knowledge"; self.index=self.root/"file_index.json"; self.inbox.mkdir(parents=True,exist_ok=True); self.knowledge.mkdir(parents=True,exist_ok=True)
    def ingest(self,path):
        p=Path(path)
        if not p.exists() or not p.is_file(): raise FileNotFoundError(str(p))
        target=self.inbox/p.name; shutil.copy2(p,target)
        try: text=p.read_text(encoding="utf-8",errors="replace")
        except Exception: text=f"Binary file: {p.name}; size={p.stat().st_size} bytes"
        digest=hashlib.sha256(p.read_bytes()).hexdigest(); record=self.knowledge/(digest+".txt"); record.write_text(text,encoding="utf-8")
        items=self._index(); items[digest]={"name":p.name,"path":str(target),"sha256":digest,"created":datetime.datetime.now().isoformat(),"chars":len(text)}; self.index.write_text(json.dumps(items,indent=2),encoding="utf-8")
        return {"name":p.name,"path":str(target),"text":text,"sha256":digest}
    def _index(self):
        try:return json.loads(self.index.read_text(encoding="utf-8"))
        except Exception:return {}
    def recent(self,limit=10): return sorted(self.inbox.iterdir(),key=lambda x:x.stat().st_mtime,reverse=True)[:limit]
