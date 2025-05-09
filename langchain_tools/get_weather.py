import os
import aiohttp
import json

from dotenv import load_dotenv

from langchain_core.tools import tool

load_dotenv()

OPEN_WEATHER_API_KEY = os.getenv("OPEN_WEATHER_API_KEY")

async def fetch_weather(session, city, lang, units):
    api_url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&APPID={OPEN_WEATHER_API_KEY}&lang={lang}&units={units}"
    
    async with session.get(api_url) as response:
        return await response.text()

def convert_temperature(temp_celsius):
    if temp_celsius < 0:
        return f"영하 -{int(abs(temp_celsius))}(C)"
    else:
        return f"{temp_celsius}(C)"
    
@tool
async def get_weather(city: str) -> tuple:
    """
    Get the current weather information for a specified city.

    This tool fetches the current sky condition and temperature for the given city
    by querying a weather API. The temperature is automatically converted 
    using a helper function.

    Args:
        city (str): Name of the city to retrieve weather information for. 
                    Example: "Seoul"

    Returns:
        Tuple[str, float]: 
            - A short description of the sky condition (e.g., "clear sky", "light rain").
            - The current temperature in degrees Celsius (after conversion).
    """
    lang = 'kr'
    units = 'metric'
    
    async with aiohttp.ClientSession() as session:
        response_text = await fetch_weather(session, city, lang, units)
        result = json.loads(response_text)

    sky = result['weather'][0]['description']
    temp = convert_temperature(result['main']['temp'])
    return sky, temp

 