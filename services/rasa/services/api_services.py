# rasa_bot/services/api_services.py
import os
import logging
import requests
from typing import Dict, Any, List
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class WeatherService:
    """OpenWeatherMap API integration"""

    def __init__(self):
        self.api_key = os.getenv("OPENWEATHER_API_KEY")
        self.base_url = os.getenv(
            "OPENWEATHER_BASE_URL", "https://api.openweathermap.org/data/2.5"
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def get_weather(self, location: str, days: int = 5) -> Dict[str, Any]:
        """Get weather forecast for a location"""
        try:
            # Current weather
            current_url = f"{self.base_url}/weather"
            current_params = {"q": location, "appid": self.api_key, "units": "metric"}

            current_response = requests.get(current_url, params=current_params)
            current_response.raise_for_status()
            current_data = current_response.json()

            # Forecast
            forecast_url = f"{self.base_url}/forecast"
            forecast_params = {
                "q": location,
                "appid": self.api_key,
                "units": "metric",
                "cnt": days * 8,  # 8 forecasts per day (every 3 hours)
            }

            forecast_response = requests.get(forecast_url, params=forecast_params)
            forecast_response.raise_for_status()
            forecast_data = forecast_response.json()

            return self._format_weather_data(current_data, forecast_data)

        except requests.RequestException as e:
            logger.error(f"Weather API error: {e}")
            return {"error": "Unable to fetch weather data", "location": location}

    def _format_weather_data(self, current: Dict, forecast: Dict) -> Dict[str, Any]:
        """Format weather data for travel recommendations"""
        current_weather = {
            "temperature": current["main"]["temp"],
            "feels_like": current["main"]["feels_like"],
            "humidity": current["main"]["humidity"],
            "description": current["weather"][0]["description"],
            "wind_speed": current["wind"]["speed"],
        }

        # Extract forecast highlights
        forecast_list = forecast["list"][:8]  # Next 24 hours
        avg_temp = sum(item["main"]["temp"] for item in forecast_list) / len(forecast_list)

        recommendations = self._get_weather_recommendations(current_weather, avg_temp)

        return {
            "location": current["name"],
            "current": current_weather,
            "forecast_24h": {
                "average_temp": round(avg_temp, 1),
                "conditions": [item["weather"][0]["description"] for item in forecast_list[:4]],
            },
            "travel_recommendations": recommendations,
            "last_updated": datetime.now().isoformat(),
        }

    def _get_weather_recommendations(self, current: Dict, avg_temp: float) -> List[str]:
        """Generate weather-based travel recommendations"""
        recommendations = []
        temp = current["temperature"]

        if temp < 5:
            recommendations.extend(
                [
                    "Pack warm, layered clothing",
                    "Consider indoor sustainable activities",
                    "Hot drinks from local cafes reduce energy consumption",
                ]
            )
        elif temp < 15:
            recommendations.extend(
                [
                    "Perfect weather for hiking and outdoor exploration",
                    "Ideal for walking tours and cycling",
                    "Layer clothing for temperature changes",
                ]
            )
        elif temp < 25:
            recommendations.extend(
                [
                    "Excellent weather for most outdoor activities",
                    "Great for walking and public transportation",
                    "Perfect for exploring local markets",
                ]
            )
        else:
            recommendations.extend(
                [
                    "Stay hydrated and seek shade during peak hours",
                    "Early morning and evening activities recommended",
                    "Use sun protection and light clothing",
                ]
            )

        if current["humidity"] > 80:
            recommendations.append("High humidity - choose breathable, quick-dry clothing")

        if current["wind_speed"] > 10:
            recommendations.append("Windy conditions - secure loose items and dress appropriately")

        return recommendations


class CarbonFootprintService:
    """Climatiq API integration for carbon footprint calculation"""

    def __init__(self):
        self.api_key = os.getenv("CLIMATIQ_API_KEY")
        self.base_url = os.getenv("CLIMATIQ_BASE_URL", "https://beta4.api.climatiq.io")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def calculate_flight_emissions(
        self, origin: str, destination: str, passengers: int = 1, cabin_class: str = "economy"
    ) -> Dict[str, Any]:
        """Calculate flight emissions using Climatiq API"""
        try:
            url = f"{self.base_url}/estimate"
            payload = {
                "emission_factor": {
                    "activity_id": f"passenger_flight-route_type_domestic-aircraft_type_average-distance_na-class_{cabin_class}",
                    "source": "climatiq",
                    "region": "global",
                    "year": 2023,
                },
                "parameters": {"passengers": passengers, "origin": origin, "destination": destination},
            }

            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            data = response.json()

            return self._format_emission_data(data, "flight", origin, destination)

        except requests.RequestException as e:
            logger.error(f"Carbon footprint API error: {e}")
            return self._estimate_flight_emissions_fallback(origin, destination, passengers)

    def calculate_accommodation_emissions(
        self, location: str, nights: int, hotel_type: str = "average"
    ) -> Dict[str, Any]:
        """Calculate accommodation emissions"""
        try:
            url = f"{self.base_url}/estimate"
            payload = {
                "emission_factor": {
                    "activity_id": f"accommodation-type_{hotel_type}",
                    "source": "climatiq",
                    "region": "global",
                    "year": 2023,
                },
                "parameters": {"nights": nights, "location": location},
            }

            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            data = response.json()

            return self._format_emission_data(data, "accommodation", location)

        except requests.RequestException as e:
            logger.error(f"Accommodation emissions error: {e}")
            return self._estimate_accommodation_emissions_fallback(nights, hotel_type)

    def _format_emission_data(self, data: Dict, emission_type: str, location1: str, location2: str = None) -> Dict[str, Any]:
        """Format emission data response"""
        co2_kg = data.get("co2e", 0)
        recommendations = self._get_emission_recommendations(co2_kg, emission_type)

        return {
            "emission_type": emission_type,
            "co2_kg": round(co2_kg, 2),
            "co2_tons": round(co2_kg / 1000, 3),
            "equivalent": self._get_emission_equivalent(co2_kg),
            "locations": [location1] + ([location2] if location2 else []),
            "recommendations": recommendations,
            "calculated_at": datetime.now().isoformat(),
        }

    def _estimate_flight_emissions_fallback(self, origin: str, destination: str, passengers: int) -> Dict[str, Any]:
        """Fallback flight emissions estimate"""
        base_emission = 0.255  # kg CO2 per km per passenger (rough average)
        estimated_distance = self._estimate_distance(origin, destination)
        co2_kg = estimated_distance * base_emission * passengers

        return {
            "emission_type": "flight",
            "co2_kg": round(co2_kg, 2),
            "co2_tons": round(co2_kg / 1000, 3),
            "equivalent": self._get_emission_equivalent(co2_kg),
            "locations": [origin, destination],
            "recommendations": self._get_emission_recommendations(co2_kg, "flight"),
            "calculated_at": datetime.now().isoformat(),
            "note": "Estimated using fallback calculation",
        }

    def _estimate_accommodation_emissions_fallback(self, nights: int, hotel_type: str) -> Dict[str, Any]:
        """Fallback accommodation emissions estimate"""
        emissions_per_night = {"eco_certified": 15, "average": 30, "luxury": 60}
        co2_kg = emissions_per_night.get(hotel_type, 30) * nights

        return {
            "emission_type": "accommodation",
            "co2_kg": round(co2_kg, 2),
            "co2_tons": round(co2_kg / 1000, 3),
            "equivalent": self._get_emission_equivalent(co2_kg),
            "locations": [hotel_type],
            "recommendations": self._get_emission_recommendations(co2_kg, "accommodation"),
            "calculated_at": datetime.now().isoformat(),
            "note": "Estimated using fallback calculation",
        }

    # --- Helpers ---
    def _estimate_distance(self, origin: str, destination: str) -> float:
        """Very rough distance estimate in km (stub - replace with geopy or API for accuracy)"""
        return 1000.0  # placeholder for demo purposes

    def _get_emission_equivalent(self, co2_kg: float) -> str:
        """Provide human-readable equivalents"""
        car_km = round(co2_kg / 0.120, 1)  # avg car emits 120 g/km
        trees = round(co2_kg / 21.77, 1)  # one tree absorbs ~21.77 kg CO2/year
        return f"{car_km} km driven by car, or {trees} trees absorbing CO2 for a year"

    def _get_emission_recommendations(self, co2_kg: float, emission_type: str) -> List[str]:
        """Suggest sustainability tips"""
        recs = []
        if emission_type == "flight":
            recs.append("Consider direct flights to reduce emissions")
            if co2_kg > 500:
                recs.append("Offset emissions via certified carbon offset programs")
        elif emission_type == "accommodation":
            recs.append("Choose eco-certified or green hotels")
            if co2_kg > 100:
                recs.append("Limit stays in luxury hotels to reduce footprint")
        return recs
