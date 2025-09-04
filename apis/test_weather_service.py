import pytest
from apis.weather_service import WeatherAPI
from apis.weather_formatter import (
    format_current_weather, format_forecast, format_historical_weather, format_alerts
)

class MockWeatherAPI(WeatherAPI):
    def _request(self, url, params, retries=3):
        # Return mock data based on URL
        if "weather" in url:
            return {
                "weather": [{"description": "clear sky", "main": "Clear"}],
                "main": {"temp": 25, "feels_like": 26, "humidity": 50},
                "wind": {"speed": 3}
            }
        if "forecast" in url:
            return {
                "list": [
                    {"dt_txt": "2023-08-12 12:00:00", "weather": [{"description": "rain", "main": "Rain"}], "main": {"temp": 18}},
                    {"dt_txt": "2023-08-13 12:00:00", "weather": [{"description": "clear sky", "main": "Clear"}], "main": {"temp": 22}},
                ] * 3
            }
        if "timemachine" in url:
            return {"current": {"weather": [{"description": "cloudy", "main": "Clouds"}], "temp": 20}}
        if "geo" in url and "direct" in url:
            return [{"lat": 52.52, "lon": 13.405}]
        if "geo" in url and "reverse" in url:
            return [{"name": "Berlin"}]
        if "onecall" in url:
            return {"alerts": [{"event": "Storm", "description": "Heavy rain expected."}]}
        return None

def test_geocode():
    api = MockWeatherAPI()
    coords = api.geocode("Berlin")
    assert coords == (52.52, 13.405)

def test_reverse_geocode():
    api = MockWeatherAPI()
    name = api.reverse_geocode(52.52, 13.405)
    assert name == "Berlin"

def test_get_current_weather():
    api = MockWeatherAPI()
    weather = api.get_current_weather("Berlin")
    assert weather["main"]["temp"] == 25
    assert "weather" in weather

def test_get_forecast():
    api = MockWeatherAPI()
    forecast = api.get_forecast("Berlin")
    assert "list" in forecast
    assert len(forecast["list"]) > 0

def test_get_historical_weather():
    api = MockWeatherAPI()
    hist = api.get_historical_weather("Berlin", 1628764800)
    assert "current" in hist

def test_get_weather_alerts():
    api = MockWeatherAPI()
    alerts = api.get_weather_alerts("Berlin")
    assert len(alerts) > 0

def test_suitability_score():
    api = MockWeatherAPI()
    weather = api.get_current_weather("Berlin")
    score = api.suitability_score(weather, "hiking")
    assert isinstance(score, int)

def test_format_current_weather():
    api = MockWeatherAPI()
    weather = api.get_current_weather("Berlin")
    msg = format_current_weather(weather, "Berlin")
    assert "Berlin" in msg
    assert "clear sky" in msg or "Clear sky" in msg

def test_format_forecast():
    api = MockWeatherAPI()
    forecast = api.get_forecast("Berlin")
    msg = format_forecast(forecast, "Berlin")
    assert "forecast" in msg

def test_format_historical_weather():
    api = MockWeatherAPI()
    hist = api.get_historical_weather("Berlin", 1628764800)
    msg = format_historical_weather(hist, "Berlin")
    assert "cloudy" in msg or "Cloudy" in msg

def test_format_alerts():
    api = MockWeatherAPI()
    alerts = api.get_weather_alerts("Berlin")
    msg = format_alerts(alerts, "Berlin")
    assert "Storm" in msg
