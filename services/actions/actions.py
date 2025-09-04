import os
import requests
import logging
from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, FollowupAction

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

AMBIGUOUS_LOCATIONS = {
    "london": ["London, UK", "London, Ontario, Canada"],
    "washington": ["Washington, D.C., USA", "Washington State, USA"],
    "cambridge": ["Cambridge, UK", "Cambridge, Massachusetts, USA"]
}

# --- TOOL 1: Weather ---
class ActionGetWeather(Action):
    def name(self) -> Text:
        return "action_get_weather"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[Dict]:
        location = tracker.get_slot("trip_destination")
        if not location:
            dispatcher.utter_message(response="utter_ask_location")
            return []
       
        api_key = os.getenv("OPENWEATHER_API_KEY")
        if not api_key:
            dispatcher.utter_message(response="utter_api_error")
            return [SlotSet("trip_destination", None)]

        url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units=metric"
        try:
            response = requests.get(url).json()
            if response.get("cod") != 200:
                dispatcher.utter_message(response="utter_api_error")
                return [SlotSet("trip_destination", None)]

            city = response['name']
            condition = response['weather'][0]['description']
            temp = response['main']['temp']
           
            dispatcher.utter_message(response="utter_weather_report", location=city, temp=temp, condition=condition)
            dispatcher.utter_message(response="utter_suggest_after_weather", trip_destination=location)
        except Exception as e:
            logger.error(f"Weather API error: {e}")
            dispatcher.utter_message(response="utter_api_error")
       
        return [SlotSet("last_bot_suggestion", "suggested_places")]

# --- TOOL 2: Places ---
class ActionFindPlaces(Action):
    def name(self) -> Text:
        return "action_find_places"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[Dict]:
        location = tracker.get_slot("trip_destination")
        place_type = tracker.get_slot("place_type")
        preference = tracker.get_slot("user_preference")
       
        if not location:
            dispatcher.utter_message(response="utter_ask_location")
            return []
        if not place_type:
            dispatcher.utter_message(response="utter_ask_place_type", trip_destination=location)
            return []

        api_key = os.getenv("GOOGLE_PLACES_API_KEY")
        if not api_key:
            dispatcher.utter_message(response="utter_api_error")
            return [SlotSet("trip_destination", None)]
           
        query = f"{preference or ''} {place_type} in {location}".strip()
        url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={query}&key={api_key}"
        try:
            response = requests.get(url).json()
            results = response.get("results", [])
            if not results:
                dispatcher.utter_message(response="utter_no_places_found", location=location, place_type=place_type)
                return [SlotSet("user_preference", None)]

            places_list = "\n".join([f"📍 **{p.get('name')}** (Rating: {p.get('rating', 'N/A')} ⭐)" for p in results[:3]])
            dispatcher.utter_message(response="utter_places_report", location=location, place_type=place_type, places_list=places_list)
            dispatcher.utter_message(response="utter_suggest_after_places", trip_destination=location)
        except Exception as e:
            logger.error(f"Google Places API error: {e}")
            dispatcher.utter_message(response="utter_api_error")
           
        return [SlotSet("last_bot_suggestion", "suggested_weather"), SlotSet("user_preference", None)]

# --- TOOL 3: Disambiguation ---
class ActionDisambiguateLocation(Action):
    def name(self) -> Text:
        return "action_disambiguate_location"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[Dict]:
        location = next(tracker.get_latest_entity_values("location"), None)
        if location and location.lower() in AMBIGUOUS_LOCATIONS:
            options = AMBIGUOUS_LOCATIONS[location.lower()]
            options_text = "\n".join([f"- {opt}" for opt in options])
            dispatcher.utter_message(response="utter_clarify_location", disambiguation_options=options_text)
            return [SlotSet("disambiguation_options", options)]
       
        # If not ambiguous, just proceed to find the place
        return [FollowupAction("action_find_places")]