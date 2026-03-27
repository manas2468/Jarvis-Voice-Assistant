import os
import asyncio
import requests
import logging
from dotenv import load_dotenv
from langchain.tools import tool

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def get_current_city():
    """Detects the user's current city based on their IP address."""
    try:
        response = await asyncio.to_thread(requests.get, "https://ipinfo.io", timeout=5)
        data = response.json()
        return data.get("city", "Unknown")
    except Exception as e:
        logger.error(f"Failed to detect current city: {e}")
        return "Unknown"


@tool
async def get_weather(city: str = "") -> str:
    """
    Provides current weather information for a given city.

    Use this tool when the user asks about weather conditions, rain,
    temperature, humidity, or wind speed.
    If no city is provided, the city is detected automatically.

    Example prompts:
    - "What is the weather like today?"
    - "Tell me the weather in Bangalore."
    - "Will it rain in Mumbai?"
    """

    api_key = os.getenv("OPENWEATHER_API_KEY")

    if not api_key:
        logger.error("OpenWeather API key is missing.")
        return "The OpenWeather API key was not found in the environment variables."

    if not city:
        city = await get_current_city()

    logger.info(f"Fetching weather data for city: {city}")
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": api_key,
        "units": "metric"
    }

    try:
        response = await asyncio.to_thread(requests.get, url, params=params, timeout=5)
        if response.status_code != 200:
            logger.error(f"OpenWeather API error: {response.status_code} - {response.text}")
            return f"Unable to fetch weather data for {city}. Please verify the city name and try again."

        data = response.json()
        weather = data["weather"][0]["description"].title()
        temperature = data["main"]["temp"]
        humidity = data["main"]["humidity"]
        wind_speed = data["wind"]["speed"]

        result = (f"Weather in {city}:\n"
                  f"- Condition: {weather}\n"
                  f"- Temperature: {temperature}°C\n"
                  f"- Humidity: {humidity}%\n"
                  f"- Wind Speed: {wind_speed} m/s")

        logger.info(f"Weather result:\n{result}")
        return result

    except Exception as e:
        logger.exception(f"An exception occurred while fetching weather data: {e}")
        return "An error occurred while retrieving the weather information. Please try again later."
