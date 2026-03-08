# Import standard packages
import random
import requests
import python_weather
from importlib.resources import files

# Import custom packages
from src.llm.models import (
    Weather
)
from src.llm.config import (
    GIPHY_API_KEY,
    GIPHY_BASE_SEARCH_URL,
    GIPHY_SEARCH_LIMIT,
    GIF_LOTTERY,
)

def load_system_prompt(prompt_file: str) -> str | None:
    """
    Load the system prompt from the given file.

    Args:
        prompt_file: The name of the prompt file to load

    Returns:
        The system prompt from the given file
    """
    
    # Load the system prompt from the given file
    try:
        return files("src.llm.prompts").joinpath(prompt_file).read_text(encoding="utf-8")
    except FileNotFoundError as e:
        print(f"Error: Prompt file {prompt_file} not found: {e}")
    except Exception as e:
        print(f"Error loading prompt file {prompt_file}: {e}")
    
    return None

async def get_weather(city: str, country: str | None) -> Weather | None:
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
    
    except Exception as e:
        print(f"Error: {e}")
    
    return

def get_gif(query: str) -> str | None:
    """
    Retrieves a randomly selected GIF URL from GIPHY matching the provided search query.

    Args:
        query (str): The search query to retrieve GIFs for

    Returns:
        str: The URL to the retrieved GIF
    """
    
    # Check to see if we should trigger GIPHY
    if random.random() < GIF_LOTTERY:
        return
    
    try:
        # Construct the query parameters
        params = {
            "api_key": GIPHY_API_KEY,
            "q": query,
            "limit": GIPHY_SEARCH_LIMIT
        }
        
        # Query the GIPHY Search API endpoint
        response = requests.get(
            url=GIPHY_BASE_SEARCH_URL,
            params=params
        )

        # Check for valid successful status
        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            return
        
        # JSONIFY the response data for easy parsing
        data = response.json().get("data", [])
        
        # Check for empty GIFs
        if not data:
            print("Error: No GIFs were returned")
            return
        
        # Retrieve ONLY the GIF URLs from the response
        # TODO: Need to type check for output validation under each GIF
        GIF_URLS = [gif["images"]["original"]["url"] for gif in data]
        
        # Rgeturn a randomly picked GIF from the response
        return random.choice(GIF_URLS)
    
    except Exception as e:
        print(f"Error: {e}")
    
    return