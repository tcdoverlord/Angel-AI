from pathlib import Path
import tempfile, shutil, sys, zipfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from angel.knowledge import KnowledgeBase
from angel.memory import Memory

root=Path(tempfile.mkdtemp(prefix="angel26-test-"))
try:
    lib=root/"knowledge"; lib.mkdir()
    (lib/"03_Python.md").write_text("# Python\nPython functions, exceptions, venv, pytest.\n",encoding="utf-8")
    (lib/"02_JavaScript.md").write_text("# JavaScript\nJavaScript promises, DOM, fetch.\n",encoding="utf-8")
    (lib/"08_Docker.md").write_text("# Docker\nDocker containers, images, volumes.\n",encoding="utf-8")
    (lib/"10_PostgreSQL.md").write_text("# PostgreSQL\nPostgreSQL SQL database and psql.\n",encoding="utf-8")
    (lib/"06_Linux.md").write_text("# Linux\nLinux Ubuntu systemd and apt.\n",encoding="utf-8")
    (lib/"11_Networking.md").write_text("# Networking\nIP DNS TCP ports firewalls.\n",encoding="utf-8")
    kb=KnowledgeBase(root,lib)
    r=kb.search("troubleshoot a Python script",8)
    assert r and r[0]["name"]=="03_Python.md", r
    assert all(x["topic"]=="python" for x in r), r
    r=kb.search("Python PostgreSQL Docker Linux networking",8)
    topics={x["topic"] for x in r}
    assert {"python","postgresql","docker","linux","networking"}.issubset(topics), (topics,r)
    z=root/"pack.zip"
    with zipfile.ZipFile(z,"w") as f:
        f.writestr("new/09_AWS.md","# AWS\nEC2 S3 IAM.\n")
        f.writestr("new/10_PostgreSQL.md","# PostgreSQL\nUpdated PostgreSQL.\n")
        f.writestr("../bad.md","bad")
    added=kb.import_zip(z)
    assert (lib/"09_AWS.md").exists()
    assert (lib/"10_PostgreSQL.md").exists()
    assert not (root/"bad.md").exists()
    assert added
    n=kb.backup_all(); assert n>=7
    # Chat persistence / pinning.
    db=root/"memory.db"; m=Memory(db)
    first=m.current_id
    m.add_message("user","hello")
    second=m.new_conversation("Python Work")
    m.add_message("assistant","ready")
    assert m.recent_messages(10,second)[0]["content"]=="ready"
    assert m.toggle_pin(second) is True
    assert any(r[0]==second and r[2]==1 for r in m.conversations())
    print("Angel 2.6 knowledge, ZIP import, backups, and chat tests: PASS")
finally:
    shutil.rmtree(root,ignore_errors=True)
