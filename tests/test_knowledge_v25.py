from pathlib import Path
import tempfile, shutil, sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from angel.knowledge import KnowledgeBase

root=Path(tempfile.mkdtemp(prefix="angel25-test-"))
lib=root/"knowledge"
lib.mkdir()
try:
    src=Path(__file__).resolve().parents[1] / "data" / "knowledge"
    # Create minimal domain sources for deterministic retrieval tests.
    (lib/"03_Python.md").write_text("# Python\nPython functions, exceptions, venv, pytest.\n",encoding="utf-8")
    (lib/"02_JavaScript.md").write_text("# JavaScript\nJavaScript promises, DOM, fetch.\n",encoding="utf-8")
    (lib/"08_Docker.md").write_text("# Docker\nDocker containers, images, volumes.\n",encoding="utf-8")
    (lib/"10_PostgreSQL.md").write_text("# PostgreSQL\nPostgreSQL SQL database and psql.\n",encoding="utf-8")
    (lib/"06_Linux.md").write_text("# Linux\nLinux Ubuntu systemd and apt.\n",encoding="utf-8")
    (lib/"11_Networking.md").write_text("# Networking\nIP DNS TCP ports firewalls.\n",encoding="utf-8")
    kb=KnowledgeBase(root,lib)
    r=kb.search("troubleshoot a Python script",6)
    assert r and r[0]["name"]=="03_Python.md", r
    assert all(x["topic"]=="python" for x in r), r
    r=kb.search("Python PostgreSQL Docker Linux networking",6)
    topics={x["topic"] for x in r}
    expected={"python","postgresql","docker","linux","networking"}
    assert expected.issubset(topics), (topics,r)
    print("Angel 2.5 knowledge retrieval tests: PASS")
finally:
    shutil.rmtree(root,ignore_errors=True)
