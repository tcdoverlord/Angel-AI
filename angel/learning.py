from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
import sqlite3, re, json


def now():
    return datetime.now(timezone.utc).isoformat()

def slugify(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9\s_-]", "", value.strip().lower())
    return re.sub(r"[-\s]+", "_", value).strip("_") or "topic"

class LearningBrain:
    """SQLite-backed learning queue, topic discovery, sessions, and derived notes.

    Important: learned notes are derived material, not authoritative knowledge.
    They are never promoted into the managed knowledge library automatically.
    """

    def __init__(self, root: Path, knowledge):
        self.root = Path(root)
        self.db_path = self.root / "data" / "learning.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.knowledge = knowledge
        self._ensure_schema()

    def _connect(self):
        c = sqlite3.connect(self.db_path)
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA foreign_keys=ON")
        return c

    def _ensure_schema(self):
        schema_file = self.root / "data" / "learning_schema.sql"
        if not schema_file.exists():
            raise FileNotFoundError(
                f"Angel Learning schema is missing: {schema_file}"
            )
        with self._connect() as con:
            con.executescript(schema_file.read_text(encoding="utf-8-sig"))
            con.commit()

    def add_topic(self, name, domain="general", description=""):
        name = name.strip()
        slug = slugify(name)
        t = now()
        with self._connect() as con:
            row = con.execute("SELECT * FROM topics WHERE slug=?", (slug,)).fetchone()
            if row:
                con.execute("UPDATE topics SET domain=?,description=?,updated_at=? WHERE id=?",
                            (domain, description, t, row["id"]))
                return dict(con.execute("SELECT * FROM topics WHERE id=?", (row["id"],)).fetchone())
            cur = con.execute(
                "INSERT INTO topics(name,slug,domain,description,created_at,updated_at) VALUES(?,?,?,?,?,?)",
                (name, slug, domain, description, t, t))
            return dict(con.execute("SELECT * FROM topics WHERE id=?", (cur.lastrowid,)).fetchone())

    def add_alias(self, topic_id, alias):
        with self._connect() as con:
            con.execute("INSERT OR IGNORE INTO topic_aliases(topic_id,alias) VALUES(?,?)",
                        (topic_id, alias.strip()))
            con.commit()

    def add_goal(self, topic_id, goal, level="beginner", priority=0):
        t = now()
        with self._connect() as con:
            cur = con.execute(
                "INSERT INTO learning_goals(topic_id,goal,level,priority,status,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",
                (topic_id, goal, level, priority, "queued", t, t))
            return int(cur.lastrowid)

    def queue_topic(self, name, domain="general", description="", goal=None, level="beginner", priority=0):
        topic = self.add_topic(name, domain, description)
        goal_id = None
        if goal:
            goal_id = self.add_goal(topic["id"], goal, level, priority)
        return topic, goal_id

    def list_topics(self):
        with self._connect() as con:
            return [dict(r) for r in con.execute(
                "SELECT * FROM topics WHERE status='active' ORDER BY domain,name").fetchall()]

    def list_goals(self, status=None):
        q = """SELECT g.*, t.name topic_name, t.domain
               FROM learning_goals g JOIN topics t ON t.id=g.topic_id"""
        params=()
        if status:
            q += " WHERE g.status=?"
            params=(status,)
        q += " ORDER BY g.priority DESC, g.created_at"
        with self._connect() as con:
            return [dict(r) for r in con.execute(q,params).fetchall()]

    def pending_goals(self, limit=5):
        return self.list_goals("queued")[:limit]

    def update_goal_status(self, goal_id, status):
        t = now()
        completed = t if status == "completed" else None
        with self._connect() as con:
            con.execute("UPDATE learning_goals SET status=?,updated_at=?,completed_at=? WHERE id=?",
                        (status,t,completed,goal_id))
            con.commit()

    def create_session(self, topic_id, goal_id=None):
        with self._connect() as con:
            cur=con.execute(
                "INSERT INTO learning_sessions(goal_id,topic_id,started_at,status) VALUES(?,?,?,?,?)",
                (goal_id,topic_id,now(),"running"))
            return int(cur.lastrowid)

    def finish_session(self, session_id, provenance, source_count, summary, status="completed"):
        with self._connect() as con:
            con.execute("""UPDATE learning_sessions
                           SET finished_at=?,status=?,provenance=?,source_count=?,summary=?
                           WHERE id=?""",
                        (now(),status,provenance,source_count,summary,session_id))
            con.commit()

    def add_sources(self, session_id, sources):
        with self._connect() as con:
            for s in sources:
                con.execute("""INSERT OR IGNORE INTO learning_sources
                               (session_id,source_id,filename,domain,topic,score)
                               VALUES(?,?,?,?,?,?)""",
                            (session_id,s.get("source_id",""),s["name"],s.get("domain","general"),
                             s.get("topic","general"),int(s.get("score",0))))
            con.commit()

    def add_note(self, session_id, topic_id, content, note_type="lesson", provenance="COMBINED", approved=False):
        with self._connect() as con:
            cur=con.execute("""INSERT INTO learned_notes
                               (session_id,topic_id,note_type,content,provenance,approved,created_at)
                               VALUES(?,?,?,?,?,?,?)""",
                            (session_id,topic_id,note_type,content,provenance,1 if approved else 0,now()))
            return int(cur.lastrowid)

    def add_candidate(self, topic_id, title, content, session_id=None):
        with self._connect() as con:
            cur=con.execute("""INSERT INTO knowledge_candidates
                               (topic_id,title,content,source_session_id,created_at)
                               VALUES(?,?,?,?,?)""",
                            (topic_id,title,content,session_id,now()))
            return int(cur.lastrowid)

    def review(self, topic_id, confidence, review_text=""):
        with self._connect() as con:
            con.execute("INSERT INTO topic_reviews(topic_id,confidence,review_text,created_at) VALUES(?,?,?,?)",
                        (topic_id,max(0,min(100,int(confidence))),review_text,now()))
            con.commit()

    def topic_stats(self, topic_id):
        with self._connect() as con:
            notes=con.execute("SELECT COUNT(*) n FROM learned_notes WHERE topic_id=?", (topic_id,)).fetchone()["n"]
            sessions=con.execute("SELECT COUNT(*) n FROM learning_sessions WHERE topic_id=?", (topic_id,)).fetchone()["n"]
            return {"notes":notes,"sessions":sessions}

    def discover_untracked_topics(self):
        """Find indexed source topics that are not yet registered as learning topics."""
        discovered=[]
        seen=set()
        for row in self.knowledge.list_sources():
            topic=row.get("topic") or "general"
            if topic in seen or topic in {"general","angel"}:
                continue
            seen.add(topic)
            with self._connect() as con:
                existing=con.execute("SELECT 1 FROM topics WHERE slug=?", (slugify(topic),)).fetchone()
            if not existing:
                discovered.append({
                    "name":topic.replace("_"," ").title(),
                    "slug":slugify(topic),
                    "domain":row.get("domain","general"),
                    "source_name":row["name"]
                })
        return discovered

    def discover_and_add_topics(self):
        created=[]
        for item in self.discover_untracked_topics():
            created.append(self.add_topic(item["name"],item["domain"],
                                          f"Discovered from local source {item['source_name']}"))
        return created

    def backup(self):
        backup = self.db_path.with_name(f"learning_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
        with self._connect() as con:
            con.execute("VACUUM INTO ?", (str(backup),))
        return backup
