# Import standard packages
import python_weather

# Import custom packages
from src.models import (
    Weather
)

async def get_weather(city: str, country: str | None) -> Weather | str:
    """
    Function to fetch the current weather for a given location using the python_weather package.

    Args:
        city (str): The city for which to fetch the weather.
        country (str | None): The country for which to fetch the weather.
    """
    try:
        # Declare the client. The measuring unit used defaults to the metric system (celcius, km/h, etc.)
        async with python_weather.Client(unit=python_weather.IMPERIAL) as client:
            
            # Fetch a weather forecast from the specified location.
            weather = await client.get(city)
            
            return Weather(
                temperature=weather.temperature,
                condition=weather.description
            )
    
    except Exception:
        return f"Sorry, I couldn't fetch the weather for {city}, {country}."
    
    return