# Import standard packages
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Defines the LLM to use
MODEL_ID = "qwen2.5:latest"

# Construct the LLM config to pass to the agent
config_list = [
  {
    "model": MODEL_ID,
    "base_url": "http://localhost:11434/v1",
    # "api_key": "ollama",
  }
]

# Load the GIPHY API key
GIPHY_API_KEY = os.getenv("GIPHY_API_KEY")

# Instantiate the GIPHY Base URL
GIPHY_BASE_SEARCH_URL = "https://api.giphy.com/v1/gifs/search"

# Define the number of GIFs to query for
GIPHY_SEARCH_LIMIT = 20

# Define the chance of querying GIPHY
# We retrieve GIFs only when the random number falls within this limit
# Higher the value, greater the chance of generating a GIF
GIF_LOTTERY = 0.5
