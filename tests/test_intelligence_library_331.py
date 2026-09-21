from angel_platform.intelligence.knowledge_loader import load_index, search_cards
def test_index_has_shared_knowledge():
    assert len(load_index()["cards"]) >= 100
def test_search_returns_cards():
    assert search_cards("Windows diagnostics")
