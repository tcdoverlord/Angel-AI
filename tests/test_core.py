from pathlib import Path
from tempfile import TemporaryDirectory
from angel.config import Config
from angel.memory import Memory
from angel.files import FileManager
from angel.knowledge import KnowledgeBase
from angel.voice import Voice

def test_memory_roundtrip():
    with TemporaryDirectory() as d:
        m=Memory(Path(d)/'m.db'); m.add('Angel AI is local.'); assert 'Angel AI is local.' in m.search('Angel local')

def test_file_ingestion():
    with TemporaryDirectory() as d:
        p=Path(d)/'x.txt'; p.write_text('BLUE ANGEL 742',encoding='utf8'); f=FileManager(Path(d)/'data'); r=f.ingest(p); assert 'BLUE ANGEL 742' in r['text']

def test_knowledge():
    with TemporaryDirectory() as d:
        kb=KnowledgeBase(Path(d)/'data'); p=Path(d)/'k.md'; p.write_text('unique angel phrase 2026',encoding='utf8'); kb.add(p); assert kb.search('unique angel phrase')

def test_voice_replay_state():
    v=Voice(False); assert v.last_text==''; assert not v.speaking(); assert not v.replay()

def test_knowledge_manage_roundtrip():
    with TemporaryDirectory() as d:
        root=Path(d)/'data'; kb=KnowledgeBase(root)
        p=Path(d)/'source.md'; p.write_text('first unique knowledge',encoding='utf8')
        target=kb.add(p); assert target.exists()
        p2=Path(d)/'replacement.md'; p2.write_text('second unique knowledge',encoding='utf8')
        target2=kb.update(target,p2); assert target2.name=='replacement.md'; assert kb.search('second unique knowledge')
        kb.remove(target2); assert not kb.list_sources() or all(x['name']!='replacement.md' for x in kb.list_sources())
