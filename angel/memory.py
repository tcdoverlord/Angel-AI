from pathlib import Path
import sqlite3, datetime, re, threading

class Memory:
    def __init__(self,path=None):
        self.path=Path(path or "data/memory/angel.db")
        self.path.parent.mkdir(parents=True,exist_ok=True)
        self.db=sqlite3.connect(self.path,check_same_thread=False)
        self.lock=threading.Lock()
        with self.lock:
            self.db.execute("PRAGMA foreign_keys=ON")
            self.db.execute("CREATE TABLE IF NOT EXISTS memories(id INTEGER PRIMARY KEY, kind TEXT, text TEXT, created TEXT)")
            self.db.execute("CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY, role TEXT, text TEXT, created TEXT)")
            self.db.execute("CREATE TABLE IF NOT EXISTS conversations(id INTEGER PRIMARY KEY, title TEXT, pinned INTEGER DEFAULT 0, created TEXT, updated TEXT)")
            mcols={r[1] for r in self.db.execute("PRAGMA table_info(messages)").fetchall()}
            if "conversation_id" not in mcols:
                self.db.execute("ALTER TABLE messages ADD COLUMN conversation_id INTEGER")
            if "gpt_slug" not in mcols:
                self.db.execute("ALTER TABLE messages ADD COLUMN gpt_slug TEXT DEFAULT 'angel'")
            ccols={r[1] for r in self.db.execute("PRAGMA table_info(conversations)").fetchall()}
            if "gpt_slug" not in ccols:
                self.db.execute("ALTER TABLE conversations ADD COLUMN gpt_slug TEXT DEFAULT 'angel'")
            row=self.db.execute("SELECT id FROM conversations ORDER BY id LIMIT 1").fetchone()
            if not row:
                now=datetime.datetime.now().isoformat()
                cur=self.db.execute("INSERT INTO conversations(title,pinned,created,updated,gpt_slug) VALUES(?,?,?,?,?)",("New Chat",0,now,now,"angel"))
                cid=cur.lastrowid
            else:
                cid=row[0]
            self.db.execute("UPDATE messages SET conversation_id=? WHERE conversation_id IS NULL",(cid,))
            self.db.execute("UPDATE conversations SET gpt_slug=COALESCE(NULLIF(gpt_slug,''),'angel')")
            self.db.commit()
        self.current_id=cid

    def add(self,text,kind="fact"):
        with self.lock:
            self.db.execute("INSERT INTO memories(kind,text,created) VALUES(?,?,?)",(kind,text,datetime.datetime.now().isoformat()))
            self.db.commit()

    def search(self,query,limit=12):
        words=[w for w in re.findall(r"[\w'-]+",query.lower()) if len(w)>2]
        if not words:return self.all(limit)
        with self.lock:
            rows=self.db.execute("SELECT text FROM memories ORDER BY id DESC LIMIT 500").fetchall()
        scored=[]
        for (text,) in rows:
            low=text.lower();score=sum(low.count(w) for w in words)
            if score:scored.append((score,text))
        return [t for _,t in sorted(scored,key=lambda x:x[0],reverse=True)[:limit]]

    def all(self,limit=50):
        with self.lock:
            rows=self.db.execute("SELECT text FROM memories ORDER BY id DESC LIMIT ?",(limit,)).fetchall()
        return [r[0] for r in rows]

    def add_message(self,role,text,conversation_id=None,gpt_slug=None):
        cid=conversation_id or self.current_id
        now=datetime.datetime.now().isoformat()
        with self.lock:
            self.db.execute("INSERT INTO messages(conversation_id,role,text,created,gpt_slug) VALUES(?,?,?,?,?)",(cid,role,text,now,gpt_slug))
            self.db.execute("UPDATE conversations SET updated=? WHERE id=?",(now,cid))
            self.db.commit()

    def recent_messages(self,limit=12,conversation_id=None):
        cid=conversation_id or self.current_id
        with self.lock:
            rows=self.db.execute("SELECT role,text FROM messages WHERE conversation_id=? ORDER BY id DESC LIMIT ?",(cid,limit)).fetchall()
        return [{"role":r[0],"content":r[1]} for r in rows[::-1]]

    def new_conversation(self,title="New Chat",gpt_slug="angel"):
        now=datetime.datetime.now().isoformat()
        with self.lock:
            cur=self.db.execute("INSERT INTO conversations(title,pinned,created,updated,gpt_slug) VALUES(?,?,?,?,?)",(title or "New Chat",0,now,now,gpt_slug or "angel"))
            self.db.commit()
            self.current_id=cur.lastrowid
        return self.current_id

    def get_conversation_gpt(self,cid=None):
        cid=cid or self.current_id
        with self.lock:
            row=self.db.execute("SELECT gpt_slug FROM conversations WHERE id=?",(cid,)).fetchone()
        return row[0] if row and row[0] else "angel"

    def set_conversation_gpt(self,cid,slug):
        with self.lock:
            self.db.execute("UPDATE conversations SET gpt_slug=? WHERE id=?",(slug,cid))
            self.db.commit()

    def conversations(self):
        with self.lock:
            return self.db.execute("SELECT id,title,pinned,created,updated,gpt_slug FROM conversations ORDER BY pinned DESC, updated DESC").fetchall()

    def get_conversation(self,cid):
        with self.lock:
            return self.db.execute("SELECT id,title,pinned,created,updated,gpt_slug FROM conversations WHERE id=?",(cid,)).fetchone()

    def set_current(self,cid):
        if not self.get_conversation(cid): raise ValueError("Chat does not exist.")
        self.current_id=int(cid)

    def rename_conversation(self,cid,title):
        with self.lock:
            self.db.execute("UPDATE conversations SET title=? WHERE id=?",(title.strip() or "New Chat",cid))
            self.db.commit()

    def toggle_pin(self,cid):
        with self.lock:
            row=self.db.execute("SELECT pinned FROM conversations WHERE id=?",(cid,)).fetchone()
            if not row: raise ValueError("Chat does not exist.")
            value=0 if row[0] else 1
            self.db.execute("UPDATE conversations SET pinned=? WHERE id=?",(value,cid))
            self.db.commit()
            return bool(value)

    def delete_conversation(self,cid):
        with self.lock:
            self.db.execute("DELETE FROM messages WHERE conversation_id=?",(cid,))
            self.db.execute("DELETE FROM conversations WHERE id=?",(cid,))
            self.db.commit()
        if self.current_id==cid:
            rows=self.conversations()
            self.current_id=rows[0][0] if rows else self.new_conversation("New Chat","angel")
