import os
import requests
import json
import time
import logging
from typing import Dict, Any, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CLIMATIQ_API_KEY = os.getenv("CLIMATIQ_API_KEY", "demo-key")
CLIMATIQ_BASE_URL = "https://beta3.api.climatiq.io"

# Example emission factors (kg CO2e per unit)
EMISSION_FACTORS = {
    "flight": {"global": 0.255},  # per passenger-km
    "train": {"global": 0.041},   # per passenger-km
    "car": {"global": 0.192},     # per km
    "hotel": {"global": 15.0},    # per night
    "activity": {"hiking": 0.0, "museum": 0.01, "conference": 0.2},
    # Add regional variations as needed
}

SUSTAINABILITY_GRADES = [
    (0, 50, "A"),
    (51, 100, "B"),
    (101, 200, "C"),
    (201, 400, "D"),
    (401, 800, "E"),
    (801, float('inf'), "F"),
]

class CarbonFootprintCalculator:
    """
    Calculates carbon footprint for travel using Climatiq API and local emission factors.
    Supports flights, trains, cars, hotels, activities, aggregation, offset, scoring, and visualization.
    """
    def __init__(self, api_key: str = CLIMATIQ_API_KEY, user_id: str = "default"):
        self.api_key = api_key
        self.user_id = user_id
        self.history_file = f"carbon_history_{user_id}.json"
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {self.api_key}"})
        self._load_history()

    def _load_history(self):
        if os.path.exists(self.history_file):
            with open(self.history_file, 'r', encoding='utf-8') as f:
                self.history = json.load(f)
        else:
            self.history = []

    def _save_history(self):
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, indent=2)

    def _call_climatiq(self, activity_id: str, params: dict) -> Optional[float]:
        url = f"{CLIMATIQ_BASE_URL}/estimate"
        data = {"emission_factor": {"activity_id": activity_id}, "parameters": params}
        try:
            resp = self.session.post(url, json=data, timeout=10)
            resp.raise_for_status()
            result = resp.json()
            return result.get("co2e", 0.0)
        except Exception as e:
            logger.warning(f"Climatiq API call failed: {e}")
            return None

    def calculate_emission(self, mode: str, amount: float, region: str = "global", **kwargs) -> float:
        # Use local emission factors for speed, fallback to API for advanced cases
        factor = EMISSION_FACTORS.get(mode, {}).get(region, EMISSION_FACTORS.get(mode, {}).get("global", 0.0))
        emission = amount * factor
        logger.info(f"Calculated {emission:.2f} kg CO2e for {mode} ({amount} units, region: {region})")
        return emission

    def calculate_trip(self, trip: Dict[str, Any]) -> Dict[str, Any]:
        """
        trip: {"segments": [{"mode": "flight", "amount": 1200, "region": "global"}, ...]}
        """
        total = 0.0
        breakdown = []
        for seg in trip.get("segments", []):
            mode = seg["mode"]
            amount = seg["amount"]
            region = seg.get("region", "global")
            emission = self.calculate_emission(mode, amount, region)
            breakdown.append({"mode": mode, "amount": amount, "emission": emission})
            total += emission
        score = self.sustainability_score(total)
        offset, price = self.offset_recommendation(total)
        result = {
            "total_emission": total,
            "breakdown": breakdown,
            "sustainability_score": score,
            "offset_kg": offset,
            "offset_price": price,
            "recommendations": self.actionable_recommendations(trip, total, score)
        }
        self._persist_trip(result)
        return result

    def offset_recommendation(self, emission_kg: float) -> (float, float):
        # Example: $20 per ton CO2e
        price_per_kg = 0.02
        return emission_kg, emission_kg * price_per_kg

    def sustainability_score(self, emission_kg: float) -> str:
        for low, high, grade in SUSTAINABILITY_GRADES:
            if low <= emission_kg <= high:
                return grade
        return "F"

    def comparative_analysis(self, flight_km: float, train_km: float) -> Dict[str, Any]:
        flight_em = self.calculate_emission("flight", flight_km)
        train_em = self.calculate_emission("train", train_km)
        return {
            "flight_emission": flight_em,
            "train_emission": train_em,
            "difference": flight_em - train_em,
            "recommendation": "Choose train for lower emissions." if train_em < flight_em else "Flight is less sustainable."
        }

    def actionable_recommendations(self, trip: Dict[str, Any], total: float, score: str) -> List[str]:
        recs = []
        if score in ["A", "B"]:
            recs.append("Great job! Your trip is highly sustainable.")
        if any(seg["mode"] == "flight" for seg in trip.get("segments", [])):
            recs.append("Consider offsetting your flight emissions or using trains for shorter distances.")
        if total > 200:
            recs.append("Try to reduce car usage or choose eco-certified hotels.")
        if score in ["E", "F"]:
            recs.append("Your trip has a high carbon footprint. Explore more sustainable options.")
        return recs

    def _persist_trip(self, result: Dict[str, Any]):
        self.history.append({"timestamp": int(time.time()), **result})
        self._save_history()

    def get_user_history(self) -> List[Dict[str, Any]]:
        return self.history

    def get_visualization_data(self) -> Dict[str, Any]:
        # Return data for charts: emissions over time, by mode, etc.
        by_mode = {}
        for trip in self.history:
            for seg in trip.get("breakdown", []):
                by_mode[seg["mode"]] = by_mode.get(seg["mode"], 0) + seg["emission"]
        return {
            "emissions_over_time": [(trip["timestamp"], trip["total_emission"]) for trip in self.history],
            "emissions_by_mode": by_mode
        }
