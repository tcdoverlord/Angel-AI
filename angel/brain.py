from .config import Config
from .memory import Memory
from .ollama import OllamaClient, OllamaError
from .files import FileManager
from .knowledge import KnowledgeBase
from .learning import LearningBrain
from .gpt import GPTManager
from .answer_validator import AnswerValidator
from .tools import current_datetime, weather
import re
import json

MODES = {
 'companion':'Warm, supportive, conversational and practical.',
 'focused':'Concise task mode. Prioritize action items, decisions, checklists and direct answers.',
 'creative':'Creative studio mode. Help brainstorm, write, remix and explore ideas with energy and originality.',
 'coding':'Technical engineering mode. Give precise code, diagnostics, architecture and safe step-by-step fixes.',
 'analyst':'Analysis mode. Separate facts, assumptions, evidence, risks and conclusions. Do not invent data.',
 'file analyst':'File-review mode. Base answers about supplied files on their actual contents and say when information is absent.'
}
CAPABILITIES = '''Actual application capabilities: local Ollama chat; persistent SQLite facts and conversation history; local text-file ingestion and review; a managed local knowledge library with topic-aware retrieval and add/update/remove; date/time lookup; weather lookup when internet access is available; Windows text-to-speech with replay and stop controls; selectable modes; selectable dark/light themes; local model discovery; and local Ollama startup/recovery.'''
ANGEL_SYSTEM = """You are Angel AI, a local-first desktop assistant. Be warm, intelligent, practical, direct, and honest.

SOURCE OF TRUTH:
- The application supplies the authoritative KNOWLEDGE INVENTORY and LOCAL KNOWLEDGE RETRIEVED FOR THIS REQUEST.
- A source is used for this request ONLY if it appears under LOCAL KNOWLEDGE RETRIEVED FOR THIS REQUEST.
- Never invent a filename, topic, retrieved source, memory, tool result, or file content.
- Never say a knowledge file was used merely because it exists in the inventory.
- Never confuse topics: JavaScript is not Python, Docker is not Linux, etc.
- If no local source was retrieved, say so when relevant. You may still answer from model knowledge, but distinguish it from local knowledge.
- If multiple sources are retrieved, combine them only when relevant.

GROUNDING:
- Treat retrieved local text as reference material, not as proof that every fact the model knows came from that source.
- Do not attribute facts to a source unless the retrieved text supports the attribution.
- Do not fabricate missing details to make a source appear more complete.
- When giving a recommendation or architecture derived by reasoning across sources, label it as a reasonable synthesis rather than a quotation from a file.
- If local knowledge conflicts with known technical behavior, explain the uncertainty instead of blindly attributing the error to the source.

INVENTORY:
- When asked what knowledge files are available, use the supplied KNOWLEDGE INVENTORY exactly. Do not reconstruct it from memory.
- When asked which knowledge source fits a topic, choose by topic metadata and retrieved evidence. Python questions prefer the Python source, not JavaScript.

CAPABILITIES:
Never claim internet access, computer access, memory, file access, tools, audio, or other capabilities unless the application actually supplies them. Never invent memories, file contents, knowledge facts, tool results, or live information.
When answering about an active file, prefer its actual contents. If a requested fact is absent, say so.
Persistent facts are separate from conversation history.
The application owns text-to-speech, so provide requested text normally.

ANSWER MODES:
- GROUNDED: primarily supported by retrieved local knowledge.
- MODEL: primarily general Ollama model knowledge when no relevant local source is retrieved.
- COMBINED: retrieved local knowledge plus model reasoning/general knowledge.
Do not claim the application displayed a mode unless the UI actually provides that status.

TECHNICAL HONESTY:
Use correct platform-specific commands and architecture. Do not present Linux commands as Windows PowerShell commands without explanation. Do not claim a Docker container is a Linux container; containers may run on supported hosts and multi-service applications commonly use separate containers.

Be concise unless the user asks for detail."""

