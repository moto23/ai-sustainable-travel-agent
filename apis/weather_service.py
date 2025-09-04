import os
import requests
import time
import logging
from typing import Dict, Any, Optional, Tuple
from functools import lru_cache

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OPENWEATHERMAP_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY", "demo-key")

class WeatherAPI:
    """
    Weather API service for travel planning using OpenWeatherMap.
    Supports current weather, 5-day forecast, historical data, geocoding, reverse geocoding, alerts, and suitability scoring.
    Includes caching, retry logic, and error handling.
    """
    BASE_URL = "https://api.openweathermap.org/data/2.5"
    GEO_URL = "http://api.openweathermap.org/geo/1.0"

    def __init__(self, api_key: str = OPENWEATHERMAP_API_KEY):
        self.api_key = api_key
        self._current_cache = {}
        self._forecast_cache = {}
        self._cache_times = {}

    def _cache_get(self, cache: dict, key: str, expiry: int) -> Optional[Any]:
        now = time.time()
        if key in cache and (now - self._cache_times.get(key, 0)) < expiry:
            return cache[key]
        return None

    def _cache_set(self, cache: dict, key: str, value: Any):
        cache[key] = value
        self._cache_times[key] = time.time()

    def _request(self, url: str, params: dict, retries: int = 3) -> Optional[dict]:
        for attempt in range(retries):
            try:
                resp = requests.get(url, params=params, timeout=10)
                resp.raise_for_status()
                return resp.json()
            except Exception as e:
                logger.warning(f"API request failed (attempt {attempt+1}): {e}")
                time.sleep(2 ** attempt)
        logger.error(f"API request failed after {retries} attempts: {url}")
        return None

    def geocode(self, location: str) -> Optional[Tuple[float, float]]:
        url = f"{self.GEO_URL}/direct"
        params = {"q": location, "limit": 1, "appid": self.api_key}
        data = self._request(url, params)
        if data and len(data) > 0:
            return data[0]["lat"], data[0]["lon"]
        return None

    def reverse_geocode(self, lat: float, lon: float) -> Optional[str]:
        url = f"{self.GEO_URL}/reverse"
        params = {"lat": lat, "lon": lon, "limit": 1, "appid": self.api_key}
        data = self._request(url, params)
        if data and len(data) > 0:
            return data[0]["name"]
        return None

    def get_current_weather(self, location: str) -> Optional[dict]:
        cache_key = f"current:{location}"
        cached = self._cache_get(self._current_cache, cache_key, 3600)
        if cached:
            return cached
        coords = self.geocode(location)
        if not coords:
            logger.error(f"Could not geocode location: {location}")
            return None
        url = f"{self.BASE_URL}/weather"
        params = {"lat": coords[0], "lon": coords[1], "appid": self.api_key, "units": "metric"}
        data = self._request(url, params)
        if data:
            self._cache_set(self._current_cache, cache_key, data)
        return data

    def get_forecast(self, location: str) -> Optional[dict]:
        cache_key = f"forecast:{location}"
        cached = self._cache_get(self._forecast_cache, cache_key, 21600)
        if cached:
            return cached
        coords = self.geocode(location)
        if not coords:
            logger.error(f"Could not geocode location: {location}")
            return None
        url = f"{self.BASE_URL}/forecast"
        params = {"lat": coords[0], "lon": coords[1], "appid": self.api_key, "units": "metric"}
        data = self._request(url, params)
        if data:
            self._cache_set(self._forecast_cache, cache_key, data)
        return data

    def get_historical_weather(self, location: str, dt: int) -> Optional[dict]:
        coords = self.geocode(location)
        if not coords:
            logger.error(f"Could not geocode location: {location}")
            return None
        url = f"{self.BASE_URL}/onecall/timemachine"
        params = {"lat": coords[0], "lon": coords[1], "dt": dt, "appid": self.api_key, "units": "metric"}
        return self._request(url, params)

    def get_weather_alerts(self, location: str) -> Optional[list]:
        coords = self.geocode(location)
        if not coords:
            logger.error(f"Could not geocode location: {location}")
            return None
        url = f"{self.BASE_URL}/onecall"
        params = {"lat": coords[0], "lon": coords[1], "appid": self.api_key, "units": "metric", "exclude": "current,minutely,hourly,daily"}
        data = self._request(url, params)
        if data and "alerts" in data:
            return data["alerts"]
        return []

    def suitability_score(self, weather: dict, activity: str) -> int:
        """
        Score weather suitability for an activity (e.g., hiking, sightseeing, beach).
        Returns 0-100.
        """
        if not weather or "main" not in weather:
            return 0
        temp = weather["main"].get("temp", 20)
        desc = weather["weather"][0]["main"].lower()
        if activity == "hiking":
            if 10 <= temp <= 25 and "rain" not in desc:
                return 90
            if "rain" in desc or temp < 5 or temp > 30:
                return 30
        if activity == "beach":
            if 22 <= temp <= 32 and "clear" in desc:
                return 95
            if temp < 18 or "rain" in desc:
                return 40
        if activity == "sightseeing":
            if 8 <= temp <= 28 and "rain" not in desc:
                return 85
            if temp < 5 or temp > 32 or "rain" in desc:
                return 35
        return 60

    def format_weather_for_conversation(self, weather: dict, location: str) -> str:
        if not weather:
            return f"Sorry, I couldn't retrieve the weather for {location}."
        desc = weather["weather"][0]["description"].capitalize()
        temp = weather["main"]["temp"]
        feels = weather["main"].get("feels_like", temp)
        humidity = weather["main"].get("humidity", "N/A")
        wind = weather["wind"].get("speed", "N/A")
        return (
            f"The current weather in {location} is {desc} with a temperature of {temp}°C (feels like {feels}°C), "
            f"humidity {humidity}%, and wind speed {wind} m/s."
        )

    def format_alerts_for_conversation(self, alerts: list, location: str) -> str:
        if not alerts:
            return f"There are no weather alerts for {location}."
        msg = f"Weather alerts for {location}:\n"
        for alert in alerts:
            msg += f"- {alert.get('event', 'Alert')}: {alert.get('description', '')}\n"
        return msg
