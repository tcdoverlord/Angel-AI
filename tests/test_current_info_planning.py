from __future__ import annotations

from angel.brain import AngelBrain


class FakeSettings:
    def __init__(self, location: str):
        self.location = location

    def get(self):
        class S:
            pass

        s = S()
        s.location = self.location
        s.connectivity_mode = "Auto"
        s.internet_search_enabled = True
        return s


class FakeTools:
    names = {"search_web", "current_datetime"}


def make_brain(location: str) -> AngelBrain:
    brain = AngelBrain.__new__(AngelBrain)
    brain.settings = FakeSettings(location)
    brain.tools = FakeTools()
    return brain


def test_planner_recognizes_combined_weather_and_datetime():
    brain = make_brain("Test City")

    request = brain._planned_tool(
        "What is the weather, date, and time today?",
        None,
        "Test City",
        "Auto",
    )

    assert request is not None
    assert request.name == "search_web"
    assert "weather" in request.arguments["query"].lower()


def test_planner_keeps_datetime_only_local():
    brain = make_brain("")

    request = brain._planned_tool(
        "What day is it and what time is it?",
        None,
        "",
        "Auto",
    )

    assert request is not None
    assert request.name == "current_datetime"
