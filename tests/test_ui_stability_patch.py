from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_chat_stability_contract():
    app = (ROOT / "angel_platform" / "webui" / "app.js").read_text(encoding="utf-8")
    assert "window.angelConversationId=null;" in app
    assert "Fresh conversation started" not in app
    assert "Welcome to Just Chat" not in app
    assert "addMessage('Me',text)" in app
    assert "who==='Me'?'M':'🪽'" in app
    assert "currently opened chat blank" in app


def test_history_append_is_serialized():
    server = (ROOT / "angel_platform" / "webui" / "server.py").read_text(encoding="utf-8")
    assert "_HISTORY_LOCK = threading.RLock()" in server
    assert "with _HISTORY_LOCK:" in server
    assert "knowledge_context = context_for(message, 6)" in server
