"""Backend. Calls Open-Meteo and decides which city is warmest. No web server here."""

import json
from urllib.parse import urlencode
from urllib.request import urlopen

CITIES = {
    "hyderabad": {"id": "hyderabad", "name": "Hyderabad", "latitude": 17.385, "longitude": 78.4867},
    "visakhapatnam": {"id": "visakhapatnam", "name": "Visakhapatnam", "latitude": 17.6868, "longitude": 83.2185},
    "denver": {"id": "denver", "name": "Denver", "latitude": 39.7392, "longitude": -104.9903},
    "melbourne": {"id": "melbourne", "name": "Melbourne", "latitude": -37.8136, "longitude": 144.9631},
    "delhi": {"id": "delhi", "name": "Delhi", "latitude": 28.6139, "longitude": 77.209},
}


def fetch_temperature(city):
    query = urlencode({
        "latitude": city["latitude"],
        "longitude": city["longitude"],
        "current": "temperature_2m",
    })
    url = "https://api.open-meteo.com/v1/forecast?" + query
    with urlopen(url) as response:
        data = json.load(response)
    call = {
        "call": "Backend calling Open-Meteo for " + city["name"],
        "protocol": "HTTPS",
        "method": "GET",
        "request": url,
        "response": data,
    }
    return round(data["current"]["temperature_2m"]), call


def warmest_sentence(readings):
    highest = max(reading["temperature"] for reading in readings)
    winners = [reading["name"] for reading in readings if reading["temperature"] == highest]
    degree = str(highest) + "°"

    if len(winners) == 1:
        return winners[0] + " is the warmest at " + degree + "."
    if len(winners) == 2:
        return winners[0] + " and " + winners[1] + " are tied at " + degree + "."
    return ", ".join(winners[:-1]) + ", and " + winners[-1] + " are tied at " + degree + "."


def weather_report(city_ids):
    chosen = []
    for city_id in city_ids:
        if city_id not in chosen:
            chosen.append(city_id)

    if not chosen:
        raise ValueError("Select at least one city.")

    unknown = [city_id for city_id in chosen if city_id not in CITIES]
    if unknown:
        raise ValueError("Unknown city: " + ", ".join(unknown) + ".")

    readings = []
    open_meteo = []
    for city_id in chosen:
        city = CITIES[city_id]
        temperature, call = fetch_temperature(city)
        readings.append({
            "id": city["id"],
            "name": city["name"],
            "temperature": temperature,
        })
        open_meteo.append(call)
    return {
        "requested": chosen,
        "cities": [
            {"id": reading["id"], "temperature": reading["temperature"]}
            for reading in readings
        ],
        "result": warmest_sentence(readings),
        "openMeteo": open_meteo,
    }
