from __future__ import annotations

import pytest

from angel.recommendations import QUICK_ACTIONS, RecommendationService


def test_every_quick_action_builds_a_contextual_prompt(services):
    database, settings, _memory = services
    settings.update(city="Indianapolis", region="IN")
    service = RecommendationService(database, settings)

    for mode in QUICK_ACTIONS:
        prompt = service.build_prompt(mode)
        assert mode in prompt
        assert "Indianapolis, IN" in prompt
        assert "Recent suggestions" in prompt


def test_suggestion_history_record_and_status(services):
    database, settings, _memory = services
    service = RecommendationService(database, settings)
    suggestion_id = service.record("Build Something", "Make a 15-minute sketch.")

    recent = service.recent()
    assert recent[0]["id"] == suggestion_id
    assert recent[0]["status"] == "suggested"
    assert service.mark_latest("completed") is True
    assert service.recent()[0]["status"] == "completed"


def test_unknown_quick_action_is_rejected(services):
    database, settings, _memory = services
    with pytest.raises(ValueError):
        RecommendationService(database, settings).build_prompt("Launch Missiles")
