import asyncio
import requests
import aiohttp
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
        "current_weather": "true"
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


async def get_weather_async(city: City) -> float | None:
    """Async version of get_weather using aiohttp for concurrent requests."""
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
        "current_weather": "true"
    }

    print('geting wheather data')

    try:
        timeout = aiohttp.ClientTimeout(total=8)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, params=params) as response:
                data = await response.json()
                temp = data["current_weather"]["temperature"]
                return float(temp)
    except asyncio.TimeoutError:
        print(f"{city}: Async request timed out after 8 seconds")
        return None
    except aiohttp.ClientError as e:
        print(f"{city}: Async request failed: {e}")
        return None