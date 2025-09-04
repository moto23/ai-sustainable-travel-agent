import pytest
from rasa_sdk import Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_bot.actions.actions import ActionWeatherLookup, ActionCarbonFootprint, ActionEcoRecommendations
from rasa_bot.actions.utils import extract_entity, validate_slot_value

class MockDispatcher(CollectingDispatcher):
    def __init__(self):
        self.messages = []
    def utter_message(self, text=None, **kwargs):
        self.messages.append(text)

@pytest.fixture
def tracker_with_entities():
    return Tracker(
        sender_id="test_user",
        slots={},
        latest_message={
            "entities": [
                {"entity": "location", "value": "Paris"},
                {"entity": "date", "value": "2023-09-15"},
                {"entity": "transport_type", "value": "train"}
            ]
        },
        events=[],
        paused=False,
        followup_action=None,
        active_loop={},
        latest_action_name=None
    )

def test_action_weather_lookup(tracker_with_entities):
    dispatcher = MockDispatcher()
    action = ActionWeatherLookup()
    result = action.run(dispatcher, tracker_with_entities, {})
    assert any("Weather for Paris" in msg for msg in dispatcher.messages)

def test_action_carbon_footprint(tracker_with_entities):
    dispatcher = MockDispatcher()
    action = ActionCarbonFootprint()
    result = action.run(dispatcher, tracker_with_entities, {})
    assert any("Estimated carbon footprint for train to Paris" in msg for msg in dispatcher.messages)

def test_action_eco_recommendations(tracker_with_entities):
    dispatcher = MockDispatcher()
    action = ActionEcoRecommendations()
    result = action.run(dispatcher, tracker_with_entities, {})
    assert any("eco-friendly travel tips" in msg for msg in dispatcher.messages)

def test_extract_entity(tracker_with_entities):
    assert extract_entity(tracker_with_entities, "location") == "Paris"
    assert extract_entity(tracker_with_entities, "date") == "2023-09-15"
    assert extract_entity(tracker_with_entities, "transport_type") == "train"
    assert extract_entity(tracker_with_entities, "nonexistent") is None

def test_validate_slot_value():
    assert validate_slot_value("location", "Paris")
    assert not validate_slot_value("location", None)
    assert validate_slot_value("date", "2023-09-15")
    assert not validate_slot_value("date", None)
