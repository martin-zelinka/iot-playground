import requests
from typing import Literal
from requests.exceptions import Timeout, RequestException

type City = Literal["LON", "PRG", "BRN"]

def get_weather(city: City) -> float | None:
    cities = {
        "LON": (51.5074, -0.1278),
        "PRG": (50.0755, 14.4378),
        "BRN": (49.1951, 16.6068)
    }

    url = "https://api.open-meteo.com/v1/forecast"

    lat, lon = cities[city]
    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": True
    }

    try:
        response = requests.get(url, params=params, timeout=8)
        data = response.json()

        temp = data["current_weather"]["temperature"]

        return float(temp)
    except Timeout:
        print(f"{city}: Request timed out after 8 seconds")
        return None
    except RequestException as e:
        print(f"{city}: Request failed: {e}")
        return None