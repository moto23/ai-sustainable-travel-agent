from typing import Dict, List

def format_current_weather(weather: Dict, location: str) -> str:
    if not weather:
        return f"Sorry, I couldn't retrieve the weather for {location}."
    desc = weather["weather"][0]["description"].capitalize()
    temp = weather["main"]["temp"]
    feels = weather["main"].get("feels_like", temp)
    humidity = weather["main"].get("humidity", "N/A")
    wind = weather["wind"].get("speed", "N/A")
    return (
        f"Right now in {location}, it's {desc} with {temp}°C (feels like {feels}°C), "
        f"humidity {humidity}%, and wind speed {wind} m/s."
    )

def format_forecast(forecast: Dict, location: str) -> str:
    if not forecast or "list" not in forecast:
        return f"Sorry, I couldn't retrieve the forecast for {location}."
    msg = f"5-day forecast for {location}:\n"
    for entry in forecast["list"][:5]:
        dt_txt = entry["dt_txt"]
        desc = entry["weather"][0]["description"].capitalize()
        temp = entry["main"]["temp"]
        msg += f"- {dt_txt}: {desc}, {temp}°C\n"
    return msg

def format_historical_weather(hist: Dict, location: str) -> str:
    if not hist or "current" not in hist:
        return f"Sorry, I couldn't retrieve historical weather for {location}."
    desc = hist["current"]["weather"][0]["description"].capitalize()
    temp = hist["current"]["temp"]
    return f"On that day in {location}, it was {desc} with a temperature of {temp}°C."

def format_alerts(alerts: List[Dict], location: str) -> str:
    if not alerts:
        return f"There are no weather alerts for {location}."
    msg = f"Weather alerts for {location}:\n"
    for alert in alerts:
        msg += f"- {alert.get('event', 'Alert')}: {alert.get('description', '')}\n"
    return msg
