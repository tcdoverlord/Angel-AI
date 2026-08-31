
from pathlib import Path
from dataclasses import dataclass, asdict
import json, re, shutil, datetime, hashlib, zipfile

@dataclass(frozen=True)
class RetrievedSource:
    source_id: str
    filename: str
    path: str
    domain: str
    topic: str
    score: int
    snippet: str

@dataclass(frozen=True)
class RetrievalManifest:
    query_id: str
    timestamp: str
    request_text: str
    provenance: str
    sources: tuple
    def filenames(self): return [s.filename for s in self.sources]

class KnowledgeBase:
    EXT={'.txt','.md','.py','.ps1','.bat','.cmd','.json','.csv','.log','.ini','.cfg','.xml','.yaml','.yml','.html','.css','.js','.ts','.sql','.toml','.jpg','.jpeg','.png'}

    EXACT_TECH={
        "01_HTML_CSS.md":"html_css","02_JavaScript.md":"javascript","03_Python.md":"python",
        "04_PowerShell.md":"powershell","05_Windows.md":"windows","06_Linux.md":"linux",
        "07_Git_GitHub.md":"git_github","08_Docker.md":"docker","09_AWS.md":"aws",
        "10_PostgreSQL.md":"postgresql","11_Networking.md":"networking","12_OBS.md":"obs",
        "13_Raspberry_Pi.md":"raspberry_pi","14_Angel_Architecture.md":"angel",
        "15_Angel_Personality.md":"angel","16_User_Interaction.md":"angel"
    }

    EDUCATION_PREFIXES=[
        ("math_","math"),("science_","science"),("english_","study_skills"),
        ("history_","history"),("us_history_","history"),("world_history_","history"),
        ("government_","civics"),("civics_","civics"),("economics_","economics"),
        ("geography_","geography"),("computer_science_","technology"),
        ("financial_literacy_","finance"),("health_wellness_","health"),
        ("physical_education_","physical_education"),("world_languages_","languages"),
        ("visual_arts_","visual_arts"),("music_","music"),("theatre_","theatre"),
        ("career_","cte"),("cte_","cte"),("study_learning_","study_skills"),("zodiac_","zodiac")
    ]

    TOPICS={
        "html_css":["html","css","html5","css3","flexbox","grid","responsive","semantic"],
        "javascript":["javascript","ecmascript","node.js","node","dom","promise","async","fetch"],
        "python":["python","pip","venv","pytest","django","flask"],
        "powershell":["powershell","power shell","ps1","cmdlet","pwsh"],
        "windows":["windows","win11","win10","registry","event viewer","task manager"],
        "linux":["linux","ubuntu","debian","bash","systemd","apt","ssh"],
        "git_github":["git","github","gitlab","commit","branch","pull request","repository"],
        "docker":["docker","container","dockerfile","compose","image","volume"],
        "aws":["aws","amazon web services","ec2","s3","iam","lambda","vpc","rds"],
        "postgresql":["postgresql","postgres","psql","rdbms"],
        "networking":["networking","network","tcp","udp","ipv4","ipv6","dns","dhcp","cidr","router","firewall"],
        "obs":["obs","obs studio","streaming","scene collection","browser source","encoder"],
        "raspberry_pi":["raspberry pi","raspberry","rpi","pi 5","pi 4"],
        "angel":["angel ai","angel architecture","angel personality","knowledge library","tts","text to speech","ollama"],
        "novel_baker":["novel baker","comic build","author intent","story architecture","governance","cognitive modules","reasoning traceability"],
        "moonlit_storyroom":["moonlit storyroom","story engine","character brain","relationship engine","heart engine","cinematic storytelling","canon and memory"],
        "math":["mathematics","math","algebra","geometry","calculus","trigonometry","statistics","probability","fractions","decimals"],
        "science":["science","biology","chemistry","physics","earth science","astronomy","scientific method"],
        "history":["history","civil war","reconstruction","world war","cold war","renaissance","imperialism"],
        "civics":["government","civics","constitution","congress","president","supreme court","election","federalism"],
        "economics":["economics","supply","demand","inflation","unemployment","fiscal policy","monetary policy"],
        "geography":["geography","population","migration","maps","resources","regions","geopolitics"],
        "finance":["financial literacy","budgeting","banking","credit","loan","interest","tax","insurance","investing","retirement"],
        "health":["health","nutrition","sleep","exercise","mental health","first aid","substance use"],
        "physical_education":["physical education","fitness","strength","cardiovascular","flexibility","sports"],
        "languages":["spanish","french","german","grammar","vocabulary","conversation","translation"],
        "visual_arts":["drawing","painting","design","art history","digital art","photography"],
        "music":["music theory","rhythm","melody","harmony","composition","music history"],
        "theatre":["theatre","drama","acting","stagecraft","scriptwriting","performance"],
        "cte":["career","trades","automotive","construction","electronics","agriculture","business","healthcare careers"],
        "study_skills":["note taking","research","time management","test preparation","critical thinking","information literacy","source evaluation"],
        "zodiac":["zodiac","aries","taurus","gemini","cancer","leo","virgo","libra","scorpio","sagittarius","capricorn","aquarius","pisces","astrology"],
    }

    def __init__(self,root,library_path=None):
        self.root=Path(root); self.default_dir=self.root/"data"/"knowledge"
        self.default_dir.mkdir(parents=True,exist_ok=True)
        self.index_path=self.root/"data"/"knowledge_index.json"
        self.manifest_path=self.root/"data"/"last_retrieval_manifest.json"
        self.backup_dir=self.root/"data"/"knowledge_backups"; self.backup_dir.mkdir(parents=True,exist_ok=True)
        self.library_path=Path(library_path) if library_path else self.default_dir; self.library_path.mkdir(parents=True,exist_ok=True)
        self._seed(); self.reindex()

    @staticmethod
    def _num(name):
        m=re.match(r"^(\d+)_",name); return int(m.group(1)) if m else None

    def _domain(self,name):
        if name in self.EXACT_TECH: return "technology"
        n=self._num(name)
        if n is not None:
            if 17<=n<=310:return "education"
            if 311<=n<=340:return "angel_core"
            if 341<=n<=377:return "novel_baker"
            if 378<=n<=603:return "moonlit_storyroom"
        low=name.lower()
        if "novel_baker" in low or "novel-baker" in low:return "novel_baker"
        if "moonlit" in low:return "moonlit_storyroom"
        if "angel" in low:return "angel_core"
        return "general"

    def _topic(self,p):
        name=p.name
        if name in self.EXACT_TECH:return self.EXACT_TECH[name]
        n=self._num(name); low=name.lower()
        if n is not None and 17<=n<=310:
            for key,topic in self.EDUCATION_PREFIXES:
                if key in low:return topic
        domain=self._domain(name)
        if domain in {"angel_core","novel_baker","moonlit_storyroom"}:return domain if domain!="angel_core" else "angel"
        # For unnumbered/general files, filename-only topic hints first; never scan entire text
        # and accidentally change a file's subject based on incidental words.
        for topic,terms in self.TOPICS.items():
            if any(term in low for term in terms): return topic
        return domain

    def _seed(self):
        p=self.default_dir/"ANGEL_LOCAL_KNOWLEDGE.md"
        if not p.exists(): p.write_text("# Angel Local Knowledge\n",encoding="utf-8")

    def files(self):
        return sorted(p for p in self.library_path.rglob("*") if p.is_file() and p.suffix.lower() in self.EXT)

    def reindex(self):
        rows=[]
        for p in self.files():
            try: text=p.read_text(encoding="utf-8",errors="replace")
            except Exception:text=""
            rows.append({"name":p.name,"path":str(p.resolve()),"relative":str(p.relative_to(self.library_path)),
                         "chars":len(text),"modified":datetime.datetime.fromtimestamp(p.stat().st_mtime).isoformat(),
                         "domain":self._domain(p.name),"topic":self._topic(p),
                         "sha256":hashlib.sha256(text.encode("utf-8")).hexdigest()})
        self.index_path.write_text(json.dumps(rows,indent=2),encoding="utf-8"); return rows

    def list_sources(self): return self.reindex()

    def read(self,path):
        p=Path(path).resolve(); lib=self.library_path.resolve()
        if p!=lib and lib not in p.parents: raise ValueError("Outside managed library.")
        return p.read_text(encoding="utf-8",errors="replace")

    def _backup(self,path,reason="change"):
        p=Path(path)
        if not p.exists() or not p.is_file(): return None
        stamp=datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        dest=self.backup_dir/f"{re.sub(r'[^A-Za-z0-9_.-]+','_',p.name)}.{stamp}.{reason}.bak"
        shutil.copy2(p,dest); return dest

    def backup_all(self): return sum(1 for p in self.files() if self._backup(p,"snapshot"))

    def add(self,path):
        p=Path(path)
        if not p.exists() or not p.is_file(): raise FileNotFoundError(str(p))
        if p.suffix.lower() not in self.EXT: raise ValueError(f"Unsupported type: {p.suffix}")
        target=self.library_path/p.name
        if target.resolve()!=p.resolve():
            if target.exists(): self._backup(target,"replace")
            shutil.copy2(p,target)
        self.reindex(); return target

    def add_many(self,paths):
        out=[]
        for p in paths:
            try:out.append(self.add(p))
            except Exception:pass
        return out

    def import_zip(self,zip_path):
        zp=Path(zip_path)
        if not zp.exists():raise FileNotFoundError(str(zp))
        out=[]
        with zipfile.ZipFile(zp) as z:
            for info in z.infolist():
                if info.is_dir():continue
                name=Path(info.filename)
                if name.is_absolute() or ".." in name.parts or name.suffix.lower() not in self.EXT:continue
                target=self.library_path.joinpath(*name.parts); target.parent.mkdir(parents=True,exist_ok=True)
                if target.exists():self._backup(target,"zip-replace")
                with z.open(info) as rf, open(target,"wb") as wf:shutil.copyfileobj(rf,wf)
                out.append(target)
        self.reindex(); return out

    def update(self,existing,path):
        old=Path(existing).resolve(); new=Path(path); lib=self.library_path.resolve()
        if old!=lib and lib not in old.parents:raise ValueError("Not managed.")
        if not new.exists():raise FileNotFoundError(str(new))
        target=old if new.name==old.name else lib/new.name
        self._backup(old,"update"); shutil.copy2(new,target)
        if target!=old and old.exists():old.unlink()
        self.reindex(); return target

    def remove(self,path):
        p=Path(path).resolve(); lib=self.library_path.resolve()
        if p!=lib and lib not in p.parents:raise ValueError("Outside managed library.")
        self._backup(p,"remove"); p.unlink(); self.reindex(); return p.name

    def _query_topics(self,q):
        out=[]
        for topic,terms in self.TOPICS.items():
            score=sum((20 if " " in t else 10) for t in terms if t in q)
            if score:out.append((score,topic))
        return sorted(out,reverse=True)

    def _domains(self,q):
        q=q.lower(); topics=[t for _,t in self._query_topics(q)]; ds=set()
        for t in topics:
            if t=="novel_baker":ds.add("novel_baker")
            elif t=="moonlit_storyroom":ds.add("moonlit_storyroom")
            elif t=="angel":ds.add("angel_core")
            elif t in {"math","science","history","civics","economics","geography","finance","health","physical_education","languages","visual_arts","music","theatre","cte","study_skills"}:ds.add("education")
            else:ds.add("technology")
        return ds

    def query_topics(self,q):
        return [topic for _,topic in self._query_topics(q)]

    @staticmethod
    def _explicit_topics(query):
        q=query.lower()
        topics=[]
        if re.search(r"\bpython\b", q):
            topics.append("python")
        if "novel baker" in q or re.search(r"\bnovel_baker\b", q):
            topics.append("novel_baker")
        if "moonlit storyroom" in q or re.search(r"\bmoonlit_storyroom\b", q):
            topics.append("moonlit_storyroom")
        if re.search(r"\bjavascript\b|\bhtml\b|\bcss\b", q):
            topics.append("javascript")
        if re.search(r"\bpowershell\b|\bwindows\b", q):
            topics.append("powershell")
        if re.search(r"\bpostgresql\b|\bpostgres\b", q):
            topics.append("postgresql")
        if re.search(r"\bdocker\b", q):
            topics.append("docker")
        if re.search(r"\blinux\b", q):
            topics.append("linux")
        return topics

    def search(self,query,limit=8,allowed_domains=None,allowed_topics=None):
        q=query.lower()
        words=[w for w in re.findall(r"[\w'-]+",q) if len(w)>2]
        requested=set(allowed_domains) if allowed_domains is not None else self._domains(q)
        explicit={x.lower() for x in (allowed_topics or []) if x.strip()}
        detected=set(self.query_topics(q))
        anchored=set(self._explicit_topics(q))
        topic_filter=explicit or anchored or detected
        results=[]
        for p in self.files():
            domain=self._domain(p.name)
            topic=self._topic(p)
            if requested and domain not in requested: continue
            if topic_filter and topic.lower() not in topic_filter: continue
            if "novel baker" in q and "moonlit storyroom" not in q and domain not in {"novel_baker","angel_core"}: continue
            if "moonlit storyroom" in q and "novel baker" not in q and domain not in {"moonlit_storyroom","angel_core"}: continue
            try:text=p.read_text(encoding="utf-8",errors="replace")
            except Exception:continue
            low=text.lower()
            score=sum(low.count(w) for w in words)+sum(35 for w in words if w in p.name.lower())
            if topic in topic_filter: score+=700
            if domain in requested: score+=150
            if score<=0:continue
            lines=text.splitlines(); matched=[]
            for i,line in enumerate(lines):
                if any(re.search(r"(?<!\w)"+re.escape(w)+r"(?!\w)",line.lower()) for w in words):
                    matched.extend(lines[max(0,i-2):min(len(lines),i+8)])
            snippet="\n".join(dict.fromkeys(matched))[:14000] if matched else text[:14000]
            sid=hashlib.sha1((str(p.resolve())+"|"+hashlib.sha256(text.encode()).hexdigest()).encode()).hexdigest()[:16]
            results.append({"source_id":sid,"name":p.name,"path":str(p.resolve()),"domain":domain,"topic":topic,"score":score,"text":snippet})
        results.sort(key=lambda x:(x["score"],x["name"]),reverse=True)
        return results[:limit]

    def retrieve(self,query,limit=8,allowed_domains=None,allowed_topics=None):
            hits=self.search(query,limit,allowed_domains,allowed_topics)
            now=datetime.datetime.now().astimezone().isoformat()
            # Retrieval alone does not establish source truth. Require meaningful
            # lexical support from the retrieved text for the query.
            qwords=[w for w in re.findall(r"[\w'-]+",query.lower()) if len(w)>2]
            stop={"what","which","that","this","tell","about","explain","give","show","does","work","with","from","only","exactly","actually","support","answer"}
            terms=[w for w in qwords if w not in stop]
            relevant=[]
            for h in hits:
                low=(h["name"]+" "+h["topic"]+" "+h["text"]).lower()
                matches=sum(1 for w in terms if re.search(r"(?<!\w)"+re.escape(w)+r"(?!\w)",low))
                anchored_topic=h.get("topic","").lower() in set(self._explicit_topics(query))
                if matches >= 1 and (matches >= 2 or anchored_topic):
                    relevant.append(h)
            sources=tuple(RetrievedSource(h["source_id"],h["name"],h["path"],h["domain"],h["topic"],h["score"],h["text"]) for h in relevant)
            prov="GROUNDED" if relevant else ("MODEL" if not hits or not terms else "MODEL")
            m=RetrievalManifest(datetime.datetime.now().strftime("%Y%m%d%H%M%S%f"),now,query,prov,sources)
            self.manifest_path.write_text(json.dumps({
                "query_id":m.query_id,"timestamp":m.timestamp,"request_text":m.request_text,
                "provenance":m.provenance,"sources":[asdict(x) for x in sources]
            },indent=2),encoding="utf-8")
            return relevant,m
