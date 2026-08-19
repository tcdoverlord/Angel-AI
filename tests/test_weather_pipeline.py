from angel.app import create_services
from angel.weather.combined import (
    asks_for_combined_current_info,
    asks_for_date_time,
    asks_for_weather,
    weather_query,
)
from angel.weather.weather_brain import WeatherBrain


def test_combined_current_information_detection():
    assert asks_for_date_time("What is the date and time?")
    assert asks_for_weather("What is the weather?")
    assert asks_for_combined_current_info("What is the weather, date and time?")


def test_current_information_separates_weather_and_clock():
    assert asks_for_date_time("What time is it?")
    assert not asks_for_weather("What time is it?")
    assert asks_for_weather("What's the forecast?")
    assert not asks_for_date_time("What's the forecast?")


def test_weather_query_adds_configured_location():
    result = weather_query("What's the weather?", "Austin, TX")
    assert "Austin, TX" in result


def test_app_uses_weather_brain():
    import inspect
    source = inspect.getsource(create_services)
    assert "WeatherBrain(" in source
    assert "brain = WeatherBrain(" in source


def test_weather_brain_preserves_angel_brain_inheritance():
    assert issubclass(WeatherBrain, __import__("angel.brain", fromlist=["AngelBrain"]).AngelBrain)