class Brain:
    def __init__(self,config=None):
        self.config=config or Config.from_env()
        self.memory=Memory(self.config.root/'data/memory/angel.db')
        self.files=FileManager(self.config.root/'data')
        self.knowledge=KnowledgeBase(self.config.root/'data',self.config.knowledge_path)
        self.learning=LearningBrain(self.config.root, self.knowledge)
        self.gpts=GPTManager(self.config.root)
        self.validator=AnswerValidator()
        self.client=OllamaClient(self.config.ollama_url,self.config.timeout)
        active=self.gpts.get_active() or {}; self.current_gpt=active.get('name','Angel'); self.current_gpt_slug=active.get('slug','angel'); self.last_file=None; self.mode=self.config.mode; self.last_knowledge=[]; self.last_source_manifest=[]; self.last_manifest=None; self.last_provenance='UNKNOWN'

    def new_chat(self,title="New Chat"):
        cid=self.memory.new_conversation(title,self.current_gpt_slug); self.last_knowledge=[]; self.last_file=None; return cid
    def list_chats(self): return self.memory.conversations()
    def open_chat(self,cid):
        self.memory.set_current(cid)
        slug=self.memory.get_conversation_gpt(cid)
        profile=self.gpts.get(slug) or self.gpts.get("angel")
        if profile:
            self.current_gpt=profile["name"]; self.current_gpt_slug=profile["slug"]
        self.last_knowledge=[]; self.last_file=None
    def pin_chat(self,cid): return self.memory.toggle_pin(cid)
    def rename_chat(self,cid,title): return self.memory.rename_conversation(cid,title)
    def delete_chat(self,cid): return self.memory.delete_conversation(cid)

    def set_mode(self,mode): self.mode=mode; self.config.mode=mode; self.config.save_settings()
    def remember(self,text): self.memory.add(text); return "I'll remember that."
    def ingest_file(self,path): self.last_file=self.files.ingest(path); return self.last_file
    def add_knowledge(self,path): return self.knowledge.add(path)
    def add_knowledge_many(self,paths): return self.knowledge.add_many(paths)
    def import_knowledge_zip(self,path): return self.knowledge.import_zip(path)
    def backup_knowledge(self): return self.knowledge.backup_all()
    def list_knowledge(self): return self.knowledge.list_sources()
    def update_knowledge(self,existing,path): return self.knowledge.update(existing,path)
    def remove_knowledge(self,path): return self.knowledge.remove(path)
    def set_knowledge_path(self,path):
        p=self.knowledge.set_library_path(path); self.config.knowledge_path=str(p); self.config.save_settings(); return p



    def gpt_profiles(self):
        return self.gpts.list()

    def get_active_gpt(self):
        return self.gpts.get_active()

    def set_gpt(self, slug):
        profile=self.gpts.set_active(slug)
        self.current_gpt=profile["name"]
        self.current_gpt_slug=profile["slug"]
        try:
            self.memory.set_conversation_gpt(self.memory.current_id, profile["slug"])
        except Exception:
            pass
        return profile

    def create_gpt(self,name,description="",system_prompt="",domains="",topics="",enabled=True):
        return self.gpts.create(name,description,system_prompt,domains,topics,enabled)

    def update_gpt(self,slug,**fields):
        return self.gpts.update(slug,**fields)

    def delete_gpt(self,slug):
        return self.gpts.delete(slug)

    def learning_topics(self):
        return self.learning.list_topics()

    def learning_goals(self,status=None):
        return self.learning.list_goals(status)

    def add_learning_topic(self,name,domain="general",description="",goal=None,level="beginner",priority=0):
        return self.learning.queue_topic(name,domain,description,goal,level,priority)

    def discover_learning_topics(self):
        return self.learning.discover_and_add_topics()

    def self_learn_topic(self, topic_name, goal=None, level="beginner"):
        """Learn from retrieved local knowledge and save the result in SQLite.
        The generated note remains DERIVED knowledge until explicitly approved.
        """
        topic = self.learning.add_topic(topic_name, description="Self-learning topic")
        query = goal or f"Teach me {topic_name} from the available local knowledge at a {level} level."
        hits, manifest = self.knowledge.retrieve(query, 8)
        session_id = self.learning.create_session(topic["id"])
        self.learning.add_sources(session_id, hits)
        if not hits:
            summary = "No matching local knowledge was retrieved for this learning session."
            self.learning.finish_session(session_id, "MODEL", 0, summary)
            return {"session_id":session_id,"provenance":"MODEL","sources":[],"summary":summary}
        kb_context='\n\n'.join(
            f"SOURCE [{x['name']}] DOMAIN [{x['domain']}] TOPIC [{x['topic']}]\n{x['text']}"
            for x in hits
        )
        prompt = f"""Create a structured learning lesson for the topic: {topic_name}.
Goal: {query}

Use ONLY the retrieved local knowledge below for source-backed facts.
Do not invent files, citations, facts, commands, or source claims.
Clearly mark any reasonable synthesis as synthesis.
At the end provide:
1. What was learned
2. Key concepts
3. Practice questions
4. What remains unknown

RETRIEVED LOCAL KNOWLEDGE:
{kb_context}
"""
        try:
            answer=self.client.chat(self.config.model,[{"role":"system","content":prompt}])
            provenance="GROUNDED"
        except OllamaError as e:
            answer=f"Self-learning session could not contact Ollama: {e}"
            provenance="UNKNOWN"
        self.learning.add_note(session_id,topic["id"],answer,"lesson",provenance,False)
        self.learning.finish_session(session_id,provenance,len(hits),answer)
        return {"session_id":session_id,"provenance":provenance,"sources":manifest.filenames(),"summary":answer}

    def approve_learning_note(self, note_id):
        with self.learning._connect() as con:
            con.execute("UPDATE learned_notes SET approved=1 WHERE id=?", (note_id,))
            con.commit()
        return True

    def _tool(self,text):
        t=text.lower()
        if any(x in t for x in ['what time','what\'s the time','what is the time','what date','what day is it','date today']):
            return current_datetime()
        if 'weather' in t or 'forecast' in t or 'temperature' in t:
            return weather(self.config.location)
        return None

    def _speak_request(self,text):
        m=re.search(r'(?:say|speak|read aloud|out loud)(?:\s+this)?\s*:["“](.+?)["”]\s*$',text.strip(),re.I)
        return m.group(1) if m else None

    def _knowledge_inventory_text(self):
        items=self.list_knowledge()
        if not items: return 'No local knowledge sources are currently loaded.'
        lines=['Current Angel local knowledge sources:']
        lines += [f"{i}. {x['name']} — topic: {x['topic']} — {x['chars']:,} characters" for i,x in enumerate(items,1)]
        return '\n'.join(lines)

    def _is_inventory_request(self,text):
        t=text.lower()
        return ('what knowledge sources' in t or 'list your knowledge' in t or 'show your knowledge sources' in t
                or 'what knowledge do you have available' in t or 'list knowledge files' in t)

    @staticmethod
    def _is_source_request(text):
        q=text.lower()
        return (
            ("which" in q or "what" in q or "tell me" in q)
            and ("file" in q or "files" in q or "source" in q or "sources" in q)
            and any(term in q for term in ("retrieved","used","knowledge","local"))
        )

    @staticmethod
    def _sanitize_source_claims(answer, manifest):
        if not answer or not manifest:
            return answer
        allowed=set(manifest.filenames())
        # Remove model-generated retrieval/provenance paragraphs. The application
        # supplies the authoritative block immediately afterward.
        paragraphs=re.split(r"\n\s*\n",answer.strip())
        blocked_phrases=(
            "local knowledge file","local knowledge files","retrieved",
            "i did not retrieve","i didn't retrieve","knowledge used",
            "knowledge files retrieved","source files retrieved",
            "upon re-examining","upon reviewing the conversation"
        )
        cleaned=[]
        for para in paragraphs:
            low=para.lower()
            # Preserve ordinary prose that merely mentions the exact filename.
            if any(p in low for p in blocked_phrases):
                # Keep the paragraph only when it is clearly instructional/content
                # and does not make a retrieval claim.
                if not any(x in low for x in ("function", "python", "example", "explain")):
                    continue
            cleaned.append(para)
        text="\n\n".join(cleaned).strip()
        names=set(re.findall(r"(?<![\w-])([A-Za-z0-9_.-]+\.md)(?![\w-])",text))
        bad=names-allowed
        if bad:
            for name in bad:
                text=re.sub(rf"(?i)\b{re.escape(name)}\b","[untrusted-source-name]",text)
        return text

    @staticmethod
    def _source_truth_block(manifest):
        lines=[
            "",
            "Application Source Truth",
            f"Knowledge Status: {manifest.provenance}",
            "Knowledge Used:"
        ]
        if manifest.sources:
            for s in manifest.sources:
                lines.append(f"- {s.filename} | domain={s.domain} | topic={s.topic}")
        else:
            lines.append("- None")
        return "\n".join(lines)

    def _current_gpt_answer(self):
        profile=self.gpts.get(self.current_gpt_slug) or self.gpts.get("angel")
        name=(profile or {}).get("name","Angel")
        domains=(profile or {}).get("domains","")
        topics=(profile or {}).get("topics","")
        return f"Current specialist GPT: {name}.\nAllowed knowledge domains: {domains or '(all relevant domains)'}.\nPreferred topics: {topics or '(none specified)'}"

    def respond(self,text):
        self.memory.add_message('user',text,gpt_slug=self.current_gpt_slug)
        normalized=text.strip().lower()
        gpt_question = (
            "what gpt" in normalized
            or "which gpt" in normalized
            or "current gpt" in normalized
            or "what specialist" in normalized
            or "which specialist" in normalized
            or normalized in {"what gpt are you", "what are you", "who are you"}
        )
        if gpt_question:
            ans=self._current_gpt_answer()
            self.memory.add_message('assistant',ans,gpt_slug=self.current_gpt_slug)
            self.last_knowledge=[]; self.last_manifest=None; self.last_source_manifest=[]; self.last_provenance='MODEL'
            return ans

        capability_question = (
            "what capabilities" in normalized
            or "what can you do" in normalized
            or "your capabilities" in normalized
            or "your limitations" in normalized
            or "what are your capabilities" in normalized
        )
        if capability_question:
            ans = CAPABILITIES + "\n\nLimitations: I only use capabilities actually provided by this application. I do not invent tools, live access, files, or external actions."
            self.memory.add_message('assistant',ans,gpt_slug=self.current_gpt_slug)
            self.last_knowledge=[]; self.last_manifest=None; self.last_source_manifest=[]; self.last_provenance='MODEL'
            return ans
        m=re.match(r'(?:remember this|remember|save this)[:\s]+(.+)',text.strip(),re.I)
        if m: return self.remember(m.group(1).strip())
        speak=self._speak_request(text)
        if speak:
            self.memory.add_message('assistant',speak,gpt_slug=self.current_gpt_slug); self.last_knowledge=[]; self.last_manifest=None; self.last_provenance='MODEL'; return speak
        if self._is_inventory_request(text):
            ans=self._knowledge_inventory_text(); self.memory.add_message('assistant',ans,gpt_slug=self.current_gpt_slug); self.last_knowledge=[]; self.last_source_manifest=[]; self.last_provenance='GROUNDED'; return ans
        tool=self._tool(text)
        if tool:
            self.memory.add_message('assistant',tool,gpt_slug=self.current_gpt_slug); self.last_knowledge=[]; self.last_manifest=None; self.last_provenance='MODEL'; return tool

        memories=self.memory.search(text,12)
        file_context=''
        if self.last_file and self.last_file.get('text'):
            file_context=f"\nCURRENT ACTIVE FILE (authoritative for file questions): {self.last_file['name']}\n{self.last_file['text'][:20000]}"
        active_profile=self.gpts.get(self.current_gpt_slug) or self.gpts.get('angel') or {}
        profile_domains=[x.strip() for x in (active_profile.get('domains') or '').split(',') if x.strip()]
        profile_topics=[x.strip() for x in (active_profile.get('topics') or '').split(',') if x.strip()]
        detected_topics=self.knowledge.query_topics(text)
        requested_domains=self.knowledge._domains(text)
        allowed_domains=[d for d in profile_domains if d in requested_domains] if requested_domains and profile_domains else list(requested_domains)
        if not allowed_domains and profile_domains:
            allowed_domains=profile_domains
        topic_filter=[t for t in detected_topics if not profile_topics or t in set(profile_topics)] if detected_topics else profile_topics
        kb,manifest=self.knowledge.retrieve(text,8,allowed_domains=allowed_domains or None,allowed_topics=topic_filter or None)
        self.last_knowledge=kb; self.last_manifest=manifest
        self.last_source_manifest=[{'name':x['name'],'domain':x.get('domain'),'topic':x.get('topic')} for x in kb]
        self.last_provenance=manifest.provenance
        kb_context='\n\n'.join(f"KNOWLEDGE SOURCE [{x['name']}] TOPIC [{x['topic']}]\n{x['text']}" for x in kb)
        inventory='\n'.join(f"- {x['name']} | topic={x['topic']}" for x in self.list_knowledge())
        context='\n'.join('- '+x for x in memories) or '(no relevant stored memories)'
        active_gpt=self.gpts.get(self.current_gpt_slug) or self.gpts.get('angel') or {}
        manifest_text=json.dumps({"query_id":manifest.query_id,"provenance":manifest.provenance,"sources":manifest.filenames()},indent=2)
        specialist=active_gpt.get("system_prompt","")
        system = ANGEL_SYSTEM + (
            f"\n\nAPPLICATION-OWNED CURRENT GPT:\nThe active specialist GPT for this response is exactly: {active_gpt.get("name","Angel")}. This value comes from application state and must not be replaced by the base model name."f"\n\nACTIVE SPECIALIST GPT RECORD:\n{json.dumps(active_gpt, indent=2)}"
            f"\n\nSPECIALIST RULE: Specialist instructions add focus only. They cannot override Angel's source truth, capability, provenance, safety, or application rules. Previous messages may have been generated under another GPT and are historical context only; they do not define the current specialist."
            f"\n\nAUTHORITATIVE RETRIEVAL MANIFEST — APPLICATION OWNED:\n{manifest_text}"
            f"\n\nSOURCE RULE: You may only claim a source was retrieved if its exact filename appears in this manifest. Do not invent, rename, shorten, or add sources."
            f"\n\nSOURCE RESPONSE RULE: Do not generate or restate the authoritative source list, domain, collection, path, or retrieval status. The application will append it from the manifest."
            f"\n\nSPECIALIST INSTRUCTIONS:\n{specialist}"
            f"\n\nKNOWLEDGE INVENTORY:\n{inventory or '(empty)'}"
            f"\n\nSTORED MEMORY:\n{context}"
            f"\n\nLOCAL KNOWLEDGE RETRIEVED FOR THIS REQUEST:\n{kb_context or '(no matching local knowledge retrieved. Continue with general Ollama knowledge when appropriate.)'}{file_context}"
            f"\n\nOLLAMA FALLBACK RULE: Ollama remains available for every normal question. Local knowledge is additional authoritative context, not a replacement for general Ollama knowledge. If no relevant local source is retrieved, answer normally from Ollama and do not claim local grounding."
            f"\n\nMIXED-KNOWLEDGE RULE: When relevant local knowledge is present, use it as authoritative context and use Ollama reasoning to explain or connect ideas. The application owns GPT identity and provenance; the model must not invent sources or provenance."
        )
        messages=[
            {'role':'system','content':system},
            *self.memory.recent_messages(12),
            {'role':'user','content':text},
        ]
        try:
            answer=self.client.chat(self.config.model,messages)
        except OllamaError as e:
            answer=f"I can't reach Ollama right now. {e}"
            self.last_provenance='UNKNOWN'
            self.memory.add_message('assistant',answer,gpt_slug=self.current_gpt_slug)
            return answer
        except Exception as e:
            answer=f"I couldn't complete that request because the local AI service returned an unexpected error: {type(e).__name__}: {e}"
            self.last_provenance='UNKNOWN'
            self.memory.add_message('assistant',answer,gpt_slug=self.current_gpt_slug)
            return answer
        if not answer:
            answer="I didn't receive a response from the local model."
            self.last_provenance='UNKNOWN'
        if self._is_source_request(text) and self.last_manifest:
            answer=self._sanitize_source_claims(answer,self.last_manifest)
            answer=(answer.rstrip()+"\n"+self._source_truth_block(self.last_manifest)).strip()
        self.memory.add_message('assistant',answer,gpt_slug=self.current_gpt_slug)
        return answer
