from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
import json, re, sqlite3

def now():
    return datetime.now(timezone.utc).isoformat()

def slugify(value: str) -> str:
    s=re.sub(r"[^a-zA-Z0-9\s_-]","",value.strip().lower())
    return re.sub(r"[-\s]+","_",s).strip("_") or "gpt"

class GPTManager:
    DEFAULTS=[
        ("Angel","angel","Main Angel assistant.","Follow Angel's main rules, source truth, safety, provenance, and capabilities.","angel_core,technology,education,novel_baker,moonlit_storyroom,general","",1),
        ("Python Engineer","python_engineer","Python development specialist.","Focus on Python design, debugging, testing, packaging, and maintainability.","technology","python",1),
        ("Windows & PowerShell","windows_powershell","Windows and PowerShell specialist.","Focus on safe Windows administration, PowerShell, diagnostics, and automation.","technology","windows,powershell",1),
        ("Web Developer","web_developer","HTML, CSS and JavaScript specialist.","Focus on web development, responsive design, accessibility, and implementation.","technology,education","html_css,javascript",1),
        ("Database & Docker","database_docker","PostgreSQL, Docker, Linux and networking specialist.","Focus on database/application stacks, containerization and service networking.","technology","postgresql,docker,linux,networking",1),
        ("Novel Baker","novel_baker","Novel Baker specialist.","Prefer Novel Baker sources for Novel Baker questions and preserve project boundaries.","novel_baker","novel_baker",1),
        ("Moonlit Storyroom","moonlit_storyroom","Moonlit Storyroom specialist.","Prefer Moonlit Storyroom sources and preserve canon/project boundaries.","moonlit_storyroom","moonlit_storyroom",1),
        ("Math Tutor","math_tutor","K-12 mathematics specialist.","Teach step by step, show work, check results, and adapt to learner level.","education","math",1),
        ("Writing & Literature","writing_literature","Writing and literature specialist.","Focus on writing, literature, narrative craft, analysis, and source use.","education,novel_baker,moonlit_storyroom","study_skills,literature,writing",1),
    ]
    def __init__(self,root):
        self.root=Path(root); self.dir=self.root/"data"/"gpts"; self.dir.mkdir(parents=True,exist_ok=True)
        self.db_path=self.dir/"gpts.db"; self.active_path=self.dir/"active_gpt.json"
        self._schema(); self._seed()
    def _connect(self):
        c=sqlite3.connect(self.db_path); c.row_factory=sqlite3.Row; return c
    def _schema(self):
        with self._connect() as c:
            c.execute("""CREATE TABLE IF NOT EXISTS gpt_profiles(
            id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT UNIQUE NOT NULL,slug TEXT UNIQUE NOT NULL,
            description TEXT NOT NULL DEFAULT '',system_prompt TEXT NOT NULL DEFAULT '',
            domains TEXT NOT NULL DEFAULT '',topics TEXT NOT NULL DEFAULT '',
            enabled INTEGER NOT NULL DEFAULT 1,created_at TEXT NOT NULL,updated_at TEXT NOT NULL)""")
            c.commit()
    def _seed(self):
        with self._connect() as c:
            if c.execute("SELECT COUNT(*) n FROM gpt_profiles").fetchone()["n"]==0:
                t=now()
                for d in self.DEFAULTS:c.execute("""INSERT INTO gpt_profiles
                (name,slug,description,system_prompt,domains,topics,enabled,created_at,updated_at)
                VALUES(?,?,?,?,?,?,?,?,?)""",(*d,t,t))
                c.commit()
        if not self.get_active():self.set_active("angel")
    def list(self,enabled_only=False):
        q="SELECT * FROM gpt_profiles"+(" WHERE enabled=1" if enabled_only else "")+" ORDER BY name"
        with self._connect() as c:return [dict(r) for r in c.execute(q).fetchall()]
    def get(self,slug):
        with self._connect() as c:
            r=c.execute("SELECT * FROM gpt_profiles WHERE slug=?",(slug,)).fetchone()
            return dict(r) if r else None
    def create(self,name,description="",system_prompt="",domains="",topics="",enabled=True):
        t=now(); slug=slugify(name)
        with self._connect() as c:
            c.execute("""INSERT INTO gpt_profiles
            (name,slug,description,system_prompt,domains,topics,enabled,created_at,updated_at)
            VALUES(?,?,?,?,?,?,?,?,?)""",(name,slug,description,system_prompt,domains,topics,int(enabled),t,t));c.commit()
        return self.get(slug)
    def update(self,slug,**fields):
        allowed={"name","description","system_prompt","domains","topics","enabled"}
        fields={k:v for k,v in fields.items() if k in allowed}; fields["updated_at"]=now()
        sets=",".join(f"{k}=?" for k in fields); vals=list(fields.values())+[slug]
        with self._connect() as c:c.execute(f"UPDATE gpt_profiles SET {sets} WHERE slug=?",vals);c.commit()
        return self.get(slug)
    def delete(self,slug):
        if slug=="angel":raise ValueError("The main Angel GPT cannot be deleted.")
        with self._connect() as c:c.execute("DELETE FROM gpt_profiles WHERE slug=?",(slug,));c.commit()
        if not self.get_active():self.set_active("angel")
    def set_active(self,slug):
        p=self.get(slug)
        if not p or not p["enabled"]:raise ValueError("GPT unavailable or disabled.")
        self.active_path.write_text(json.dumps({"slug":slug,"updated_at":now()},indent=2),encoding="utf-8");return p
    def get_active(self):
        try:s=json.loads(self.active_path.read_text(encoding="utf-8")).get("slug","angel")
        except Exception:s="angel"
        return self.get(s) or self.get("angel")
    def backup(self):
        dest=self.dir/f"gpts_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        with self._connect() as c:c.execute("VACUUM INTO ?",(str(dest),))
        return dest
